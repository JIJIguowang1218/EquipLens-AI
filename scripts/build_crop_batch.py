# -*- coding: utf-8 -*-
"""批量裁框编辑器 v2：支持同一车型多张图，框可以挂到"有这件的那张图"上。

用法:
  PYTHONPATH=src python scripts/build_crop_batch.py \
      --analysis-dir data-test/analysis-20261031 --out data-test/edit-batch
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SLOT_CN = {"grille": "进气格栅", "bumper": "保险杠", "side_guard": "侧防护栏",
           "wheel_arch": "前轮轮拱", "step": "登车踏步", "headlamp": "大灯",
           "mirror": "后视镜", "sun_visor": "遮阳板", "under_guard": "下护板"}

VIEW_CN = {"hero_lf": "主图", "hero_rf": "主图", "hero_45": "主图", "side_l": "侧视",
           "side": "侧视", "side_r": "侧视", "front": "正视", "rear": "后视",
           "detail": "特写"}

HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>裁框 · 批量</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0e1013;color:#e6e8ec;font:14px/1.6 "Microsoft YaHei",sans-serif;
height:100vh;display:flex;flex-direction:column;overflow:hidden}
.top{display:flex;align-items:center;gap:14px;padding:10px 20px;border-bottom:1px solid #23272e;
background:#12151a}
.top h1{font-size:13px;letter-spacing:.04em;font-weight:600;color:#a7b0bb}
.chips{display:flex;gap:5px}
.chip{width:24px;height:24px;border-radius:5px;background:#1d2127;border:1px solid #2a2f38;
display:flex;align-items:center;justify-content:center;font-size:10.5px;color:#8b93a1;cursor:pointer}
.chip.cur{box-shadow:0 0 0 2px #4ea1ff;color:#fff}
.chip.done{background:#17351f;border-color:#2b6b3d;color:#8fdcae}
.spacer{flex:1}
.btn{background:#4ea1ff;color:#06121f;border:0;border-radius:6px;padding:8px 14px;font-weight:700;
cursor:pointer;font-size:13px}
.btn.ghost{background:#232833;color:#c9d1d9;font-weight:500}
.wrap{flex:1;display:grid;grid-template-columns:1fr 340px;min-height:0}
.stagewrap{padding:16px 20px;display:flex;flex-direction:column;gap:10px;background:#14161a;
overflow:auto}
.tabs{display:flex;gap:8px}
.tab{padding:5px 12px;border-radius:6px;background:#1d2127;border:1px solid #2a2f38;font-size:12px;
color:#9aa3ae;cursor:pointer}
.tab.cur{background:#26303e;border-color:#4ea1ff;color:#fff}
.canvas{flex:1;display:flex;align-items:center;justify-content:center;min-height:0}
#stage{position:relative;line-height:0;box-shadow:0 12px 40px rgba(0,0,0,.5)}
#stage img{display:block;max-width:100%;max-height:calc(100vh - 190px);user-select:none}
.box{position:absolute;border:1.5px solid #4ea1ff;background:rgba(78,161,255,.10);cursor:move;
touch-action:none}
.box.sel{border-color:#ffd166;background:rgba(255,209,102,.14);z-index:5}
.box .lab{position:absolute;top:-21px;left:-1px;white-space:nowrap;font-size:10.5px;background:#4ea1ff;
color:#08111c;padding:0 6px;letter-spacing:.03em;line-height:17px}
.box.sel .lab{background:#ffd166}
.h{position:absolute;width:10px;height:10px;background:#fff;border:1.5px solid #4ea1ff;border-radius:50%}
.h.nw{left:-5px;top:-5px;cursor:nwse-resize}.h.ne{right:-5px;top:-5px;cursor:nesw-resize}
.h.sw{left:-5px;bottom:-5px;cursor:nesw-resize}.h.se{right:-5px;bottom:-5px;cursor:nwse-resize}
aside{background:#171a1f;border-left:1px solid #23272e;padding:16px;display:flex;flex-direction:column;
gap:10px;overflow:auto}
aside h2{font-size:14px}
.hint{font-size:11.5px;color:#8b93a1;line-height:1.65}
ul{list-style:none;display:flex;flex-direction:column;gap:5px}
li{display:flex;align-items:center;gap:7px;font-size:12px;padding:6px 8px;border-radius:6px;
background:#1d2127;cursor:pointer}
li.sel{background:#2a3240;box-shadow:inset 0 0 0 1px #4ea1ff}
li.skip{opacity:.42;text-decoration:line-through}
li i{width:7px;height:7px;border-radius:2px;background:#4ea1ff;flex:none}
li.sel i{background:#ffd166}
li .badge{font-size:9.5px;padding:0 5px;border-radius:3px;background:#2b3542;color:#9fb6cc;margin-left:auto}
li .act{font-size:10px;color:#6f7887;padding:1px 5px;border:1px solid #2a2f38;border-radius:4px}
li .act:hover{color:#ffd166;border-color:#ffd166}
textarea{min-height:90px;background:#0d0f13;color:#9fe0a0;border:1px solid #23272e;border-radius:6px;
padding:8px;font:11px/1.45 Consolas,monospace;resize:none}
.done-panel{position:absolute;inset:0;background:rgba(10,12,15,.93);display:none;align-items:center;
justify-content:center;flex-direction:column;gap:12px;z-index:20;text-align:center;padding:40px}
.done-panel.on{display:flex}
.done-panel p{color:#8b93a1;font-size:13px;max-width:520px}
</style></head><body>
<div class="top">
  <h1>部件裁框</h1>
  <div class="chips" id="chips"></div>
  <div class="spacer"></div>
  <span id="status" style="font-size:12px;color:#6f7887"></span>
  <button class="btn ghost" id="prev">上一台</button>
  <button class="btn ghost" id="copy">复制本台</button>
  <button class="btn" id="ok">这张好了 → 下一台</button>
</div>
<div class="wrap">
  <div class="stagewrap">
    <div class="tabs" id="tabs"></div>
    <div class="canvas"><div id="stage"><img id="img" alt=""></div></div>
  </div>
  <aside>
    <h2 id="vname">—</h2>
    <div class="hint">选一张<b>有该部件</b>的图，把框拖上去——框属于当前这张图。某件所有图都看不到就点「跳过」。</div>
    <ul id="list"></ul>
    <textarea id="out" readonly></textarea>
  </aside>
</div>
<div class="done-panel" id="panel">
  <h2 style="font-size:20px">全部完成</h2>
  <p id="psum"></p>
  <button class="btn ghost" id="again">回到第一台</button>
</div>
<script>
const DATA = __DATA__;
let idx = 0, sel = 0, imgIdx = 0;
const done = new Set();
const img = document.getElementById('img'), stage = document.getElementById('stage');
const list = document.getElementById('list'), chips = document.getElementById('chips');
const tabsEl = document.getElementById('tabs'), out = document.getElementById('out');
const panel = document.getElementById('panel');
const cur = () => DATA[idx];
const curImg = () => cur().imgs[imgIdx];

function pct(b){return {l:b[0]/10,t:b[1]/10,w:(b[2]-b[0])/10,h:(b[3]-b[1])/10};}
function draw(){
  stage.querySelectorAll('.box').forEach(e=>e.remove());
  cur().parts.forEach((p,i)=>{
    if(p.skip || p.src !== curImg().src || !p.bbox) return;
    const b=pct(p.bbox);
    const d=document.createElement('div');
    d.className='box'+(i===sel?' sel':'');
    d.style.cssText=`left:${b.l}%;top:${b.t}%;width:${b.w}%;height:${b.h}%`;
    d.dataset.i=i;
    d.innerHTML='<span class="lab">'+(i+1)+' · '+p.label+'</span>'+
      ['nw','ne','sw','se'].map(k=>'<span class="h '+k+'" data-k="'+k+'"></span>').join('');
    stage.appendChild(d);
  });
  renderList(); renderChips(); renderTabs(); dump();
}
function renderList(){
  list.innerHTML='';
  cur().parts.forEach((p,i)=>{
    const li=document.createElement('li');
    if(i===sel) li.className='sel';
    if(p.skip) li.className=(li.className+' skip').trim();
    const n=cur().imgs.findIndex(im=>im.src===p.src)+1;
    li.innerHTML='<i></i><span>'+(i+1)+' · '+p.label+'</span>'+
      '<span class="badge">'+(p.skip?'跳过':'图'+n)+'</span>'+
      '<span class="act" data-skip="'+i+'">'+(p.skip?'恢复':'跳过')+'</span>';
    li.onclick=(e)=>{
      if(e.target.dataset.skip!==undefined){ p.skip=!p.skip; draw(); return; }
      sel=i;
      const j=cur().imgs.findIndex(im=>im.src===p.src);
      if(j>=0 && j!==imgIdx){ imgIdx=j; img.src=curImg().src; }
      draw();
    };
    list.appendChild(li);
  });
}
function renderChips(){
  chips.innerHTML='';
  DATA.forEach((d,i)=>{
    const c=document.createElement('div');
    c.className='chip'+(i===idx?' cur':'')+(done.has(i)?' done':'');
    c.textContent=done.has(i)?'✓':(i+1); c.title=d.title;
    c.onclick=()=>{idx=i;sel=0;imgIdx=0;render();};
    chips.appendChild(c);
  });
  document.getElementById('vname').textContent=`${idx+1} / ${DATA.length} · ${cur().title}`;
  document.getElementById('prev').disabled = idx===0;
}
function renderTabs(){
  tabsEl.innerHTML='';
  cur().imgs.forEach((im,j)=>{
    const t=document.createElement('div');
    t.className='tab'+(j===imgIdx?' cur':'');
    t.textContent='图'+(j+1)+' · '+im.view;
    t.onclick=()=>{imgIdx=j;img.src=im.src;draw();};
    tabsEl.appendChild(t);
  });
}
function render(){
  imgIdx=0; sel=0; img.src=curImg().src;
  document.getElementById('status').textContent = done.has(idx)?'已确认':'';
  draw();
}
function dump(){
  out.value=JSON.stringify({slug:cur().slug,parts:cur().parts.map(p=>
    ({slot:p.slot,bbox:p.skip?null:p.bbox,src:p.skip?null:p.src,skip:!!p.skip}))},null,1);
}
let drag=null;
stage.addEventListener('pointerdown',e=>{
  const handle=e.target.closest('.h'), box=e.target.closest('.box');
  if(!box) return;
  sel=+box.dataset.i; draw();
  const r=stage.getBoundingClientRect();
  drag={i:sel,handle:handle?handle.dataset.k:null,sx:e.clientX,sy:e.clientY,
        orig:cur().parts[sel].bbox.slice(),rw:r.width,rh:r.height};
  e.target.setPointerCapture(e.pointerId);
});
window.addEventListener('pointermove',e=>{
  if(!drag) return;
  const dx=(e.clientX-drag.sx)/drag.rw*1000, dy=(e.clientY-drag.sy)/drag.rh*1000;
  let [x1,y1,x2,y2]=drag.orig;
  if(!drag.handle){x1+=dx;x2+=dx;y1+=dy;y2+=dy;}
  else{
    if(drag.handle.includes('w')) x1=Math.min(x2-15,x1+dx);
    if(drag.handle.includes('e')) x2=Math.max(x1+15,x2+dx);
    if(drag.handle.includes('n')) y1=Math.min(y2-10,y1+dy);
    if(drag.handle.includes('s')) y2=Math.max(y1+10,y2+dy);
  }
  const p=cur().parts[drag.i];
  p.bbox=[x1,y1,x2,y2].map(v=>Math.round(Math.max(0,Math.min(1000,v))));
  p.src=curImg().src;
  const el=stage.querySelectorAll('.box')[drag.i], b=pct(p.bbox);
  el.style.cssText=`left:${b.l}%;top:${b.t}%;width:${b.w}%;height:${b.h}%`;
  dump();
});
window.addEventListener('pointerup',()=>{drag=null;});
const SERVER='http://127.0.0.1:8766/save';
function setStatus(t){document.getElementById('status').textContent=t;}
async function persist(){
  const d=cur();
  const payload={slug:d.slug,parts:d.parts.map(p=>({slot:p.slot,bbox:p.skip?null:p.bbox,
    src:p.skip?null:p.src,skip:!!p.skip}))};
  try{
    const r=await fetch(SERVER,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)});
    if(r.ok){ setStatus('已保存'); return; }
  }catch(e){}
  setStatus('保存失败，请点复制');
}
document.getElementById('ok').onclick=()=>{
  persist(); done.add(idx);
  if(idx<DATA.length-1){ idx++; render(); }
  else{ renderChips();
    document.getElementById('psum').textContent=`已确认 ${done.size} / ${DATA.length} 台`;
    panel.classList.add('on'); }
};
document.getElementById('prev').onclick=()=>{if(idx>0){idx--;render();}};
document.getElementById('copy').onclick=async()=>{
  await navigator.clipboard.writeText(out.value); setStatus('已复制');
};
document.getElementById('again').onclick=()=>{panel.classList.remove('on');idx=0;render();};
img.onload=draw;
render();
</script></body></html>"""


