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


def color_composition(path: Path, max_colors: int = MAX_COLORS, bg=None) -> list[dict]:
    """返回 [{hex, r,g,b, pct}]，按面积降序，最多 4 段。"""
    im = Image.open(path).convert("RGB")
    im.thumbnail((220, 220))
    arr = np.asarray(im).reshape(-1, 3).astype(float)

    if bg is None:
        border = np.concatenate([arr[:12], arr[-12:], arr[:, :12].reshape(-1, 3),
                                 arr[:, -12:].reshape(-1, 3)])
        bg = np.median(border, axis=0)
    else:
        bg = np.asarray(bg, dtype=float)

    centers, counts = _kmeans(arr, k=max(5, max_colors + 1))
    order = np.argsort(-counts)
    kept = []
    for i in order:
        c = centers[i]
        share = counts[i] / counts.sum()
        if share < 0.015:
            continue
        lum = c.mean() / 255
        sat = (c.max() - c.min()) / max(c.max(), 1)
        if len(kept) < 2 and (np.linalg.norm(c - bg) < 55 or
                              (lum > 0.72 and sat < 0.13)):
            continue  # 背景或地面投影
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

def crop_parts(src: Path, data: dict, outdir: Path, slug: str) -> dict[str, str]:
    im = Image.open(src).convert("RGB")
    w, h = im.size
    outdir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for p in data.get("parts", []):
        bbox = p.get("bbox")
        if p.get("visible") == "not_visible" or not bbox:
            continue
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
        if crop.size[0] < 160 or crop.size[1] < 120:
            cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
            half_w, half_h = max(90, (box[2] - box[0])), max(70, (box[3] - box[1]))
            box = (max(0, cx - half_w), max(0, cy - half_h),
                   min(w, cx + half_w), min(h, cy + half_h))
            crop = im.crop(box)
        gray = np.asarray(crop.convert("L"))
        if gray.mean() < 35:
            continue  # 全黑区域，判为无效裁图
        # 统一成 4:3，避免卡片里高度参差
        cw, ch = crop.size
        target = 4 / 3
        if cw / ch > target:
            new_w = int(ch * target)
            crop = crop.crop(((cw - new_w) // 2, 0, (cw - new_w) // 2 + new_w, ch))
        else:
            new_h = int(cw / target)
            top = max(0, (ch - new_h) // 2)
            crop = crop.crop((0, top, cw, top + new_h))
        name = f"{slug}-{p['slot']}.jpg"
        crop.resize((720, 540), Image.LANCZOS).save(outdir / name, quality=90)
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
main{margin-top:20px;height:668px;display:grid;grid-template-columns:540px 1fr;gap:20px}
.left{display:grid;grid-template-rows:430px 218px;gap:20px}
.hero{position:relative;background:#fff;border:1px solid var(--line);overflow:hidden;align-self:start;justify-self:center}
.hero img{width:100%;height:100%;object-fit:contain}
.mark{position:absolute;border:1px solid var(--accent);background:rgba(255,255,255,.06)}
.mark b{position:absolute;top:-9px;left:-9px;width:18px;height:18px;background:var(--accent);
color:#fff;font-size:10px;display:flex;align-items:center;justify-content:center;
font-family:Consolas,monospace}
.textblock{background:var(--block);padding:16px 18px;display:flex;flex-direction:column;gap:8px;
overflow:hidden}
.eyebrow{font-size:9px;letter-spacing:.22em;color:var(--muted);text-transform:uppercase;
font-family:Bahnschrift,"Arial Narrow",sans-serif}
.lead{font-size:15px;line-height:1.65;font-weight:600}
.lines{list-style:none;font-size:12.5px;line-height:1.55;color:#2b2e33;display:flex;
flex-direction:column;gap:3px}
.lines li{padding-left:14px;position:relative}
.lines li:before{content:"";position:absolute;left:0;top:7px;width:6px;height:1px;
background:var(--accent)}
.meta{font-size:11.5px;color:var(--graphite);line-height:1.5}
.grid{display:grid;grid-template-columns:repeat(2,1fr);grid-template-rows:repeat(3,1fr);gap:16px}
.card{background:#fff;border:1px solid var(--line);display:grid;grid-template-rows:130px 1fr;
overflow:hidden}
.card .shot{position:relative;overflow:hidden;background:#f1efe9}
.card .shot img{width:100%;height:100%;object-fit:cover}
.card .shot.empty{display:flex;align-items:center;justify-content:center;background:#f4f2ec;border-bottom:1px solid var(--line)}
.card .na{font-size:11px;color:#a9a59b;letter-spacing:.1em}
.card .no{position:absolute;top:8px;left:8px;font-size:9px;letter-spacing:.12em;
background:var(--ink);color:#fff;padding:2px 6px;font-family:Consolas,monospace}
.card .body{padding:10px 12px;background:var(--block);display:flex;flex-direction:column;gap:4px;
overflow:hidden}
.card h3{font-size:13px;font-weight:700;letter-spacing:.02em;line-height:1.2}
.card .fam{font-size:9px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}
.card p{font-size:11.5px;line-height:1.45;color:#2b2e33;
display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.card .cmf{font-size:10.5px;color:var(--graphite)}
.chips{display:flex;flex-direction:column;gap:9px;background:var(--block);padding:14px 16px}
.chip{display:flex;align-items:center;gap:10px}
.chip .sw{width:34px;height:22px;border-radius:2px;border:1px solid rgba(0,0,0,.08)}
.chip .v{font-family:Consolas,monospace;font-size:11px;color:var(--ink)}
.chip .p{font-family:Consolas,monospace;font-size:11px;color:var(--muted);margin-left:auto}
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


def build_html(data: dict, hero_rel: str, crops: dict[str, str], palette: list[dict],
               page: int, total: int, brand_rule: str, hero_box=None,
               hero_size=None) -> str:
    u = data.get("unit", {})
    v = data.get("vehicle", {})
    tags = u.get("style_tags", [])
    accent = accent_of(palette)

    marks = ""
    parts_vis = [x for x in data.get("parts", [])
                 if x.get("bbox") and x.get("visible") != "not_visible"]
    for i, p in enumerate(parts_vis, 1):
        x1, y1, x2, y2 = p["bbox"]
        if hero_box and hero_size:
            W, H = hero_size
            bx1, by1, bx2, by2 = hero_box
            bw, bh = max(1, bx2 - bx1), max(1, by2 - by1)
            x1 = (x1 / 1000 * W - bx1) / bw * 1000
            y1 = (y1 / 1000 * H - by1) / bh * 1000
            x2 = (x2 / 1000 * W - bx1) / bw * 1000
            y2 = (y2 / 1000 * H - by1) / bh * 1000
            x1, x2 = max(0, min(1000, x1)), max(0, min(1000, x2))
            y1, y2 = max(0, min(1000, y1)), max(0, min(1000, y2))
        marks += (f'<div class="mark" style="left:{x1/10:.2f}%;top:{y1/10:.2f}%;'
                  f'width:{(x2-x1)/10:.2f}%;height:{(y2-y1)/10:.2f}%"><b>{i:02d}</b></div>')

    cards = ""
    order = [p for p in data.get("parts", []) if p.get("visible") != "not_visible"]
    for i, p in enumerate(order, 1):
        slot = p["slot"]
        img = crops.get(slot)
        shot = (f'<div class="shot"><img src="crops/{esc(img)}" alt="">'
                f'<span class="no">{i:02d} / {esc(slot.upper())}</span></div>') if img else \
               (f'<div class="shot empty"><span class="no">{i:02d} / {esc(slot.upper())}</span>'
                f'<span class="na">该视角不可判读</span></div>')
        cmf = p.get("cmf") or {}
        cards += f"""
        <article class="card">{shot}
          <div class="body">
            <h3>{esc(p.get('term') or SLOT_CN.get(slot, slot))}</h3>
            <div class="fam">{esc(FAMILY_CN.get(p.get('part_family'), ''))}</div>
            <p>{esc(p.get('form') or '')}</p>
            <div class="cmf">{esc(cmf.get('material_class') or '')} · {esc(cmf.get('finish') or '')}</div>
          </div>
        </article>"""

    chips = "".join(
        f'<div class="chip"><span class="sw" style="background:{c["hex"]}"></span>'
        f'<span class="v">{c["hex"]}</span>'
        f'<span class="p">{c["pct"]*100:.0f}%</span></div>' for c in palette)

    barbits = "".join(
        f'<i style="width:{c["pct"]*100:.2f}%;background:{c["hex"]}"></i>' for c in palette)

    lines = "".join(f"<li>{esc(x)}</li>" for x in (u.get("character_lines") or [])[:3])

    hw, hh = 540, 430
    if hero_size:
        asp = hero_size[0] / max(1, hero_size[1])
        if asp >= hw / hh:
            hero_w, hero_h = hw, int(hw / asp)
        else:
            hero_w, hero_h = int(hh * asp), hh
    else:
        hero_w, hero_h = hw, hh

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
      <div class="hero" style="width:{hero_w}px;height:{hero_h}px"><img src="{esc(hero_rel)}" alt="">{marks}</div>
      <div class="textblock">
        <div class="eyebrow">Front Face / 前脸</div>
        <div class="lead">{esc(u.get('gesture'))}</div>
        <ul class="lines">{lines}</ul>
        <div class="meta">{esc(u.get('proportion'))}　{esc(u.get('judgement'))}</div>
      </div>
    </div>
    <div class="grid">
      {cards}
      <div class="chips">
        <div class="eyebrow">Color / 色彩构成</div>
        {chips}
        <div class="meta" style="margin-top:auto">{esc(u.get('cmf'))}</div>
      </div>
    </div>
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
        by_slot = {x["slot"]: x.get("bbox") for x in edited.get("parts", [])}
        for p in data.get("parts", []):
            if p.get("slot") in by_slot and by_slot[p["slot"]]:
                p["bbox"] = by_slot[p["slot"]]
                p["visible"] = "full" if p.get("visible") == "not_visible" else p.get("visible")

    slug = re.sub(r"\s+", "-", (data.get("vehicle") or {}).get("model", src.stem))
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    cropdir = outdir / "crops"
    crops = crop_parts(hero_abs, data, cropdir, slug)

    hero_view, hero_box, hero_bg = trim_hero(hero_abs, outdir, slug)
    palette = color_composition(hero_view, bg=hero_bg)
    (outdir / f"{slug}-palette.json").write_text(
        json.dumps(palette, ensure_ascii=False, indent=2), encoding="utf-8")

    # 图片用相对路径（从 out 目录指向 data-test）
    import os
    hero_rel = os.path.relpath(hero_view, outdir)

    html = build_html(data, str(hero_rel).replace("\\", "/"), crops, palette,
                      args.page, args.total, args.brand_rule, hero_box,
                      Image.open(hero_abs).size)
    out = outdir / f"{slug}.html"
    out.write_text(html, encoding="utf-8")
    print(f"[ok] {out}  crops={len(crops)}  palette={[c['hex'] for c in palette]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
