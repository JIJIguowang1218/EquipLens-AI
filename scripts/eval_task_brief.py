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


def auto_checks(brief: dict, raw: str) -> dict:
    parts = brief.get("part_requirements") or []
    return {
        "schema_ok": briefing.validate_brief_json(brief) == [],
        "parts": len(parts),
        "custom_parts": len([p for p in parts if str(p.get("part", "")).startswith("custom_")]),
        "all_have_design_axes": all(p.get("design_axes") for p in parts),
        "assumptions": len(brief.get("assumptions") or []),
        "regions": [r.get("region") for r in brief.get("region_requirements") or []],
        "raw_mentions": [x for x in ("防沙板", "涉水喉", "爬梯", "尾灯", "支腿", "吊臂") if x in raw],
    }


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
                checks = auto_checks(brief, case["prompt"])
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
             "| case | arm | status | parts | custom | axes | assumptions |",
             "|---|---|---|---:|---:|---|---:|"]
    for r in rows:
        c = r["checks"] or {}
        lines.append(f"| {r['case']} | {r['arm']} | {r['status']} | {c.get('parts','')} | "
                     f"{c.get('custom_parts','')} | {c.get('all_have_design_axes','')} | "
                     f"{c.get('assumptions','')} |")
    lines += ["", "> 人工 rubric 必须另填：品类/基型/构型、对象分类、关系轴、设计轴、未知部件、是否编造。"]
    (out_dir / "RESULTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out_dir), "rows": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
