# -*- coding: utf-8 -*-
"""LLM rank vs 确定性排序的小 A/B：固定同一份 plan，只改排序方式。

用法：
  PYTHONPATH=src python scripts/ab_rank.py --base data-test/runs/ab-rank-20261113
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
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

PY = sys.executable
CASES = [("c1-desert-tractor", "with"), ("c2-reach-stacker", "with")]
ARMS = ("llm", "deterministic")


def run(cmd, log_path, timeout) -> tuple[int, float]:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
               PYTHONIOENCODING="utf-8")
    t0 = time.time()
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("$ " + " ".join(cmd) + "\n\n")
        f.flush()
        try:
            p = subprocess.run(cmd, cwd=ROOT, env=env, timeout=timeout,
                               stdout=f, stderr=subprocess.STDOUT)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            f.write(f"\n[TIMEOUT after {timeout}s]\n")
            rc = 124
    return rc, round(time.time() - t0, 1)


def read(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect(arm: Path) -> dict:
    d = read(arm / "run" / "DELIVERY.json") or {}
    st = read(arm / "run" / "state.json") or {}
    rk = read(arm / "plan-ranked.json") or {}
    s = (d.get("user_delivery") or {}).get("summary") or {}
    mon = d.get("monitoring") or {}
    return {
        "delivered": s.get("delivered"), "required": s.get("required"),
        "backup": len((d.get("user_delivery") or {}).get("backup") or []),
        "degraded": s.get("degraded"),
        "status": s.get("status"),
        "cost": (mon.get("cost_cny") or {}).get("peak", {}).get("total"),
        "elapsed_s": round((mon.get("elapsed_ms") or 0) / 1000, 1),
        "targets": len(st.get("targets") or {}),
        "order": [c.get("model") for c in (rk.get("candidates") or [])],
        "method": (rk.get("ranking") or {}).get("method", "llm"),
    }


def render(rows: list[dict]) -> str:
    lines = ["# rank 小 A/B：LLM vs 确定性排序", "",
             "> 同一份 plan；只改 rank 方式；loop 用固定 ranked plan。", "",
             "| case | 臂 | 交付 | 备选 | degraded | 成本¥ | 耗时s | 目标数 |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        for arm in ARMS:
            m = r.get(arm) or {}
            lines.append(f"| {r['case']} | {arm} | {m.get('delivered')}/{m.get('required')} | "
                         f"{m.get('backup')}/4 | {m.get('degraded')} | "
                         f"{m.get('cost')} | {m.get('elapsed_s')} | {m.get('targets')} |")
    lines += ["", "## 排序重合", ""]
    for r in rows:
        a = set((r.get("llm") or {}).get("order") or [])
        b = set((r.get("deterministic") or {}).get("order") or [])
        top_a = (r.get("llm") or {}).get("order", [])[:10]
        top_b = (r.get("deterministic") or {}).get("order", [])[:10]
        ov = len(set(top_a) & set(top_b)) / max(1, len(set(top_a) | set(top_b)))
        lines.append(f"- {r['case']}：全量重合 {len(a & b)}/{len(a | b)}，top10 Jaccard {ov:.2f}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--source", default=str(ROOT / "data-test" / "runs"
                                            / "ab-negative-20261113"))
    ap.add_argument("--only", default="")
    args = ap.parse_args(argv)
    base = Path(args.base)
    source = Path(args.source)
    base.mkdir(parents=True, exist_ok=True)
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    rows = []
    for case, src_arm in CASES:
        key = f"{case}/{src_arm}"
        if only and key not in only:
            continue
        src = source / case / src_arm
        rec = {"case": key}
        for arm in ARMS:
            d = base / case / src_arm / arm
            d.mkdir(parents=True, exist_ok=True)
            (d / "brief.json").write_text((src / "brief.json").read_text(encoding="utf-8"),
                                          encoding="utf-8")
            (d / "plan.json").write_text((src / "plan.json").read_text(encoding="utf-8"),
                                         encoding="utf-8")
            cmd = [PY, "scripts/rank_plan.py", "--plan", str(d / "plan.json"),
                   "--brief", str(d / "brief.json"), "--out", str(d / "plan-ranked.json")]
            if arm == "deterministic":
                cmd.append("--deterministic")
            rc, sec = run(cmd, d / "1-rank.log", 600)
            print(f"[{key}/{arm}] rank rc={rc} {sec}s", flush=True)
            if rc != 0:
                rec[arm] = {"error": rc}
                continue
            rc, sec = run([PY, "-m", "equiplens.retrieval_engine",
                           "--brief", str(d / "brief.json"), "--web-only",
                           "--plan", str(d / "plan-ranked.json"),
                           "--run-root", str(d), "--run-id", "run",
                           "--evidence-db", str(d / "run" / "evidence.db")],
                          d / "2-loop.log", 2400)
            print(f"[{key}/{arm}] loop rc={rc} {sec}s", flush=True)
            if rc not in (0, 2):
                rec[arm] = {"error": rc}
                continue
            run([PY, "scripts/render_fetch_audit.py", str(d / "run")], d / "3-audit.log", 300)
            run([PY, "scripts/build_delivery_manifest.py", "--run", str(d / "run"),
                 "--brief", str(d / "brief.json"), "--plan", str(d / "plan-ranked.json")],
                d / "4-manifest.log", 300)
            rec[arm] = collect(d)
        rows = [r for r in rows if r["case"] != key] + [rec]
        (base / "SUMMARY.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                                           encoding="utf-8")
        (base / "SUMMARY.md").write_text(render(rows), encoding="utf-8")
    print("done", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
