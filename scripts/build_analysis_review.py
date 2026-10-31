# -*- coding: utf-8 -*-
"""把批量分析结果渲染成单文件审阅页（图 + 文本）。

用法:
  PYTHONPATH=src python scripts/build_analysis_review.py --dir data-test/analysis-20261031
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SLOT_LABEL = {
    "grille": "进气格栅", "bumper": "保险杠", "side_guard": "侧防护栏",
    "wheel_arch": "前轮轮拱", "step": "登车踏步", "headlamp": "大灯",
    "mirror": "后视镜", "sun_visor": "遮阳板", "under_guard": "下护板",
    "brand_zone": "品牌标识区", "paint_scheme": "涂装与分色",
}
FAMILY_LABEL = {
    "sheet_metal": "钣金覆盖件", "frame_profile": "型材框架件",
    "cast_forged": "铸锻机加件", "function_attachment": "功能附件",
}
VIS_LABEL = {"full": "完整", "partial": "部分", "not_visible": "不可见"}

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#0f1115;color:#e8eaed;font:15px/1.65 -apple-system,"Segoe UI",
"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:36px 24px 80px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:.5px}
.sub{color:#8b93a1;font-size:13px;margin-bottom:28px}
.stats{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:34px}
.stat{background:#171a21;border:1px solid #232833;border-radius:10px;padding:12px 16px;min-width:130px}
.stat b{display:block;font-size:20px;color:#7cc4ff}
.stat span{font-size:12px;color:#8b93a1}
.card{background:#151820;border:1px solid #232833;border-radius:14px;margin-bottom:26px;overflow:hidden}
.card-head{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;
border-bottom:1px solid #232833;background:#1a1e27}
.model{font-size:18px;font-weight:600}
.model small{color:#8b93a1;font-weight:400;font-size:13px;margin-left:8px}
.tags{display:flex;gap:8px}
.tag{background:#1d3a52;color:#8fd0ff;border-radius:999px;padding:4px 12px;font-size:13px}
.body{display:grid;grid-template-columns:380px 1fr;gap:20px;padding:20px}
.body.one{grid-template-columns:1fr}
.shots img{width:100%;border-radius:8px;display:block;margin-bottom:10px;background:#000}
.shots .cap{font-size:11px;color:#6f7887;margin:-4px 0 12px}
.block{margin-bottom:16px}
.block h4{margin:0 0 4px;font-size:11px;letter-spacing:1.5px;color:#6f7887;text-transform:uppercase}
.block p{margin:0;color:#d5d9e0}
.lines{list-style:none;padding:0;margin:0;counter-reset:ln}
.lines li{position:relative;padding-left:22px;margin-bottom:3px;color:#d5d9e0}
.lines li:before{counter-increment:ln;content:counter(ln);position:absolute;left:0;top:1px;
width:15px;height:15px;border-radius:50%;background:#26303e;color:#8fd0ff;font-size:10px;
text-align:center;line-height:15px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin-top:6px}
th{text-align:left;color:#6f7887;font-weight:500;font-size:11px;letter-spacing:1px;
border-bottom:1px solid #232833;padding:6px 8px}
td{border-bottom:1px solid #1d222b;padding:10px 8px;vertical-align:top}
tr:last-child td{border-bottom:none}
.term{font-weight:600;color:#fff}
.meta{font-size:11.5px;color:#7d8695;margin-top:2px}
.badge{display:inline-block;font-size:10px;padding:1px 6px;border-radius:4px;margin-left:6px}
.b-full{background:#1b3a2a;color:#6fdc9b}
.b-partial{background:#3a3418;color:#e3c56a}
.b-none{background:#3a1f22;color:#ff8a8a}
.b-src{background:#2a2340;color:#b79cff}
.muted{color:#6f7887}
.foot{margin-top:40px;color:#5c6472;font-size:12px;text-align:center}
"""


def esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""


