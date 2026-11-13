# -*- coding: utf-8 -*-
"""一次性交付测试驱动：5 个用户输入 → brief(API) → plan(API) → loop → 清单。

隔离原则：
- 每个 case 独立目录（brief/plan/run/images/api_log 全在 case 内）；
- 不读历史 brief/plan/run；--web-only 空库；
- 不做任何手工改字段或注入数据；只调用 CLI。
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data-test" / "runs" / "delivery-20261112"
PY = sys.executable

CASES = [
    ("c1-desert-tractor",
     "沙漠牵引车（前保险杠、侧防护栏、登车踏步、大灯、前轮拱）；沙漠/油田工况；6×6；10 台",
     "沙漠牵引车", 10),
    ("c2-reach-stacker",
     "港口集装箱正面吊（驾驶室外罩、配重罩、走台护栏、登车踏步、灯具护罩）；港口堆场工况；4×2 底盘；10 台",
     "港口集装箱正面吊", 10),
    ("c3-tractor",
     "大马力轮式拖拉机（发动机罩侧板、前配重罩、挡泥板、登车踏步、后视镜支架）；农田/复合作业；4×4；10 台",
     "大马力轮式拖拉机", 10),
    ("c4-forklift",
     "电动叉车（护顶架、配重罩、车身侧板、登车踏板、警示灯支架）；仓储物流工况；四轮；6 台",
     "电动叉车", 6),
    ("c5-roller",
     "单钢轮振动压路机（机罩、ROPS 驾驶室框架、钢轮挡泥板、扶手踏板、灯具后视镜）；道路施工工况；单钢轮；14 台",
     "单钢轮振动压路机", 14),
]


def run(cmd, log_path, timeout):
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


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=str(BASE))
    ap.add_argument("--topup", type=int, default=0)
    ap.add_argument("--concurrency", type=int, default=1,
                    help="plan_candidates 的查询并发（默认 1=串行）")
    ap.add_argument("--reuse-brief", action="store_true",
                    help="复用 case 目录里已冻结的 brief.json（回归用；不重新生成）")
    ap.add_argument("--cases", default="",
                    help="逗号分隔的 case 名单，默认全部")
    args = ap.parse_args()
    only = {x.strip() for x in args.cases.split(",") if x.strip()}
    base_dir = Path(args.base)
    base_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for name, text, klass, slots in CASES:
        if only and name not in only:
            continue
        case = base_dir / name
        (case / "logs").mkdir(parents=True, exist_ok=True)
        brief = case / "brief.json"
        plan = case / "plan.json"
        rec = {"case": name, "slots": slots, "class": klass,
               "plan_concurrency": args.concurrency,
               "brief_reused": bool(args.reuse_brief and brief.exists())}
        print(f"\n=== {name} (slots={slots}) ===", flush=True)

        steps = []
        if args.reuse_brief and brief.exists():
            steps.append({"step": "brief", "rc": 0, "sec": 0, "reused": True})
            print("  brief 复用冻结文件", flush=True)
        else:
            cmd = [PY, "scripts/build_brief.py", "--input", text,
                   "--class", klass, "--slots", str(slots), "--out", str(brief)]
            rc, sec = run(cmd, case / "logs" / "1-brief.log", 600)
            steps.append({"step": "brief", "rc": rc, "sec": sec})
            print(f"  brief rc={rc} {sec}s", flush=True)
            if rc != 0:
                rec["steps"] = steps
                results.append(rec)
                continue

        cmd = [PY, "scripts/plan_candidates.py", "--brief", str(brief),
               "--out", str(plan)]
        if args.topup:
            cmd += ["--topup", str(args.topup)]
        if args.concurrency and args.concurrency > 1:
            cmd += ["--concurrency", str(args.concurrency)]
        rc, sec = run(cmd, case / "logs" / "2-plan.log", 1200)
        steps.append({"step": "plan", "rc": rc, "sec": sec})
        print(f"  plan  rc={rc} {sec}s", flush=True)
        if rc != 0:
            rec["steps"] = steps
            results.append(rec)
            continue

        # 意向排序（生产链路第 3 步）：给 primary/backup 优先级
        ranked = case / "plan-ranked.json"
        cmd = [PY, "scripts/rank_plan.py", "--plan", str(plan),
               "--brief", str(brief), "--out", str(ranked)]
        rc, sec = run(cmd, case / "logs" / "2b-rank.log", 600)
        steps.append({"step": "rank", "rc": rc, "sec": sec})
        print(f"  rank  rc={rc} {sec}s", flush=True)
        if rc != 0:
            rec["steps"] = steps
            results.append(rec)
            continue

        # plan 池大小（来自 plan.pool）
        try:
            pj = json.loads(ranked.read_text(encoding="utf-8"))
            rec["plan_pool"] = pj.get("pool") or {}
            rec["plan_candidates"] = len(pj.get("candidates") or [])
        except Exception:  # noqa: BLE001
            pass

        cmd = [PY, "-m", "equiplens.retrieval_engine",
               "--brief", str(brief), "--web-only", "--plan", str(ranked),
               "--run-root", str(case), "--run-id", "run",
               "--evidence-db", str(case / "run" / "evidence.db")]
        rc, sec = run(cmd, case / "logs" / "3-loop.log", 2400)
        steps.append({"step": "loop", "rc": rc, "sec": sec})
        print(f"  loop  rc={rc} {sec}s", flush=True)
        # CLI 约定：0=完整交付，2=交付不足（仍是有效 run，要继续出清单）
        if rc not in (0, 2):
            rec["steps"] = steps
            results.append(rec)
            continue

        cmd = [PY, "scripts/render_fetch_audit.py", str(case / "run")]
        rc, sec = run(cmd, case / "logs" / "4-audit.log", 300)
        steps.append({"step": "audit", "rc": rc, "sec": sec})
        print(f"  audit rc={rc} {sec}s", flush=True)

        cmd = [PY, "scripts/build_delivery_manifest.py",
               "--run", str(case / "run"), "--brief", str(brief),
               "--plan", str(ranked)]
        rc, sec = run(cmd, case / "logs" / "5-manifest.log", 300)
        steps.append({"step": "manifest", "rc": rc, "sec": sec})
        print(f"  manifest rc={rc} {sec}s", flush=True)

        try:
            sm = json.loads((case / "run" / "summary.json")
                            .read_text(encoding="utf-8"))
            rec["summary"] = {
                "state": sm.get("state"),
                "delivery": sm.get("delivery", {}).get("status"),
                "delivered": sm.get("delivery", {}).get("delivered"),
                "required": sm.get("delivery", {}).get("required"),
                "degraded": sm.get("delivery", {}).get("degraded"),
                "backup": sm.get("delivery", {}).get("backup", {}),
                "budget": sm.get("budget_used"),
                "elapsed_ms": sm.get("elapsed_ms"),
            }
        except Exception:  # noqa: BLE001
            pass
        rec["steps"] = steps
        results.append(rec)

    out = base_dir / "SUITE.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("\n=== done ===", flush=True)
    for r in results:
        s = r.get("summary") or {}
        print(f"{r['case']}: {s.get('delivered')}/{s.get('required')} "
              f"backup={((s.get('backup') or {}).get('delivered'))} "
              f"state={s.get('state')} steps={[(x['step'], x['rc']) for x in r.get('steps', [])]}",
              flush=True)


if __name__ == "__main__":
    main()
