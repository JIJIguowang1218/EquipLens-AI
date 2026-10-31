# -*- coding: utf-8 -*-
"""把 10 页报告串成一本翻页册（index.html）。

用法:
  PYTHONPATH=src python scripts/build_report_book.py \
      --analysis-dir data-test/analysis-20261031 --pages-dir data-test/report-book
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>竞品分析 · 10 台车</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0b0c0e;color:#e6e8ec;font:14px/1.6 "Microsoft YaHei",sans-serif;
height:100vh;display:flex;flex-direction:column;overflow:hidden}
.top{display:flex;align-items:center;gap:14px;padding:10px 20px;border-bottom:1px solid #23272e;
background:#111318;flex:none}
.top b{font-size:13px;letter-spacing:.04em}
.top .meta{color:#7d8695;font-size:12px}
.spacer{flex:1}
.btn{background:#1d2127;border:1px solid #2a2f38;color:#c9d1d9;border-radius:7px;padding:7px 14px;
cursor:pointer;font-size:12.5px}
.btn:hover{border-color:#4ea1ff;color:#fff}
.btn:disabled{opacity:.35;cursor:not-allowed}
.stage{flex:1;display:flex;align-items:center;justify-content:center;padding:16px;min-height:0}
.frame{width:min(100%, calc((100vh - 150px) * 16 / 9));aspect-ratio:16/9;background:#fff;
box-shadow:0 20px 60px rgba(0,0,0,.6);border-radius:4px;overflow:hidden;position:relative}
.scaler{position:absolute;top:0;left:0;width:1600px;height:900px;transform-origin:top left}
iframe{width:100%;height:100%;border:0;display:block}
.chips{display:flex;gap:6px;padding:10px 20px;border-top:1px solid #23272e;background:#111318;flex:none;
overflow-x:auto}
.chip{flex:none;padding:5px 12px;border-radius:6px;background:#1a1e25;border:1px solid #262b34;
color:#8b93a1;font-size:11.5px;cursor:pointer;white-space:nowrap}
.chip.cur{border-color:#4ea1ff;color:#fff;background:#22303f}
</style></head><body>
<div class="top">
  <b>竞品分析 · 10 台牵引车</b>
  <span class="meta" id="meta">—</span>
  <div class="spacer"></div>
  <button class="btn" id="prev">← 上一页</button>
  <button class="btn" id="next">下一页 →</button>
</div>
<div class="stage"><div class="frame" id="frame"><div class="scaler" id="scaler"><iframe id="view" src=""></iframe></div></div></div>
<div class="chips" id="chips"></div>
<script>
const PAGES = __PAGES__;
let i = 0;
const view = document.getElementById('view');
const chips = document.getElementById('chips');
function show(k){
  i = Math.max(0, Math.min(PAGES.length-1, k));
  view.src = PAGES[i].file;
  document.getElementById('meta').textContent =
    `${i+1} / ${PAGES.length} · ${PAGES[i].title} · ${PAGES[i].tags.join(' / ')}`;
  document.getElementById('prev').disabled = i===0;
  document.getElementById('next').disabled = i===PAGES.length-1;
  [...chips.children].forEach((c,j)=>c.classList.toggle('cur', j===i));
}
PAGES.forEach((p,k)=>{
  const c=document.createElement('div');
  c.className='chip'; c.textContent=(k+1)+' · '+p.title;
  c.onclick=()=>show(k); chips.appendChild(c);
});
document.getElementById('prev').onclick=()=>show(i-1);
document.getElementById('next').onclick=()=>show(i+1);
document.addEventListener('keydown',e=>{
  if(e.key==='ArrowRight'||e.key===' ') show(i+1);
  if(e.key==='ArrowLeft') show(i-1);
});
function fit(){
  const f=document.getElementById('frame');
  const k=f.clientWidth/1600;
  const sc=document.getElementById('scaler');
  sc.style.transform='scale('+k+')';
  sc.style.height=(900)+'px';
}
window.addEventListener('resize',fit);
show(0); fit();
</script></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--pages-dir", required=True)
    args = ap.parse_args()

    adir = ROOT / args.analysis_dir
    pdir = ROOT / args.pages_dir
    pages = []
    for f in sorted(adir.glob("*.json")):
        if f.name.startswith("_"):
            continue
        d = json.loads(f.read_text(encoding="utf-8"))
        v = d.get("vehicle", {})
        model = v.get("model", "")
        html = pdir / f"{model}.html"
        if not html.exists():
            print(f"[skip] {model} 无页面")
            continue
        pages.append({"file": html.name,
                      "title": f"{v.get('brand','')} {model}".strip(),
                      "tags": [t["tag"] for t in (d.get("unit") or {}).get("style_tags", [])]})

    out = pdir / "index.html"
    out.write_text(HTML.replace("__PAGES__", json.dumps(pages, ensure_ascii=False)),
                   encoding="utf-8")
    print(f"[ok] {out}  pages={len(pages)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
