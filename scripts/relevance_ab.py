# -*- coding: utf-8 -*-
"""相关性 A/B 评测：读 relevance-pool.json，算 vehicle_precision / stratum_recall / wrong_type_rate，
生成可直接阅读的对照文档。

用法: PYTHONPATH=src python scripts/relevance_ab.py
输出: data-test/evals/ab-20261031/RELEVANCE.md
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "data-test" / "evals" / "ab-20261031" / "relevance-pool.json"
OUT = ROOT / "data-test" / "evals" / "ab-20261031" / "RELEVANCE.md"

LABEL_TXT = {2: "✅ 直证", 1: "🟡 类比", 0: "⛔ 陷阱"}
ARM_TXT = {"named": "车型", "direction": "方向", None: "—"}


def _arm_stats(rows: list[dict], arm: str) -> dict:
    proposed = [r for r in rows if r.get(arm)]
    named = [r for r in proposed if r[arm] == "named"]
    direction = [r for r in proposed if r[arm] == "direction"]
    ok = lambda rs: [r for r in rs if r["label"] >= 1]  # noqa: E731
    return {
        "proposed": len(proposed),
        "named": len(named),
        "named_ok": len(ok(named)),
        "named_precision": round(len(ok(named)) / len(named), 3) if named else None,
        "direction": len(direction),
        "direction_ok": len(ok(direction)),
        "direction_precision": round(len(ok(direction)) / len(direction), 3)
        if direction else None,
        "wrong": sum(1 for r in proposed if r["label"] == 0),
        "wrong_rate": round(sum(1 for r in proposed if r["label"] == 0) / len(proposed), 3)
        if proposed else 0.0,
        "strong": sum(1 for r in proposed if r["label"] == 2),
        "strata": sorted({r["stratum"] for r in ok(proposed) if r.get("stratum")}),
    }


def main() -> int:
    data = json.loads(POOL.read_text(encoding="utf-8"))
    cases = data["cases"]
    agg = {"a": {"named": 0, "named_ok": 0, "direction": 0, "direction_ok": 0,
                 "proposed": 0, "wrong": 0, "strong": 0},
           "b": {"named": 0, "named_ok": 0, "direction": 0, "direction_ok": 0,
                 "proposed": 0, "wrong": 0, "strong": 0}}
    md = ["# 相关性对照：有 skill vs 无 skill（2026-10-31）", "",
          "| 属性 | 内容 |", "|---|---|",
          "| 评的是什么 | 两臂给出的**目标是否与“这类车 + 这个部件”相关**（不是占槽数） |",
          "| 池子 | 两臂候选并集 + 陷阱项（结构上不该出现的车），共 "
          f"{sum(len(c['rows']) for c in cases)} 条 |",
          "| 判定 | 2 直证（同类目/同构型且部件可裁）/ 1 类比（异类目但能提供部件或环境证据）/ 0 陷阱 |",
          "| 两臂 | A＝无 skill（自由格式）；B＝skill v0.2（含 provisional） |",
          "| 标注 | 本文件为**模型标注草案**，需产品负责人抽查（尤其天锦/北奔构型、吨位门槛、厨余是否算压缩式） |",
          ""]

    for case in cases:
        rows = case["rows"]
        a, b = _arm_stats(rows, "a"), _arm_stats(rows, "b")
        for k in ("named", "named_ok", "direction", "direction_ok", "proposed", "wrong",
                  "strong"):
            agg["a"][k] += a[k]
            agg["b"][k] += b[k]
        need = case["strata_needed"]
        md += [f"## {case['id']} · {case['title']}", "",
               "| 候选目标 | 层级 | A | B | 判定 | 依据 |",
               "|---|---|:--:|:--:|---|---|"]
        for r in rows:
            md.append(f"| {r['target']} | {r.get('stratum') or '—'} | "
                      f"{ARM_TXT[r.get('a')]} | {ARM_TXT[r.get('b')]} | "
                      f"{LABEL_TXT[r['label']]} | {r['why']} |")
        cov_a = [s for s in need if s in a["strata"]]
        cov_b = [s for s in need if s in b["strata"]]
        md += ["", f"**{case['id']} 小结**：A 提出 {a['proposed']} 条（车型 {a['named']} / 方向 {a['direction']}），"
               f"车型精确率 {a['named_precision']}，层覆盖 {len(cov_a)}/{len(need)}"
               f"（{'、'.join(cov_a) or '无'}）；B 提出 {b['proposed']} 条"
               f"（车型 {b['named']} / 方向 {b['direction']}），"
               f"车型精确率 {b['named_precision']}，层覆盖 {len(cov_b)}/{len(need)}"
               f"（{'、'.join(cov_b) or '无'}）。", ""]

    def _pct(x):
        return "—" if x is None else f"{x*100:.0f}%"

    np_a = round(agg["a"]["named_ok"] / agg["a"]["named"], 3) if agg["a"]["named"] else None
    np_b = round(agg["b"]["named_ok"] / agg["b"]["named"], 3) if agg["b"]["named"] else None
    dp_a = (round(agg["a"]["direction_ok"] / agg["a"]["direction"], 3)
            if agg["a"]["direction"] else None)
    dp_b = (round(agg["b"]["direction_ok"] / agg["b"]["direction"], 3)
            if agg["b"]["direction"] else None)

    md += ["## 总体对比", "",
           "| 指标 | A（无 skill） | B（skill v0.2） | 怎么看 |",
           "|---|---:|---:|---|",
           f"| 提出目标总数 | {agg['a']['proposed']} | {agg['b']['proposed']} | 数量不代表质量 |",
           f"| 其中具体车型 | {agg['a']['named']} | {agg['b']['named']} | B 大多只给到“方向” |",
           f"| 其中方向级 | {agg['a']['direction']} | {agg['b']['direction']} | 方向级要能转正才算数 |",
           f"| **车型精确率**（label≥1） | **{_pct(np_a)}** | **{_pct(np_b)}** | 报出来的车对不对 |",
           f"| 其中**直证**（label=2） | **{agg['a']['strong']}** | **{agg['b']['strong']}** | 真正能当主证据的 |",
           f"| 方向精确率（label≥1） | {_pct(dp_a)} | {_pct(dp_b)} | 方向是不是该去的方向 |",
           f"| 硬错误（label=0 被提出） | {agg['a']['wrong']} | {agg['b']['wrong']} | 必须为 0 |",
           "",
           "## 结论", ""]

    # 结论按数据写死计算，不手写数字
    cov_cases = []
    for case in cases:
        rows = case["rows"]
        a, b = _arm_stats(rows, "a"), _arm_stats(rows, "b")
        need = case["strata_needed"]
        cov_cases.append((case["id"], len([s for s in need if s in a["strata"]]),
                          len([s for s in need if s in b["strata"]]), len(need)))
    a_cover = sum(c[1] for c in cov_cases)
    b_cover = sum(c[2] for c in cov_cases)
    total_need = sum(c[3] for c in cov_cases)
    md += [
        f"1. **相关性上两臂没有明显差距**：车型精确率 A {_pct(np_a)} vs B {_pct(np_b)}；"
        f"真正算得上“直证”的目标 A {agg['a']['strong']} 条 / B {agg['b']['strong']} 条；"
        f"陷阱项两臂都是 {agg['a']['wrong']}/{agg['b']['wrong']}——"
        "也就是说，**skill 并没有让模型选出“更相关”的车**。",
        f"2. **差别在“给什么、给多少”**：A 给出 {agg['a']['named']} 个具体车型（含待核的“X 级”），"
        f"B 只给 {agg['b']['named']} 个车型、其余 {agg['b']['direction']} 条是方向。"
        "对需要 12 页车型的报告，B 的产物不能直接开爬。",
        f"3. **层覆盖 A 更全**：三案例所需 {total_need} 个层级，A 覆盖 {a_cover} 个、B 覆盖 {b_cover} 个。"
        "B 把跨车型/平台对照压进 backlog（`allow_cross_vehicle=false`），"
        "导致“为什么这么设计”的那层证据没进清单。",
        "4. 因此 skill v0.2 的价值仍是**合规与可审计**（结构排除、缺口分类、转正路径），"
        "**不是判断质量**；而它现在反而**牺牲了覆盖与交付**。",
        "",
        "## 这把尺子之后的用法", "",
        "- 主指标：`vehicle_precision`（车型精确率）与 `strata_coverage`（层覆盖），"
        "`fill_rate` 只作可行性约束；",
        "- 每次改 skill 或换模型，都重跑这 3 个案例并对比这两个数；",
        "- 标注草案需产品负责人抽查一遍，抽查通过后冻结为评测集 v1"
        "（`data-test/evals/association-relevance-v1.json`）。",
        ""]

    OUT.write_text("\n".join(md), encoding="utf-8")
    _write_html(data, cases, agg, np_a, np_b, a_cover, b_cover, total_need)
    print("\n".join(md[:8]))
    print(f"\n→ {OUT}")
    print(f"→ {OUT.with_suffix('.html')}")
    return 0


def _write_html(data, cases, agg, np_a, np_b, a_cover, b_cover, total_need) -> None:
    """并排对照页：色块标 2/1/0，便于快速扫读。"""
    color = {2: "#e6f4ea", 1: "#fff7e0", 0: "#fde8e8"}
    tag = {2: "直证", 1: "类比", 0: "陷阱"}
    arm = {"named": "车型", "direction": "方向", None: "—"}
    h = ["<!doctype html><html lang='zh'><head><meta charset='utf-8'>",
         "<title>关联清单 A/B 相关性对照</title><style>",
         "body{font:14px/1.6 -apple-system,'Segoe UI','Microsoft YaHei',sans-serif;"
         "margin:24px;color:#222;background:#fafafa}",
         "h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:28px 0 8px}",
         ".sub{color:#666;margin-bottom:16px}",
         "table{border-collapse:collapse;width:100%;background:#fff;margin-bottom:8px}",
         "th,td{border:1px solid #e3e3e3;padding:6px 8px;vertical-align:top;text-align:left}",
         "th{background:#f3f4f6;font-weight:600;font-size:13px}",
         "td.c{text-align:center;white-space:nowrap;font-size:12px}",
         ".card{display:inline-block;background:#fff;border:1px solid #e3e3e3;"
         "border-radius:8px;padding:10px 16px;margin:0 10px 10px 0}",
         ".big{font-size:22px;font-weight:700}",
         ".muted{color:#888;font-size:12px}",
         "ol{margin:8px 0 0 20px}li{margin:6px 0}",
         "</style></head><body>",
         "<h1>关联清单 A/B 相关性对照</h1>",
         "<div class='sub'>A＝无 skill（自由格式）｜B＝skill v0.2（含 provisional）｜"
         f"池子 {sum(len(c['rows']) for c in cases)} 条 = 两臂并集 + 陷阱项</div>",
         "<div>",
         f"<div class='card'><div class='muted'>车型精确率 A</div>"
         f"<div class='big'>{'—' if np_a is None else f'{np_a*100:.0f}%'}</div>"
         f"<div class='muted'>提出 {agg['a']['named']} 个车型</div></div>",
         f"<div class='card'><div class='muted'>车型精确率 B</div>"
         f"<div class='big'>{'—' if np_b is None else f'{np_b*100:.0f}%'}</div>"
         f"<div class='muted'>提出 {agg['b']['named']} 个车型</div></div>",
         f"<div class='card'><div class='muted'>层覆盖（A / B）</div>"
         f"<div class='big'>{a_cover} / {b_cover}</div>"
         f"<div class='muted'>共需 {total_need} 层</div></div>",
         f"<div class='card'><div class='muted'>硬错误（A / B）</div>"
         f"<div class='big'>{agg['a']['wrong']} / {agg['b']['wrong']}</div>"
         f"<div class='muted'>陷阱项被提出次数</div></div>",
         f"<div class='card'><div class='muted'>直证数（A / B）</div>"
         f"<div class='big'>{agg['a']['strong']} / {agg['b']['strong']}</div>"
         f"<div class='muted'>label=2 的目标</div></div>",
         "</div>"]

    for case in cases:
        rows = case["rows"]
        h += [f"<h2>{case['id']} · {case['title']}</h2>",
              "<table><tr><th>候选目标</th><th>层级</th><th>A</th><th>B</th>"
              "<th>判定</th><th>依据</th></tr>"]
        for r in rows:
            bg = color[r["label"]]
            h.append(
                f"<tr style='background:{bg}'><td>{r['target']}</td>"
                f"<td class='c'>{r.get('stratum') or '—'}</td>"
                f"<td class='c'>{arm[r.get('a')]}</td>"
                f"<td class='c'>{arm[r.get('b')]}</td>"
                f"<td class='c'><b>{tag[r['label']]}</b></td>"
                f"<td>{r['why']}</td></tr>")
        h.append("</table>")

    h += ["<h2>结论</h2><ol>",
          f"<li>相关性没有明显差距：车型精确率 A {'—' if np_a is None else f'{np_a*100:.0f}%'}"
          f" vs B {'—' if np_b is None else f'{np_b*100:.0f}%'}；陷阱项两臂都未提出。</li>",
          f"<li>差别在“给什么”：A 给 {agg['a']['named']} 个具体车型，B 只给 {agg['b']['named']} 个、"
          f"其余 {agg['b']['direction']} 条是方向级。</li>",
          f"<li>层覆盖 A 更全（{a_cover}/{total_need} vs {b_cover}/{total_need}）："
          "B 把平台/跨车型层压进 backlog，导致“为什么这么设计”的证据缺失。</li>",
          "<li>skill 的价值在合规与可审计（结构排除、缺口分类、转正路径），不在“选得更准”；"
          "而它当前牺牲了覆盖与交付。</li>",
          "</ol>", "</body></html>"]
    OUT.with_suffix(".html").write_text("\n".join(h), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
