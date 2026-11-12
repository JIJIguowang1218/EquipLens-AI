# -*- coding: utf-8 -*-
"""去重审核页：把 plan 里的合并结果给人看，人工判定“合并是否正确”。

背景：q12 沙漠牵引车 27 条抽取合并成 14 个候选（去重率 48%），
是否并错/该并没并，机器判不了，需要人审。

输入：plan.json（含 model_variants / source_queries / sources）
输出：单文件 HTML（可离线打开；localStorage 不可用时用导出 JSON 兜底）

用法:
  PYTHONPATH=src python scripts/build_dedupe_review.py \
    --plan data-test/runs/.../plan.json --out .../dedupe-review.html
"""
from __future__ import annotations

import argparse
import json
import re
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tokens(s: str) -> set[str]:
    s = (s or "").lower().replace("×", "x")
    out = set(re.findall(r"[a-z]{2,}\d*|\d{3,}|[\u4e00-\u9fff]{2,4}", s))
    return {t for t in out if t not in {"沙漠", "牵引", "车型", "卡车", "全驱"}}


def similarity(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def build_payload(plan: dict, brief: dict | None) -> dict:
    cands = plan.get("candidates") or []
    rows = []
    for c in cands:
        rows.append({
            "model": c.get("model"),
            "identity_kind": c.get("identity_kind"),
            "identity": c.get("identity"),
            "variants": c.get("model_variants") or [c.get("model")],
            "queries": [q for q in (c.get("source_queries") or []) if q.get("query")],
            "sources": c.get("sources") or [],
            "source_count": c.get("source_count") or len(c.get("sources") or []),
            "reason": c.get("reason") or "",
        })
    pairs = []
    for (i, a), (j, b) in combinations(enumerate(rows), 2):
        s = similarity(a["model"], b["model"])
        if s >= 0.34:
            pairs.append({"a": i, "b": j, "score": round(s, 2)})
    pairs.sort(key=lambda p: -p["score"])
    return {
        "class": ((brief or {}).get("request") or {}).get("class", ""),
        "brief_id": (brief or {}).get("brief_id") or plan.get("brief_id"),
        "candidates": rows,
        "suggested_pairs": pairs[:12],
        "stats": {
            "unique": len(rows),
            "variants": sum(len(r["variants"]) for r in rows),
            "dedupe": plan.get("dedupe") or {},
            "queries": len(plan.get("queries") or []),
            "topup": plan.get("topup") or {},
        },
    }


def render_html(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>去重审核 · {payload.get('class','')}</title>
<style>
:root{{--bg:#f7f6f2;--ink:#1b1b1b;--sub:#6b6b6b;--line:#dcd7cc;--acc:#2f6f4f;--warn:#b3541e}}
*{{box-sizing:border-box}} body{{margin:0;font:14px/1.6 -apple-system,"Segoe UI","Noto Sans SC",sans-serif;background:var(--bg);color:var(--ink)}}
header{{padding:18px 24px;border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:5}}
h1{{margin:0 0 4px;font-size:17px}} .sub{{color:var(--sub);font-size:12px}}
.stats{{display:flex;gap:18px;margin-top:8px;font-size:12px;color:var(--sub);flex-wrap:wrap}}
main{{padding:20px 24px;max-width:1180px;margin:0 auto}}
.card{{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin-bottom:12px}}
.card.suspect{{border-left:4px solid var(--warn)}}
.model{{font-weight:600;font-size:15px}}
.meta{{color:var(--sub);font-size:12px;margin:2px 0 8px}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}}
.chip{{background:#eef1ea;border:1px solid var(--line);border-radius:999px;padding:1px 9px;font-size:12px}}
.chip.dup{{background:#fdeee6;border-color:#f0c9b3}}
details summary{{cursor:pointer;color:var(--sub);font-size:12px;margin-top:6px}}
.src{{font-size:12px;word-break:break-all;color:#33566d}}
.verdict{{display:flex;gap:14px;margin-top:10px;font-size:13px;flex-wrap:wrap}}
.verdict label{{cursor:pointer}}
input[type=text]{{width:100%;margin-top:8px;padding:6px 8px;border:1px solid var(--line);border-radius:6px;font:inherit}}
.bar{{position:fixed;right:18px;bottom:18px;display:flex;gap:8px}}
button{{padding:8px 14px;border-radius:6px;border:1px solid var(--line);background:#fff;cursor:pointer;font:inherit}}
button.primary{{background:var(--acc);color:#fff;border-color:var(--acc)}}
.hint{{color:var(--sub);font-size:12px}}
</style></head><body>
<header>
  <h1>去重审核 · {payload.get('class','')}</h1>
  <div class="sub">任务单 {payload.get('brief_id','')} · 目标：判断「合并是否正确」以及「疑似同款是否该合并」</div>
  <div class="stats" id="stats"></div>
</header>
<main>
  <p class="hint">每张卡 = 合并后的一个候选。红色左边框 = 与其他候选词元重叠较高（疑似同款，需你判断是“该合并”还是“本来就不同”）。判完点右下角导出 JSON。</p>
  <div id="cards"></div>
</main>
<div class="bar">
  <button onclick="copyJSON()">复制 JSON</button>
  <button class="primary" onclick="exportJSON()">导出判定 JSON</button>
</div>
<script>
const DATA = {data};
const KEY = 'dedupe-review:' + (DATA.brief_id || '') + ':' + (DATA.class || '');
let state = {{}};
try {{ state = JSON.parse(localStorage.getItem(KEY) || '{{}}'); }} catch (e) {{ state = {{}}; }}
const suspect = new Set();
(DATA.suggested_pairs || []).forEach(p => {{ suspect.add(p.a); suspect.add(p.b); }});

function save() {{
  try {{ localStorage.setItem(KEY, JSON.stringify(state)); }} catch (e) {{}}
}}

function render() {{
  const st = DATA.stats || {{}};
  document.getElementById('stats').innerHTML = [
    '唯一候选 <b>' + st.unique + '</b>',
    '合并进来的写法 <b>' + st.variants + '</b>',
    '抽取行 <b>' + ((st.dedupe||{{}}).input ?? '—') + '</b>',
    '去重移除 <b>' + ((st.dedupe||{{}}).removed ?? '—') + '</b>',
    '查询 <b>' + (st.queries ?? '—') + '</b>',
    '补查 <b>' + ((st.topup||{{}}).queries ?? 0) + '</b>'
  ].join(' · ');

  const box = document.getElementById('cards');
  box.innerHTML = '';
  DATA.candidates.forEach((c, i) => {{
    const div = document.createElement('div');
    div.className = 'card' + (suspect.has(i) ? ' suspect' : '');
    const v = c.variants || [];
    const variantChips = v.map(x => `<span class="chip${{v.length>1?' dup':''}}">${{esc(x)}}</span>`).join('');
    const qs = (c.queries || []).map(q => `<span class="chip">${{esc(q.query_id||'')}} · ${{esc((q.query||'').slice(0,60))}}</span>`).join('');
    const srcs = (c.sources || []).slice(0, 6).map(u => `<div class="src">${{esc(u)}}</div>`).join('');
    div.innerHTML = `
      <div class="model">${{i+1}}. ${{esc(c.model)}}</div>
      <div class="meta">identity=${{esc(c.identity_kind||'')}} · 来源 ${{c.source_count||0}} 条 · 写法 ${{v.length}} 种${{v.length>1?' <b>（合并了）</b>':''}}</div>
      <div class="chips">${{variantChips}}</div>
      <div class="chips">${{qs}}</div>
      <details><summary>来源链接（${{(c.sources||[]).length}}）</summary>${{srcs || '<div class="src">—</div>'}}</details>
      <div class="verdict">
        <label><input type="radio" name="v${{i}}" value="ok" ${{state[i]?.verdict==='ok'?'checked':''}}> 合并正确</label>
        <label><input type="radio" name="v${{i}}" value="split" ${{state[i]?.verdict==='split'?'checked':''}}> 应拆分</label>
        <label><input type="radio" name="v${{i}}" value="drop" ${{state[i]?.verdict==='drop'?'checked':''}}> 不该保留</label>
      </div>
      <input type="text" placeholder="备注：要拆成哪几台 / 为什么不该保留（可空）"
             value="${{esc(state[i]?.note||'')}}" oninput="setNote(${{i}}, this.value)">
    `;
    div.querySelectorAll('input[type=radio]').forEach(r => r.onchange = () => {{
      state[i] = state[i] || {{}}; state[i].verdict = r.value; save();
    }});
    box.appendChild(div);
  }});
}}
function setNote(i, val) {{ state[i] = state[i] || {{}}; state[i].note = val; save(); }}
function esc(s) {{ return String(s ?? '').replace(/[&<>"']/g, m => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}})[m]); }}
function payload() {{
  return {{
    class: DATA.class, brief_id: DATA.brief_id, exported_at: new Date().toISOString(),
    verdicts: DATA.candidates.map((c, i) => ({{
      index: i + 1, model: c.model, identity_kind: c.identity_kind,
      variants: c.variants, verdict: (state[i]||{{}}).verdict || '',
      note: (state[i]||{{}}).note || ''
    }}))
  }};
}}
function exportJSON() {{
  const blob = new Blob([JSON.stringify(payload(), null, 1)], {{type: 'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'dedupe-verdicts.json';
  a.click();
}}
function copyJSON() {{ navigator.clipboard?.writeText(JSON.stringify(payload(), null, 1)); }}
render();
</script></body></html>"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--brief", default="")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    brief = (json.loads(Path(args.brief).read_text(encoding="utf-8"))
             if args.brief else None)
    out = Path(args.out) if args.out else Path(args.plan).with_name("dedupe-review.html")
    out.write_text(render_html(build_payload(plan, brief)), encoding="utf-8")
    print(json.dumps({"out": str(out),
                      "candidates": len(plan.get("candidates") or []),
                      "variants": sum(len(c.get("model_variants") or [])
                                      for c in (plan.get("candidates") or []))},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
