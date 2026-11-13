# -*- coding: utf-8 -*-
"""A 测试：plan 阶段串行 vs 并发（只改调用方式，不改查询/抽取语义）。

用法：
  PYTHONPATH=src python scripts/ab_plan_concurrency.py \\
      --base data-test/runs/ab-plan-concurrency-20261113 --conc 4
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
CASES = ["c1-desert-tractor", "c2-reach-stacker", "c3-tractor",
         "c4-forklift", "c5-roller"]


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


def metrics(arm: Path) -> dict:
    plan = read(arm / "plan.json") or {}
    rows = []
    try:
        for line in (arm / "api_log.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    except OSError:
        pass
    chat = [r for r in rows if r.get("api") == "chat"]
    search = [r for r in rows if r.get("api") == "search"]
    return {
        "candidates": len(plan.get("candidates") or []),
        "kept": sum(int(q.get("kept") or 0) for q in (plan.get("queries") or [])),
        "queries": len(plan.get("queries") or []),
        "search_results": plan.get("search_results"),
        "dedupe": plan.get("dedupe"),
        "pool_required": (plan.get("pool") or {}).get("required"),
        "tokens_in": sum(int(r.get("prompt_tokens") or 0) for r in chat),
        "tokens_out": sum(int(r.get("completion_tokens") or 0) for r in chat),
        "search_calls": len(search),
        "chat_calls": len(chat),
        "chat_ms_sum": sum(int(r.get("ms") or 0) for r in chat),
        "search_ms_sum": sum(int(r.get("ms") or 0) for r in search),
        "chat_ms_max": max([int(r.get("ms") or 0) for r in chat] or [0]),
    }


def render(rows: list[dict]) -> str:
    lines = [
        "# A 测试：plan 串行 vs 并发",
        "",
        "> 唯一变量：`--concurrency`。查询构造、抽取 prompt、模型、温度、topup 全部相同。",
        "> 只跑 plan 阶段，不进 rank/loop。",
        "",
        "| case | 臂 | 耗时 s | 候选 | 抽取 kept | tokens in/out | chat 调用 | chat 总 ms | 单次最大 ms |",
        "|---|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for r in rows:
        for arm in ("serial", "concurrent"):
            m = r.get(arm) or {}
            if not m:
                continue
            lines.append(
                f"| {r['case']} | {arm} | {r[arm + '_sec']} | {m['candidates']} | "
                f"{m['kept']} | {m['tokens_in']}/{m['tokens_out']} | {m['chat_calls']} | "
                f"{m['chat_ms_sum']} | {m['chat_ms_max']} |")
    lines += ["", "## 汇总", ""]
    for arm in ("serial", "concurrent"):
        sec = sum(float(r.get(arm + "_sec") or 0) for r in rows if r.get(arm))
        cand = sum(int((r.get(arm) or {}).get("candidates") or 0) for r in rows)
        tok = sum(int((r.get(arm) or {}).get("tokens_out") or 0) for r in rows)
        lines.append(f"- **{arm}**：总耗时 {sec:.1f}s，候选 {cand}，输出 tokens {tok}")
    if rows:
        s = sum(float(r["serial_sec"]) for r in rows)
        c = sum(float(r["concurrent_sec"]) for r in rows)
        lines += ["", f"**加速比：{s / c:.2f}×**（{s:.0f}s → {c:.0f}s）"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--source", default=str(ROOT / "data-test" / "runs"
                                            / "delivery-20261112-clean"))
    ap.add_argument("--conc", type=int, default=4)
    ap.add_argument("--only", default="")
    args = ap.parse_args(argv)
    base = Path(args.base)
    source = Path(args.source)
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    base.mkdir(parents=True, exist_ok=True)
    rows = []
    for case in CASES:
        if only and case not in only:
            continue
        brief = source / case / "brief.json"
        if not brief.exists():
            raise SystemExit(f"missing brief: {brief}")
        rec = {"case": case}
        for arm, conc in (("serial", 1), ("concurrent", args.conc)):
            d = base / case / arm
            d.mkdir(parents=True, exist_ok=True)
            (d / "brief.json").write_text(brief.read_text(encoding="utf-8"),
                                          encoding="utf-8")
            cmd = [PY, "scripts/plan_candidates.py", "--brief", str(brief),
                   "--out", str(d / "plan.json"), "--concurrency", str(conc)]
            rc, sec = run(cmd, d / "plan.log", 1800)
            print(f"[{case}/{arm}] rc={rc} {sec}s", flush=True)
            rec[arm + "_sec"] = sec
            rec[arm + "_rc"] = rc
            if rc == 0:
                rec[arm] = metrics(d)
        rows = [r for r in rows if r["case"] != case] + [rec]
        (base / "SUMMARY.json").write_text(
            json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        (base / "SUMMARY.md").write_text(render(rows), encoding="utf-8")
    print("done ->", base / "SUMMARY.md", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
