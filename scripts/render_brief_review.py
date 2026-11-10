# -*- coding: utf-8 -*-
"""把 task-brief 评测结果渲染成人工审核页（不需要看 JSON）。"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

AXES_CN = {
    "form_gesture": "姿态/线条", "proportion": "比例", "structure": "结构/分缝",
    "cmf": "CMF", "function_ergonomics": "功能/人机",
    "environment_protection": "环境防护", "regulation": "法规",
    "manufacturing": "制造约束",
}
REL_CN = {"exact": "精确类目", "environment": "工况特化",
          "platform": "平台继承", "cross_vehicle": "跨车型"}
KIND_CN = {"part": "部件", "function": "功能件", "region": "区域"}


def esc(v) -> str:
    return html.escape(str(v or ""))


def brief_block(b: dict) -> str:
    if not b:
        return '<p class="empty">无输出</p>'
    req = b.get("request") or {}
    parts = b.get("part_requirements") or []
    regions = b.get("region_requirements") or []
    rows = "".join(
        f"<tr><td><b>{esc(p.get('label') or p.get('part'))}</b>"
        f"<div class='muted'>{esc(p.get('part'))}</div></td>"
        f"<td>{esc(KIND_CN.get(p.get('kind'), p.get('kind') or '—'))}</td>"
        f"<td>{esc(REL_CN.get(p.get('relation_axis'), p.get('relation_axis') or '—'))}</td>"
        f"<td>{esc(' / '.join(AXES_CN.get(a, a) for a in (p.get('design_axes') or [])))}</td>"
        f"<td>{esc(p.get('views') and '/'.join(p['views']) or '—')}</td>"
        f"<td>{esc((p.get('why') or '')[:120])}</td></tr>"
        for p in parts
    )
    regs = "".join(
        f"<li><b>{esc(r.get('label') or r.get('region'))}</b>"
        f" · {esc(' / '.join(AXES_CN.get(a, a) for a in (r.get('design_axes') or [])))}"
        f" · {esc('/'.join(r.get('views') or []))}</li>"
        for r in regions
    )
    assumptions = "".join(
        f"<li><b>{esc(a.get('field'))}</b> = {esc(a.get('value'))}"
        f"（{esc(a.get('why'))}，置信 {esc(a.get('confidence'))}）</li>"
        for a in (b.get("assumptions") or [])
    )
    base = req.get("base_platform")
    base_val = base.get("value") if isinstance(base, dict) else base
    return (
        f"<div class='kv'><span>品类</span><b>{esc(req.get('class'))}</b></div>"
        f"<div class='kv'><span>基型</span><b>{esc(base_val or '—')}</b></div>"
        f"<div class='kv'><span>构型</span><b>{esc(req.get('configuration') or '—')}</b></div>"
        f"<div class='kv'><span>区域</span><b>{esc(' / '.join(r.get('label') or r.get('region') for r in regions) or '—')}</b></div>"
        f"<table><thead><tr><th>对象</th><th>类型</th><th>关系轴</th>"
        f"<th>设计轴</th><th>视角</th><th>why</th></tr></thead><tbody>{rows}</tbody></table>"
        f"<div class='cols'><div><h4>区域要求</h4><ul>{regs or '<li>—</li>'}</ul></div>"
        f"<div><h4>假设</h4><ul>{assumptions or '<li>—</li>'}</ul></div></div>"
    )


def main(argv=None) -> int:
    base = Path(argv[1] if argv and len(argv) > 1 else
                "data-test/evals/task-brief-eval-20261111")
    results = json.loads((base / "results.json").read_text(encoding="utf-8"))
    rows = results["rows"]
    by = {}
    for r in rows:
        by.setdefault(r["case"], {})[r["arm"]] = r

    def load(cid: str, arm: str) -> dict:
        p = base / f"{cid}__{arm}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    cards = []
    for cid in sorted(by):
        data = load(cid, "with_skill")
        no = load(cid, "without_skill")
        w = by[cid].get("with_skill") or {}
        wo = by[cid].get("without_skill") or {}
        wf = (w.get("checks") or {}).get("failed") or []
        wof = (wo.get("checks") or {}).get("failed") or []
        case = data.get("case") or {}
        dims = ("品类/基型", "对象分类", "关系轴", "设计轴", "未知部件", "不编造", "总体可用")
        rubric = "".join(
            f"<label class='score'>{d}<br><select data-k='{cid}:{i}'>"
            "<option value=''>—</option><option>0</option><option>1</option><option>2</option>"
            "</select></label>" for i, d in enumerate(dims))
        cards.append(f"""
