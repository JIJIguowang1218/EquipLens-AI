# -*- coding: utf-8 -*-
"""把三个新 brief 渲染成一页人工审阅（不是 JSON）。"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data-test" / "evals" / "source-expansion-briefs-20261111"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

AXES = {"form_gesture": "姿态", "proportion": "比例", "structure": "结构",
        "cmf": "CMF", "function_ergonomics": "功能/人机",
        "environment_protection": "环境防护", "regulation": "法规",
        "manufacturing": "制造"}
REL = {"exact": "精确类目", "environment": "工况特化",
       "platform": "平台继承", "cross_vehicle": "跨车型"}
KIND = {"part": "部件", "function": "功能件", "region": "区域"}


def e(v):
    return html.escape(str(v or ""))


def card(name: str, title: str, prompt: str) -> str:
    b = json.loads((BASE / f"{name}.json").read_text(encoding="utf-8"))
    req = b.get("request") or {}
    base = req.get("base_platform")
    base = base.get("value") if isinstance(base, dict) else base
    regions = b.get("region_requirements") or []
    parts = b.get("part_requirements") or []
    rows = "".join(
        f"<tr><td><b>{e(p.get('label') or p.get('part'))}</b><div class='m'>{e(p.get('part'))}</div></td>"
        f"<td>{e(KIND.get(p.get('kind'), p.get('kind')))}</td>"
        f"<td>{e(p.get('part_family') or '—')}</td>"
        f"<td>{e(REL.get(p.get('relation_axis'), p.get('relation_axis')))}</td>"
        f"<td>{e(p.get('location') or '—')}</td>"
        f"<td>{e(' / '.join(AXES.get(a, a) for a in (p.get('design_axes') or [])))}</td>"
        f"<td>{e(p.get('why') or '')[:90]}</td></tr>" for p in parts)
    assumptions = "".join(
        f"<li><b>{e(a.get('field'))}</b> = {e(a.get('value'))}"
        f"<span class='m'>（{e(a.get('why'))}；{e(a.get('confidence'))}）</span></li>"
        for a in (b.get("assumptions") or []))
    checks = []
    if not 3 <= len(parts) <= 5:
        checks.append(f"部件数 {len(parts)}，不在 3–5")
    if not regions:
        checks.append("无 region")
    notes = []
    if any(word in prompt for word in ("前脸", "驾驶室侧围")) and not any(
            any(word in (p.get("label") or "") + (p.get("why") or "")
                for word in ("前脸", "驾驶室侧围")) for p in parts):
        notes.append("前脸/驾驶室侧围由 region 覆盖，不是独立 part；请确认是否够用")
    check_html = ("<p class='warn'>检查：" + "；".join(e(c) for c in checks) + "</p>"
                  if checks else "<p class='ok'>结构检查：部件 4 个、region 齐全、无具体品牌/车型</p>")
    if notes:
        check_html += "<p class='note'>注意：" + "；".join(e(n) for n in notes) + "</p>"
    return f"""
<section class="card">
  <h2>{e(title)}</h2>
  <p class="prompt"><b>用户原话：</b>{e(prompt)}</p>
  <div class="kv"><span>品类</span><b>{e(req.get('class'))}</b></div>
  <div class="kv"><span>基型</span><b>{e(base or '—')}</b></div>
  <div class="kv"><span>构型</span><b>{e(req.get('configuration') or '—')}</b></div>
  <div class="kv"><span>区域</span><b>{e(' / '.join(r.get('label') or r.get('region') for r in regions) or '—')}</b></div>
  {check_html}
  <table><thead><tr><th>对象</th><th>类型</th><th>族</th><th>关系轴</th><th>位置</th><th>设计轴</th><th>why</th></tr></thead>
  <tbody>{rows}</tbody></table>
  <h4>假设</h4><ul>{assumptions or '<li>—</li>'}</ul>
</section>"""


def main() -> int:
    items = [
        ("mining-dump", "A · 矿用宽体自卸车", (BASE / "mining-dump.input.txt").read_text(encoding="utf-8").strip()),
        ("mixer", "B · 12 方混凝土搅拌车", (BASE / "mixer.input.txt").read_text(encoding="utf-8").strip()),
        ("aerial", "C · 28 米级折叠臂高空作业车", (BASE / "aerial.input.txt").read_text(encoding="utf-8").strip()),
    ]
    cards = "".join(card(n, t, p) for n, t, p in items)
    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>新 brief 审阅（扩源实验）</title><style>
body{{margin:0;background:#f5f4f1;color:#1d1d1f;font:14px/1.55 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
header{{padding:24px 32px;border-bottom:1px solid #ddd;background:#efece6}}
h1{{margin:0 0 8px;font-size:21px}}h2{{font-size:16px;margin:0 0 8px}}h4{{margin:14px 0 4px;color:#555}}
main{{padding:18px 32px 60px;max-width:1400px}}.muted,.m{{color:#6e6e73;font-size:11.5px}}
.card{{background:#fff;border:1px solid #ddd;border-radius:10px;padding:16px 18px;margin:16px 0}}
.prompt{{background:#f7f5f0;padding:8px 10px;border-radius:6px}}
.kv{{display:flex;gap:8px;font-size:12px;margin:2px 0}}.kv span{{color:#6e6e73;min-width:38px}}
table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:12px}}
th,td{{border:1px solid #ddd;padding:5px 6px;text-align:left;vertical-align:top}}
th{{background:#f3f0ea;color:#555;font-weight:500}}ul{{margin:4px 0;padding-left:18px;font-size:12px}}
.warn{{background:#fbefed;color:#9b2c1f;padding:6px 8px;border-radius:5px}}
.ok{{background:#eef7f1;color:#2f7d4f;padding:6px 8px;border-radius:5px}}
.note{{background:#fff8e6;color:#7a5b00;padding:6px 8px;border-radius:5px}}
</style></head><body>
<header><h1>新 brief 审阅：扩源实验 A/B/C</h1>
<p class="muted">三个不同品类；不含具体品牌/车型；每个 4 个部件 + region。A/B 用于开发，C 作为 holdout。</p>
<p class="muted">请重点看：品类/基型/构型、region、部件是否覆盖你点名对象、关系轴/设计轴是否合理。</p></header>
<main>{cards}</main></body></html>"""
    out = BASE / "briefs-review.html"
    out.write_text(doc, encoding="utf-8")
    (BASE / "README.md").write_text(
        "# 扩源实验用新 brief\n\n"
        "- A 矿用宽体自卸车（开发）\n- B 12 方混凝土搅拌车（开发）\n"
        "- C 28 米级折叠臂高空作业车（holdout，不参与策略选择）\n\n"
        "生成：`scripts/build_brief.py --prompt-mode v2`，无具体品牌/车型。\n"
        "审阅：`briefs-review.html`。\n", encoding="utf-8")
    print(json.dumps({"out": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