def render_card(d: dict, base: Path) -> str:
    v = d.get("vehicle", {})
    u = d.get("unit", {}) or {}
    tags = u.get("style_tags", [])
    hero = (d.get("assets") or {}).get("hero")
    side = (d.get("assets") or {}).get("side")
    supp = (d.get("supplement") or {})
    supp_slots = set(supp.get("slots") or [])

    def img(path, cap):
        if not path:
            return ""
        rel = Path("..") / path
        return (f'<img src="{esc(rel)}" alt="{esc(cap)}">'
                f'<div class="cap">{esc(cap)}</div>')

    shots = img(hero, f"主图 · {(d.get('assets') or {}).get('hero_view', '')}")
    if side and side != hero:
        shots += img(side, f"补证视角 · {(d.get('assets') or {}).get('side_view', '')}")

    tag_html = "".join(f'<span class="tag">{esc(t.get("tag"))}</span>' for t in tags)

    lines = "".join(f"<li>{esc(x)}</li>" for x in (u.get("character_lines") or []))

    rows = []
    for p in d.get("parts", []):
        vis = p.get("visible")
        badge = f'<span class="badge b-{ {"full":"full","partial":"partial","not_visible":"none"}.get(vis,"none") }">{VIS_LABEL.get(vis,vis)}</span>'
        src = ""
        if p.get("source_view") and p.get("visible") != "not_visible":
            if p.get("source_view") != (d.get("assets") or {}).get("hero_view"):
                src = f'<span class="badge b-src">来源 {esc(p.get("source_view"))}</span>'
        if vis == "not_visible":
            content = '<span class="muted">该视角不可见，未作判断</span>'
        else:
            cmf = p.get("cmf") or {}
            content = (f'<div>{esc(p.get("form"))}</div>'
                       f'<div class="meta">{esc(cmf.get("material_class"))}'
                       f' · {esc(cmf.get("finish"))}</div>'
                       f'<div class="meta">意图：{esc(p.get("intent"))}</div>')
        rows.append(
            f"<tr><td><div class='term'>{esc(p.get('term') or '—')}</div>"
            f"<div class='meta'>{esc(SLOT_LABEL.get(p.get('slot'), p.get('slot')))}{badge}{src}</div></td>"
            f"<td>{esc(FAMILY_LABEL.get(p.get('part_family'), p.get('part_family')) or '—')}"
            f"<div class='meta'>{esc(p.get('family_reason') or '')}</div></td>"
            f"<td>{content}</td></tr>")

    return f"""
<div class="card">
  <div class="card-head">
    <div class="model">{esc(v.get('brand'))} {esc(v.get('model'))}
      <small>{esc(v.get('category'))}</small></div>
    <div class="tags">{tag_html}</div>
  </div>
  <div class="body">
    <div class="shots">{shots}</div>
    <div>
      <div class="block"><h4>走势</h4><p>{esc(u.get('gesture'))}</p></div>
      <div class="block"><h4>特征线</h4><ol class="lines">{lines}</ol></div>
      <div class="block"><h4>比例</h4><p>{esc(u.get('proportion'))}</p></div>
      <div class="block"><h4>CMF</h4><p>{esc(u.get('cmf'))}</p></div>
      <div class="block"><h4>判断</h4><p>{esc(u.get('judgement'))}</p></div>
      <div class="block"><h4>风格依据</h4><p class="muted">
        {'；'.join(esc(t.get('tag')) + ' ← ' + esc(t.get('evidence')) for t in tags)}</p></div>
    </div>
  </div>
  <div style="padding:0 20px 20px">
    <table><thead><tr><th style="width:22%">部件 / 构型名</th>
    <th style="width:24%">族</th><th>形态 · 材料 · 意图</th></tr></thead>
    <tbody>{''.join(rows)}</tbody></table>
  </div>
</div>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--title", default="EquipLens · 分析模块 10 台车审阅")
    args = ap.parse_args()

    d = ROOT / args.dir
    files = sorted(p for p in d.glob("*.json") if not p.name.startswith("_"))
    if not files:
        raise SystemExit(f"{d} 里没有 JSON")

    data = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    summary = {}
    if (d / "_summary.json").exists():
        summary = json.loads((d / "_summary.json").read_text(encoding="utf-8"))

    cards = "".join(render_card(x, d) for x in data)
    tags = [t.get("tag") for x in data for t in (x.get("unit") or {}).get("style_tags", [])]
    dup = len(tags) - len(set(tags))
    review = sum(1 for x in data
                 if (x.get("_meta") or {}).get("status") == "needs_review")
    invisible = sum(1 for x in data for p in x.get("parts", [])
                    if p.get("visible") == "not_visible")

    stats = f"""
<div class="stats">
  <div class="stat"><b>{len(data)}</b><span>车型</span></div>
  <div class="stat"><b>{len(set(tags))}/{len(tags)}</b><span>风格词去重</span></div>
  <div class="stat"><b>{dup}</b><span>跨车重复</span></div>
  <div class="stat"><b>{review}</b><span>待复核</span></div>
  <div class="stat"><b>{invisible}</b><span>不可见部件</span></div>
  <div class="stat"><b>{summary.get('tokens', 0)}</b><span>tokens</span></div>
</div>"""

    out = d / "review.html"
    out.write_text(
        f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        f'<title>{esc(args.title)}</title><style>{CSS}</style></head><body><div class="wrap">'
        f'<h1>{esc(args.title)}</h1>'
        f'<div class="sub">部件：前脸整体 / 进气格栅 / 保险杠 / 侧防护栏 / 前轮轮拱 / 登车踏步'
        f' · 三词一车、跨车去重 · 主图不可见的部位由侧视补证</div>'
        f'{stats}{cards}'
        f'<div class="foot">生成自 {esc(args.dir)} · 契约见 '
        f'docs/superpowers/specs/2026-10-31-analysis-schema-design.md</div>'
        f'</div></body></html>', encoding="utf-8")
    print(f"[ok] {out}  ({len(data)} 台, {len(tags)} 词, 重复 {dup})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
