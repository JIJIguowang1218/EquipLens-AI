# -*- coding: utf-8 -*-
"""A/B 清单实图核对：用真实 `imagesearch` 模块给两臂清单逐车型搜图，生成审核页。

只调用 `equiplens.imagesearch.search_images_ex`（360→百度→Bing 多通道 + 相关性护栏），
不在脚本里另起炉灶；通道被拦/不相关由模块如实返回，本脚本只记录与展示。

用法:
    PYTHONPATH=src python scripts/ab_image_crawl.py [--per-model 4]
输出:
    data-test/ab-images/<序号>-<车型slug>/*.jpg
    data-test/ab-images/manifest.json     # 每车型：图、搜图标题、通道诊断
    data-test/ab-images/review.html
    data-test/ab-images/verdicts.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AB = ROOT / "data-test" / "evals" / "ab-20261031"
OUT = ROOT / "data-test" / "ab-images"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def _norm(s: str) -> str:
    t = str(s).lower().replace("×", "x")
    return "".join(ch for ch in t if not ch.isspace() and ch not in "-_*·/()（）")


def _slug(s: str) -> str:
    return (re.sub(r"[^\w\u4e00-\u9fff]+", "-", s).strip("-")[:40] or "model")


def parse_a(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| ---") or "序号" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        rows.append({"arm": "a", "model": cells[1], "tier": cells[2],
                     "strength": cells[3], "url": cells[4]})
    return rows


def parse_b(path: Path) -> list[dict]:
    d = json.loads(path.read_text(encoding="utf-8"))
    out = []
    for t in d["targets"]:
        if not t.get("slots"):
            continue
        ev = (t.get("evidence") or [{}])[0]
        out.append({"arm": "b", "model": " / ".join(t.get("models") or []),
                    "tier": t.get("tier"),
                    "strength": "弱" if t.get("relevance_strength") == "weak" else "强",
                    "url": ev.get("url", "")})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-model", type=int, default=4)
    a = ap.parse_args(argv)

    from equiplens import gate
    from equiplens.imagesearch import search_model_images

    rows = parse_a(AB / "armA3-c01.md") + parse_b(AB / "armB3-c01.json")
    models: dict[str, dict] = {}
    for r in rows:
        k = _norm(r["model"])
        m = models.setdefault(k, {"model": r["model"], "a": False, "b": False,
                                  "tier": r["tier"], "strength": r["strength"],
                                  "url": r["url"]})
        m[r["arm"]] = True

    OUT.mkdir(parents=True, exist_ok=True)
    manifest = []
    for i, (_, meta) in enumerate(models.items(), 1):
        d = OUT / f"{i:02d}-{_slug(meta['model'])}"
        d.mkdir(exist_ok=True)
        hits, diag = search_model_images(meta["model"], max(a.per_model * 3, 12))
        saved, gate_log, saved_meta = [], [], []
        for h in hits:
            if len(saved) >= a.per_model:
                break
            try:
                import requests as _rq
                src = h.get("thumb_url") or h["url"]
                rz = _rq.get(src, headers={"User-Agent": UA, "Referer": "https://image.so.com/"},
                             timeout=20)
                if rz.status_code != 200 or len(rz.content) < 8000:
                    continue
                g = gate.check_exterior(rz.content)
            except Exception as e:  # noqa: BLE001
                gate_log.append({"title": h.get("title", "")[:40],
                                 "gate": f"error:{type(e).__name__}"})
                continue
            gate_log.append({"title": h.get("title", "")[:40], "pass": g.get("pass"),
                             "margin": g.get("margin"),
                             "drop": (g.get("drop_label") or "")[:30],
                             "view": g.get("view"), "reason": g.get("reason")})
            if not (g.get("pass") and g.get("exterior")):
                continue  # 门卫判废 / 非整车外观（内饰、局部特写）：不落盘
            n = len(saved) + 1
            fp = d / f"{n}.jpg"
            fp.write_bytes(rz.content)
            saved.append(f"{d.name}/{fp.name}")
            saved_meta.append({"file": f"{d.name}/{fp.name}",
                               "title": h.get("title", ""), "url": h.get("url", ""),
                               "channel": h.get("channel", ""),
                               "margin": g.get("margin")})
        for old in d.glob("*.jpg"):  # 清理上一轮多出来的图
            if int(old.stem) > len(saved):
                old.unlink(missing_ok=True)
        meta["gate_log"] = gate_log
        meta["images"] = saved
        meta["hits"] = saved_meta
        meta["diag"] = diag
        manifest.append(meta)
        print(f"[{i}/{len(models)}] {meta['model']}: 搜到 {len(hits)} / 存 {len(saved)} "
              f"/ 查询 {[d['query'] for d in diag]}")

    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    with (OUT / "verdicts.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["序号", "清单里的车型", "A提出", "B提出", "人类判定(对/部分/错)", "备注"])
        for i, m in enumerate(manifest, 1):
            w.writerow([i, m["model"], "Y" if m["a"] else "", "Y" if m["b"] else "", "", ""])

    h = ["<!doctype html><html lang='zh'><head><meta charset='utf-8'>",
         "<title>A/B 清单实图核对</title><style>",
         "body{font:14px/1.6 -apple-system,'Segoe UI','Microsoft YaHei',sans-serif;margin:20px;background:#fafafa}",
         "h1{font-size:19px;margin:0 0 4px}.sub{color:#666;margin-bottom:14px}",
         ".row{background:#fff;border:1px solid #e3e3e3;border-radius:10px;padding:12px;margin-bottom:14px}",
         ".hd{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap}.m{font-weight:700;font-size:15px}",
         ".tag{font-size:12px;padding:1px 8px;border-radius:10px;background:#eef2ff;color:#334}",
         ".tag.a{background:#e6f4ea;color:#1a6b34}.tag.b{background:#e8f0fe;color:#1a3d8f}",
         ".tag.w{background:#fff3e0;color:#8a4b00}.tag.d{background:#f3f4f6;color:#555}",
         "a{color:#1558c0;text-decoration:none;font-size:12px}",
         ".imgs{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}",
         ".imgs figure{margin:0;width:250px}.imgs img{width:250px;height:180px;object-fit:cover;border-radius:6px;background:#eee}",
         "figcaption{font-size:11px;color:#777}", "</style></head><body>",
         "<h1>A/B 清单实图核对</h1>",
         f"<div class='sub'>共 {len(manifest)} 个车型 · 图由 imagesearch（360/百度/Bing 多通道）实时抓取 · "
         "判定填 verdicts.csv</div>"]
    for i, m in enumerate(manifest, 1):
        tags = []
        if m["a"]:
            tags.append("<span class='tag a'>A 提出</span>")
        if m["b"]:
            tags.append("<span class='tag b'>B 提出</span>")
        tags.append(f"<span class='tag'>{m['tier']} · {m['strength']}</span>")
        if str(m["strength"]).startswith("弱"):
            tags.append("<span class='tag w'>弱关联</span>")
        dg = "；".join(
            f"{q['query']}: " + "/".join(f"{c['channel']} {c['relevant']}/{c['returned']}"
                                         for c in q["channels"])
            for q in m.get("diag", []))
        tags.append(f"<span class='tag d'>{dg}</span>")
        h.append("<div class='row'><div class='hd'>"
                 f"<span class='m'>{i}. {m['model']}</span>{''.join(tags)}"
                 f"<a href='{m['url']}' target='_blank'>清单证据页</a></div><div class='imgs'>")
        for j, rel in enumerate(m.get("images", []), 1):
            t = (m.get("hits") or [{}] * j)[j - 1].get("title", "") if j <= len(m.get("hits") or []) else ""
            h.append(f"<figure><img src='{rel}'><figcaption>{j}. {t[:38]}</figcaption></figure>")
        if not m.get("images"):
            h.append("<div style='color:#b00'>未抓到图（通道被拦或不相关，见右侧诊断）</div>")
        h.append("</div></div>")
    h.append("</body></html>")
    (OUT / "review.html").write_text("\n".join(h), encoding="utf-8")
    print(f"\n→ {OUT/'review.html'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
