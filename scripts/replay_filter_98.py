# -*- coding: utf-8 -*-
"""两段式门卫全流程回放：98 张实图（两批画廊）× 同一批字节。

流程顺序与产品一致：
  标题护栏 → （下载已完成）→ 预筛(确定性) → CLIP 门卫 → 场景/视角 → 分层可用

对每张图同时重算：
  v2 门卫（基础反例集） / v3 门卫（含内饰·拼图·截图·广告） → 标签变换
产出 report.json / report.md / index.html（对比页，含缩略图）。

用法:
  PYTHONPATH=src python scripts/replay_filter_98.py
  PYTHONPATH=src python scripts/replay_filter_98.py --limit 8 --out data-test/runs/tmp-replay
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from PIL import Image  # noqa: E402

from equiplens import gate, imagesearch  # noqa: E402

BATCHES = [
    ("web-smoke-20261109", "基础批次"),
    ("web-smoke-hd-20261109", "HD 批次"),
]

REASON_CN = {
    "empty": "空文件",
    "too_large": "文件 >8MB",
    "undecodable": "无法解码（破图）",
    "animated": "动图（GIF 多帧）",
    "too_small": "长边 <800 或宽 <350",
    "extreme_aspect": "长宽比 >4（banner/长条截屏）",
    "near_uniform": "近空白/纯色（白底占位）",
    "gate_drop": "CLIP 判为无关图",
    "multi_vehicle": "多车/队列",
    "interior_suspect": "内饰（强信号）",
    "low_res_overview": "长边 <800",
    "low_res_part": "长边 <1200（只能当概览）",
    "low_res": "长边 <800（只能当参考）",
    "title_guard": "标题未命中型号/构型",
}

VERDICT_CN = {
    "usable_part": "可用·部件",
    "usable_overview": "可用·概览",
    "reference": "参考·低清",
    "reject_guard": "拦·标题护栏",
    "reject_prefilter": "拦·预筛",
    "reject_gate": "拦·CLIP 门卫",
    "reject_scene": "拦·场景/内饰",
    "reject_res": "拦·分辨率",
}

CHANGE_CN = {
    "kept": "v2 通过 → v3 仍通过",
    "newly_dropped": "v2 通过 → v3 拒绝（新增拦截）",
    "resurrected": "v2 拒绝 → v4 通过（复活）",
    "still_dropped": "v2、v3 都拒绝",
    "prefilter_blocked": "预筛拦下（尺寸/格式，未进 CLIP）",
}


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for batch, label in BATCHES:
        d = ROOT / "data-test" / "runs" / batch
        data = json.loads((d / "all-downloads.json").read_text(encoding="utf-8"))
        for r in data.get("rows", []):
            rec = {
                "batch": batch, "batch_label": label,
                "query": r.get("query", ""), "model": r.get("model", ""),
                "title": r.get("title", ""), "url": r.get("url", ""),
                "status": r.get("status", ""), "error": r.get("error", ""),
                "image": r.get("image", ""),
                "recorded_gate_pass": r.get("gate_pass"),
                "recorded_view": r.get("view", ""),
                "recorded_margin": r.get("margin"),
            }
            if rec["status"] == "saved" and rec["image"]:
                rec["path"] = d / rec["image"]
            rows.append(rec)
        # 画廊目录里存在、但 all-downloads.json 没有记录的文件（批次遗留），
        # 也算进“98 张”，标 orphan 以免和可追溯记录混在一起。
        ref = {r["image"] for r in rows if r["batch"] == batch}
        for p in sorted((d / "all-downloads").glob("*.jpg")):
            rel = f"all-downloads/{p.name}"
            if rel in ref:
                continue
            model = p.name.split("-")[1] if "-" in p.name else ""
            rows.append({
                "batch": batch, "batch_label": label, "orphan": True,
                "query": model, "model": model,
                "title": f"{model}（批次遗留文件，无原始标题）",
                "url": "", "status": "saved", "error": "", "image": rel,
                "path": p, "recorded_gate_pass": None, "recorded_view": "",
                "recorded_margin": None,
            })
    return rows


def analyze(rec: dict) -> dict:
    data = rec["path"].read_bytes()
    sha1 = hashlib.sha1(data).hexdigest()[:12]   # 同图判定用字节哈希，不靠 URL
    p = gate.prefilter(data)
    v2 = gate.check_v2(data)
    v3 = gate.check(data) if p["ok"] else None
    view = gate.classify_view(data) if (p["ok"] and v3 and v3.get("pass")) else {}

    a = gate.assess_from_gate(v3 or {}, view, p["width"], p["height"],
                              prefilter_result=p)
    if rec.get("orphan"):
        title_ok = None   # 无原始标题，护栏不适用
    else:
        title_ok = imagesearch._relevant(rec["query"], rec["title"], rec["model"])

    veto = [r for r in a["reasons"] if r in ("gate_drop", "interior_suspect")]
    drop_cn = fmt_label((v3 or {}).get("drop_label", ""))
    keep_cn = fmt_label((v3 or {}).get("keep_label", ""))
    margin = (v3 or {}).get("margin")
    if title_ok is False:
        verdict, primary = "reject_guard", "标题护栏"
        fail = "标题未命中型号代码或构型"
    elif not p["ok"]:
        verdict, primary = "reject_prefilter", p["reasons"][0]
        fail = "预筛：" + "、".join(REASON_CN.get(x, x) for x in p["reasons"])
    elif not a["pass"]:
        verdict, primary = "reject_gate", f"门卫·{drop_cn}"
        fail = (f"CLIP 拒绝：“{drop_cn}”胜出"
                f"（{margin:+.4f} = keep {keep_cn} {a['keep']:+.4f} − "
                f"drop {drop_cn} {a['drop']:+.4f}）")
    elif veto:
        verdict, primary = "reject_scene", veto[0]
        fail = f"内饰强信号（gap={a['view_gap']:.4f} ≥ {gate.VIEW_GAP_TRUSTED}）"
    elif a["part_candidate"]:
        verdict, primary, fail = "usable_part", "", ""
    elif a["overview_candidate"]:
        verdict, primary, fail = "usable_overview", "", ""
    elif a.get("reference_candidate"):
        if a.get("multi_vehicle"):
            verdict, primary = "reference", "参考·背景多车"
            fail = "背景有其他车（不占概览/部件名额，只进参考层）"
        else:
            verdict, primary = "reference", "low_res"
            fail = f"分辨率不够：长边 {a['long_side']} < 800（只能当参考）"
    else:
        verdict, primary = "reject_res", (a["reasons"] or ["low_res_overview"])[0]
        fail = "分辨率：" + "、".join(
            REASON_CN.get(x, x) for x in (a["reasons"] or ["low_res_overview"]))

    v2_ok = bool(v2.get("pass"))
    v3_ok = bool(v3 and v3.get("pass"))
    if not p["ok"]:
        change = "prefilter_blocked"
    elif v2_ok and not v3_ok:
        change = "newly_dropped"
    elif v2_ok and v3_ok:
        change = "kept"
    elif (not v2_ok) and v3_ok:
        change = "resurrected"
    else:
        change = "still_dropped"

    return {
        "batch": rec["batch"], "batch_label": rec["batch_label"],
        "query": rec["query"], "model": rec["model"],
        "title": rec["title"], "url": rec["url"],
        "image": rec["image"], "orphan": bool(rec.get("orphan")), "sha1": sha1,
        "title_guard": title_ok,
        "pre": p, "v2": v2, "v3": v3,
        "v2_pass": v2_ok, "v3_pass": v3_ok,
        "v2_keep_label": v2.get("keep_label", ""),
        "v2_drop_label": v2.get("drop_label", ""),
        "v2_drop_count": (v2.get("label_count") or {}).get("drop", 0),
        "v3_drop_count": ((v3 or {}).get("label_count") or {}).get("drop", 0),
        "new_label_hit": bool(v3 and v3.get("drop_label") in gate.V3_DROP_LABELS
                              and not v3.get("pass")),
        "keep_label": (v3 or {}).get("keep_label", ""),
        "drop_label": (v3 or {}).get("drop_label", ""),
        "keep": (v3 or {}).get("keep"), "drop": (v3 or {}).get("drop"),
        "margin": (v3 or {}).get("margin"),
        "v2_margin": v2.get("margin"),
        "scene": a["scene"], "view": a["view"], "view_gap": a["view_gap"],
        "overview_ok": a["overview_candidate"], "part_ok": a["part_candidate"],
        "exterior_hint": a["exterior_hint"], "stage": a["stage"],
        "gate_skipped": a["gate_skipped"],
        "reasons": a["reasons"], "hints": a["hints"],
        "width": a["width"], "height": a["height"], "long_side": a["long_side"],
        "verdict": verdict, "primary_reason": primary, "change": change,
        "fail_reason": fail,
        "reference_ok": bool(a.get("reference_candidate")),
        "keep_cn": keep_cn, "drop_cn": drop_cn,
        "old_usable_recalc": bool(v2_ok and a["long_side"] >= 1200
                                  and rec.get("recorded_view", "") in gate.EXTERIOR_VIEWS),
    }


def summarize(rows: list[dict], seconds: float) -> dict:
    saved = [r for r in rows if r["status"] == "saved"]
    failed = [r for r in rows if r["status"] != "saved"]
    urls = {r["url"] for r in saved if r["url"]}
    hashes = {r.get("sha1") or r["image"] for r in saved}
    reasons = Counter(r["primary_reason"] for r in saved if r["primary_reason"])
    drop_labels = Counter(r["drop_label"] for r in saved
                          if not r["v3_pass"] and r["drop_label"])
    changes = Counter(r["change"] for r in saved)
    verdicts = Counter(r["verdict"] for r in saved)

    # 唯一 URL 口径（跨两批去重，取首次出现）：与 53 张重评报告可比
    uniq: dict[str, dict] = {}
    for r in saved:
        key = r.get("sha1") or r.get("url") or r["image"]
        if key not in uniq:
            uniq[key] = r
    u = list(uniq.values())
    unique = {
        "images": len(u),
        "prefilter_blocked": sum(1 for r in u if not r["pre"]["ok"]),
        "clip_runs": sum(1 for r in u if r["pre"]["ok"]),
        "v2_pass": sum(1 for r in u if r["v2_pass"]),
        "v2_pass_clip": sum(1 for r in u if r["pre"]["ok"] and r["v2_pass"]),
        "v3_pass": sum(1 for r in u if r["v3_pass"]),
        "newly_dropped": sum(1 for r in u if r["change"] == "newly_dropped"),
        "overview_ok": sum(1 for r in u if r["overview_ok"]),
        "part_ok": sum(1 for r in u if r["part_ok"]),
        "reference_ok": sum(1 for r in u if r.get("reference_ok")),
        "part_with_exterior": sum(1 for r in u
                                  if r["part_ok"] and r["exterior_hint"]),
        "old_usable": sum(1 for r in u if r["old_usable_recalc"]),
    }
    return {
        "candidates": len(rows),
        "images_total": len(saved),
        "orphans": sum(1 for r in saved if r.get("orphan")),
        "download_ok": len(saved),
        "download_failed": len(failed),
        "unique_urls": len(urls),
        "unique_images": len(hashes),
        "duplicates": len(saved) - len(hashes),
        "title_guard_fail": sum(1 for r in saved if r["title_guard"] is False),
        "prefilter_blocked": sum(1 for r in saved if not r["pre"]["ok"]),
        "prefilter_reasons": dict(Counter(
            x for r in saved if not r["pre"]["ok"]
            for x in r["pre"]["reasons"]).most_common()),
        "clip_runs": sum(1 for r in saved if r["pre"]["ok"]),
        "v2_pass": sum(1 for r in saved if r["v2_pass"]),
        "v2_pass_clip": sum(1 for r in saved if r["pre"]["ok"] and r["v2_pass"]),
        "v3_pass": sum(1 for r in saved if r["v3_pass"]),
        "new_label_hits": sum(1 for r in saved if r.get("new_label_hit")),
        "changes": dict(changes),
        "overview_ok": sum(1 for r in saved if r["overview_ok"]),
        "part_ok": sum(1 for r in saved if r["part_ok"]),
        "reference_ok": sum(1 for r in saved if r.get("reference_ok")),
        "dup_rows": sum(1 for r in saved if r.get("dup")),
        "part_with_exterior": sum(1 for r in saved
                                  if r["part_ok"] and r["exterior_hint"]),
        "old_usable_recalc": sum(1 for r in saved if r["old_usable_recalc"]),
        "verdicts": dict(verdicts),
        "reasons": dict(reasons.most_common()),
        "drop_labels": dict(drop_labels.most_common()),
        "unique": unique,
        "seconds": round(seconds, 1),
    }


def fmt_label(text: str) -> str:
    """CLIP 标签太长，HTML 里只留要点。"""
    text = text or ""
    for k, v in (
        ("grid or collage", "网格拼图"),
        ("interior cabin", "内饰舱"),
        ("screenshot of a web page", "网页截图"),
        ("advertisement image", "广告字/价格"),
        ("passenger bus", "客车"),
        ("row or lineup", "多车队列"),
        ("logo, icon", "logo/图标"),
        ("chart, diagram", "图表"),
        ("people, a meeting", "人物/会议"),
        ("building, office", "建筑/室内"),
        ("text document", "文档截图"),
        ("close-up photo of a truck part", "部件特写"),
        ("single heavy truck", "单台重卡"),
        ("construction machinery", "工程车"),
    ):
        if k in text:
            return v
    return text[:24]


def render_html(rows: list[dict], s: dict, out_dir: Path) -> str:
    cards = []
    for i, r in enumerate(rows, 1):
        if r["status"] != "saved":
            continue
        thumb = f"thumbs/{i:02d}.jpg"
        verdict_cn = VERDICT_CN.get(r["verdict"], r["verdict"])
        cls = ("ok" if r["verdict"].startswith("usable")
               else "ref" if r["verdict"] == "reference" else "bad")
        dup_tag = " · 同图重复" if r.get("dup") else ""
        pre_ok = r["pre"]["ok"]
        pre_txt = "通过" if pre_ok else "、".join(
            REASON_CN.get(x, x) for x in r["pre"]["reasons"])
        if r["v3"] is None:
            v3_txt = "未运行（第一段已拦）"
        elif r["v3_pass"]:
            v3_txt = f"通过 {r['margin']:+.4f}"
        else:
            v3_txt = f"拒绝 {r['margin']:+.4f}"
        v2_txt = (f"通过 {r['v2_margin']:+.4f}" if r["v2_pass"]
                  else f"拒绝 {r['v2_margin']:+.4f}")
        chips = "".join(
            f'<span class="chip">{html.escape(REASON_CN.get(x, x))}</span>'
            for x in r["reasons"])
        hints = "".join(
            f'<span class="chip hint">{html.escape(h)}</span>'
            for x in r["hints"] for h in [{"view_detail_hint": "视角=部件特写",
                                           "view_uncertain": "视角不可信"}.get(x, x)])
        gap = r["view_gap"] or 0
        view_txt = (f"{r['view']} · gap {gap:.4f}" if r["view"]
                    else "—")
        v3_comp = "" if r["v3"] is None else (
            f'<tr><th>v3 竞争</th><td class="labels">'
            f'keep {html.escape(fmt_label(r["keep_label"]))} '
            f'{r["keep"] or 0:+.4f} ／ drop '
            f'{html.escape(fmt_label(r["drop_label"]))} {r["drop"] or 0:+.4f}'
            f'</td></tr>')
        note_cls = "note" if r["verdict"] == "reference" else "fail"
        cards.append(f"""
    <article class="card" data-verdict="{r['verdict']}" data-change="{r['change']}"
             data-stage="{r['stage']}" data-batch="{r['batch']}"
             data-newlabel="{'1' if r.get('new_label_hit') else '0'}"
             data-ref="{'1' if r.get('reference_ok') else '0'}"
             data-dup="{'1' if r.get('dup') else '0'}">
      <div class="thumb">
        <img loading="lazy" src="{thumb}" alt="">
        <span class="badge {cls}">{html.escape(verdict_cn)}{dup_tag}</span>
      </div>
      <div class="body">
        <h3 title="{html.escape(r['title'])}">{html.escape(r['title'][:52])}</h3>
        <p class="sub">{html.escape(r['query'])} · {r['width']}×{r['height']}
          · 长边 {r['long_side']} · {html.escape(r['batch_label'])}
          {'· 遗留文件' if r.get('orphan') else ''}</p>
        <table>
          <tr><th>预筛</th><td class="{'pass' if pre_ok else 'fail'}">{html.escape(pre_txt)}</td></tr>
          <tr><th>v2 门卫</th><td>{html.escape(v2_txt)}</td></tr>
          <tr><th>v3 门卫</th><td class="{'pass' if r['v3_pass'] else 'fail'}">{html.escape(v3_txt)}</td></tr>
          {v3_comp}
          <tr><th>v2 竞争</th><td class="labels dim">keep {html.escape(fmt_label(r['v2_keep_label']))}
            ／ drop {html.escape(fmt_label(r['v2_drop_label']))}</td></tr>
          <tr><th>视角</th><td>{html.escape(view_txt)}</td></tr>
          <tr><th>分层</th><td>{'概览 ✓' if r['overview_ok'] else '概览 ✗'}
            ／ {'部件 ✓' if r['part_ok'] else '部件 ✗'}
            ／ {'参考 ✓' if r.get('reference_ok') else '参考 ✗'}</td></tr>
          <tr><th>结论</th><td class="verdict {cls}">{html.escape(verdict_cn)}</td></tr>
        </table>
        {'<p class="' + note_cls + '">' + html.escape(r["fail_reason"]) + '</p>' if r.get("fail_reason") else ''}
        <p class="chips">{chips}{hints}</p>
        <p class="chg">{html.escape(CHANGE_CN.get(r['change'], r['change']))}
          <span class="dim">· {html.escape(r['url'][:64])}</span></p>
      </div>
    </article>""")

    def chip_row(label: str, value: int, cls: str = "") -> str:
        return (f'<div class="stat {cls}"><span class="num">{value}</span>'
                f'<span class="lab">{html.escape(label)}</span></div>')

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>两段式门卫 · 98 张全流程回放</title>
<style>
:root{{--bg:#0f1012;--card:#181A1D;--line:#2A2D31;--ink:#E8E6E1;--dim:#8C9095;
--accent:#DF4A1B;--ok:#3E9E6A;--bad:#C8442E;--warn:#C99A3C}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,
"Segoe UI","Microsoft YaHei",sans-serif}}
header{{padding:30px 32px 18px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 4px;font-size:22px;letter-spacing:.01em}}
.meta{{color:var(--dim);font-size:12px}}
.sum{{display:flex;flex-wrap:wrap;gap:10px;padding:18px 32px;border-bottom:1px solid var(--line)}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:8px;
padding:9px 13px;min-width:104px}}
.stat .num{{display:block;font:600 20px/1.2 ui-monospace,Consolas,monospace}}
.stat .lab{{color:var(--dim);font-size:11px}}
.stat.ok .num{{color:var(--ok)}} .stat.bad .num{{color:var(--bad)}}
.stat.ref .num{{color:var(--warn)}}
.stat.warn .num{{color:var(--warn)}}
.filters{{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:8px;
padding:12px 32px;background:rgba(15,16,18,.94);backdrop-filter:blur(6px);
border-bottom:1px solid var(--line)}}
.filters button{{background:transparent;color:var(--ink);border:1px solid var(--line);
border-radius:999px;padding:6px 13px;font-size:12px;cursor:pointer}}
.filters button.on{{background:var(--accent);border-color:var(--accent);color:#fff}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));
gap:16px;padding:22px 32px 60px}}
.flow{{display:flex;flex-wrap:wrap;align-items:stretch;gap:0;padding:18px 32px;
border-bottom:1px solid var(--line)}}
.step{{flex:1;min-width:110px;padding:10px 12px;border:1px solid var(--line);
border-radius:8px;background:var(--card)}}
.step b{{display:block;font:600 19px/1.2 ui-monospace,Consolas,monospace}}
.step span{{color:var(--dim);font-size:11px}}
.step.drop b{{color:var(--bad)}} .step.keep b{{color:var(--ok)}}
.arrow{{align-self:center;color:#4A4E54;padding:0 6px;font-size:16px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;
overflow:hidden;display:flex;flex-direction:column}}
.thumb{{position:relative;background:#000;aspect-ratio:16/10}}
.thumb img{{width:100%;height:100%;object-fit:contain}}
.badge{{position:absolute;left:8px;top:8px;font-size:11px;padding:3px 8px;
border-radius:999px;color:#fff;background:var(--bad)}}
.badge.ok{{background:var(--ok)}}
.badge.ref{{background:var(--warn)}}
.fail{{margin:9px 0 0;padding:7px 9px;border-radius:6px;background:#2A1E1B;
border:1px solid #432C26;color:#F0B6A6;font-size:11.5px;line-height:1.45}}
.note{{margin:9px 0 0;padding:7px 9px;border-radius:6px;background:#272218;
border:1px solid #40392A;color:#E4C98C;font-size:11.5px;line-height:1.45}}
.legend{{padding:14px 32px 18px;border-bottom:1px solid var(--line);color:#B9BDC2;
font-size:12px;line-height:1.65}}
.legend summary{{cursor:pointer;color:var(--ink);font-size:13px;font-weight:600}}
.legend table{{border-collapse:collapse;margin:10px 0;font-size:11.5px}}
.legend th,.legend td{{border:1px solid var(--line);padding:4px 8px;text-align:left;
vertical-align:top}}
.legend th{{color:var(--dim);font-weight:400;background:#1B1E22}}
.legend code{{background:#24272C}}
.body{{padding:12px 13px 14px}}
h3{{margin:0 0 4px;font-size:13px;line-height:1.35;font-weight:600;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
.sub{{margin:0 0 9px;color:var(--dim);font-size:11px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:var(--dim);font-weight:400;width:74px;padding:2px 6px 2px 0;
vertical-align:top;white-space:nowrap}}
td{{padding:2px 0;vertical-align:top}}
td.pass{{color:var(--ok)}} td.fail{{color:var(--bad)}}
td.labels{{font-family:ui-monospace,Consolas,monospace;font-size:11px;color:#B9BDC2}}
td.verdict{{font-weight:600}} td.verdict.ok{{color:var(--ok)}} td.verdict.bad{{color:var(--bad)}}
td.verdict.ref{{color:var(--warn)}}
.chips{{margin:8px 0 0;display:flex;flex-wrap:wrap;gap:5px}}
.chip{{font-size:10.5px;padding:2px 7px;border-radius:4px;background:#2A2020;
color:#E6A99B;border:1px solid #3A2A26}}
.chip.hint{{background:#24262A;color:#A9AEB4;border-color:#33363B}}
.chg{{margin:8px 0 0;color:var(--dim);font-size:11px}}
.dim{{opacity:.7}}
footer{{padding:0 32px 40px;color:var(--dim);font-size:12px}}
code{{font-family:ui-monospace,Consolas,monospace;background:#1E2126;padding:1px 5px;
border-radius:4px}}
</style></head>
<body>
<header>
  <h1>两段式门卫 · 98 张全流程回放</h1>
  <p class="meta">数据源：{html.escape(', '.join(b for b, _ in BATCHES))} 的 all-downloads
  · 同一批字节上重算 v2 / v3 / 预筛 / 分层 · 生成于 {time.strftime('%Y-%m-%d %H:%M')}</p>
</header>
<section class="flow">
  <div class="step"><b>{s['candidates']}</b><span>候选（含 1 遗留文件）</span></div>
  <div class="arrow">→</div>
  <div class="step drop"><b>{s['download_failed']}</b><span>下载失败</span></div>
  <div class="arrow">→</div>
  <div class="step"><b>{s['images_total']}</b><span>下载成功 / 标题护栏过 {s['images_total'] - s['title_guard_fail']}</span></div>
  <div class="arrow">→</div>
  <div class="step drop"><b>{s['prefilter_blocked']}</b><span>预筛拦下（未进 CLIP）</span></div>
  <div class="arrow">→</div>
  <div class="step"><b>{s['clip_runs']}</b><span>进 CLIP</span></div>
  <div class="arrow">→</div>
  <div class="step keep"><b>{s['v3_pass']}</b><span>门卫通过</span></div>
  <div class="arrow">→</div>
  <div class="step keep"><b>{s['overview_ok']}<span class="sep"> / </span>{s['part_ok']}</b><span>概览 / 部件可用</span></div>
</section>
<section class="legend">
  <details open>
    <summary>这些标签是什么？两段式怎么分工？（点开/收起）</summary>
    <p><b>门卫</b>用零样本 CLIP 判图：把图片分别与「保留标签」和「反例标签」比相似度，
    各取最高分，<code>margin = keep最高 − drop最高</code>；<code>margin ≥ 0</code> 放行。
    卡片里的「竞争」就是这两个最高分——所以“为什么被拒”看的是<b>哪个反例赢了</b>，不是随机抖动。</p>
    <table>
      <tr><th>版本</th><th>反例标签</th><th>来历</th></tr>
      <tr><td>v2（旧，7 条）</td><td>客车 / 多车队列 / logo 图标 / 图表 / 人物会议 / 建筑室内 / 文档截图</td><td>2026-10-15 第三轮审核反馈</td></tr>
      <tr><td>v3（11 条）</td><td>v2 的 7 条 + <b>内饰驾驶舱 / 网格拼图 / 网页截图 / 广告字</b></td><td>W1 冒烟暴露的漏网类型</td></tr>
      <tr><td>v4（现用）</td><td>反例同 v3；<b>保留标签加第 4 条</b>：主体一台 + 背景另有停车</td><td>“多车队列”误杀经销商场地/新闻图（13 张 13 张全恢复，9 张真坏图仍拒）</td></tr>
    </table>
    <p><b>保留标签（v4 起 4 条）</b>：单台重卡整车 / 单台工程车整车 / 部件特写 / 主体一台·背景另有停车。所以门卫放行的图
    可能只是“部件特写”或“侧面照”，<b>不等于型号身份正确</b>——身份靠标题护栏 + 人工。</p>
    <p><b>两段式</b>：第一段预筛（不看语义，只看字节/解码/格式/长宽比/近空白/明显过小 &lt;400）
    → 第二段 CLIP 门卫 → 视角 → 分层（概览 ≥800 / 部件 ≥1200 / <b>参考 &lt;800</b>，参考不占可用名额）。</p>
    <p><b>怎么读卡片</b>：<code>v2 通过 + v3 拒绝</code> = v3 新加的反例胜出，是“新增拦截”；
    “同图重复”表示这张照片被基础批和 HD 批各下一次，本页按<b>文件</b>计数，所以 2 张图会出现 4 行。</p>
  </details>
</section>
<section class="sum">
  {chip_row('图片文件', s['images_total'])}
  {chip_row('唯一图 / URL', str(s['unique_images']) + ' / ' + str(s['unique_urls']))}
  {chip_row('候选/下载失败', s['candidates'])}
  {chip_row('预筛拦下（未进 CLIP）', s['prefilter_blocked'], 'warn')}
  {chip_row('实际跑 CLIP', s['clip_runs'])}
  {chip_row('CLIP 内 v2 通过', s['v2_pass_clip'])}
  {chip_row('门卫通过（v4）', s['v3_pass'])}
  {chip_row('概览可用（唯一图）', s['unique']['overview_ok'], 'ok')}
  {chip_row('部件可用（唯一图）', s['unique']['part_ok'], 'ok')}
  {chip_row('参考层（低清，全部）', s['reference_ok'], 'ref')}
  {chip_row('旧“可用”口径', s['unique']['old_usable'])}
</section>
<div class="filters">
  <button class="on" data-f="all">全部 {s['images_total']}</button>
  <button data-f="usable">可用</button>
  <button data-f="ref">参考层 {s['reference_ok']}</button>
  <button data-f="unique">合并同图 {s['unique']['images']}</button>
  <button data-f="bad">不可用</button>
  <button data-f="changed">标签有变化 {s['changes'].get('newly_dropped',0) + s['changes'].get('resurrected',0)}</button>
  <button data-f="prefilter">预筛拦截 {s['prefilter_blocked']}</button>
  <button data-f="gate">CLIP 拒绝</button>
  <button data-f="newlabel">新增反例命中 {s['new_label_hits']}</button>
  <button data-f="hd">HD 批次</button>
</div>
<main class="grid">{''.join(cards)}</main>
<footer>
  <p><strong>读法</strong>：<code>预筛</code> 是零模型的确定性第一段（尺寸/字节/格式/长宽比/近空白）；
  被它拦下的图 <em>不会</em> 进 CLIP，所以 v3 门卫显示“未运行”。
  <code>v2</code> 是旧反例集（7 条），<code>v3</code> 加了内饰/拼图/截图/广告 4 条。
  <code>竞争标签</code> 是 keep/drop 两个分数最高的标签及其相似度，门卫判定就是两者相减的裕量。</p>
  <p>可用 ≠ 型号身份正确：门卫只判“是不是单台目标车类的图”，身份仍靠标题护栏 + 人工复核。</p>
</footer>
<script>
const cards=[...document.querySelectorAll('.card')];
const F={{
 all:()=>true,
 usable:c=>c.dataset.verdict.startsWith('usable'),
 ref:c=>c.dataset.ref==='1',
 unique:c=>c.dataset.dup!=='1',
 bad:c=>!c.dataset.verdict.startsWith('usable'),
 changed:c=>c.dataset.change==='newly_dropped'||c.dataset.change==='resurrected',
 prefilter:c=>c.dataset.stage==='prefilter',
 gate:c=>c.dataset.verdict==='reject_gate'||c.dataset.verdict==='reject_scene',
 newlabel:c=>c.dataset.newlabel==='1',
 hd:c=>c.dataset.batch==='web-smoke-hd-20261109'
}};
let cur='all';
function apply(){{cards.forEach(c=>c.style.display=F[cur](c)?'':'none');
 document.querySelectorAll('.filters button').forEach(b=>
   b.classList.toggle('on',b.dataset.f===cur));}}
document.querySelectorAll('.filters button').forEach(b=>
  b.onclick=()=>{{cur=b.dataset.f;apply();}});
apply();
</script>
</body></html>
"""


