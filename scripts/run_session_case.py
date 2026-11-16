# -*- coding: utf-8 -*-
"""M4.3 session arm: same brief+plan as the baseline, but apply a session patch
(`plan.add_targets`) at the FETCH boundary, then measure the delta.

Baseline arm uses `python -m equiplens.retrieval_engine ... --json`.
Both arms must share brief + plan to be comparable.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from equiplens.retrieval_engine import RetrievalEngine
from equiplens.retrieval_engine.contracts import load_brief
from equiplens.retrieval_engine.web import WebWorld


def _pick_model(state: dict, plan: list) -> str:
    taken = {" ".join(str((t or {}).get("model") or "").lower().split())
             for t in (state.get("targets") or {}).values()}
    for c in plan:
        m = " ".join(str((c or {}).get("model") or "").split())
        if m and m.lower() not in taken:
            return m
    return ""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--plan", required=True)
    ap.add_argument("--run-root", default="data-test/runs")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--download-workers", type=int, default=4)
    ap.add_argument("--add-model", default="",
                    help="delta 新增车型；空=从 plan 里挑一个尚未进入 targets 的")
    ap.add_argument("--max-steps", type=int, default=240)
    args = ap.parse_args(argv)

    brief = load_brief(args.brief)
    plan_doc = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    plan = plan_doc.get("candidates") or []
    plan_meta = {"concurrency": plan_doc.get("concurrency"),
                 "rank_method": ((plan_doc.get("ranking") or {}).get("method") or None),
                 "created_at": plan_doc.get("created_at")}
    run_dir = Path(args.run_root) / args.run_id
    world = WebWorld(None, brief.parts_by_key,
                     image_dir=run_dir / "images", plan=plan,
                     citation_check=True, plan_meta=plan_meta, pins=[],
                     unit_quotas={u.unit_id: u.quota for u in brief.research_units},
                     download_workers=args.download_workers,
                     brief={"request": brief.request})
    engine = RetrievalEngine(brief, world, run_root=args.run_root, run_id=args.run_id)
    state = engine._load_or_init()

    t0 = time.perf_counter()
    patched = None
    patch_info: dict = {}
    steps = 0
    fetch_rounds = 0
    q_after_patch = None
    while not state.get("finished") and steps < args.max_steps:
        if state.get("state") == "FETCH" and state.get("active_targets"):
            # 只数“真的有 target 要抓”的 FETCH：第 1 轮是首轮抓取，
            # 从第 2 轮（中途/补抓）开始打 patch，delta 查询才是增量。
            fetch_rounds += 1
            if patched is None and fetch_rounds >= 2:
                model = args.add_model or _pick_model(state, plan)
                if model:
                    queries_before = int(getattr(world, "query_count", 0) or 0)
                    res = engine.apply_patches(state, [{
                        "target": "plan.add_targets",
                        "value": {"data": {"models": [model]}},
                    }])
                    patched = model
                    patch_info = {"added_model": model, "applied": res["applied"],
                                  "queries_at_patch": queries_before,
                                  "fetch_round": fetch_rounds,
                                  "targets_at_patch": len(state.get("targets") or {})}
        state = engine.step(state)
        steps += 1
        if patched and q_after_patch is None and state.get("state") == "FILL":
            q_after_patch = int(getattr(world, "query_count", 0) or 0)
    if not state.get("finished"):
        state["final_state"] = "FAILED"
        state["state"] = "WRITEBACK"
        engine.store.save(state)
    summary = engine._summary(state)
    engine.store.save_summary(summary)
    seconds = round(time.perf_counter() - t0, 1)

    deliv = summary.get("delivery") or {}
    queries_total = int(getattr(world, "query_count", 0)
                        or (summary.get("budget_used") or {}).get("queries", 0) or 0)
    delta_q = max(0, queries_total - int(patch_info.get("queries_at_patch", 0) or 0)) if patched else 0
    models = [t for u in (summary.get("accepted_targets") or {}).values() for t in u]
    out = {
        "case": args.run_id, "arm": "session", "state": summary.get("state"),
        "delivered": deliv.get("delivered"), "required": deliv.get("required"),
        "missing": deliv.get("missing"), "degraded": deliv.get("degraded"),
        "backup_delivered": (deliv.get("backup") or {}).get("delivered"),
        "backup_required": (deliv.get("backup") or {}).get("required"),
        "queries_total": queries_total, "delta_queries": delta_q,
        "delta_ratio": round(delta_q / queries_total, 3) if queries_total else None,
        "delta_queries_round": (max(0, int(q_after_patch) - int(patch_info.get("queries_at_patch", 0)))
                                if (patched and q_after_patch is not None) else None),
        "delta_round_ratio": (round(max(0, int(q_after_patch) - int(patch_info.get("queries_at_patch", 0)))
                                    / queries_total, 3)
                              if (patched and q_after_patch is not None and queries_total) else None),
        "seconds": seconds, "elapsed_ms": summary.get("elapsed_ms"),
        "status": deliv.get("status"), "patched": bool(patched), "patch": patch_info,
        "delivered_targets": len(set(models)),
        "duplicate_targets": len(models) - len(set(models)),
        "summary_path": str(run_dir / "summary.json"),
    }
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
