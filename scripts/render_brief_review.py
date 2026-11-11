# -*- coding: utf-8 -*-
"""把 task-brief 评测结果渲染成人工审核页（v2 vs v1 格式组，不需要看 JSON）。"""
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
ARMS = (("v2_method", "v2 方法"), ("v1_format", "v1 只给格式"), ("no_method", "裸基线"))
DIMS = ("品类/基型/构型", "对象分类", "关系轴", "设计轴", "未知部件", "不编造", "总体可用")


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
        f"<td>{esc((p.get('why') or '')[:100])}</td></tr>"
        for p in parts
    )
    regs = "".join(
        f"<li><b>{esc(r.get('label') or r.get('region'))}</b>"
        f" · {esc(' / '.join(AXES_CN.get(a, a) for a in (r.get('design_axes') or [])))}</li>"
        for r in regions
    )
    assumptions = "".join(
        f"<li><b>{esc(a.get('field'))}</b> = {esc(a.get('value'))}"
        f"（{esc(a.get('why'))}）</li>" for a in (b.get("assumptions") or [])
    )
    base = req.get("base_platform")
    base_val = base.get("value") if isinstance(base, dict) else base
    return (
        f"<div class='kv'><span>品类</span><b>{esc(req.get('class'))}</b></div>"
        f"<div class='kv'><span>基型</span><b>{esc(base_val or '—')}</b></div>"
        f"<div class='kv'><span>构型</span><b>{esc(req.get('configuration') or '—')}</b></div>"
        f"<div class='kv'><span>区域</span><b>{esc(' / '.join(r.get('label') or r.get('region') for r in regions) or '—')}</b></div>"
        f"<table><thead><tr><th>对象</th><th>类型</th><th>关系轴</th>"
        f"<th>设计轴</th><th>why</th></tr></thead><tbody>{rows}</tbody></table>"
        f"<div class='cols'><div><h4>区域</h4><ul>{regs or '<li>—</li>'}</ul></div>"
        f"<div><h4>假设</h4><ul>{assumptions or '<li>—</li>'}</ul></div></div>"
    )


