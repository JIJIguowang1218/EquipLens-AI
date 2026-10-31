# -*- coding: utf-8 -*-
"""把单车报告页导出为可编辑 PPTX：每个元素都是原生形状/文本框/图片。

用法:
  python scripts/export_pptx.py --blocks data-test/report-book --out data-test/report.pptx
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

ROOT = Path(__file__).resolve().parents[1]
PX = 12192000 / 1600.0          # 1 px → EMU（13.333in 宽 / 1600px）
INK = RGBColor(0x11, 0x12, 0x14)
GRAPHITE = RGBColor(0x5C, 0x61, 0x69)
MUTED = RGBColor(0x8B, 0x8F, 0x96)
BLOCK_BG = RGBColor(0xEF, 0xEC, 0xE5)
PAPER = RGBColor(0xFA, 0xF9, 0xF6)
LINE = RGBColor(0xD9, 0xD6, 0xCF)
FONT = "Microsoft YaHei"
FONT_EA = "Microsoft YaHei"


def set_run_font(run, size: float, color, bold: bool = False):
    """同时设置拉丁与东亚字体，避免中文回落到宋体。"""
    f = run.font
    f.size = Pt(size)
    f.bold = bold
    f.color.rgb = color
    f.name = FONT
    rPr = run._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {})
            rPr.append(el)
        el.set("typeface", FONT_EA)


def E(px: float) -> Emu:
    return Emu(int(round(px * PX)))


def rgb(hexstr: str) -> RGBColor:
    h = hexstr.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def add_rect(slide, x, y, w, h, fill=None, line=None, shape=MSO_SHAPE.RECTANGLE):
    sh = slide.shapes.add_shape(shape, E(x), E(y), E(w), E(h))
    sh.shadow.inherit = False
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(0.75)
    sh.text_frame.word_wrap = True
    return sh


def add_text(slide, x, y, w, h, text, size, color=INK, bold=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, spacing=1.0):
    tb = slide.shapes.add_textbox(E(x), E(y), E(w), E(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Emu(0)
    tf.margin_top = tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = spacing
    r = p.add_run(); r.text = text
    set_run_font(r, size, color, bold)
    return tb


def cover_crop(path: Path, w_px: float, h_px: float, tmp: Path) -> Path:
    im = Image.open(path).convert("RGB")
    target = w_px / max(1.0, h_px)
    iw, ih = im.size
    if iw / ih > target:
        nw = int(ih * target)
        im = im.crop(((iw - nw) // 2, 0, (iw - nw) // 2 + nw, ih))
    else:
        nh = int(iw / target)
        top = max(0, (ih - nh) // 2)
        im = im.crop((0, top, iw, top + nh))
    out = tmp / f"{path.stem}-{int(w_px)}x{int(h_px)}.jpg"
    im.save(out, quality=92)
    return out


CANVAS_LEFT, CANVAS_TOP = 64, 156   # 画布在页面中的原点（page padding 48 + 居中留白 16 / 40+96+20）


def build_slide(prs, data: dict, tmp: Path):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_rect(slide, 0, 0, 1600, 900, fill=PAPER)

    u = data.get("unit") or {}
    v = data.get("vehicle") or {}
    palette = data.get("palette") or []

    # ---- 上栏 ----
    add_text(slide, 48, 40, 400, 40, "竞品分析", 20, INK, True)
    add_text(slide, 48, 84, 460, 18, "COMPETITIVE DESIGN ANALYSIS", 7.5, MUTED)
    accent = rgb(palette[0]["hex"]) if palette else INK
    add_rect(slide, 48, 132, 150, 3, fill=accent)

    tags = [t.get("tag", "") for t in (u.get("style_tags") or [])][:3]
    tx = 1552
    for tag in reversed(tags):
        w = 26 + len(tag) * 15
        sh = add_rect(slide, tx - w, 40, w, 30, fill=None, line=INK,
                      shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        tf = sh.text_frame
        tf.margin_left = tf.margin_right = Emu(0)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = tag
        set_run_font(r, 9, INK)
        tx -= w + 8

    # 色彩构成条
    if palette:
        bx, bw = 1252, 300
        add_text(slide, bx, 80, bw, 12, "COLOR COMPOSITION", 6, MUTED)
        add_text(slide, bx + bw - 60, 80, 60, 12, "4 / AREA", 6, MUTED, align=PP_ALIGN.RIGHT)
        x = bx
        for c in palette:
            seg = bw * c["pct"]
            add_rect(slide, x, 96, seg, 13, fill=rgb(c["hex"]))
            x += seg

    # ---- 内容块 ----
    for b in data.get("blocks", []):
        b = dict(b, x=b["x"] + CANVAS_LEFT, y=b["y"] + CANVAS_TOP)
        if b["kind"] == "img":
            src = Path(b["src"])
            if not src.exists():
                continue
            pic = cover_crop(src, b["w"], b["h"], tmp)
            slide.shapes.add_picture(str(pic), E(b["x"]), E(b["y"]), E(b["w"]), E(b["h"]))
            if b.get("idx"):
                badge = add_rect(slide, b["x"] + 6, b["y"] + 6, 26, 16,
                                 fill=RGBColor(0x1A, 0x1C, 0x1F))
                tf = badge.text_frame
                tf.margin_left = tf.margin_right = Emu(0)
                tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
                r = p.add_run(); r.text = f"{b['idx']:02d}"
                set_run_font(r, 6, RGBColor(0xFF, 0xFF, 0xFF))
        else:
            sh = add_rect(slide, b["x"], b["y"], b["w"], b["h"], fill=BLOCK_BG)
            tf = sh.text_frame
            tf.word_wrap = True
            tf.margin_left = E(11); tf.margin_right = E(9)
            tf.margin_top = E(9); tf.margin_bottom = E(6)
            tf.vertical_anchor = MSO_ANCHOR.TOP
            tf.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE

            if b["id"] == "front_text":
                lines = [
                    ("FRONT FACE / 前脸", 6, MUTED, True, 1.0),
                    (u.get("gesture") or "", 10.5, INK, True, 1.25),
                ]
                for ln in (u.get("character_lines") or [])[:3]:
                    lines.append(("· " + ln, 8.5, RGBColor(0x2B, 0x2E, 0x33), False, 1.35))
                meta = "　".join(x for x in [u.get("proportion") or "",
                                            u.get("judgement") or ""] if x)
                lines.append((meta, 7.5, GRAPHITE, False, 1.3))
            else:
                cmf = b.get("cmf") or ""
                lines = [
                    (f"{b.get('idx', 0):02d}  {b.get('term', '')}", 7.6, INK, True, 1.15),
                    (b.get("fam", ""), 5.4, MUTED, False, 1.1),
                    (b.get("form", ""), 6.6, RGBColor(0x2B, 0x2E, 0x33), False, 1.25),
                    (cmf, 6.0, GRAPHITE, False, 1.15),
                ]

            first = True
            for text, size, color, bold, ls in lines:
                if not text:
                    continue
                p = tf.paragraphs[0] if first else tf.add_paragraph()
                first = False
                p.line_spacing = ls
                p.space_after = Pt(1)
                r = p.add_run(); r.text = text
                set_run_font(r, size, color, bold)

    # ---- 下栏 ----
    add_rect(slide, 48, 848, 1504, 1, fill=LINE)
    add_text(slide, 48, 858, 900, 20,
             f"{v.get('brand', '')} {v.get('model', '')}　{v.get('category', '')}　·　"
             f"{data.get('brand_rule', '')}", 7.5, GRAPHITE)
    add_text(slide, 1452, 858, 100, 20, f"{int(data.get('page', 1)):02d} / "
             f"{int(data.get('total', 10)):02d}", 7, MUTED, align=PP_ALIGN.RIGHT)


def patch_theme_fonts(path: Path):
    """把主题里的东亚字体改成无衬线，保证用户新建的文本框也不再回落宋体。"""
    import shutil, zipfile
    tmp = path.with_suffix(".tmp.pptx")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("ppt/theme/theme") and item.filename.endswith(".xml"):
                txt = data.decode("utf-8")
                txt = txt.replace('<a:ea typeface=""', '<a:ea typeface="Microsoft YaHei"')
                txt = txt.replace('<a:ea typeface="宋体"', '<a:ea typeface="Microsoft YaHei"')
                data = txt.encode("utf-8")
            zout.writestr(item, data)
    shutil.move(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--blocks", required=True, help="含 *-blocks.json 的目录")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    src = ROOT / args.blocks
    files = sorted(src.glob("*-blocks.json"))
    if not files:
        raise SystemExit("没找到 *-blocks.json")

    prs = Presentation()
    prs.slide_width = Emu(12192000)   # 13.333in
    prs.slide_height = Emu(6858000)   # 7.5in

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            build_slide(prs, data, tmp)

    out = ROOT / args.out
    prs.save(out)
    patch_theme_fonts(out)
    print(f"[ok] {out}  slides={len(prs.slides)}  size={out.stat().st_size/1024:.0f}KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
