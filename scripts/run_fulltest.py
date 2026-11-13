# -*- coding: utf-8 -*-
"""完整测试驱动：cases.json → plan → rank → loop → manifest（可重复）。

用法:
  PYTHONPATH=src python scripts/run_fulltest.py --cases data-test/evals/fulltest-20261114/CASES.json \
      --root data-test/runs/p2-screen-20261114 --repeat 1
cases.json: [{"name":"c1","brief":".../brief.json"}, ...]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
ENV = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8")


def run(cmd, log_path, timeout):
    t0 = time.time()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("$ " + " ".join(cmd) + "\n\n")
        f.flush()
        try:
            p = subprocess.run(cmd, cwd=ROOT, env=ENV, timeout=timeout,
                               stdout=f, stderr=subprocess.STDOUT)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            f.write(f"\n[TIMEOUT after {timeout}s]\n")
            rc = 124
    return rc, round(time.time() - t0, 1)


def one_case(case: dict, case_dir: Path) -> dict:
    brief = case_dir / "brief.json"
    src = Path(case["brief"])
    brief.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    plan = case_dir / "plan.json"
    ranked = case_dir / "plan-ranked.json"
    steps = []
    logs = case_dir / "logs"

    cmd = [PY, "scripts/plan_candidates.py", "--brief", str(brief), "--out", str(plan)]
    rc, sec = run(cmd, logs / "1-plan.log", 1200)
    steps.append({"step": "plan", "rc": rc, "sec": sec})
    if rc != 0:
        return {"name": case["name"], "steps": steps, "error": "plan"}

    cmd = [PY, "scripts/rank_plan.py", "--plan", str(plan), "--brief", str(brief),
           "--out", str(ranked)]
    rc, sec = run(cmd, logs / "2-rank.log", 600)
    steps.append({"step": "rank", "rc": rc, "sec": sec})
    if rc != 0:
        return {"name": case["name"], "steps": steps, "error": "rank"}

    cmd = [PY, "-m", "equiplens.retrieval_engine", "--brief", str(brief),
           "--web-only", "--plan", str(ranked), "--run-root", str(case_dir),
           "--run-id", "run"]
    rc, sec = run(cmd, logs / "3-loop.log", 3600)
    steps.append({"step": "loop", "rc": rc, "sec": sec})
    if rc not in (0, 2):
        return {"name": case["name"], "steps": steps, "error": "loop"}

    cmd = [PY, "scripts/build_delivery_manifest.py", "--run", str(case_dir / "run"),
           "--brief", str(brief), "--plan", str(ranked)]
    rc, sec = run(cmd, logs / "4-manifest.log", 300)
    steps.append({"step": "manifest", "rc": rc, "sec": sec})
    return {"name": case["name"], "steps": steps}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--repeat", type=int, default=1)
    args = ap.parse_args()
    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    root = ROOT / args.root
    root.mkdir(parents=True, exist_ok=True)
    out = []
    for rep in range(1, args.repeat + 1):
        for case in cases:
            name = case["name"] if args.repeat == 1 else f"{case['name']}-r{rep}"
            case_dir = root / name
            case_dir.mkdir(parents=True, exist_ok=True)
            print(f"=== {name} ===", flush=True)
            rec = one_case(case, case_dir)
            rec["repeat"] = rep
            out.append(rec)
            print(f"  {rec.get('error') or 'ok'} {[s['step'] + ':' + str(s['rc']) for s in rec['steps']]}",
                  flush=True)
    (root / "SUITE.json").write_text(json.dumps(out, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print("done:", root / "SUITE.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
