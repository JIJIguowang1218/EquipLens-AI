# -*- coding: utf-8 -*-
"""评估确定性闸门：在 T18-roster 265 段（模型判定为金标）上算精确率/召回率。

用法: PYTHONPATH=src python tmp/eval_l3gate.py
输出: data-test/evals/l3-gate-v1.md / .json
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equiplens import l3gate  # noqa: E402

EV = ROOT / "data-test" / "evals"
sheet = json.loads((EV / "roster-judge-sheet-20261030.json").read_text(encoding="utf-8"))
evalj = json.loads((EV / "roster-eval-20261030.json").read_text(encoding="utf-8"))
tiers = {it["id"]: it["tier"] for it in evalj["items"]}


def main() -> int:
    rows, by_tier, reasons = [], Counter(), Counter()
    for it in sheet["items"]:
        tier = tiers.get(it["id"])
        if tier is None:
            continue
        r = l3gate.evaluate(it["text"], title=it["title"], url=it["url"],
                            subject=it.get("doc_subject"))
        usable = tier != "C"
        rows.append({"id": it["id"], "tier": tier, "gate_pass": r["pass"],
                     "usable": usable, "reasons": r["reasons"]})
        by_tier[(tier, r["pass"])] += 1
        if not r["pass"]:
            reasons.update(r["reasons"])

    m = l3gate.metrics(rows)
    md = ["# 确定性闸门评估 v1（T18-roster 265 段）", "",
          f"- 金标：模型逐段判定（V/P/G=可用 {sum(1 for x in rows if x['usable'])}，"
          f"C=剔除 {sum(1 for x in rows if not x['usable'])}）",
          f"- 闸门：**精确率 {m['precision']*100:.1f}%** / 召回率 "
          f"{m['recall']*100:.1f}% / F1 {m['f1']:.3f} / 假阳性 "
          f"{m['false_positive_rate']*100:.1f}%",
          f"- 混淆：TP {m['tp']} / FP {m['fp']} / FN {m['fn']} / TN {m['tn']}", "",
          "## 分档通过率", "", "| 金标档 | 段数 | 闸门通过 |", "|---|---:|---:|"]
    for tier in ("V", "P", "G", "C"):
        n = sum(v for (t, _), v in by_tier.items() if t == tier)
        p = sum(v for (t, pp), v in by_tier.items() if t == tier and pp)
        md.append(f"| {tier} | {n} | {p} |")
    md += ["", "## 拒绝理由 Top", ""]
    for r, n in reasons.most_common(8):
        md.append(f"- {r}: {n}")
    (EV / "l3-gate-v1.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (EV / "l3-gate-v1.json").write_text(
        json.dumps({"metrics": m, "by_tier": {f"{t}:{p}": n for (t, p), n in by_tier.items()},
                    "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(m, ensure_ascii=False))
    print("\n".join(md[:10]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
