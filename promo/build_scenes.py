# -*- coding: utf-8 -*-
"""从真实 harvest 数据生成宣传片场景 02 / 03（静态 HTML，供 hyperframes 渲染）。"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "assets" / "data.json").read_text(encoding="utf-8"))

KEYWORDS = ["德龙6X6", "德龙X3000", "德龙", "豪沃", "天锦", "JH6", "沙漠牵引车"]
COLX = [120, 470, 820]
ROWY = [180 + i * 170 for i in range(5)]


def hl(title: str) -> tuple[str, bool]:
    """把标题里的车型词包成 <em>，返回 (html, 是否命中)。"""
    out, hit, last = [], False, 0
    marks = []
    for kw in KEYWORDS:
        start = 0
        while True:
            i = title.find(kw, start)
            if i < 0:
                break
            marks.append((i, i + len(kw)))
            start = i + len(kw)
    marks.sort()
    merged = []
    for a, b in marks:
        if merged and a <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], b))
        else:
            merged.append((a, b))
    for a, b in merged:
        out.append(html.escape(title[last:a]))
        out.append(f'<em class="on">{html.escape(title[a:b])}</em>')
        last = b
        hit = True
    out.append(html.escape(title[last:]))
    return "".join(out), hit


def build_02() -> str:
    cards = []
    for i, t in enumerate(DATA["titles"][:15]):
        body, hit = hl(t)
        cls = "card lit" if hit else "card"
        cards.append(
            f'      <div class="{cls}" id="c{i}" style="grid-column:{i % 3 + 1};grid-row:{i // 3 + 1}">'
            f'<div class="t">{body}</div></div>')

    rows = []
    top = max(c["mentions"] for c in DATA["candidates"])
    for i, c in enumerate(DATA["candidates"]):
        sc = round(c["mentions"] / top, 3)
        rows.append(
            f'      <div class="row" id="row{i}">'
            f'<div class="name">{html.escape(c["brand"])}<small>{html.escape(c["model"])}</small></div>'
            f'<div class="track"><div class="fill" style="transform:scaleX({sc})"></div></div>'
            f'<div class="n" data-n="{c["mentions"]}">{c["mentions"]}</div></div>')

    tpl = (ROOT / "templates" / "02-retrieval.html.tpl").read_text(encoding="utf-8")
    return (tpl.replace("__CARDS__", "\n".join(cards))
               .replace("__ROWS__", "\n".join(rows))
               .replace("__ARTICLES__", str(DATA["articles"]))
               .replace("__NCAND__", str(len(DATA["candidates"]))))


def curve(x1, y1, x2, y2) -> str:
    mx = (x1 + x2) / 2
    return f"M {x1} {y1} C {mx} {y1}, {mx} {y2}, {x2} {y2}"


def build_03() -> str:
    cands = DATA["candidates"]
    arts = []
    for c in cands:
        if c["evidence"] not in arts:
            arts.append(c["evidence"])
    arts = arts[:5]

    qx, qy = 300, 600
    art_pos = {t: (780, 270 + i * 145) for i, t in enumerate(arts)}
    car_y = [230 + i * 125 for i in range(len(cands))]

    wires, nodes = [], []
    for t, (ax, ay) in art_pos.items():
        wires.append(f'<path class="wire art" d="{curve(qx + 80, qy, ax - 180, ay)}" '
                     f'pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>')
    for i, c in enumerate(cands):
        ax, ay = art_pos[c["evidence"]]
        mx, my = 1560, car_y[i]
        keep = " keep" if i == 0 else ""
        wires.append(f'<path class="wire car{keep}" d="{curve(ax + 180, ay, mx - 190, my)}" '
                     f'pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/>')

    nodes.append(f'  <div class="node q" id="n-q" style="left:{qx}px;top:{qy}px">'
                 f'{html.escape(DATA["category"])}</div>')
    for i, t in enumerate(arts):
        x, y = art_pos[t]
        nodes.append(f'  <div class="node art" id="a{i}" style="left:{x}px;top:{y}px">'
                     f'<div class="t">{html.escape(t[:34])}</div>'
                     f'<div class="m">文章 {i + 1}</div></div>')
    for i, c in enumerate(cands):
        y = car_y[i]
        big = " big" if i == 0 else ""
        nodes.append(f'  <div class="node car{big}" id="k{i}" style="left:1560px;top:{y}px">'
                     f'<div class="b">{html.escape(c["brand"])}<small>{html.escape(c["model"])}</small></div>'
                     f'<div class="tag">{html.escape(c["relation"])}</div>'
                     f'<div class="c">{c["mentions"]} 篇</div></div>')

    top = cands[0]
    tpl = (ROOT / "templates" / "03-association.html.tpl").read_text(encoding="utf-8")
    return (tpl.replace("__WIRES__", "\n".join(wires))
               .replace("__NODES__", "\n".join(nodes))
               .replace("__TOP__", html.escape(f'{top["brand"]} {top["model"]}'))
               .replace("__REASON__", html.escape(top["reason"])))


def main() -> int:
    (ROOT / "compositions" / "02-retrieval.html").write_text(build_02(), encoding="utf-8")
    (ROOT / "compositions" / "03-association.html").write_text(build_03(), encoding="utf-8")
    print("[ok] scenes built")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