def main(argv=None) -> int:
    base = Path(argv[1] if argv and len(argv) > 1 else
                "data-test/evals/task-brief-eval-v1b-20261111")
    results = json.loads((base / "results.json").read_text(encoding="utf-8"))
    rows = results["rows"]
    by: dict[str, dict] = {}
    for r in rows:
        by.setdefault(r["case"], {})[r["arm"]] = r
    arms = [a for a in ARMS if any(a[0] in v for v in by.values())]

    def load(cid: str, arm: str) -> dict:
        p = base / f"{cid}__{arm}.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    cards = []
    for cid in sorted(by):
        data = {arm: load(cid, arm) for arm, _ in arms}
        case = next((d.get("case") for d in data.values() if d.get("case")), {})
        badges = "".join(
            f"<span class='badge {'ok' if not ((by[cid].get(arm) or {}).get('checks', {}).get('failed')) else 'bad'}'>"
            f"{label}：{'PASS' if not ((by[cid].get(arm) or {}).get('checks', {}).get('failed')) else '; '.join((by[cid][arm]['checks'].get('failed') or [])[:2])}</span>"
            for arm, label in arms
        )
        grids = "".join(
            f"<div><h3>{esc(label)}</h3>{brief_block(data[arm].get('brief'))}</div>"
            for arm, label in arms
        )
        rubric_rows = "".join(
            f"<tr><td>{d}</td>" + "".join(
                f"<td><select data-k='{cid}|{arm}|{i}'><option value=''>—</option>"
                "<option>PASS</option><option>FAIL</option><option>NA</option></select></td>"
                for arm, _ in arms) + "</tr>"
            for i, d in enumerate(DIMS)
        )
        head = "".join(f"<th>{esc(label)}</th>" for _, label in arms)
        evidence = "".join(
            f"<label class='note'>{esc(label)} 证据/意见"
            f"<textarea data-note='{cid}|{arm}' rows='2'></textarea></label>"
            for arm, label in arms)
        pref = (f"<label class='pref'>优先采用：<select data-k='{cid}|pref'>"
                "<option value=''>—</option>" + "".join(
                    f"<option>{esc(label)}</option>" for _, label in arms) + "</select></label>")
        cards.append(f"""
<section class="case" id="{cid}">
  <header><h2>{cid} · {esc(case.get('prompt'))}</h2>
    <p class="muted">期望：{esc(case.get('expected_output'))}</p></header>
  <div class="badges">{badges}</div>
  <div class="grid">{grids}</div>
  <h3>人工判断（PASS/FAIL/NA；PASS 必须能指出具体证据）</h3>
  <table class="rubric"><thead><tr><th>维度</th>{head}</tr></thead>
  <tbody>{rubric_rows}</tbody></table>
  {evidence}{pref}
</section>""")

    doc = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>task-brief v2 vs v1 人工审核</title><style>
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
select{{width:100%;padding:3px}}
.note{{display:block;margin-top:8px;font-size:12px;color:var(--dim)}}
textarea{{width:100%;border:1px solid var(--line);border-radius:4px;padding:5px;font:inherit}}
.pref{{display:block;margin-top:10px;font-size:12px}}
.bar{{position:sticky;top:0;z-index:2;background:var(--bg);padding:10px 36px;border-bottom:1px solid var(--line);
display:flex;gap:10px;align-items:center}}
button{{border:1px solid var(--line);background:#fff;border-radius:6px;padding:6px 12px;cursor:pointer}}
button.primary{{background:#1d1d1f;color:#fff;border-color:#1d1d1f}}
.btn{{border:1px solid var(--line);background:#fff;border-radius:6px;padding:6px 12px;cursor:pointer;font-size:13px}}
</style></head><body>
<header class="page"><h1>task-brief：v2 方法 vs v1 格式组</h1>
<p class="muted">两边看到的是同一 prompt、同一模型、同一 schema；唯一差别是 v2 有工程分析方法，v1 只给输出字段。</p>
<p class="muted">自动断言只查结构；语义请按 PASS/FAIL/NA 判，PASS 必须写具体证据（例如“关系轴写成 environment，依据是沙尘”）。</p></header>
<div class="bar">
<button class="primary" id="fs">选择文件并开启实时保存</button>
<button id="export">导出评分/反馈</button>
<label class="btn">导入评分<input type="file" id="import" accept=".json" hidden></label>
<span class="muted" id="saved">输入会自动保存在本浏览器；建议点左侧按钮写入文件</span></div>
<main>{''.join(cards)}</main>
<script>
const KEY='task-brief-review-v1b';
let fileHandle=null, timer=null;
const statusEl=document.getElementById('saved');
function collect(){{
  const a={{}}; document.querySelectorAll('select,textarea').forEach(el=>{{
    const k=el.dataset.k||el.dataset.note; if(k) a[k]=el.value;
  }}); return a;
}}
function saveLocal(){{
  try{{localStorage.setItem(KEY,JSON.stringify(collect()));return true}}
  catch(e){{statusEl.textContent='浏览器本地存储不可用：请用“选择文件并开启实时保存”';return false}}
}}
function payload(){{return JSON.stringify({{review:collect(),saved_at:new Date().toISOString()}},null,1)}}
async function saveFile(){{
  if(!fileHandle) return;
  try{{
    const w=await fileHandle.createWritable(); await w.write(payload()); await w.close();
    statusEl.textContent='已写入文件 · '+new Date().toLocaleTimeString();
  }}catch(e){{statusEl.textContent='写文件失败：'+e.message}}
}}
function schedule(){{
  if(saveLocal()) statusEl.textContent='已保存到本浏览器 · '+new Date().toLocaleTimeString();
  if(fileHandle){{clearTimeout(timer);timer=setTimeout(saveFile,250);}}
}}
document.querySelectorAll('select,textarea').forEach(el=>{{
  const k=el.dataset.k||el.dataset.note;
  try{{const all=JSON.parse(localStorage.getItem(KEY)||'{{}}'); if(all[k]!==undefined) el.value=all[k];}}catch(e){{}}
  el.addEventListener('input',schedule); el.addEventListener('change',schedule);
}});
document.getElementById('fs').onclick=async()=>{{
  if(!window.showSaveFilePicker){{statusEl.textContent='当前浏览器不支持直接写文件；已用本地存储，请用“导出”备份';return}}
  try{{
    fileHandle=await window.showSaveFilePicker({{suggestedName:'task-brief-review.json',
      types:[{{description:'JSON',accept:{{'application/json':['.json']}}}}]}});
    await saveFile();
  }}catch(e){{statusEl.textContent='未选择文件（输入仍保存在本浏览器）';}}
}};
document.getElementById('export').onclick=()=>{{
  const blob=new Blob([payload()],{{type:'application/json'}});
  const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='task-brief-review-v1b.json';a.click();
}};
document.getElementById('import').onchange=async(e)=>{{
  const f=e.target.files[0]; if(!f) return;
  try{{
    const d=JSON.parse(await f.text()); const rev=d.review||d;
    document.querySelectorAll('select,textarea').forEach(el=>{{
      const k=el.dataset.k||el.dataset.note;
      if(rev[k]!==undefined) el.value=rev[k];
    }});
    saveLocal(); if(fileHandle) await saveFile();
    statusEl.textContent='已导入 '+f.name;
  }}catch(err){{statusEl.textContent='导入失败：'+err.message}}
}};
window.addEventListener('beforeunload',()=>{{ saveLocal(); if(fileHandle) saveFile(); }});
window.addEventListener('pagehide',()=>{{ saveLocal(); }});
</script></body></html>"""
    out = base / "review.html"
    out.write_text(doc, encoding="utf-8")
    print(json.dumps({"out": str(out), "cases": len(by), "arms": [a for a, _ in arms]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
