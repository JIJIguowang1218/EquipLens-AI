# -*- coding: utf-8 -*-
"""Merge + validate the P3 staged inputs and render a Chinese review sheet."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

FILES = ["data-test/evals/p3-A-120-20261117.jsonl",
         "data-test/evals/p3-B-70-20261117.jsonl",
         "data-test/evals/p3-C-100-20261117.jsonl"]
OUT = Path("data-test/evals/p3-staged-290-20261117.jsonl")
REVIEW = Path("data-test/evals/p3-staged-290-20261117-review.md")

CN = {
    "plan.quantity": "改总量", "plan.quantity_per_model": "每款张数",
    "fill.quota": "同车补图", "plan.add_targets": "加品牌/车型",
    "plan.negative": "排除项", "scope.ratio": "改范围/比例",
    "plan.configuration": "改构型/配置", "fetch.filters.views": "视角",
    "fetch.parts": "部件", "fetch.filters.quality": "画质",
    "verify.blacklist": "拉黑单图", "delivered.remove": "删除/降级已交付",
    "delivered.replace": "换已交付图", "delivery.report": "交付格式/报告",
    "session.pause": "暂停", "session.resume": "继续", "session.reset": "整批重来",
    "fill.replace": "补位替换",
}
EXPECT_COUNTS = {
    "A1": 15, "A2": 15, "A3": 10, "A4": 15, "A5": 15, "A6": 15, "A7": 20,
    "A8": 10, "A9": 5,
    "B1": 20, "B2": 20, "B3": 10, "B4": 15, "B5": 5,
    "C1": 30, "C2": 20, "C3": 20, "C4": 15, "C5": 10, "C6": 5,
}


def main() -> int:
    rows = []
    for f in FILES:
        p = Path(f)
        if not p.exists():
            print("MISSING", f)
            return 1
        rows += [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows.sort(key=lambda r: (r["stage"], r["id"]))
    counts = Counter(r["category"] for r in rows)
    problems = [f"{k}:{counts.get(k,0)}!={v}" for k, v in EXPECT_COUNTS.items() if counts.get(k, 0) != v]
    ids = [r["id"] for r in rows]
    dup = [i for i, c in Counter(ids).items() if c > 1]
    if problems or dup or len(rows) != 290:
        print("VALIDATION FAIL", problems, "dups", dup[:5], "n", len(rows))
        return 1
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                   encoding="utf-8")

    def cn(targets):
        return " + ".join(CN.get(t, t) for t in targets) if targets else "—"

    lines = ["# P3 分阶段输入清单（290 条，待产品负责人审）", "",
             "> 审完即视为真实原话；有问题的行请标 ID，我按你的意见改。", ""]
    for stage, title in (("pre_run", "A 输入阶段（120）"),
                         ("running", "B 运行中（70）"),
                         ("delivered", "C 看到结果后（100）")):
        lines += [f"## {title}", "",
                  "| ID | 类别 | 用户原话 | 期望 | 备注 |", "|---|---|---|---|---|"]
        for r in [x for x in rows if x["stage"] == stage]:
            exp = cn(r["expect_targets"])
            if r.get("expect_action") in ("guide", "explain"):
                exp = r["expect_action"] + "：" + (r.get("note") or "")
            note = r.get("note") or ""
            lines.append(f"| {r['id']} | {r['category']} | {r['text']} | {exp} | {note} |")
        lines.append("")
    REVIEW.write_text("\n".join(lines), encoding="utf-8")
    print(f"OK n={len(rows)} categories={len(counts)} -> {OUT} / {REVIEW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
