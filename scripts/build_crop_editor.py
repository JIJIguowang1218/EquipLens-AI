# -*- coding: utf-8 -*-
"""裁框编辑器：在原图上把部件框画出来，允许拖动/缩放，导出 JSON。

用法:
  PYTHONPATH=src python scripts/build_crop_editor.py --analysis <json> --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SLOT_CN = {
    "grille": "进气格栅", "bumper": "保险杠", "side_guard": "侧防护栏",
    "wheel_arch": "前轮轮拱", "step": "登车踏步", "headlamp": "大灯",
    "mirror": "后视镜", "sun_visor": "遮阳板", "under_guard": "下护板",
}

HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>裁框 · __TITLE__</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0e1013;color:#e6e8ec;font:14px/1.6 "Microsoft YaHei",sans-serif}
.wrap{display:grid;grid-template-columns:1fr 320px;gap:0;height:100vh}
.stagewrap{padding:28px;display:flex;align-items:center;justify-content:center;
background:#14161a;overflow:auto}
#stage{position:relative;line-height:0;box-shadow:0 12px 40px rgba(0,0,0,.5)}
#stage img{display:block;max-width:100%;max-height:calc(100vh - 56px);user-select:none}
.box{position:absolute;border:1.5px solid #4ea1ff;background:rgba(78,161,255,.10);
cursor:move;touch-action:none}
.box.sel{border-color:#ffd166;background:rgba(255,209,102,.14);z-index:5}
.box .lab{position:absolute;top:-22px;left:-1px;white-space:nowrap;font-size:11px;
background:#4ea1ff;color:#08111c;padding:1px 7px;letter-spacing:.04em;line-height:18px}
.box.sel .lab{background:#ffd166}
.h{position:absolute;width:11px;height:11px;background:#fff;border:1.5px solid #4ea1ff;
border-radius:50%}
.h.nw{left:-6px;top:-6px;cursor:nwse-resize}.h.ne{right:-6px;top:-6px;cursor:nesw-resize}
.h.sw{left:-6px;bottom:-6px;cursor:nesw-resize}.h.se{right:-6px;bottom:-6px;cursor:nwse-resize}
aside{background:#171a1f;border-left:1px solid #23272e;padding:20px;display:flex;
flex-direction:column;gap:14px;overflow:auto}
h1{font-size:15px;letter-spacing:.05em}
.hint{font-size:12px;color:#8b93a1;line-height:1.7}
.hint b{color:#c9d1d9;font-weight:600}
ul{list-style:none;display:flex;flex-direction:column;gap:6px}
li{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:5px 8px;border-radius:6px;
background:#1d2127;cursor:pointer}
li.sel{background:#2a3240;box-shadow:inset 0 0 0 1px #4ea1ff}
li i{width:8px;height:8px;border-radius:2px;background:#4ea1ff;flex:none}
li.sel i{background:#ffd166}
textarea{flex:1;min-height:120px;background:#0d0f13;color:#9fe0a0;border:1px solid #23272e;
border-radius:6px;padding:10px;font:12px/1.5 Consolas,monospace;resize:none}
button{background:#4ea1ff;color:#06121f;border:0;border-radius:6px;padding:9px 14px;
font-weight:700;cursor:pointer;letter-spacing:.03em}
button.ghost{background:#232833;color:#c9d1d9}
.row{display:flex;gap:8px}
</style></head><body>
<div class="wrap">
  <div class="stagewrap"><div id="stage"><img id="img" src="__IMG__" alt=""></div></div>
  <aside>
    <h1>部件裁框 · __TITLE__</h1>
    <div class="hint">拖动框移动，拖四角缩放。<b>框内只留该部件本身</b>。全部调完再排版。</div>
    <ul id="list"></ul>
    <div class="row"><button id="copy">保存裁框</button>
      <button class="ghost" id="reset">复位</button></div>
    <textarea id="out" readonly></textarea>
  </aside>
</div>
<script>
const PARTS = __PARTS__;
const INIT = JSON.parse(JSON.stringify(PARTS));
const img = document.getElementById('img');
const stage = document.getElementById('stage');
const list = document.getElementById('list');
const out = document.getElementById('out');
let sel = 0;

function pct(b){return {l:b[0]/10,t:b[1]/10,w:(b[2]-b[0])/10,h:(b[3]-b[1])/10};}
function toBox(l,t,w,h){
  const cl=v=>Math.max(0,Math.min(100,v));
  const x1=cl(l),y1=cl(t),x2=cl(l+w),y2=cl(t+h);
  return [Math.round(x1*10),Math.round(y1*10),Math.round(x2*10),Math.round(y2*10)];
}
function draw(){
  stage.querySelectorAll('.box').forEach(e=>e.remove());
  PARTS.forEach((p,i)=>{
    const b=pct(p.bbox);
    const d=document.createElement('div');
    d.className='box'+(i===sel?' sel':'');
    d.style.left=b.l+'%';d.style.top=b.t+'%';d.style.width=b.w+'%';d.style.height=b.h+'%';
    d.dataset.i=i;
    d.innerHTML='<span class="lab">'+(i+1)+' · '+p.label+'</span>'+
      ['nw','ne','sw','se'].map(k=>'<span class="h '+k+'" data-k="'+k+'"></span>').join('');
    stage.appendChild(d);
  });
  renderList(); dump();
}
function renderList(){
  list.innerHTML='';
  PARTS.forEach((p,i)=>{
    const li=document.createElement('li');
    if(i===sel) li.className='sel';
    li.innerHTML='<i></i><span>'+(i+1)+' · '+p.label+'</span>'+
      '<span style="margin-left:auto;color:#6f7887">'+p.term+'</span>';
    li.onclick=()=>{sel=i;draw();};
    list.appendChild(li);
  });
}
function dump(){
  out.value=JSON.stringify({parts:PARTS.map((p,i)=>({slot:p.slot,bbox:p.bbox}))},null,1);
}
let drag=null;
stage.addEventListener('pointerdown',e=>{
  const handle=e.target.closest('.h');
  const box=e.target.closest('.box');
  if(!box) return;
  sel=+box.dataset.i; draw();
  const r=stage.getBoundingClientRect();
  drag={i:sel,handle:handle?handle.dataset.k:null,
    sx:e.clientX,sy:e.clientY,orig:PARTS[sel].bbox.slice(),rw:r.width,rh:r.height};
  e.target.setPointerCapture(e.pointerId);
});
window.addEventListener('pointermove',e=>{
  if(!drag) return;
  const dx=(e.clientX-drag.sx)/drag.rw*1000;
  const dy=(e.clientY-drag.sy)/drag.rh*1000;
  let [x1,y1,x2,y2]=drag.orig;
  if(!drag.handle){x1+=dx;x2+=dx;y1+=dy;y2+=dy;}
  else{
    if(drag.handle.includes('w')) x1=Math.min(x2-15,x1+dx);
    if(drag.handle.includes('e')) x2=Math.max(x1+15,x2+dx);
    if(drag.handle.includes('n')) y1=Math.min(y2-10,y1+dy);
    if(drag.handle.includes('s')) y2=Math.max(y1+10,y2+dy);
  }
  PARTS[drag.i].bbox=[x1,y1,x2,y2].map(v=>Math.round(Math.max(0,Math.min(1000,v))));
  const el=stage.querySelectorAll('.box')[drag.i];
  const b=pct(PARTS[drag.i].bbox);
  el.style.left=b.l+'%';el.style.top=b.t+'%';el.style.width=b.w+'%';el.style.height=b.h+'%';
  dump();
});
window.addEventListener('pointerup',()=>{drag=null;});
document.getElementById('copy').onclick=async()=>{
  const q=new URLSearchParams(location.search);
  const run=q.get('run_id'), slug=q.get('slug');
  const btn=document.getElementById('copy');
  if(run && slug){
    try{
      const r=await fetch('/api/boxes',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({run_id:run, slug:slug, parts: JSON.parse(out.value).parts})});
      btn.textContent = r.ok ? '已保存' : '保存失败';
    }catch(e){ btn.textContent='保存失败'; }
  }else{
    await navigator.clipboard.writeText(out.value);
    btn.textContent='已复制';
  }
  setTimeout(()=>btn.textContent='保存裁框',1200);
};
document.getElementById('reset').onclick=()=>{PARTS.forEach((p,i)=>p.bbox=INIT[i].bbox.slice());draw();};
img.onload=draw;
</script></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--data-dir", default="data-test")
    args = ap.parse_args()

    data = json.loads((ROOT / args.analysis).read_text(encoding="utf-8"))
    hero = ROOT / args.data_dir / data["assets"]["hero"]
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    parts = []
    for p in data.get("parts", []):
        bbox = p.get("bbox") or [400, 400, 600, 600]
        parts.append({"slot": p["slot"], "label": p.get("label") or SLOT_CN.get(p["slot"], p["slot"]),
                      "term": p.get("term") or "", "bbox": bbox})

    import os
    img_rel = os.path.relpath(hero, outdir).replace("\\", "/")
    v = data.get("vehicle", {})
    title = f"{v.get('brand', '')} {v.get('model', '')}".strip()
    html = (HTML.replace("__IMG__", img_rel)
                .replace("__PARTS__", json.dumps(parts, ensure_ascii=False))
                .replace("__TITLE__", title))
    out = outdir / f"{v.get('model', 'page')}-crop-editor.html"
    out.write_text(html, encoding="utf-8")
    print(f"[ok] {out}  parts={len(parts)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
