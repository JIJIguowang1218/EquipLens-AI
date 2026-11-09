# -*- coding: utf-8 -*-
"""W1 网页检索冒烟测试：10 条查询 × 360 × 下载/门卫/视角。

用法:
  PYTHONPATH=src python scripts/retrieval_web_smoke.py --limit 8 \
      --out data-test/runs/web-smoke-20261109
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image  # noqa: E402

from equiplens import gate, imagesearch  # noqa: E402

QUERIES = [
    ("豪沃 6X6 侧视", "豪沃 6X6"),
    ("豪沃 6X6 前脸", "豪沃 6X6"),
    ("德龙 X3000 侧视", "德龙X3000"),
    ("德龙 X3000 前脸", "德龙X3000"),
    ("汕德卡 C7H 侧视", "汕德卡C7H"),
    ("汕德卡 C7H 前脸", "汕德卡C7H"),
    ("解放 J6G 侧视", "解放J6G"),
    ("解放 J6G 前脸", "解放J6G"),
    ("北奔 NG80 侧视", "北奔NG80"),
    ("北奔 NG80 前脸", "北奔NG80"),
]

def slug(s: str) -> str:
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", s).strip("-")
    return s[:40] or "q"


def download_one(hit: dict) -> dict:
    out = {"hit": hit, "ok": False, "gate": None, "view": "", "width": 0,
           "height": 0, "error": ""}
    try:
        r = imagesearch._download_and_gate(hit)
        if r.get("error") or not r.get("data"):
            out["error"] = r.get("error") or "no_data"
            return out
        data = r["data"]
        pre = r.get("prefilter") or gate.prefilter(data)
        out["prefilter"] = pre
        out["width"], out["height"] = pre["width"], pre["height"]
        out["gate"] = r.get("gate") or {}
        out["ok"] = bool(out["gate"].get("pass"))
        out["scene"] = out["gate"].get("scene", "")
        out["margin"] = out["gate"].get("margin", 0)
        if pre["ok"]:
            view_result = gate.classify_view(data)
            out["view"] = view_result.get("view", "")
            out["view_gap"] = view_result.get("gap", 0)
        else:
            # 第一段已否决：不进 CLIP、不跑视角
            view_result = {}
        # 分层判定复用已算好的两段结果，避免同一张图重复编码
        a = gate.assess_from_gate(out["gate"], view_result,
                                  out["width"], out["height"],
                                  prefilter_result=pre)
        out["stage"] = a["stage"]
        out["gate_skipped"] = a["gate_skipped"]
        out["overview_ok"] = a["overview_candidate"]
        out["part_ok"] = a["part_candidate"]
        out["reference_ok"] = a["reference_candidate"]
        out["upgraded"] = bool(r.get("upgraded"))
        out["exterior_hint"] = a["exterior_hint"]
        out["reasons"] = a["reasons"]
        out["hints"] = a["hints"]
        # 兼容旧口径：部件可用 + 视角落在外观（仅提示，不否决）
        out["usable"] = a["part_candidate"] and a["exterior_hint"]
        out["_data"] = data
        return out
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}: {e}"
        return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="W1 web retrieval smoke")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--out", default="data-test/runs/web-smoke-20261109")
    parser.add_argument("--max-queries", type=int, default=0)
    parser.add_argument("--harvest", type=int, default=0,
                        help="回访前 N 个来源页（文章/图集），抽整页图片")
    args = parser.parse_args(argv)

    queries = QUERIES[:args.max_queries] if args.max_queries else QUERIES
    out_dir = Path(args.out)
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    report = {"batch_id": out_dir.name, "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
              "stage": "mid-retrieval", "module": "web-smoke",
              "test": "W1-HD" if "hd" in out_dir.name else "W1-baseline",
              "source": "360", "limit": args.limit, "queries": []}
    t0 = time.time()

    for qi, (query, model) in enumerate(queries, 1):
        try:
            hits, diag = imagesearch.search_images_hd(
                query, limit=args.limit, model=model, hd=True,
                harvest=args.harvest)
        except Exception as e:  # noqa: BLE001
            hits, diag = [], [{"channel": "error", "status": f"error:{e}"}]
        # search_images_hd 的 diag 是 [{query, channels}]；拍平成通道诊断
        if diag and isinstance(diag[0], dict) and "channels" in diag[0]:
            channel_diag = [c for entry in diag for c in (entry.get("channels") or [])]
        else:
            channel_diag = diag
        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(download_one, hits))
        rows = []
        for ri, r in enumerate(results, 1):
            hit = r["hit"]
            row = {"index": ri, "title": hit.get("title", ""),
                   "url": hit.get("url", ""), "channel": hit.get("channel", ""),
                   "source_url": hit.get("source_url", ""),
                   "download_ok": not bool(r["error"]), "gate_pass": r["ok"],
                   "usable": bool(r.get("usable")),
                   "overview_ok": bool(r.get("overview_ok")),
                   "part_ok": bool(r.get("part_ok")),
                   "reference_ok": bool(r.get("reference_ok")),
                   "upgraded": bool(r.get("upgraded")),
                   "exterior_hint": bool(r.get("exterior_hint")),
                   "scene": r.get("scene", ""), "margin": r.get("margin", 0),
                   "view": r["view"], "view_gap": r.get("view_gap", 0),
                   "width": r["width"], "height": r["height"],
                   "stage": r.get("stage", ""),
                   "gate_skipped": bool(r.get("gate_skipped")),
                   "reasons": r.get("reasons", []),
                   "hints": r.get("hints", []),
                   "error": r["error"]}
            if r["ok"] and r.get("_data"):
                name = f"{qi:02d}-{slug(model)}-{ri:02d}.jpg"
                Image.open(BytesIO(r["_data"])).convert("RGB").save(
                    img_dir / name, "JPEG", quality=88)
                row["image"] = f"images/{name}"
            rows.append(row)
        gated = sum(1 for r in rows if r["gate_pass"])
        report["queries"].append({"query": query, "model": model,
                                  "hits": len(hits), "gated": gated,
                                  "diag": channel_diag, "rows": rows})
        print(f"[{qi}/{len(queries)}] hits={len(hits)} gated={gated} "
              f"query={query}")
        time.sleep(imagesearch.SLEEP_SECONDS)

    all_rows = [r for q in report["queries"] for r in q["rows"]]
    n = max(1, len(all_rows))
    report["summary"] = {
        "queries": len(report["queries"]),
        "hits": len(all_rows),
        "download_ok": sum(1 for r in all_rows if r["download_ok"]),
        "gated": sum(1 for r in all_rows if r["gate_pass"]),
        "gate_rate": round(sum(1 for r in all_rows if r["gate_pass"]) / n, 3),
        # 分层口径：概览可用（≥800）/ 部件可用（≥1200）/ 旧口径（部件+外观提示）
        "overview_ok": sum(1 for r in all_rows if r.get("overview_ok")),
        "part_ok": sum(1 for r in all_rows if r.get("part_ok")),
        "exterior_hint": sum(1 for r in all_rows if r.get("exterior_hint")),
        "reference_ok": sum(1 for r in all_rows if r.get("reference_ok")),
        "upgraded": sum(1 for r in all_rows if r.get("upgraded")),
        "usable": sum(1 for r in all_rows if r.get("usable")),
        "usable_rate": round(sum(1 for r in all_rows if r.get("usable")) / n, 3),
        "width_ge_800": sum(1 for r in all_rows if r["width"] >= 800),
        "width_ge_1200": sum(1 for r in all_rows if r["width"] >= 1200),
        # 两段式：第一段拦下的图不进 CLIP，clip_runs 才是实际推理次数
        "prefilter_blocked": sum(1 for r in all_rows
                                 if r.get("stage") == "prefilter"),
        "clip_runs": sum(1 for r in all_rows if r.get("stage") == "gate"),
        "seconds": round(time.time() - t0, 1),
        "gate_labels": f"{gate.GATE_LABEL_VERSION} "
                        "(2026-11-09: +interior/collage/screenshot/ad)",
        "channels": {},
    }
    for r in all_rows:
        ch = r["channel"] or "?"
        report["summary"]["channels"][ch] = \
            report["summary"]["channels"].get(ch, 0) + 1

    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "meta.json").write_text(json.dumps({
        "batch_id": report["batch_id"], "stage": report["stage"],
        "module": report["module"], "test": report["test"],
        "date": report["started_at"][:10], "source": "360",
        "limit_per_query": args.limit, "queries": len(report["queries"]),
        "gate_labels": report["summary"].get("gate_labels"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(render_md(report), encoding="utf-8")
    (out_dir / "review.html").write_text(render_html(report), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=1))
    print(f"out: {out_dir}")
    return 0


def render_md(report: dict) -> str:
    s = report["summary"]
    lines = [
        "# W1 网页检索冒烟测试（360）", "",
        f"- 开始：{report['started_at']}",
        f"- 门卫标签集：{s.get('gate_labels', 'legacy')}",
        f"- 查询数：{s['queries']}；候选：{s['hits']}；下载成功：{s['download_ok']}；"
        f"门卫通过：{s['gated']}（{s['gate_rate']:.0%}）",
        f"- **概览可用**（门卫+长边≥800+非拼图）：{s.get('overview_ok', 0)}；"
        f"**部件可用**（≥1200）：{s.get('part_ok', 0)}；"
        f"参考层：{s.get('reference_ok', 0)}；升图 {s.get('upgraded', 0)}；"
        f"外观提示：{s.get('exterior_hint', 0)}；"
        f"旧口径（部件+外观提示）：{s.get('usable', 0)}",
        f"- 长边≥800：{s.get('width_ge_800', 0)}；≥1200：{s['width_ge_1200']}",
        f"- 两段式：预筛拦下 {s.get('prefilter_blocked', 0)} 张（未进 CLIP）；"
        f"实际跑 CLIP {s.get('clip_runs', 0)} 次",
        f"- 耗时：{s['seconds']}s；通道分布：{s['channels']}", "",
        "| # | 查询 | 命中 | 门卫通过 | 概览可用 | 部件可用 | 备注 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for i, q in enumerate(report["queries"], 1):
        blocked = [d for d in q["diag"] if str(d.get("status")).startswith("blocked")]
        note = "blocked: " + ",".join(d["channel"] for d in blocked) if blocked else ""
        lines.append(f"| {i} | {q['query']} | {q['hits']} | {q['gated']} | "
                     f"{sum(1 for r in q['rows'] if r.get('overview_ok'))} | "
                     f"{sum(1 for r in q['rows'] if r.get('part_ok'))} | {note} |")
    lines += ["", "## 明细（门卫通过）", "",
              "| 查询 | 文件名 | 视角(gap) | 尺寸 | 概览/部件 | 否决理由 | 提示 | 标题 |",
              "|---|---|---|---:|---|---|---|---|"]
    for q in report["queries"]:
        for r in q["rows"]:
            if r["gate_pass"]:
                flag = ("概览" if r.get("overview_ok") else "-") + "/" + \
                       ("部件" if r.get("part_ok") else "-")
                lines.append(
                    f"| {q['query']} | {r.get('image','')} | {r['view']}"
                    f"({r.get('view_gap', 0)}) | "
                    f"{r['width']}×{r['height']} | {flag} | "
                    f"{','.join(r.get('reasons', []))} | "
                    f"{','.join(r.get('hints', []))} | {r['title'][:50]} |")
    lines += ["", "## 说明", "",
              "- 门卫通过 = 标签集 v3 判为单台工程车；不等于“型号身份正确”。",
              "- 概览可用/部件可用是两层分辨率口径，**不再用视角当硬门槛**：",
              "  视角 top1−top2 实测中位数 ~0.003，只作提示。",
              "- 网页结果只算 `candidate`，不能直接当可信证据。"]
    return "\n".join(lines) + "\n"


def render_html(report: dict) -> str:
    cards = []
    for q in report["queries"]:
        for r in q["rows"]:
            if not r["gate_pass"]:
                continue
            src = html.escape(r.get("image", ""))
            flag = ("概览" if r.get("overview_ok") else "—") + " / " + \
                   ("部件" if r.get("part_ok") else "—")
            cards.append(
                f"<figure><img src='{src}' loading='lazy'>"
                f"<figcaption><b>{html.escape(q['query'])}</b><br>"
                f"{html.escape(r['view'])} (gap {r.get('view_gap', 0)}) · "
                f"{r['width']}×{r['height']}<br>"
                f"<span class='tier'>{flag}</span><br>"
                f"{html.escape(r['title'][:80])}</figcaption></figure>")
    s = report["summary"]
    return f"""<!doctype html><meta charset="utf-8">
<title>W1 web smoke</title>
<style>
body{{font:14px/1.5 system-ui;margin:24px;background:#111;color:#eee}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}
figure{{margin:0;background:#1b1b1b;border:1px solid #333;border-radius:8px;overflow:hidden}}
img{{width:100%;height:180px;object-fit:cover;display:block}}
figcaption{{padding:8px;font-size:12px;color:#bbb}}
.tier{{color:#b8f0b8}}
</style>
<h1>W1 网页检索冒烟测试（360）</h1>
<p>查询 {s['queries']} · 候选 {s['hits']} · 门卫通过 {s['gated']}（{s['gate_rate']:.0%}） ·
概览可用 {s.get('overview_ok', 0)} · 部件可用 {s.get('part_ok', 0)} ·
外观提示 {s.get('exterior_hint', 0)} · {s['seconds']}s</p>
<p>视角只作提示，不作硬门槛（top1−top2 中位数 ~0.003）。</p>
<div class="grid">{''.join(cards)}</div>"""


if __name__ == "__main__":
    raise SystemExit(main())
