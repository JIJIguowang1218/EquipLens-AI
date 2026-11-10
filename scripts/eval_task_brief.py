# -*- coding: utf-8 -*-
"""task-brief skill 必要性 A/B：with_skill vs without_skill。

用法:
  PYTHONPATH=src python scripts/eval_task_brief.py \
    --out data-test/evals/task-brief-eval-20261111
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import briefing  # noqa: E402

EVALS = ROOT / "skills" / "task-brief" / "evals" / "evals.json"
KEY_FILE = Path.home() / ".equiplens" / "deepseek.env"


def load_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key and KEY_FILE.exists():
        for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        raise SystemExit("no DEEPSEEK_API_KEY")
    return key


def auto_checks(brief: dict, spec: dict, raw: str) -> dict:
    parts = brief.get("part_requirements") or []
    regions = brief.get("region_requirements") or []
    checks = {
        "schema_ok": briefing.validate_brief_json(brief) == [],
        "parts": len(parts),
        "custom_parts": len([p for p in parts if str(p.get("part", "")).startswith("custom_")]),
        "all_have_design_axes": all(p.get("design_axes") for p in parts),
        "assumptions": len(brief.get("assumptions") or []),
        "regions": len(regions),
        "failed": [],
    }
    a = spec.get("assertions") or {}
    if "parts_between" in a:
        lo, hi = a["parts_between"]
        if not (lo <= len(parts) <= hi):
            checks["failed"].append(f"parts {len(parts)} not in [{lo},{hi}]")
    if a.get("all_have_design_axes") and not checks["all_have_design_axes"]:
        checks["failed"].append("missing design_axes")
    if len(regions) < int(a.get("regions_min", 0)):
        checks["failed"].append("regions < min")
    if len([p for p in parts if str(p.get("part", "")).startswith("custom_")]) < int(a.get("custom_min", 0)):
        checks["failed"].append("custom < min")
    if len(brief.get("assumptions") or []) < int(a.get("assumptions_min", 1)):
        checks["failed"].append("assumptions < min")
    if not checks["schema_ok"]:
        checks["failed"].append("schema")
    return checks


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="deepseek-flash")
    args = ap.parse_args(argv)
    key = load_key()
    spec = json.loads(EVALS.read_text(encoding="utf-8"))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in spec["cases"]:
        for arm, use_skill in (("with_skill", True), ("without_skill", False)):
            t0 = time.time()
            try:
                result = briefing.generate_brief(case["prompt"], key, slots=12,
                                                 model=args.model, use_skill=use_skill)
                brief = result["brief"]
                checks = auto_checks(brief, case, case["prompt"])
                status = "ok"
            except Exception as e:  # noqa: BLE001
                brief, checks, status = {}, {}, f"{type(e).__name__}: {e}"[:200]
            cid = f"{case['id']}__{arm}"
            (out_dir / f"{cid}.json").write_text(
                json.dumps({"case": case, "arm": arm, "status": status,
                            "checks": checks, "brief": brief},
                           ensure_ascii=False, indent=1), encoding="utf-8")
            rows.append({"case": case["id"], "arm": arm, "status": status,
                         "checks": checks, "ms": round((time.time() - t0) * 1000)})
    (out_dir / "results.json").write_text(
        json.dumps({"skill_version": briefing.SKILL_VERSION, "rows": rows},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["# task-brief 必要性 A/B（自动检查）", "",
             "| case | arm | status | parts | custom | regions | axes | assertions |",
             "|---|---|---|---:|---:|---:|---|---|"]
    for r in rows:
        c = r["checks"] or {}
        failed = c.get("failed") or []
        lines.append(f"| {r['case']} | {r['arm']} | {r['status']} | {c.get('parts','')} | "
                     f"{c.get('custom_parts','')} | {c.get('regions','')} | "
                     f"{c.get('all_have_design_axes','')} | "
                     f"{'PASS' if not failed else '; '.join(failed)} |")
    lines += ["", "> 人工 rubric 必须另填：品类/基型/构型、对象分类、关系轴、设计轴、未知部件、是否编造。"]
    (out_dir / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out_dir), "rows": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