<section class="case" id="{cid}">
  <header><h2>{cid} · {esc(case.get('prompt'))}</h2>
    <p class="muted">期望：{esc(case.get('expected_output'))}</p></header>
  <div class="badges">
    <span class="badge {'ok' if not wf else 'bad'}">with skill 自动：{'PASS' if not wf else '; '.join(wf)}</span>
    <span class="badge {'ok' if not wof else 'bad'}">without skill：{'PASS' if not wof else '; '.join(wof)}</span>
  </div>
  <div class="grid">
    <div><h3>with_skill（task-brief@v2）</h3>{brief_block(data.get('brief'))}</div>
    <div><h3>without_skill（基线）</h3>{brief_block(no.get('brief'))}</div>
  </div>
  <h3>人工评分（0=错，1=部分，2=可直接用）</h3>
  <div class="rubric">{rubric}</div>
  <label class="note">备注<textarea data-note="{cid}" rows="2"></textarea></label>
</section>""")

    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>task-brief 10 案例人工审核</title><style>
:root{{--bg:#f6f5f2;--card:#fff;--ink:#1d1d1f;--dim:#6e6e73;--line:#ddd;--ok:#2f7d4f;--bad:#b23b2e}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.55 -apple-system,"Segoe UI","Microsoft YaHei",sans-serif}}
header.page{{padding:28px 36px 16px;border-bottom:1px solid var(--line);background:#efece6}}
h1{{margin:0 0 6px;font-size:22px}}h2{{font-size:16px;margin:0 0 6px}}
h3{{font-size:13px;margin:14px 0 6px}}h4{{font-size:12px;margin:8px 0 4px;color:var(--dim)}}
.muted{{color:var(--dim);font-size:12px;margin:2px 0}}main{{padding:18px 36px 80px}}
.case{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px;margin:16px 0}}
.badges{{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0 4px}}
.badge{{font-size:11px;padding:3px 8px;border-radius:999px;border:1px solid var(--line)}}
.badge.ok{{color:var(--ok);border-color:#b9d8c5;background:#eef7f1}}
.badge.bad{{color:var(--bad);border-color:#e3c3bd;background:#fbefed}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:8px}}
@media(max-width:1100px){{.grid{{grid-template-columns:1fr}}}}
.kv{{display:flex;gap:8px;font-size:12px;margin:2px 0}}.kv span{{color:var(--dim);min-width:38px}}
table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:11.5px}}
th,td{{border:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top}}
th{{background:#f3f0ea;font-weight:500;color:var(--dim)}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}ul{{margin:4px 0;padding-left:18px;font-size:12px}}
.rubric{{display:grid;grid-template-columns:repeat(7,minmax(80px,1fr));gap:8px;margin:6px 0}}
.score{{font-size:11px;color:var(--dim)}}select{{width:100%;padding:3px}}
input[type=text],textarea{{width:100%;border:1px solid var(--line);border-radius:4px;padding:5px;font:inherit}}
.note{{display:block;margin-top:8px;font-size:12px;color:var(--dim)}}
.empty{{color:var(--dim);font-size:12px}}
.bar{{position:sticky;top:0;z-index:2;background:var(--bg);padding:10px 36px;border-bottom:1px solid var(--line);
display:flex;gap:10px;align-items:center}}
button{{border:1px solid var(--line);background:#fff;border-radius:6px;padding:6px 12px;cursor:pointer}}
button.primary{{background:#1d1d1f;color:#fff;border-color:#1d1d1f}}
</style></head><body>
<header class="page"><h1>task-brief 10 案例人工审核</h1>
<p class="muted">with_skill = task-brief@v2；without_skill = 只给输出字段的基线。自动断言只查结构，语义请按 0/1/2 打分。</p>
<p class="muted">重点：C02 口语类目；C06–C10 新品类；C08–C10 上装件是否 custom；C01/C05 关系轴差异。</p></header>
<div class="bar"><button class="primary" id="export">导出我的评分 JSON</button>
<span class="muted" id="saved"></span></div>
<main>{''.join(cards)}</main>
<script>
const KEY='task-brief-review-20261111';
function key(el){{return el.dataset.k||el.dataset.note}}
document.querySelectorAll('select,textarea').forEach(el=>{{
  const k=key(el); const v=JSON.parse(localStorage.getItem(KEY)||'{{}}')[k];
  if(v!==undefined) el.value=v;
  el.addEventListener('input',()=>{{
    const all=JSON.parse(localStorage.getItem(KEY)||'{{}}'); all[k]=el.value;
    localStorage.setItem(KEY,JSON.stringify(all)); document.getElementById('saved').textContent='已保存 '+new Date().toLocaleTimeString();
  }});
}});
document.getElementById('export').onclick=()=>{{
  const all=JSON.parse(localStorage.getItem(KEY)||'{{}}');
  const blob=new Blob([JSON.stringify({{review:all,saved_at:new Date().toISOString()}},null,1)],{{type:'application/json'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='task-brief-review.json';a.click();
}};
</script></body></html>"""
    out = base / "review.html"
    out.write_text(doc, encoding="utf-8")
    print(json.dumps({"out": str(out), "cases": len(by)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
