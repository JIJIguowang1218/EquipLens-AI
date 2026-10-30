# -*- coding: utf-8 -*-
"""离线回放：同一批已落盘语料，关键词基线 vs L3 确定性闸门，逐批对照。

用途：`l3gate` 接入 text-run 的 grade 阶段后，用历史批次（无需联网）量化
"闸门砍掉了多少 A 档字数、理由分布如何"，避免只有金标 265 段一个口径。

用法:
    PYTHONPATH=src python scripts/replay_gate.py                 # 默认 T18-roster 四批
    PYTHONPATH=src python scripts/replay_gate.py <batch_dir> ...  # 指定批次
输出:
    data-test/evals/gate-replay-<YYYYMMDD>.md / .json
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equiplens import passage  # noqa: E402

EV = ROOT / "data-test" / "evals"
DEFAULT_GLOB = "batch-corpus-roster-*-20261030"


def _registry() -> dict:
    p = ROOT / "data" / "source_registry.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"sources": []}


def _row(name: str, m: dict) -> dict:
    return {
        "batch": name,
        "articles": m["articles"],
        "total_chars": m["total_chars"],
        "a_chars": m["a_chars"],
        "a_share": m["a_share"],
        "gated_a_chars": m.get("gated_a_chars", 0),
        "gated_a_share": m.get("gated_a_share", 0.0),
        "gated_keep_rate": m.get("gated_keep_rate", 0.0),
        "gate_pass_count": m.get("gate_pass_count", 0),
        "gate_candidate_count": m.get("gate_candidate_count", 0),
        "gate_pass_rate": m.get("gate_pass_rate", 0.0),
        "gate_reject_reasons": m.get("gate_reject_reasons", {}),
    }


def main(argv: list[str]) -> int:
    dirs = [Path(a) for a in argv[1:]] or sorted(
        (ROOT / "data-test" / "corpus").glob(DEFAULT_GLOB))
    dirs = [d for d in dirs if (d / "index.json").exists()]
    if not dirs:
        print("没有可用批次（缺 index.json）", file=sys.stderr)
        return 1
    registry = _registry()
    rows, rejects = [], Counter()
    for d in dirs:
        t0 = time.perf_counter()
        rep = passage.grade_batch(d, registry, gate_l3=True)
        r = _row(d.name, rep["metrics"])
        r["seconds"] = round(time.perf_counter() - t0, 2)
        rows.append(r)
        rejects.update(r["gate_reject_reasons"])
        print(f"[{r['seconds']:>5.2f}s] {r['batch']}: A {r['a_chars']} → "
              f"闸门 {r['gated_a_chars']} 字（保留 {r['gated_keep_rate']*100:.1f}%）")

    agg = {k: sum(r[k] for r in rows) for k in
           ("articles", "total_chars", "a_chars", "gated_a_chars",
            "gate_pass_count", "gate_candidate_count")}
    agg["a_share"] = round(agg["a_chars"] / agg["total_chars"], 4) if agg["total_chars"] else 0.0
    agg["gated_a_share"] = (round(agg["gated_a_chars"] / agg["total_chars"], 4)
                            if agg["total_chars"] else 0.0)
    agg["gated_keep_rate"] = (round(agg["gated_a_chars"] / agg["a_chars"], 4)
                              if agg["a_chars"] else 0.0)
    agg["gate_pass_rate"] = (round(agg["gate_pass_count"] / agg["gate_candidate_count"], 4)
                             if agg["gate_candidate_count"] else 0.0)

    md = ["# 闸门离线回放（关键词基线 vs L3 确定性闸门）", "",
          f"- 生成：{time.strftime('%Y-%m-%d %H:%M')}；批次 {len(rows)} 个；"
          f"正文 {agg['total_chars']:,} 字；候选段 {agg['gate_candidate_count']:,}",
          f"- 合计：基线 A **{agg['a_chars']:,} 字**（{agg['a_share']*100:.1f}%）→ "
          f"过闸 A **{agg['gated_a_chars']:,} 字**（{agg['gated_a_share']*100:.1f}%），"
          f"保留 **{agg['gated_keep_rate']*100:.1f}%**；段通过率 "
          f"{agg['gate_pass_rate']*100:.1f}%（{agg['gate_pass_count']}/"
          f"{agg['gate_candidate_count']}）", "",
          "## 分批次", "",
          "| 批次 | 文章 | 正文(字) | 基线A(字) | 过闸A(字) | 保留 | 段通过 |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        md.append(f"| {r['batch']} | {r['articles']} | {r['total_chars']:,} | "
                  f"{r['a_chars']:,} | {r['gated_a_chars']:,} | "
                  f"{r['gated_keep_rate']*100:.1f}% | {r['gate_pass_rate']*100:.1f}% |")
    md += ["", "## 拒绝理由分布（全批）", ""]
    for reason, n in rejects.most_common(10):
        md.append(f"- `{reason}`: {n}")
    md += ["", "## 说明", "",
           "- 基线 = `passage` 关键词 A/B/C（既有口径，未改动）；过闸 = A 段再经 "
           "`l3gate` 对象锚定+主题排除+具体性判定。",
           "- 本回放只读已落盘语料，不触网；用于量化接线后的产出变化，"
           "免去再爬一轮的成本。", ""]

    EV.mkdir(parents=True, exist_ok=True)
    out = EV / f"gate-replay-{time.strftime('%Y%m%d')}"
    (out.with_suffix(".md")).write_text("\n".join(md), encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(
        {"generated": time.strftime("%Y-%m-%d %H:%M"), "batches": rows,
         "aggregate": agg, "rejects": dict(rejects)},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md))
    print(f"\n→ {out.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
