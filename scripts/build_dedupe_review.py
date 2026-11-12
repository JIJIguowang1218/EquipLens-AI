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
import html as _html
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


_TEMPLATE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>去重审核 · %%CLASS%%</title>
<style>
:root{--bg:#f7f6f2;--ink:#1b1b1b;--sub:#6b6b6b;--line:#dcd7cc;--acc:#2f6f4f;--warn:#b3541e}
*{box-sizing:border-box} body{margin:0;font:14px/1.6 -apple-system,"Segoe UI","Noto Sans SC",sans-serif;background:var(--bg);color:var(--ink)}
header{padding:16px 24px;border-bottom:1px solid var(--line);background:#fff;position:sticky;top:0;z-index:5}
h1{margin:0 0 4px;font-size:17px} .sub{color:var(--sub);font-size:12px}
.stats{display:flex;gap:18px;margin-top:8px;font-size:12px;color:var(--sub);flex-wrap:wrap}
main{padding:18px 24px 90px;max-width:1180px;margin:0 auto}
.card{background:#fff;border:1px solid var(--line);border-radius:8px;padding:14px 16px;margin-bottom:12px;scroll-margin-top:130px}
.card.suspect{border-left:4px solid var(--warn)}
.model{font-weight:600;font-size:15px}
.meta{color:var(--sub);font-size:12px;margin:2px 0 6px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0;align-items:center}
.chip{border:1px solid var(--line);border-radius:999px;padding:1px 9px;font-size:12px;background:#eef1ea}
.chip.var{background:#eef1ea}
.chip.var.merged{background:#fdeee6;border-color:#f0c9b3}
.chip.q{background:#e8f3ec;border-color:#bcd9c8;color:#245c3f}
.chip.q.topup{border-style:dashed;font-weight:600}
.tag{font-size:11px;color:var(--sub);margin-right:4px}
details summary{cursor:pointer;color:var(--sub);font-size:12px;margin-top:6px}
.src{font-size:12px;word-break:break-all;color:#33566d}
.verdict{display:flex;gap:14px;margin-top:10px;font-size:13px;flex-wrap:wrap}
.verdict label{cursor:pointer}
input[type=text]{width:100%;margin-top:8px;padding:6px 8px;border:1px solid var(--line);border-radius:6px;font:inherit}
.bar{position:fixed;right:18px;bottom:18px;display:flex;gap:8px}
button{padding:8px 14px;border-radius:6px;border:1px solid var(--line);background:#fff;cursor:pointer;font:inherit}
button.primary{background:var(--acc);color:#fff;border-color:var(--acc)}
.hint{color:var(--sub);font-size:12px}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:12px;color:var(--sub);margin-top:8px}
.legend i{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:5px;vertical-align:-1px;border:1px solid var(--line)}
.legend i.red{width:12px;border-left:4px solid var(--warn);background:#fff}
.rules{background:#fff;border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:14px 0;font-size:13px}
.rules b{color:var(--acc)}
</style></head><body>
<header>
  <h1>去重审核 · %%CLASS%%</h1>
  <div class="sub">任务单 %%BRIEF%% · 判断两件事：① 这张卡把几种写法合并对了吗？② 两张卡是不是同一台车、该合并？</div>
  <div class="stats" id="stats"></div>
  <div class="legend">
    <span><i style="background:#eef1ea"></i>写法</span>
    <span><i style="background:#fdeee6"></i>合并了多种写法</span>
    <span><i style="background:#e8f3ec"></i>来源查询</span>
    <span><i style="background:#e8f3ec;border-style:dashed"></i>补查查询</span>
    <span><i class="red"></i>疑似同款</span>
  </div>
</header>
<main>
  <div class="rules">
    <b>怎么判：</b>
    ① 同一台车的不同写法（品牌前缀、空格/全半角、马力描述、括号补充）→ <b>合并正确</b>；
    ② 同车系但型号码/吨位/构型不同（Zetros 4051 vs 3643、400 马力 vs 460 马力）→ <b>应拆分</b>；
    ③ 两条卡描述同一台车（只差品牌前缀或一个“车”字）→ 备注写“应与 #N 合并”；
    ④ 泛称且无法定位到具体车型 → <b>不该保留</b>（或保留并注明泛称）。
    判完点右下角导出 JSON。
  </div>
  <p class="hint">橙色左边框 = 系统按词元相似度给的“疑似同款”提示，不是结论；写法区（灰/橙）才是合并结果，绿色是来源查询。</p>
  <div id="cards"></div>
</main>
<div class="bar">
  <button onclick="copyJSON()">复制 JSON</button>
  <button class="primary" onclick="exportJSON()">导出判定 JSON</button>
</div>
<script>
const DATA = %%DATA%%;
const KEY = 'dedupe-review:' + (DATA.brief_id || '') + ':' + (DATA.class || '');
let state = {};
try { state = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { state = {}; }
const suspects = {};
(DATA.suggested_pairs || []).forEach(function (p) {
  (suspects[p.a] = suspects[p.a] || []).push(p.b + 1);
  (suspects[p.b] = suspects[p.b] || []).push(p.a + 1);
});
function save() { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} }
function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (m) { return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]; }); }
function render() {
  const st = DATA.stats || {};
  document.getElementById('stats').innerHTML = [
    '唯一候选 <b>' + st.unique + '</b>',
    '合并写法 <b>' + st.variants + '</b>',
    '抽取行 <b>' + (((st.dedupe||{}).input) == null ? '—' : (st.dedupe||{}).input) + '</b>',
    '去重移除 <b>' + (((st.dedupe||{}).removed) == null ? '—' : (st.dedupe||{}).removed) + '</b>',
    '查询 <b>' + (st.queries == null ? '—' : st.queries) + '</b>',
    '补查 <b>' + (((st.topup||{}).queries) == null ? 0 : (st.topup||{}).queries) + '</b>'
  ].join(' · ');
  const box = document.getElementById('cards');
  box.innerHTML = '';
  DATA.candidates.forEach(function (c, i) {
    const div = document.createElement('div');
    div.className = 'card' + (suspects[i] ? ' suspect' : '');
    div.id = 'c' + (i + 1);
    const v = c.variants || [];
    const variantChips = v.map(function (x) {
      return '<span class="chip var' + (v.length > 1 ? ' merged' : '') + '">' + esc(x) + '</span>';
    }).join('');
    const qs = (c.queries || []).map(function (q) {
      const id = q.query_id || '';
      const top = id.indexOf('q-topup') === 0;
      return '<span class="chip q' + (top ? ' topup' : '') + '">' + (top ? '补查 · ' : '') + esc(id) +
             ' · ' + esc((q.query || '').slice(0, 60)) + '</span>';
    }).join('');
    const srcs = (c.sources || []).slice(0, 8).map(function (u) { return '<div class="src">' + esc(u) + '</div>'; }).join('');
    const sus = (suspects[i] || []).map(function (n) { return '<a href="#c' + n + '">#' + n + '</a>'; }).join('、');
    const cur = state[i] || {};
    div.innerHTML =
      '<div class="model">' + (i + 1) + '. ' + esc(c.model) + '</div>' +
      '<div class="meta">identity=' + esc(c.identity_kind || '') + ' · 来源 ' + (c.source_count || 0) +
        ' 条 · 写法 ' + v.length + ' 种' + (v.length > 1 ? ' <b>（合并了）</b>' : '') + '</div>' +
      (sus ? '<div class="meta" style="color:var(--warn)">疑似同款：' + sus + '（点编号跳转）</div>' : '') +
      '<div class="chips"><span class="tag">写法</span>' + variantChips + '</div>' +
      '<div class="chips"><span class="tag">来源查询</span>' + (qs || '<span class="chip">—</span>') + '</div>' +
      '<details><summary>来源链接（' + (c.sources || []).length + '）</summary>' + (srcs || '<div class="src">—</div>') + '</details>' +
      '<div class="verdict">' +
        '<label><input type="radio" name="v' + i + '" value="ok" ' + (cur.verdict === 'ok' ? 'checked' : '') + '> 合并正确</label>' +
        '<label><input type="radio" name="v' + i + '" value="split" ' + (cur.verdict === 'split' ? 'checked' : '') + '> 应拆分</label>' +
        '<label><input type="radio" name="v' + i + '" value="drop" ' + (cur.verdict === 'drop' ? 'checked' : '') + '> 不该保留</label>' +
      '</div>' +
      '<input type="text" placeholder="备注：要拆成哪几台 / 应与 #N 合并 / 为什么不该保留（可空）" value="' + esc(cur.note || '') + '" oninput="setNote(' + i + ', this.value)">';
    div.querySelectorAll('input[type=radio]').forEach(function (r) {
      r.onchange = function () { state[i] = state[i] || {}; state[i].verdict = r.value; save(); };
    });
    box.appendChild(div);
  });
}
function setNote(i, val) { state[i] = state[i] || {}; state[i].note = val; save(); }
function payload() {
  const pairs = [];
  DATA.candidates.forEach(function (c, i) {
    const note = (state[i] || {}).note || '';
    const m = note.match(/#(\\d+)/g) || [];
    m.forEach(function (x) { pairs.push({from: i + 1, to: parseInt(x.slice(1), 10)}); });
  });
  return {
    class: DATA.class, brief_id: DATA.brief_id, exported_at: new Date().toISOString(),
    verdicts: DATA.candidates.map(function (c, i) {
      const cur = state[i] || {};
      return {index: i + 1, model: c.model, identity_kind: c.identity_kind,
              variants: c.variants, verdict: cur.verdict || '', note: cur.note || ''};
    }),
    merge_suggestions: pairs
  };
}
function exportJSON() {
  const blob = new Blob([JSON.stringify(payload(), null, 1)], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'dedupe-verdicts.json';
  a.click();
}
function copyJSON() { if (navigator.clipboard) navigator.clipboard.writeText(JSON.stringify(payload(), null, 1)); }
render();
</script></body></html>"""


def render_html(payload: dict) -> str:
    return (_TEMPLATE
            .replace("%%DATA%%", json.dumps(payload, ensure_ascii=False))
            .replace("%%CLASS%%", _html.escape(payload.get("class", "")))
            .replace("%%BRIEF%%", _html.escape(str(payload.get("brief_id", "")))))


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
