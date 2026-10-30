# -*- coding: utf-8 -*-
"""对比两轮域名基准结果，标记稳定性（用于决定晋升/降级是否保留）。

用法: python tmp/compare_domain_bench.py <r1_dir> <r2_dir>
输出: data-test/evals/domain-bench-compare-20261030.md
"""
import json
import sys
from pathlib import Path


def load(d: Path) -> dict:
    lb = json.loads((d / "leaderboard.json").read_text(encoding="utf-8"))
    return {r["domain"]: r for r in lb["rows"]}


def main() -> int:
    r1, r2 = load(Path(sys.argv[1])), load(Path(sys.argv[2]))
    domains = sorted(set(r1) | set(r2),
                     key=lambda d: -max(r1.get(d, {}).get("a_per_kchar", 0),
                                        r2.get(d, {}).get("a_per_kchar", 0)))
    lines = ["# 域名基准两轮对比（复测确认）", "",
             "| 域名 | R1 A/千字 | R1 页 | R2 A/千字 | R2 页 | 稳定性 | 建议 |",
             "|---|---:|---:|---:|---:|---|---|"]
    for d in domains:
        a, b = r1.get(d), r2.get(d)
        a1 = a["a_per_kchar"] if a else None
        a2 = b["a_per_kchar"] if b else None
        if a1 is not None and a2 is not None:
            hi, lo = max(a1, a2), min(a1, a2)
            stable = ("稳定" if lo >= hi * 0.4 and hi > 0
                      else "波动" if hi > 0 else "稳定(均低)")
        else:
            stable = "仅一轮"
        suggested = (b or a or {}).get("trust_suggested", "?")
        lines.append(f"| {d} | {'-' if a1 is None else f'{a1:.1f}'} | "
                     f"{a['pages'] if a else '-'} | "
                     f"{'-' if a2 is None else f'{a2:.1f}'} | "
                     f"{b['pages'] if b else '-'} | {stable} | {suggested} |")
    out = Path("data-test/evals/domain-bench-compare-20261030.md")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"对比表 → {out}")
    for line in lines[4:]:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