def candidates(conn, model: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """select a.file_path, a.view_angle, a.width*a.height px from assets a
           join vehicles v on v.id=a.vehicle_id
           where v.model_name=? and a.file_path is not null
             and a.view_angle in ('hero_lf','hero_rf','hero_45','side_l','side',
                                  'side_r','front','rear')
           order by px desc""", (model,)).fetchall()
    best: dict[str, dict] = {}
    for r in rows:
        if r["view_angle"] not in best:
            best[r["view_angle"]] = dict(r)
    order = ["hero_lf", "hero_45", "hero_rf", "side_l", "side", "side_r", "front", "rear"]
    out = []
    for v in order:
        if v in best and len(out) < 4:
            out.append({"src": best[v]["file_path"], "view": VIEW_CN.get(v, v)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--data-dir", default="data-test")
    ap.add_argument("--boxes-dir", default="data-test/edit-batch")
    args = ap.parse_args()

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ROOT / args.data_dir / "equiplens.db")
    files = sorted(p for p in (ROOT / args.analysis_dir).glob("*.json")
                   if not p.name.startswith("_"))
    data = []
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        v = d.get("vehicle", {})
        hero = d["assets"]["hero"]
        others = [x for x in candidates(conn, v.get("model", "")) if x["src"] != hero]
        imgs = [{"src": hero, "view": "主图"}] + others[:3]
        saved = {}
        fp = ROOT / args.boxes_dir / f"{v.get('model','')}-boxes.json"
        if fp.exists():
            saved = {p["slot"]: p for p in json.loads(fp.read_text(encoding="utf-8")).get("parts", [])}
        rel = {i["src"]: os.path.relpath(ROOT / args.data_dir / i["src"], outdir)
                            .replace("\\", "/") for i in imgs}
        parts = []
        for p in d.get("parts", []):
            base = saved.get(p["slot"], {})
            src = base.get("src") or hero
            if src not in rel:
                src = hero
            src = rel[src]
            parts.append({"slot": p["slot"], "label": SLOT_CN.get(p["slot"], p["slot"]),
                          "term": p.get("term") or "",
                          "bbox": base.get("bbox") or p.get("bbox") or [400, 400, 600, 600],
                          "src": src, "skip": bool(base.get("skip"))})
        data.append({"slug": v.get("model", f.stem),
                     "title": f"{v.get('brand','')} {v.get('model','')}".strip(),
                     "imgs": [{"src": rel[i["src"]], "view": i["view"]} for i in imgs],
                     "parts": parts})

    html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    out = outdir / "crop-batch.html"
    out.write_text(html, encoding="utf-8")
    print(f"[ok] {out}  vehicles={len(data)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
