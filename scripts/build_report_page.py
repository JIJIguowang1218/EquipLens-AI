# -*- coding: utf-8 -*-
"""单车报告页（16:9）生成器：analysis.json + 主图 → 一页 HTML。

设计要点
- 顶部：左上标题（中英）/ 右上三词 + 色彩构成条（各页等长，按面积分段）
- 底部：左车型号 / 右页码
- 主体：主图（带部件定位框）+ 前脸分析 + 5 个部件卡（图 ≥ 文本）
- 图片块面积不得小于同卡文本块

用法:
  PYTHONPATH=src python scripts/build_report_page.py \
      --analysis data-test/analysis-20261031/01-JH6.json --out data-test/report-20261031 --page 1 --total 10
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SLOT_CN = {
    "grille": "进气格栅", "bumper": "保险杠", "side_guard": "侧防护栏",
    "wheel_arch": "前轮轮拱", "step": "登车踏步", "headlamp": "大灯",
    "mirror": "后视镜", "sun_visor": "遮阳板", "under_guard": "下护板",
    "brand_zone": "品牌标识区", "paint_scheme": "涂装与分色",
}
FAMILY_CN = {
    "sheet_metal": "钣金覆盖件", "frame_profile": "型材框架件",
    "cast_forged": "铸锻机加件", "function_attachment": "功能附件",
}
MAX_COLORS = 4


# ---------------------------------------------------------------- 色彩构成

def _kmeans(px: np.ndarray, k: int = 5, iters: int = 12) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(7)
    centers = px[rng.choice(len(px), k, replace=False)].astype(float)
    for _ in range(iters):
        d = ((px[:, None, :] - centers[None, :, :]) ** 2).sum(2)
        lab = d.argmin(1)
        for i in range(k):
            sel = px[lab == i]
            if len(sel):
                centers[i] = sel.mean(0)
    counts = np.bincount(lab, minlength=k).astype(float)
    return centers, counts



def _bg_mask(arr: np.ndarray, tol: int = 78) -> np.ndarray:
    """从四边向内做漫水填充，标记与边缘同色的背景像素（保留车身内部同色区域）。"""
    from collections import deque
    h, w, _ = arr.shape
    edge = np.concatenate([arr[:2].reshape(-1, 3), arr[-2:].reshape(-1, 3),
                           arr[:, :2].reshape(-1, 3), arr[:, -2:].reshape(-1, 3)])
    bg = np.median(edge, axis=0)
    near = np.abs(arr - bg).sum(2) < tol
    mask = np.zeros((h, w), bool)
    dq = deque()
    for x in range(w):
        for y in (0, h - 1):
            if near[y, x] and not mask[y, x]:
                mask[y, x] = True; dq.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if near[y, x] and not mask[y, x]:
                mask[y, x] = True; dq.append((y, x))
    while dq:
        y, x = dq.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and not mask[ny, nx] and near[ny, nx]:
                mask[ny, nx] = True; dq.append((ny, nx))
    return mask

def color_composition(path: Path, max_colors: int = MAX_COLORS, bg=None) -> list[dict]:
    """返回 [{hex, r,g,b, pct}]，按面积降序，最多 4 段。"""
    im = Image.open(path).convert("RGB")
    im.thumbnail((220, 220))
    grid = np.asarray(im).astype(float)
    mask = _bg_mask(grid)
    flat = grid.reshape(-1, 3)
    keep = ~mask.reshape(-1)
    arr = flat[keep] if keep.sum() > 400 else flat
    arr = arr.astype(float)

    bg = np.asarray(bg, dtype=float) if bg is not None else np.array([255.0, 255.0, 255.0])

    centers, counts = _kmeans(arr, k=max(5, max_colors + 1))
    order = np.argsort(-counts)
    kept = []
    for i in order:
        c = centers[i]
        share = counts[i] / counts.sum()
        if share < 0.015:
            continue
        lum = c.mean() / 255
        if len(kept) < 3 and lum > 0.93:
            continue  # 纯白高光，通常是被抠掉的地面反光
        if any(np.linalg.norm(c - k["rgb"]) < 22 for k in kept):
            continue
        kept.append({"rgb": c, "share": share})
        if len(kept) >= max_colors:
            break
    if not kept:
        i = order[0]
        kept = [{"rgb": centers[i], "share": counts[i] / counts.sum()}]

    total = sum(k["share"] for k in kept)
    out = []
    for k in kept:
        r, g, b = [int(round(v)) for v in k["rgb"]]
        out.append({"hex": f"#{r:02X}{g:02X}{b:02X}", "r": r, "g": g, "b": b,
                    "pct": k["share"] / total})
    return out


def accent_of(palette: list[dict]) -> str:
    """取饱和度最高且面积够的一段作为强调色。"""
    best, score = palette[0]["hex"], -1
    for p in palette:
        mx, mn = max(p["r"], p["g"], p["b"]), min(p["r"], p["g"], p["b"])
        sat = (mx - mn) / max(mx, 1)
        s = sat * (0.35 + p["pct"])
        if s > score:
            score, best = s, p["hex"]
    return best


# ---------------------------------------------------------------- 主图裁白

def trim_hero(src: Path, outdir: Path, slug: str):
    """裁掉与环境背景同色的外框，让整车填满主图区；返回 (新路径, 原图裁剪框)。"""
    im = Image.open(src).convert("RGB")
    arr = np.asarray(im).astype(int)
    h, w, _ = arr.shape
    edge = np.concatenate([arr[:8].reshape(-1, 3), arr[-8:].reshape(-1, 3),
                           arr[:, :8].reshape(-1, 3), arr[:, -8:].reshape(-1, 3)])
    bg = np.median(edge, axis=0)
    mask = np.abs(arr - bg).sum(2) > 40
    ys, xs = np.where(mask)
    if len(xs) == 0 or (xs.max() - xs.min()) < w * 0.3:
        return src, (0, 0, w, h), bg
    pad = int(0.03 * max(xs.max() - xs.min(), ys.max() - ys.min()))
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad),
           min(w, xs.max() + pad), min(h, ys.max() + pad))
    crop = im.crop(box)
    out = outdir / f"{slug}-hero.jpg"
    crop.save(out, quality=92)
    return out, box, bg


# ---------------------------------------------------------------- 裁图

def crop_parts(src: Path, data: dict, outdir: Path, slug: str,
               data_root: Path | None = None) -> dict[str, str]:
    outdir.mkdir(parents=True, exist_ok=True)
    cache: dict[str, Image.Image] = {}
    paths: dict[str, str] = {}
    for p in data.get("parts", []):
        bbox = p.get("bbox")
        if p.get("skip") or p.get("visible") == "not_visible" or not bbox:
            continue
        src_p = src
        if data_root and p.get("src"):
            cand = data_root / p["src"]
            if cand.exists():
                src_p = cand
        key = str(src_p)
        if key not in cache:
            cache[key] = Image.open(src_p).convert("RGB")
        im = cache[key]
        w, h = im.size
        x1, y1, x2, y2 = [max(0, min(1000, v)) for v in bbox]
        if x2 - x1 < 20 or y2 - y1 < 20:
            continue
        pad_x, pad_y = (x2 - x1) * 0.04, (y2 - y1) * 0.04
        box = (int((x1 - pad_x) / 1000 * w), int((y1 - pad_y) / 1000 * h),
               int((x2 + pad_x) / 1000 * w), int((y2 + pad_y) / 1000 * h))
        box = (max(0, box[0]), max(0, box[1]), min(w, box[2]), min(h, box[3]))
        if box[2] - box[0] < 24 or box[3] - box[1] < 24:
            continue
        crop = im.crop(box)
        if crop.size[0] < 24 or crop.size[1] < 24:
            continue
        gray = np.asarray(crop.convert("L"))
        if float(gray.std()) < 4:
            continue  # 无纹理（纯色块），判为无效裁图
        # 严格按框裁切，不做比例归一化；只放大、不改变长宽比
        long_side = max(crop.size)
        if long_side < 900:
            k = 900 / long_side
            crop = crop.resize((max(1, int(crop.size[0] * k)),
                                max(1, int(crop.size[1] * k))), Image.LANCZOS)
        name = f"{slug}-{p['slot']}.jpg"
        crop.save(outdir / name, quality=92)
        paths[p["slot"]] = name
    return paths


# ---------------------------------------------------------------- 模板

CSS = """
:root{--ink:#111214;--graphite:#5c6169;--muted:#8b8f96;--line:#d9d6cf;
--paper:#faf9f6;--block:#efece5;--accent:%ACCENT%}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#e7e5e0;font-family:"Source Han Sans SC","Noto Sans SC","Microsoft YaHei",sans-serif;
-webkit-font-smoothing:antialiased}
.page{position:relative;width:1600px;height:900px;background:var(--paper);color:var(--ink);
padding:40px 48px 32px;overflow:hidden}
.mono{font-family:Consolas,"SF Mono",monospace;font-variant-numeric:tabular-nums}
/* ---- header ---- */
header{height:96px;display:flex;justify-content:space-between;align-items:flex-start;
border-bottom:1px solid var(--line);position:relative}
header:after{content:"";position:absolute;left:0;bottom:-1px;width:100%;height:3px;
background:linear-gradient(90deg,var(--accent) 0 120px,transparent 120px)}
.title-cn{font-size:31px;font-weight:700;letter-spacing:.05em;line-height:1.05}
.title-en{margin-top:7px;font-family:Bahnschrift,"Arial Narrow",sans-serif;font-size:12.5px;
letter-spacing:.26em;color:var(--muted);text-transform:uppercase}
.tools{display:flex;flex-direction:column;align-items:flex-end;gap:12px}
.tags{display:flex;gap:8px}
.tag{font-size:15px;letter-spacing:.1em;padding:7px 17px;border:1px solid var(--ink);
border-radius:999px;line-height:1}
.bar{display:flex;width:300px;height:13px;border-radius:2px;overflow:hidden}
.bar i{display:block;height:100%}
.bar-cap{font-size:10.5px;letter-spacing:.16em;color:var(--muted);margin-top:6px;width:300px;
display:flex;justify-content:space-between}
/* ---- body ---- */
main{margin-top:20px;height:668px;display:grid;grid-template-columns:540px 1fr;gap:20px;overflow:hidden}
.left{display:flex;flex-direction:column;gap:20px;height:668px}
.hero{position:relative;background:transparent;border:0;overflow:hidden;flex:0 0 auto;
align-self:flex-start;width:540px;height:430px;display:flex;align-items:center;justify-content:center}
.hero img{width:auto;height:auto;max-width:100%;max-height:100%;object-fit:contain;display:block}
.mark{position:absolute;border:1px solid var(--accent);background:rgba(255,255,255,.06)}
.mark b{position:absolute;top:-9px;left:-9px;width:18px;height:18px;background:var(--accent);
color:#fff;font-size:10px;display:flex;align-items:center;justify-content:center;
font-family:Consolas,monospace}
.textblock{background:var(--block);padding:18px 20px;display:flex;flex-direction:column;gap:10px;
overflow:hidden;flex:1 1 auto;min-height:0}
.eyebrow{font-size:9px;letter-spacing:.22em;color:var(--muted);text-transform:uppercase;
font-family:Bahnschrift,"Arial Narrow",sans-serif}
.lead{font-size:17px;line-height:1.7;font-weight:600}
.lines{list-style:none;font-size:13.5px;line-height:1.85;color:#2b2e33;display:flex;
flex-direction:column;gap:7px}
.lines li{padding-left:14px;position:relative}
.lines li:before{content:"";position:absolute;left:0;top:7px;width:6px;height:1px;
background:var(--accent)}
.meta{font-size:12.5px;color:var(--graphite);line-height:1.7;margin-top:6px}
.canvas{position:relative;width:1472px;height:668px;margin:0 auto;overflow:hidden}
.blk{position:absolute;overflow:hidden;box-sizing:border-box}
.blk.img img{width:100%;height:100%;object-fit:cover;display:block}
.blk.text{background:var(--block);padding:9px 11px;display:flex;flex-direction:column;gap:2px}
.guide{position:absolute;background:#ff3b6b;z-index:99;display:none;pointer-events:none}
.guide.v{width:1px;height:100%;top:0}
.guide.h{height:1px;width:100%;left:0}
.editbar{position:fixed;right:18px;bottom:18px;display:flex;gap:8px;align-items:center;z-index:300}
.editbar button{background:#111318;color:#cfd6df;border:1px solid #2b323d;border-radius:7px;
padding:8px 13px;font-size:12px;cursor:pointer}
.editbar button.on{background:#1d3a52;border-color:#4ea1ff;color:#cfe8ff}
.editbar button:disabled{opacity:.4;cursor:not-allowed}
.tip{font-size:11px;color:#8b93a1}
body.editing .blk{outline:1px dashed rgba(78,161,255,.55);cursor:move}
body.editing .blk.text{outline-color:rgba(224,163,58,.7)}
body.editing .blk.sel{outline:2px solid #4ea1ff;z-index:60}
.hdl{position:absolute;width:9px;height:9px;background:#fff;border:1.5px solid #4ea1ff;
border-radius:2px;display:none;z-index:70}
body.editing .blk.sel .hdl{display:block}
.hdl.nw{left:0;top:0;cursor:nwse-resize}.hdl.ne{right:0;top:0;cursor:nesw-resize}
.hdl.sw{left:0;bottom:0;cursor:nesw-resize}.hdl.se{right:0;bottom:0;cursor:nwse-resize}
.imgzone{display:flex;flex-direction:column;justify-content:space-between;min-height:0}
.imgrow{display:flex;gap:0;min-height:0}
.imgrow img{display:block;flex:0 0 auto}
.txtzone{flex:1 1 auto;display:flex;flex-direction:column;justify-content:space-between;min-height:0}
.mtext{flex:1 1 0;min-height:0;overflow:hidden;margin-bottom:8px}
.mtext{background:var(--block);padding:9px 11px;overflow:hidden;flex:0 0 auto;
display:flex;flex-direction:column;gap:2px;justify-content:flex-start}
.mt-term{font-size:12px;font-weight:700;line-height:1.3;display:flex;gap:5px;align-items:baseline}
.mt-no{font-family:Consolas,monospace;font-size:9px;color:var(--muted);letter-spacing:.06em}
.mt-fam{font-size:8.5px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}
.mt-form{font-size:10.5px;line-height:1.35;color:#2b2e33;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.mt-cmf{font-size:9.5px;line-height:1.3;color:var(--graphite);
display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}
/* ---- footer ---- */
footer{position:absolute;left:48px;right:48px;bottom:20px;height:32px;display:flex;
justify-content:space-between;align-items:flex-end;border-top:1px solid var(--line);
padding-top:8px}
footer .model{font-size:12px;letter-spacing:.04em;color:var(--graphite)}
footer .model b{color:var(--ink);font-weight:600}
footer .pn{font-family:Consolas,monospace;font-size:11px;color:var(--muted);letter-spacing:.1em}
"""


def esc(s) -> str:
    from html import escape
    return escape(str(s)) if s is not None else ""



def _partitions(n: int):
    """所有连续行划分。"""
    from itertools import combinations
    for k in range(1, n + 1):
        for cuts in combinations(range(1, n), k - 1):
            rows, prev = [], 0
            for c in list(cuts) + [n]:
                rows.append((prev, c)); prev = c
            yield rows


def layout_split(aspects: list[float], W: float, H: float, img_ratio: float = 0.63,
                 gap: float = 13) -> dict:
    """左：图按行铺满；右：文本整列铺满。"""
    w_img = W * img_ratio
    n = len(aspects)
    best = None
    for rows in _partitions(n):
        hs = [w_img / sum(aspects[a:b]) for a, b in rows]
        total = sum(hs) + gap * (len(rows) - 1)
        if total > H * 1.02:
            continue
        score = abs(H - total)
        if best is None or score < best[0]:
            best = (score, rows, hs)
    if not best:
        rows = [(0, n)]
        hs = [w_img / sum(aspects)]
        best = (0, rows, hs)
    _, rows, hs = best
    return {"w_img": w_img, "rows": rows, "hs": hs}



JS_EDITOR = """<script>
(function(){
  const canvas = document.getElementById('canvas');
  if(!canvas) return;
  const slug = canvas.dataset.slug || 'page';
  const page = document.querySelector('.page');
  let editing = false, sel = null, drag = null, changed = false;
  const W = 1472, H = 668;

  const blocks = () => [...canvas.querySelectorAll('.blk')];
  blocks().forEach(b=>{
    ['nw','ne','sw','se'].forEach(k=>{
      const h = document.createElement('span');
      h.className = 'hdl ' + k; h.dataset.h = k; b.appendChild(h);
    });
  });

  function tip(t){ document.getElementById('tip').textContent = t || ''; }
  function rectOf(el){ return {x:parseFloat(el.style.left)||0, y:parseFloat(el.style.top)||0,
                               w:parseFloat(el.style.width)||0, h:parseFloat(el.style.height)||0}; }
  function apply(el, r){ el.style.left=r.x+'px'; el.style.top=r.y+'px';
                         el.style.width=r.w+'px'; el.style.height=r.h+'px'; }
  function fitText(el){
    const box = el;
    let fs = 12;
    box.classList.add('fit');
    while(fs > 7){
      box.style.fontSize = fs + 'px';
      if(box.scrollHeight <= box.clientHeight + 1) break;
      fs -= 0.5;
    }
  }
  function select(el){
    blocks().forEach(b=>b.classList.toggle('sel', b===el));
    sel = el;
  }

  // 拖动 / 缩放
  canvas.addEventListener('pointerdown', e=>{
    if(!editing) return;
    const blk = e.target.closest('.blk');
    if(!blk) { select(null); return; }
    select(blk);
    const hdl = e.target.closest('.hdl');
    const r = rectOf(blk);
    drag = {el:blk, h: hdl?hdl.dataset.h:null, sx:e.clientX, sy:e.clientY, r, id:blk.dataset.id};
    e.preventDefault();
  });
  window.addEventListener('pointermove', e=>{
    if(!drag || !editing) return;
    const dx = e.clientX - drag.sx, dy = e.clientY - drag.sy;
    let r = {...drag.r};
    if(!drag.h){ r.x += dx; r.y += dy; }
    else {
      if(drag.h.includes('w')){ r.x += dx; r.w -= dx; }
      if(drag.h.includes('e')){ r.w += dx; }
      if(drag.h.includes('n')){ r.y += dy; r.h -= dy; }
      if(drag.h.includes('s')){ r.h += dy; }
    }
    r.w = Math.max(40, r.w); r.h = Math.max(30, r.h);
    // 吸附
    const tol = 6, gv = document.getElementById('gv'), gh = document.getElementById('gh');
    gv.style.display = gh.style.display = 'none';
    if(!drag.h){
      const others = blocks().filter(b=>b!==drag.el).map(rectOf);
      const edgesX = [0, W/2, W, ...others.flatMap(o=>[o.x, o.x+o.w, o.x+o.w/2])];
      const edgesY = [0, H/2, H, ...others.flatMap(o=>[o.y, o.y+o.h, o.y+o.h/2])];
      for(const ex of edgesX){
        if(Math.abs(r.x - ex) < tol){ r.x = ex; gv.style.display='block'; gv.style.left = ex+'px'; break; }
        if(Math.abs(r.x + r.w - ex) < tol){ r.x = ex - r.w; gv.style.display='block'; gv.style.left = ex+'px'; break; }
      }
      for(const ey of edgesY){
        if(Math.abs(r.y - ey) < tol){ r.y = ey; gh.style.display='block'; gh.style.top = ey+'px'; break; }
        if(Math.abs(r.y + r.h - ey) < tol){ r.y = ey - r.h; gh.style.display='block'; gh.style.top = ey+'px'; break; }
      }
    }
    r.x = Math.max(0, Math.min(W-40, r.x));
    r.y = Math.max(0, Math.min(H-30, r.y));
    apply(drag.el, r);
    changed = true;
  });
  window.addEventListener('pointerup', ()=>{
    if(drag && drag.el && drag.el.dataset.kind === 'text') fitText(drag.el);
    if(drag){ drag = null; }
  });

  document.getElementById('btnEdit').onclick = ()=>{
    editing = !editing;
    document.body.classList.toggle('editing', editing);
    document.getElementById('btnEdit').classList.toggle('on', editing);
    document.getElementById('btnEdit').textContent = editing ? '退出编辑' : '编辑布局';
    document.getElementById('btnSave').disabled = !editing;
    document.getElementById('btnReset').disabled = !editing;
    if(!editing) select(null);
  };
  document.getElementById('btnSave').onclick = async ()=>{
    const data = blocks().map(b=>({id:b.dataset.id, ...rectOf(b)}));
    try{
      const r = await fetch('http://127.0.0.1:8766/save', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({kind:'layout', slug, blocks:data})});
      tip(r.ok ? '已保存' : '保存失败');
    }catch(e){ tip('保存失败：本地服务未启动'); }
  };
  document.getElementById('btnReset').onclick = ()=>{ location.reload(); };
})();
</script>"""


def build_html(data: dict, hero_rel: str, crops: dict[str, str], palette: list[dict],
               page: int, total: int, brand_rule: str, hero_box=None,
               hero_size=None, crop_sizes=None, layout_path=None) -> str:
    u = data.get("unit", {})
    v = data.get("vehicle", {})
    tags = u.get("style_tags", [])
    accent = accent_of(palette)


    order = [p for p in data.get("parts", [])
             if p.get("visible") != "not_visible" and not p.get("skip")]
    order = [p for p in order if crops.get(p["slot"])]

    sizes = crop_sizes or {}
    aspects = []
    for p in order:
        w, h = sizes.get(p["slot"], (4, 3))
        aspects.append(max(0.2, w / max(1, h)))

    W_GRID, H_GRID, GAP = 912, 668, 12
    n = len(order)
    TEXT_H = 96
    # 4 行：图 / 文 / 图 / 文，图片行等高
    img_h = (H_GRID - 2 * TEXT_H - 3 * GAP) / 2

    from itertools import combinations
    best = None
    for k in range(1, n):
        for a in combinations(range(n), k):
            band1 = list(a)
            band2 = [i for i in range(n) if i not in band1]
            if not band2:
                continue
            loss = 0.0
            for band in (band1, band2):
                bw = (W_GRID - GAP * (len(band) - 1)) / len(band)
                tgt = bw / img_h
                for i in band:
                    loss += abs(math.log(max(0.05, aspects[i]) / tgt))
            loss += 0.35 * abs(len(band1) - len(band2))
            if best is None or loss < best[0]:
                best = (loss, band1, band2)
    _, band1, band2 = best

    lines = "".join(f"<li>{esc(x)}</li>" for x in (u.get("character_lines") or [])[:3])

    layout_override = {}
    if layout_path and layout_path.exists():
        try:
            layout_override = {b["id"]: b for b in json.loads(
                layout_path.read_text(encoding="utf-8")).get("blocks", [])}
        except Exception:
            layout_override = {}

    blocks = [{"id": "hero", "kind": "img", "x": 0, "y": 0, "w": 540, "h": 430,
               "src": hero_rel},
              {"id": "front_text", "kind": "text", "x": 0, "y": 442, "w": 540,
               "h": H_GRID - 442}]

    def add_band(band, y0):
        bw = (W_GRID - GAP * (len(band) - 1)) / len(band)
        for k, i in enumerate(band):
            p = order[i]
            slot = p["slot"]
            cmf = p.get("cmf") or {}
            x = 560 + k * (bw + GAP)
            blocks.append({"id": f"img{i}", "kind": "img", "x": x, "y": y0,
                           "w": bw, "h": img_h, "src": f"crops/{crops[slot]}", "idx": i + 1})
            blocks.append({"id": f"txt{i}", "kind": "text", "x": x, "y": y0 + img_h + 10,
                           "w": bw, "h": TEXT_H, "idx": i + 1,
                           "term": p.get("term") or SLOT_CN.get(slot, slot),
                           "fam": FAMILY_CN.get(p.get("part_family"), ""),
                           "form": p.get("form") or "",
                           "cmf": " · ".join(v for v in [(cmf.get("material_class") or ""),
                                                         (cmf.get("finish") or "")] if v)})

    add_band(band1, 0)
    add_band(band2, img_h + 10 + TEXT_H + GAP)

    for blk in blocks:
        ov = layout_override.get(blk["id"])
        if ov:
            for k in ("x", "y", "w", "h"):
                if k in ov:
                    blk[k] = float(ov[k])

    blocks_html = ""
    for blk in blocks:
        style = (f"left:{blk['x']:.1f}px;top:{blk['y']:.1f}px;"
                 f"width:{blk['w']:.1f}px;height:{blk['h']:.1f}px")
        if blk["kind"] == "img":
            idx = f'<span class="pno">{blk["idx"]:02d}</span>' if blk.get("idx") else ""
            inner = f'<img src="{esc(blk["src"])}" alt="">{idx}'
        elif blk["id"] == "front_text":
            inner = (f'<div class="eyebrow">Front Face / 前脸</div>'
                     f'<div class="lead">{esc(u.get("gesture"))}</div>'
                     f'<ul class="lines">{lines}</ul>'
                     f'<div class="meta">{esc(u.get("proportion"))}｜{esc(u.get("judgement"))}</div>')
        else:
            inner = (f'<div class="mt-term"><span class="mt-no">{blk.get("idx", 0):02d}</span>'
                     f'{esc(blk.get("term", ""))}</div>'
                     f'<div class="mt-fam">{esc(blk.get("fam", ""))}</div>'
                     f'<div class="mt-form">{esc(blk.get("form", ""))}</div>'
                     f'<div class="mt-cmf">{esc(blk.get("cmf", ""))}</div>')
        blocks_html += (f'<div class="blk {blk["kind"]}" data-id="{blk["id"]}" '
                        f'data-kind="{blk["kind"]}" style="{style}">{inner}</div>')

    mosaic = ""


    barbits = "".join(
        f'<i style="width:{c["pct"]*100:.2f}%;background:{c["hex"]}"></i>' for c in palette)



    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<title>{esc(v.get('brand'))} {esc(v.get('model'))}</title>
<style>{CSS.replace('%ACCENT%', accent)}</style></head>
<body><div class="page">
  <header>
    <div>
      <div class="title-cn">竞品分析</div>
      <div class="title-en">Competitive Design Analysis</div>
    </div>
    <div class="tools">
      <div class="tags">{''.join(f'<span class="tag">{esc(t.get("tag"))}</span>' for t in tags)}</div>
      <div>
        <div class="bar">{barbits}</div>
        <div class="bar-cap"><span>COLOR COMPOSITION</span><span>4 / AREA</span></div>
      </div>
    </div>
  </header>

  <main>
    <div class="canvas" id="canvas" data-slug="{esc(v.get('model'))}">{blocks_html}
      <div class="guide v" id="gv"></div><div class="guide h" id="gh"></div>
    </div>
  </main>
  <div class="editbar">
    <button id="btnEdit">编辑布局</button>
    <button id="btnSave" disabled>保存</button>
    <button id="btnReset" disabled>重置</button>
    <span class="tip" id="tip"></span>
  </div>

  <footer>
    <div class="model"><b>{esc(v.get('brand'))} {esc(v.get('model'))}</b>　{esc(v.get('category'))}　·　{esc(brand_rule)}</div>
    <div class="pn">{page:02d} / {total:02d}</div>
  </footer>
</div></body></html>""" + JS_EDITOR


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--total", type=int, default=10)
    ap.add_argument("--data-dir", default="data-test")
    ap.add_argument("--brand-rule", default="")
    ap.add_argument("--boxes", help="编辑器导出的裁框 JSON（覆盖 bbox）")
    ap.add_argument("--layout", help="编辑器保存的版式 JSON（覆盖块位置）")
    args = ap.parse_args()

    src = ROOT / args.analysis
    data = json.loads(src.read_text(encoding="utf-8"))
    hero_rel_db = (data.get("assets") or {}).get("hero")
    if not hero_rel_db:
        raise SystemExit("缺 assets.hero")
    hero_abs = ROOT / args.data_dir / hero_rel_db

    if args.boxes:
        edited = json.loads((ROOT / args.boxes).read_text(encoding="utf-8"))
        by_slot = {x["slot"]: x for x in edited.get("parts", [])}
        for p in data.get("parts", []):
            b = by_slot.get(p.get("slot"))
            if not b:
                continue
            if b.get("skip"):
                p["skip"] = True
                continue
            if b.get("bbox"):
                p["bbox"] = b["bbox"]
                p["visible"] = "full"
            if b.get("src"):
                p["src"] = b["src"]

    slug = re.sub(r"\s+", "-", (data.get("vehicle") or {}).get("model", src.stem))
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    cropdir = outdir / "crops"
    crops = crop_parts(hero_abs, data, cropdir, slug, data_root=ROOT / args.data_dir)
    crop_sizes = {}
    for _slot, _fn in crops.items():
        try:
            crop_sizes[_slot] = Image.open(cropdir / _fn).size
        except Exception:
            crop_sizes[_slot] = (4, 3)

    hero_view, hero_box, hero_bg = trim_hero(hero_abs, outdir, slug)
    palette = color_composition(hero_view, bg=hero_bg)
    (outdir / f"{slug}-palette.json").write_text(
        json.dumps(palette, ensure_ascii=False, indent=2), encoding="utf-8")

    # 图片用相对路径（从 out 目录指向 data-test）
    import os
    hero_rel = os.path.relpath(hero_view, outdir)

    html = build_html(data, str(hero_rel).replace("\\", "/"), crops, palette,
                      args.page, args.total, args.brand_rule, hero_box,
                      Image.open(hero_abs).size, crop_sizes,
                      (ROOT / args.layout) if args.layout else None)
    out = outdir / f"{slug}.html"
    out.write_text(html, encoding="utf-8")
    print(f"[ok] {out}  crops={len(crops)}  palette={[c['hex'] for c in palette]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
