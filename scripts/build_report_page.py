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
.mosaic{position:relative;height:100%;min-height:0;width:100%}
.blk{position:absolute;overflow:hidden;display:flex;flex-direction:column}
.blk img{display:block;flex:0 0 auto;margin:0 auto}
.mtext{flex:1 1 auto;min-height:0;width:100%}
.mtext{background:var(--block);padding:9px 11px;overflow:hidden;flex:0 0 auto;
display:flex;flex-direction:column;gap:2px;justify-content:flex-start}
.mt-term{font-size:12px;font-weight:700;line-height:1.25}
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



def _squarify(weights: list[float], x: float, y: float, w: float, h: float) -> list[tuple]:
    """squarified treemap：把带权重的矩形铺满 (x,y,w,h)，返回各自 rect。"""
    total = sum(weights)
    scaled = [wt / total * w * h for wt in weights]
    rects: list[tuple] = []
    i = 0
    while i < len(scaled):
        # 取一行（或列）
        short = min(w, h)
        row, row_sum, j = [], 0.0, i
        best = None
        while j < len(scaled):
            trial = row + [scaled[j]]
            ssum = row_sum + scaled[j]
            side = ssum / short
            worst = max(max(side / (s_ / side) if s_ else 0,
                            (s_ / side) / side if s_ else 0) for s_ in trial)
            if best is not None and worst > best:
                break
            best = worst
            row, row_sum = trial, ssum
            j += 1
        side = row_sum / short
        if w >= h:  # 竖条
            yy = y
            for s_ in row:
                hh = s_ / side if side else 0
                rects.append((x, yy, side, hh))
                yy += hh
            x += side; w -= side
        else:       # 横条
            xx = x
            for s_ in row:
                ww = s_ / side if side else 0
                rects.append((xx, y, ww, side))
                xx += ww
            y += side; h -= side
        i = j
    return rects


def build_html(data: dict, hero_rel: str, crops: dict[str, str], palette: list[dict],
               page: int, total: int, brand_rule: str, hero_box=None,
               hero_size=None, crop_sizes=None) -> str:
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

    W_GRID, H_GRID = 912, 668
    T_TEXT = 86  # 每个文本块的最小高度

    # 解出统一的图高 h：Σ a*h*(h+T) = W*H
    A = sum(aspects)
    import math
    h = (-T_TEXT * A + math.sqrt((T_TEXT * A) ** 2 + 4 * A * W_GRID * H_GRID)) / (2 * A)
    weights = [a * h * (h + T_TEXT) for a in aspects]
    rects = _squarify(weights, 0.0, 0.0, float(W_GRID), float(H_GRID))

    cols_html = ""
    for i, (rx, ry, rw, rh) in enumerate(rects):
        if i >= len(order):
            break
        p = order[i]
        slot = p["slot"]
        cmf = p.get("cmf") or {}
        img_h = min(rw / aspects[i], max(40.0, rh - 54))
        left = rw - aspects[i] * img_h
        cols_html += f"""
        <div class="blk" style="left:{rx:.1f}px;top:{ry:.1f}px;width:{rw:.1f}px;height:{rh:.1f}px">
          <img src="crops/{esc(crops[slot])}" style="width:{aspects[i]*img_h:.1f}px;height:{img_h:.1f}px">
          <div class="mtext">
            <div class="mt-term">{esc(p.get('term') or SLOT_CN.get(slot, slot))}</div>
            <div class="mt-fam">{esc(FAMILY_CN.get(p.get('part_family'), ''))}</div>
            <div class="mt-form">{esc(p.get('form') or '')}</div>
            <div class="mt-cmf">{esc(cmf.get('material_class') or '')} · {esc(cmf.get('finish') or '')}</div>
          </div>
        </div>"""

    mosaic = cols_html

    barbits = "".join(
        f'<i style="width:{c["pct"]*100:.2f}%;background:{c["hex"]}"></i>' for c in palette)

    lines = "".join(f"<li>{esc(x)}</li>" for x in (u.get("character_lines") or [])[:3])


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
    <div class="left">
      <div class="hero"><img src="{esc(hero_rel)}" alt=""></div>
      <div class="textblock">
        <div class="eyebrow">Front Face / 前脸</div>
        <div class="lead">{esc(u.get('gesture'))}</div>
        <ul class="lines">{lines}</ul>
        <div class="meta">{esc(u.get('proportion'))}　{esc(u.get('judgement'))}</div>
      </div>
    </div>
    <div class="mosaic">{mosaic}</div>
  </main>

  <footer>
    <div class="model"><b>{esc(v.get('brand'))} {esc(v.get('model'))}</b>　{esc(v.get('category'))}　·　{esc(brand_rule)}</div>
    <div class="pn">{page:02d} / {total:02d}</div>
  </footer>
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--page", type=int, default=1)
    ap.add_argument("--total", type=int, default=10)
    ap.add_argument("--data-dir", default="data-test")
    ap.add_argument("--brand-rule", default="")
    ap.add_argument("--boxes", help="编辑器导出的裁框 JSON（覆盖 bbox）")
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
                      Image.open(hero_abs).size, crop_sizes)
    out = outdir / f"{slug}.html"
    out.write_text(html, encoding="utf-8")
    print(f"[ok] {out}  crops={len(crops)}  palette={[c['hex'] for c in palette]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
