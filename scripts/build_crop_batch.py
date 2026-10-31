# -*- coding: utf-8 -*-
"""批量裁框编辑器：10 台车逐张过，点「这张好了」即下载该车 bbox 并跳下一张。

用法:
  PYTHONPATH=src python scripts/build_crop_batch.py \
      --analysis-dir data-test/analysis-20261031 --out data-test/edit-batch
"""

from __future__ import annotations

import argparse
import json
import os
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

HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>裁框 · 批量</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0e1013;color:#e6e8ec;font:14px/1.6 "Microsoft YaHei",sans-serif;
height:100vh;display:flex;flex-direction:column;overflow:hidden}
.top{display:flex;align-items:center;gap:16px;padding:12px 22px;border-bottom:1px solid #23272e;
background:#12151a}
.top h1{font-size:14px;letter-spacing:.04em;font-weight:600}
.chips{display:flex;gap:6px}
.chip{width:26px;height:26px;border-radius:6px;background:#1d2127;border:1px solid #2a2f38;
display:flex;align-items:center;justify-content:center;font-size:11px;color:#8b93a1;cursor:pointer}
.chip.cur{box-shadow:0 0 0 2px #4ea1ff;color:#fff}
.chip.done{background:#17351f;border-color:#2b6b3d;color:#8fdcae}
.spacer{flex:1}
.btn{background:#4ea1ff;color:#06121f;border:0;border-radius:7px;padding:9px 16px;font-weight:700;
cursor:pointer;letter-spacing:.02em}
.btn.ghost{background:#232833;color:#c9d1d9;font-weight:500}
.btn:disabled{opacity:.4;cursor:not-allowed}
.wrap{flex:1;display:grid;grid-template-columns:1fr 330px;min-height:0}
.stagewrap{padding:22px;display:flex;align-items:center;justify-content:center;background:#14161a;
overflow:auto}
#stage{position:relative;line-height:0;box-shadow:0 12px 40px rgba(0,0,0,.5)}
#stage img{display:block;max-width:100%;max-height:calc(100vh - 120px);user-select:none}
.box{position:absolute;border:1.5px solid #4ea1ff;background:rgba(78,161,255,.10);cursor:move;
touch-action:none}
.box.sel{border-color:#ffd166;background:rgba(255,209,102,.14);z-index:5}
.box .lab{position:absolute;top:-22px;left:-1px;white-space:nowrap;font-size:11px;background:#4ea1ff;
color:#08111c;padding:1px 7px;letter-spacing:.04em;line-height:18px}
.box.sel .lab{background:#ffd166}
.h{position:absolute;width:11px;height:11px;background:#fff;border:1.5px solid #4ea1ff;border-radius:50%}
.h.nw{left:-6px;top:-6px;cursor:nwse-resize}.h.ne{right:-6px;top:-6px;cursor:nesw-resize}
.h.sw{left:-6px;bottom:-6px;cursor:nesw-resize}.h.se{right:-6px;bottom:-6px;cursor:nwse-resize}
aside{background:#171a1f;border-left:1px solid #23272e;padding:18px;display:flex;flex-direction:column;
gap:12px;overflow:auto}
aside h2{font-size:15px}
.hint{font-size:12px;color:#8b93a1;line-height:1.7}
ul{list-style:none;display:flex;flex-direction:column;gap:6px}
li{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:6px 8px;border-radius:6px;
background:#1d2127;cursor:pointer}
li.sel{background:#2a3240;box-shadow:inset 0 0 0 1px #4ea1ff}
li i{width:8px;height:8px;border-radius:2px;background:#4ea1ff;flex:none}
li.sel i{background:#ffd166}
textarea{min-height:110px;background:#0d0f13;color:#9fe0a0;border:1px solid #23272e;border-radius:6px;
padding:10px;font:11.5px/1.5 Consolas,monospace;resize:none}
.done-panel{position:absolute;inset:0;background:rgba(10,12,15,.92);display:none;align-items:center;
justify-content:center;flex-direction:column;gap:14px;z-index:20}
.done-panel.on{display:flex}
.done-panel p{color:#8b93a1;font-size:13px}
</style></head><body>
<div class="top">
  <h1>部件裁框 · 批量</h1>
  <div class="chips" id="chips"></div>
  <div class="spacer"></div>
  <button class="btn ghost" id="prev">上一台</button>
  <button class="btn ghost" id="copy">复制本台 JSON</button>
  <span id="status" style="font-size:12px;color:#8b93a1;min-width:96px;text-align:right"></span>
  <button class="btn" id="ok">这张好了 → 下一台</button>
</div>
<div class="wrap">
  <div class="stagewrap"><div id="stage"><img id="img" alt=""></div></div>
  <aside>
    <h2 id="vname">—</h2>
    <div class="hint">拖动框移动，拖四角缩放。框内只留该部件本身。点「这张好了」会下载该车的 JSON 并跳到下一台。</div>
    <ul id="list"></ul>
    <textarea id="out" readonly></textarea>
    <div class="hint" id="tip"></div>
  </aside>
</div>
<div class="done-panel" id="panel">
  <h2 style="font-size:20px">全部完成</h2>
  <p id="psum"></p>
  <p>JSON 已逐个下载到浏览器下载目录，把文件放进 <code>data-test/edit-batch/</code> 即可回灌排版。</p>
  <button class="btn ghost" id="again">回到第一台</button>
</div>
<script>
const DATA = __DATA__;
let idx = 0, sel = 0;
const done = new Set();
const img = document.getElementById('img');
const stage = document.getElementById('stage');
const list = document.getElementById('list');
const chips = document.getElementById('chips');
const out = document.getElementById('out');
const panel = document.getElementById('panel');
const cur = () => DATA[idx];

function pct(b){return {l:b[0]/10,t:b[1]/10,w:(b[2]-b[0])/10,h:(b[3]-b[1])/10};}
function draw(){
  stage.querySelectorAll('.box').forEach(e=>e.remove());
  cur().parts.forEach((p,i)=>{
    const b=pct(p.bbox);
    const d=document.createElement('div');
    d.className='box'+(i===sel?' sel':'');
    d.style.cssText=`left:${b.l}%;top:${b.t}%;width:${b.w}%;height:${b.h}%`;
    d.dataset.i=i;
    d.innerHTML='<span class="lab">'+(i+1)+' · '+p.label+'</span>'+
      ['nw','ne','sw','se'].map(k=>'<span class="h '+k+'" data-k="'+k+'"></span>').join('');
    stage.appendChild(d);
  });
  renderList(); renderChips(); dump();
}
function renderList(){
  list.innerHTML='';
  cur().parts.forEach((p,i)=>{
    const li=document.createElement('li');
    if(i===sel) li.className='sel';
    li.innerHTML='<i></i><span>'+(i+1)+' · '+p.label+'</span>'+
      '<span style="margin-left:auto;color:#6f7887;font-size:11px">'+p.term+'</span>';
    li.onclick=()=>{sel=i;draw();};
    list.appendChild(li);
  });
}
function renderChips(){
  chips.innerHTML='';
  DATA.forEach((d,i)=>{
    const c=document.createElement('div');
    c.className='chip'+(i===idx?' cur':'')+(done.has(i)?' done':'');
    c.textContent=done.has(i)?'✓':(i+1);
    c.title=d.title;
    c.onclick=()=>{idx=i;sel=0;render();};
    chips.appendChild(c);
  });
  document.getElementById('vname').textContent=`${idx+1} / ${DATA.length} · ${cur().title}`;
  document.getElementById('prev').disabled = idx===0;
}
function render(){
  img.src=cur().img; sel=0;
  document.getElementById('tip').textContent = done.has(idx) ? '这台已确认过，可再调后重下。' : '';
  draw();
}
function dump(){
  out.value=JSON.stringify({slug:cur().slug,parts:cur().parts.map(p=>({slot:p.slot,bbox:p.bbox}))},null,1);
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
  cur().parts[drag.i].bbox=[x1,y1,x2,y2].map(v=>Math.round(Math.max(0,Math.min(1000,v))));
  const el=stage.querySelectorAll('.box')[drag.i], b=pct(cur().parts[drag.i].bbox);
  el.style.cssText=`left:${b.l}%;top:${b.t}%;width:${b.w}%;height:${b.h}%`;
  dump();
});
window.addEventListener('pointerup',()=>{drag=null;});
const SERVER = 'http://127.0.0.1:8766/save';
async function persist(){
  const d=cur();
  const payload={slug:d.slug,parts:d.parts.map(p=>({slot:p.slot,bbox:p.bbox}))};
  try{
    const r=await fetch(SERVER,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)});
    if(r.ok){ setStatus('已保存到本地'); return; }
  }catch(e){}
  download(); setStatus('浏览器下载');
}
function setStatus(t){document.getElementById('status').textContent=t;}
function download(){
  const d=cur();
  const blob=new Blob([JSON.stringify({slug:d.slug,parts:d.parts.map(p=>({slot:p.slot,bbox:p.bbox}))},null,1)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob); a.download=`${d.slug}-boxes.json`;
  document.body.appendChild(a); a.click(); a.remove();
}
document.getElementById('ok').onclick=()=>{
  persist(); done.add(idx);
  if(idx<DATA.length-1){ idx++; render(); }
  else{
    renderChips();
    document.getElementById('psum').textContent=`已确认 ${done.size} / ${DATA.length} 台`;
    panel.classList.add('on');
  }
};
document.getElementById('prev').onclick=()=>{if(idx>0){idx--;render();}};
document.getElementById('copy').onclick=async()=>{
  await navigator.clipboard.writeText(out.value);
  setStatus('已复制，粘贴给助手');
};
document.getElementById('again').onclick=()=>{panel.classList.remove('on');idx=0;render();};
img.onload=draw;
render();
</script></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--data-dir", default="data-test")
    args = ap.parse_args()

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in (ROOT / args.analysis_dir).glob("*.json")
                   if not p.name.startswith("_"))
    data = []
    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        v = d.get("vehicle", {})
        hero = ROOT / args.data_dir / d["assets"]["hero"]
        parts = [{"slot": p["slot"], "label": SLOT_CN.get(p["slot"], p["slot"]),
                  "term": p.get("term") or "", "bbox": p.get("bbox") or [400, 400, 600, 600]}
                 for p in d.get("parts", [])]
        data.append({"slug": v.get("model", f.stem), "title": f"{v.get('brand','')} {v.get('model','')}".strip(),
                     "img": os.path.relpath(hero, outdir).replace("\\", "/"), "parts": parts})

    html = HTML.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    out = outdir / "crop-batch.html"
    out.write_text(html, encoding="utf-8")
    print(f"[ok] {out}  vehicles={len(data)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
