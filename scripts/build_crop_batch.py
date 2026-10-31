# -*- coding: utf-8 -*-
"""批量裁框编辑器 v3：同一车型的多张图并排显示，框可以拖到另一张图上。

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
           "side": "侧视", "side_r": "侧视", "front": "正视", "rear": "后视"}

HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>裁框 · 批量</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#0e1013;color:#e6e8ec;font:14px/1.6 "Microsoft YaHei",sans-serif;
height:100vh;display:flex;flex-direction:column;overflow:hidden}
.top{display:flex;align-items:center;gap:12px;padding:9px 18px;border-bottom:1px solid #23272e;
background:#12151a;flex:none}
.top h1{font-size:13px;color:#a7b0bb;letter-spacing:.04em}
.chips{display:flex;gap:5px}
.chip{width:24px;height:24px;border-radius:5px;background:#1d2127;border:1px solid #2a2f38;
display:flex;align-items:center;justify-content:center;font-size:10.5px;color:#8b93a1;cursor:pointer}
.chip.cur{box-shadow:0 0 0 2px #4ea1ff;color:#fff}
.chip.done{background:#17351f;border-color:#2b6b3d;color:#8fdcae}
.spacer{flex:1}
.btn{background:#4ea1ff;color:#06121f;border:0;border-radius:6px;padding:7px 13px;font-weight:700;
cursor:pointer;font-size:12.5px}
.btn.ghost{background:#232833;color:#c9d1d9;font-weight:500}
.wrap{flex:1;display:grid;grid-template-columns:1fr 300px;min-height:0}
.panels{display:grid;gap:12px;padding:12px;overflow:auto;align-content:start}
.panels.g1{grid-template-columns:1fr}
.panels.g2{grid-template-columns:1fr 1fr}
.panels.g4{grid-template-columns:1fr 1fr}
.panel{background:#14161a;border:1px solid #23272e;border-radius:8px;overflow:hidden;
display:flex;flex-direction:column;min-height:0}
.panel.drop{border-color:#ffd166;box-shadow:0 0 0 2px rgba(255,209,102,.35) inset}
.phead{padding:5px 10px;font-size:11px;color:#8b93a1;background:#171a1f;
border-bottom:1px solid #23272e;flex:none}
.stage{position:relative;line-height:0;display:flex;align-items:center;justify-content:center;
min-height:0;padding:6px}
.stage img{display:block;max-width:100%;max-height:34vh;user-select:none;border-radius:3px}
.box{position:absolute;border:1.5px solid #4ea1ff;background:rgba(78,161,255,.10);cursor:grab;
touch-action:none}
.box.sel{border-color:#ffd166;background:rgba(255,209,102,.16);z-index:6}
.box .lab{position:absolute;top:-19px;left:-1px;white-space:nowrap;font-size:10px;background:#4ea1ff;
color:#08111c;padding:0 5px;line-height:15px}
.box.sel .lab{background:#ffd166}
.h{position:absolute;width:10px;height:10px;background:#fff;border:1.5px solid #4ea1ff;border-radius:50%}
.h.nw{left:-5px;top:-5px;cursor:nwse-resize}.h.ne{right:-5px;top:-5px;cursor:nesw-resize}
.h.sw{left:-5px;bottom:-5px;cursor:nesw-resize}.h.se{right:-5px;bottom:-5px;cursor:nwse-resize}
aside{background:#171a1f;border-left:1px solid #23272e;padding:14px;display:flex;flex-direction:column;
gap:9px;overflow:auto}
aside h2{font-size:13.5px}
.hint{font-size:11px;color:#8b93a1;line-height:1.6}
ul{list-style:none;display:flex;flex-direction:column;gap:5px}
li{display:flex;align-items:center;gap:6px;font-size:12px;padding:5px 7px;border-radius:6px;
background:#1d2127;cursor:pointer}
li.sel{background:#2a3240;box-shadow:inset 0 0 0 1px #4ea1ff}
li.skip{opacity:.4;text-decoration:line-through}
li i{width:7px;height:7px;border-radius:2px;background:#4ea1ff;flex:none}
li.sel i{background:#ffd166}
li .badge{font-size:9.5px;padding:0 5px;border-radius:3px;background:#2b3542;color:#9fb6cc;margin-left:auto}
li .act{font-size:10px;color:#6f7887;padding:0 5px;border:1px solid #2a2f38;border-radius:4px}
textarea{min-height:80px;background:#0d0f13;color:#9fe0a0;border:1px solid #23272e;border-radius:6px;
padding:8px;font:10.5px/1.4 Consolas,monospace;resize:none}
.done-panel{position:absolute;inset:0;background:rgba(10,12,15,.93);display:none;align-items:center;
justify-content:center;flex-direction:column;gap:12px;z-index:20}
.done-panel.on{display:flex}
</style></head><body>
<div class="top">
  <h1>部件裁框</h1>
  <div class="chips" id="chips"></div>
  <div class="spacer"></div>
  <span id="status" style="font-size:11.5px;color:#6f7887"></span>
  <button class="btn ghost" id="prev">上一台</button>
  <button class="btn ghost" id="copy">复制本台</button>
  <button class="btn" id="ok">这张好了 → 下一台</button>
</div>
<div class="wrap">
  <div class="panels" id="panels"></div>
  <aside>
    <h2 id="vname">—</h2>
    <div class="hint">框属于它所在的那张图。<b>把框直接拖到另一张图上</b>，它就改挂那张；某件所有图都看不到点「跳过」。</div>
    <ul id="list"></ul>
    <textarea id="out" readonly></textarea>
  </aside>
</div>
<div class="done-panel" id="panel">
  <h2 style="font-size:20px">全部完成</h2>
  <p id="psum" style="color:#8b93a1;font-size:13px"></p>
  <button class="btn ghost" id="again">回到第一台</button>
</div>
<script>
const DATA = __DATA__;
let idx = 0, sel = 0, dragging = null;
const done = new Set();
const panelsEl = document.getElementById('panels');
const list = document.getElementById('list'), chips = document.getElementById('chips');
const out = document.getElementById('out'), panel = document.getElementById('panel');
const cur = () => DATA[idx];
const clamp = (v,a,b) => Math.max(a, Math.min(b, v));
const pct = b => ({l:b[0]/10, t:b[1]/10, w:(b[2]-b[0])/10, h:(b[3]-b[1])/10});

/* 只在换车 / 跳过 / 跨图落地时重建 */
function buildPanels(){
  const d = cur();
  panelsEl.className = 'panels g' + (d.imgs.length >= 3 ? 2 : 1);
  panelsEl.innerHTML = '';
  d.imgs.forEach((im,k)=>{
    const el = document.createElement('div');
    el.className='panel'; el.dataset.k=k;
    el.innerHTML = `<div class="phead">图${k+1} · ${im.view}</div>
      <div class="stage" data-k="${k}"><img src="${im.src}" alt=""></div>`;
    const st = el.querySelector('.stage');
    d.parts.forEach((part,i)=>{
      if(part.skip || part.src !== im.src || !part.bbox) return;
      const b = pct(part.bbox);
      const bx = document.createElement('div');
      bx.className='box'+(i===sel?' sel':'');
      bx.style.cssText=`left:${b.l}%;top:${b.t}%;width:${b.w}%;height:${b.h}%`;
      bx.dataset.i=i;
      bx.innerHTML=`<span class="lab">${i+1} · ${part.label}</span>`+
        ['nw','ne','sw','se'].map(c=>`<span class="h ${c}" data-c="${c}"></span>`).join('');
      st.appendChild(bx);
    });
    panelsEl.appendChild(el);
  });
  syncList(); syncChips(); dump();
}
function boxEl(i){ return panelsEl.querySelector(`.box[data-i="${i}"]`); }
function place(el,b){ el.style.left=b.l+'%'; el.style.top=b.t+'%';
  el.style.width=b.w+'%'; el.style.height=b.h+'%'; }

function syncList(){
  list.innerHTML='';
  cur().parts.forEach((p,i)=>{
    const li=document.createElement('li');
    if(i===sel) li.className='sel';
    if(p.skip) li.className=(li.className+' skip').trim();
    const n=cur().imgs.findIndex(im=>im.src===p.src)+1;
    li.innerHTML=`<i></i><span>${i+1} · ${p.label}</span>
      <span class="badge">${p.skip?'跳过':'图'+n}</span>
      <span class="act" data-skip="${i}">${p.skip?'恢复':'跳过'}</span>`;
    li.onclick=(e)=>{
      if(e.target.dataset.skip!==undefined){ p.skip=!p.skip; buildPanels(); return; }
      sel=i;
      document.querySelectorAll('.box').forEach(b=>b.classList.toggle('sel', +b.dataset.i===i));
      syncList();
    };
    list.appendChild(li);
  });
}
function syncChips(){
  chips.innerHTML='';
  DATA.forEach((d,i)=>{
    const c=document.createElement('div');
    c.className='chip'+(i===idx?' cur':'')+(done.has(i)?' done':'');
    c.textContent=done.has(i)?'✓':(i+1); c.title=d.title;
    c.onclick=()=>{ idx=i; sel=0; render(); };
    chips.appendChild(c);
  });
  document.getElementById('vname').textContent=`${idx+1} / ${DATA.length} · ${cur().title}`;
  document.getElementById('prev').disabled = idx===0;
}
function dump(){
  out.value=JSON.stringify({slug:cur().slug, parts:cur().parts.map(p=>({
    slot:p.slot, bbox:p.skip?null:p.bbox, src:p.skip?null:p.src, skip:!!p.skip}))},null,1);
}

/* ---- 拖动：只动当前这个框 ---- */
panelsEl.addEventListener('pointerdown', e=>{
  const bx = e.target.closest('.box');
  if(!bx) return;
  e.preventDefault();
  const i = +bx.dataset.i;
  sel = i;
  document.querySelectorAll('.box').forEach(b=>b.classList.toggle('sel', b===bx));
  syncList();
  const handle = e.target.closest('.h');
  const stage = bx.closest('.stage');
  const r = stage.getBoundingClientRect();
  dragging = {i, el:bx, k:+stage.dataset.k, c:handle?handle.dataset.c:null,
              sx:e.clientX, sy:e.clientY, r, orig:cur().parts[i].bbox.slice()};
  bx.setPointerCapture?.(e.pointerId);
});
window.addEventListener('pointermove', e=>{
  if(!dragging) return;
  const d = dragging;
  const dx = (e.clientX-d.sx)/d.r.width*1000, dy = (e.clientY-d.sy)/d.r.height*1000;
  let [x1,y1,x2,y2] = d.orig;
  if(!d.c){ x1+=dx; x2+=dx; y1+=dy; y2+=dy; }
  else{
    if(d.c.includes('w')) x1 = Math.min(x2-15, x1+dx);
    if(d.c.includes('e')) x2 = Math.max(x1+15, x2+dx);
    if(d.c.includes('n')) y1 = Math.min(y2-10, y1+dy);
    if(d.c.includes('s')) y2 = Math.max(y1+10, y2+dy);
  }
  const p = cur().parts[d.i];
  p.bbox = [x1,y1,x2,y2].map(v=>Math.round(clamp(v,0,1000)));
  place(d.el, pct(p.bbox));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('drop'));
  if(!d.c){
    const t = document.elementFromPoint(e.clientX,e.clientY)?.closest('.panel');
    if(t && +t.dataset.k !== d.k) t.classList.add('drop');
  }
  dump();
});
window.addEventListener('pointerup', e=>{
  if(!dragging) return;
  const d = dragging; dragging = null;
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('drop'));
  if(!d.c){
    const t = document.elementFromPoint(e.clientX,e.clientY)?.closest('.panel');
    if(t && +t.dataset.k !== d.k){
      const k = +t.dataset.k, p = cur().parts[d.i];
      const st = t.querySelector('.stage').getBoundingClientRect();
      const w = p.bbox[2]-p.bbox[0], h = p.bbox[3]-p.bbox[1];
      const cx = (e.clientX-st.left)/st.width*1000, cy = (e.clientY-st.top)/st.height*1000;
      p.src = cur().imgs[k].src;
      p.bbox = [Math.round(clamp(cx-w/2,0,1000-w)), Math.round(clamp(cy-h/2,0,1000-h)),
                Math.round(clamp(cx+w/2,w,1000)), Math.round(clamp(cy+h/2,h,1000))];
      buildPanels();
      return;
    }
  }
  dump();
});

const SERVER='http://127.0.0.1:8766/save';
function setStatus(t){ document.getElementById('status').textContent=t; }
async function persist(){
  const d = cur();
  const payload={slug:d.slug, parts:d.parts.map(p=>({slot:p.slot,
    bbox:p.skip?null:p.bbox, src:p.skip?null:p.src, skip:!!p.skip}))};
  try{
    const r = await fetch(SERVER,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify(payload)});
    if(r.ok){ setStatus('已保存'); return; }
  }catch(e){}
  setStatus('保存失败，请点复制');
}
function render(){ sel=0; buildPanels(); }
document.getElementById('ok').onclick=()=>{
  persist(); done.add(idx);
  if(idx < DATA.length-1){ idx++; render(); }
  else{ syncChips(); document.getElementById('psum').textContent=
    `已确认 ${done.size} / ${DATA.length} 台`; panel.classList.add('on'); }
};
document.getElementById('prev').onclick=()=>{ if(idx>0){ idx--; render(); } };
document.getElementById('copy').onclick=async()=>{
  await navigator.clipboard.writeText(out.value); setStatus('已复制');
};
document.getElementById('again').onclick=()=>{ panel.classList.remove('on'); idx=0; render(); };
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
    order = ["side_l", "side", "side_r", "hero_lf", "hero_45", "hero_rf", "front", "rear"]
    return [{"src": best[v]["file_path"], "view": VIEW_CN.get(v, v)}
            for v in order if v in best][:4]


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
        rel = {i["src"]: os.path.relpath(ROOT / args.data_dir / i["src"], outdir)
                            .replace("\\", "/") for i in imgs}
        saved = {}
        fp = ROOT / args.boxes_dir / f"{v.get('model','')}-boxes.json"
        if fp.exists():
            saved = {p["slot"]: p for p in json.loads(fp.read_text(encoding="utf-8")).get("parts", [])}
        parts = []
        for p in d.get("parts", []):
            base = saved.get(p["slot"], {})
            src = base.get("src") or hero
            if src not in rel:
                src = hero
            parts.append({"slot": p["slot"], "label": SLOT_CN.get(p["slot"], p["slot"]),
                          "term": p.get("term") or "",
                          "bbox": base.get("bbox") or p.get("bbox") or [400, 400, 600, 600],
                          "src": rel[src], "skip": bool(base.get("skip"))})
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