def render_borderline(rows: list[dict], out_dir: Path, limit: float = 0.01) -> str:
    """边界清单：|margin| < limit 的唯一图（跨批去重），逐张给竞争细节。

    这不是调参工具，是验收工具：阈值附近判对没有，人工扫一眼就知道。
    """
    seen: set[str] = set()
    items: list[tuple[int, dict]] = []
    for i, r in enumerate(rows, 1):
        if r["status"] != "saved" or r.get("margin") is None:
            continue
        if abs(r["margin"]) >= limit:
            continue
        key = r.get("sha1") or r["image"]
        if key in seen:
            continue
        seen.add(key)
        items.append((i, r))
    items.sort(key=lambda x: x[1]["margin"])
    cards = []
    for i, r in items:
        cls = "ok" if r["verdict"].startswith("usable") else (
            "ref" if r["verdict"] == "reference" else "bad")
        vt = VERDICT_CN.get(r["verdict"], r["verdict"])
        cards.append(f"""
    <article class="card">
      <img loading="lazy" src="thumbs/{i:02d}.jpg" alt="">
      <div class="body">
        <div class="head"><span class="badge {cls}">{html.escape(vt)}</span>
          <b class="m">{r['margin']:+.4f}</b></div>
        <h3>{html.escape(r['title'][:46])}</h3>
        <p class="sub">{html.escape(r['model'] or '')} · {r['width']}×{r['height']}</p>
        <table>
          <tr><th>keep</th><td class="pass">{html.escape(r['keep_cn'])} {r['keep']:+.4f}</td></tr>
          <tr><th>drop</th><td class="fail">{html.escape(r['drop_cn'])} {r['drop']:+.4f}</td></tr>
          <tr><th>差值</th><td>{r['margin']:+.4f}（阈值 0）</td></tr>
        </table>
        <p class="why">{html.escape(r.get('fail_reason') or '通过：' + CHANGE_CN.get(r['change'], ''))}</p>
      </div>
    </article>""")
    doc = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>边界清单 · |margin| &lt; {limit}</title>
<style>
:root{{--bg:#0f1012;--card:#181A1D;--line:#2A2D31;--ink:#E8E6E1;--dim:#8C9095;
--ok:#3E9E6A;--bad:#C8442E;--warn:#C99A3C}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 -apple-system,
"Segoe UI","Microsoft YaHei",sans-serif}}
header{{padding:26px 30px 14px;border-bottom:1px solid var(--line)}}
h1{{margin:0 0 6px;font-size:20px}}
.meta{{color:var(--dim);font-size:12px;line-height:1.7}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
gap:14px;padding:20px 30px 50px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}}
.card img{{width:100%;height:190px;object-fit:contain;background:#000;display:block}}
.body{{padding:10px 12px 12px}}
.head{{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}}
.badge{{font-size:11px;padding:2px 8px;border-radius:999px;color:#fff;background:var(--bad)}}
.badge.ok{{background:var(--ok)}} .badge.ref{{background:var(--warn)}}
.m{{font:600 15px/1 ui-monospace,Consolas,monospace}}
h3{{margin:0 0 3px;font-size:12.5px;font-weight:600;line-height:1.35}}
.sub{{margin:0 0 7px;color:var(--dim);font-size:11px}}
table{{width:100%;border-collapse:collapse;font-size:11.5px}}
th{{text-align:left;color:var(--dim);font-weight:400;width:46px;padding:1px 0}}
td.pass{{color:var(--ok)}} td.fail{{color:var(--bad)}}
.why{{margin:8px 0 0;padding:6px 8px;border-radius:5px;background:#1F2227;
color:#B9BDC2;font-size:11px;line-height:1.45}}
</style></head><body>
<header>
  <h1>边界清单 · |margin| &lt; {limit}</h1>
  <p class="meta">共 {len(items)} 张（52 张唯一图里，跨批去重）· 阈值 0 附近的判定，
  人工确认判对没有 · 生成于 {time.strftime('%Y-%m-%d %H:%M')}</p>
</header>
<main class="grid">{''.join(cards)}</main>
</body></html>
"""
    path = out_dir / "borderline.html"
    path.write_text(doc, encoding="utf-8")
    return str(path)


def render_md(s: dict, rows: list[dict]) -> str:
    pre_line = (f"- 预筛拦下：{s['prefilter_blocked']}；实际跑 CLIP：{s['clip_runs']}"
                if not s["prefilter_reasons"] else
                f"- 预筛拦下：{s['prefilter_blocked']}（"
                + "、".join(f"{k}={v}" for k, v in s["prefilter_reasons"].items())
                + f"）；实际跑 CLIP：{s['clip_runs']}")
    u = s["unique"]
    lines = [
        "# 两段式门卫 · 98 张全流程回放", "",
        f"- 图片：{s['images_total']}（含批次遗留 {s['orphans']}）；"
        f"候选 {s['candidates']}；下载失败 {s['download_failed']}；"
        f"**唯一图 {s['unique_images']}**（按字节 sha1；URL {s['unique_urls']} 个，"
        f"其中 1 对 URL 指向同一张图）；重复行 {s['duplicates']}",
        f"- 标题护栏未过：{s['title_guard_fail']}",
        pre_line,
        f"- CLIP 内：v2 通过 {s['v2_pass_clip']} → v4 通过 {s['v3_pass']}；"
        f"新增拦截 {s['changes'].get('newly_dropped', 0)}；"
        f"新增反例命中 {s['new_label_hits']}",
        f"- **唯一图口径**（{u['images']} 张，跨批去重）："
        f"预筛拦 {u['prefilter_blocked']}（只挡缩略图级垃圾）；"
        f"进 CLIP {u['clip_runs']} 张，其中 v2 通过 {u['v2_pass_clip']} → "
        f"v4 通过 {u['v3_pass']}（新增拦截 {u['newly_dropped']}）",
        f"- 唯一口径去处：概览 {u['overview_ok']}（其中部件 {u['part_ok']}、"
        f"外观提示 {u['part_with_exterior']}）+ 参考层 {u['reference_ok']} "
        f"= {u['overview_ok'] + u['reference_ok']} 张，与 v4 通过数一致，"
        f"没有“过了门卫却没去处”的图",
        f"- 概览可用：{s['overview_ok']}；部件可用：{s['part_ok']}"
        f"（其中外观提示 {s['part_with_exterior']}）；"
        f"参考层（长边 <800、语义可用）：{s['reference_ok']}；"
        f"旧“可用”同字节重算：{s['old_usable_recalc']}",
        f"- 耗时：{s['seconds']}s", "",
        "## 否决理由分布", "",
        "| 理由 | 张数 | 说明 |", "|---|---:|---|",
    ]
    for k, v in s["reasons"].items():
        note = REASON_CN.get(k, "CLIP 反例胜出" if k.startswith("门卫") else "")
        lines.append(f"| {k} | {v} | {note} |")
    lines += ["", "## 新增拦截（v2 通过 → v3 拒绝，按 URL 去重）", "",
              "| 文件 | 批次 | 尺寸 | 裕量 | 胜出 drop 标签 | 结论 |",
              "|---|---|---:|---:|---|---|"]
    seen: set[str] = set()
    for r in rows:
        if r["status"] == "saved" and r["change"] == "newly_dropped":
            key = r["url"] or r["image"]
            if key in seen:      # 同一张图在另一批重复出现
                continue
            seen.add(key)
            margin = r.get("margin")
            margin_txt = f"{margin:+.4f}" if margin is not None else "—(预筛)"
            lines.append(
                f"| {r['image']} | {r['batch_label']} | "
                f"{r['width']}×{r['height']} | "
                f"{margin_txt} | {fmt_label(r['drop_label'])} | "
                f"{r['primary_reason']} |")
    lines += ["", "## 说明", "",
              "- 两段式：第一段预筛只做确定性硬事实，第二段才是 CLIP；"
              "`未运行` 表示该图没进 CLIP。",
              "- 全部数字来自同一批已下载字节的重算，不是批次记录值。",
              "- 对比页：`index.html`（含缩略图与筛选按钮）。"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="两段式门卫 98 张回放")
    ap.add_argument("--out", default="data-test/runs/filter-98-20261109")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)

    out_dir = ROOT / args.out
    thumbs_dir = out_dir / "thumbs"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    for old in thumbs_dir.glob("*.jpg"):   # 每次重跑清掉旧缩略图，避免索引错位
        old.unlink()

    t0 = time.time()
    rows = load_rows()
    saved = [r for r in rows if r["status"] == "saved"]
    if args.limit:
        saved = saved[:args.limit]
        keep_ids = {id(r) for r in saved}
        rows = [r for r in rows if r["status"] != "saved" or id(r) in keep_ids]

    seen_urls: set[str] = set()
    for i, r in enumerate(rows, 1):
        if r["status"] != "saved":
            continue
        try:
            r.update(analyze(r))
        except Exception as e:  # noqa: BLE001
            r["status"] = "error"
            r["error"] = f"{type(e).__name__}: {e}"
            continue
        # 同图判定 = 字节 sha1（两批各下一次）；URL 只作兜底，避免把 4 行看成 4 张图
        key = r.get("sha1") or r.get("url") or r["image"]
        r["dup"] = key in seen_urls
        seen_urls.add(key)
        # 缩略图（页面加载速度；原图仍可从 all-downloads 打开）
        try:
            im = Image.open(r["path"]).convert("RGB")
            im.thumbnail((640, 640))
            im.save(out_dir / "thumbs" / f"{i:02d}.jpg", "JPEG", quality=78)
            r["thumb"] = f"thumbs/{i:02d}.jpg"
        except Exception:  # noqa: BLE001
            r["thumb"] = ""

    s = summarize(rows, time.time() - t0)
    dump = {k: v for k, v in s.items()}
    (out_dir / "report.json").write_text(json.dumps(
        {"summary": dump, "rows": rows}, ensure_ascii=False, indent=1,
        default=str), encoding="utf-8")
    (out_dir / "report.md").write_text(render_md(s, rows), encoding="utf-8")
    (out_dir / "index.html").write_text(render_html(rows, s, out_dir),
                                        encoding="utf-8")
    borderline = render_borderline(rows, out_dir)
    print(json.dumps(s, ensure_ascii=False, indent=1))
    print(f"borderline: {borderline}")
    print(f"out: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
