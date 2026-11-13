# -*- coding: utf-8 -*-
"""negative A/B：同一份 brief，唯一变量是查询是否追加 -"短词"。

设计（2026-11-13）：
- brief 冻结：直接复用 delivery-20261112-clean 里由 API 生成的任务单，
  不重跑 brief、不手工改字段；
- 同一 case 内先 with 后 without，back-to-back，尽量对齐搜索时间；
- 全链路照旧：plan → rank → loop（--web-only, 固定 ranked plan）→ audit → manifest；
- 先验证两臂的查询计划除后缀外逐字相同（写 QUERY-DIFF.json），再跑真实循环。

用法：
  PYTHONPATH=src python scripts/ab_negative.py \\
      --base data-test/runs/ab-negative-20261113 \\
      --source data-test/runs/delivery-20261112-clean
"""
from __future__ import annotations

import argparse
import json
import os
import re
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

from equiplens import planning  # noqa: E402
from equiplens import pricing  # noqa: E402

PY = sys.executable
CASES = [
    ("c1-desert-tractor", "沙漠牵引车", 10),
    ("c2-reach-stacker", "港口集装箱正面吊", 10),
    ("c3-tractor", "大马力轮式拖拉机", 10),
    ("c4-forklift", "电动叉车", 6),
    ("c5-roller", "单钢轮振动压路机", 14),
]
ARMS = ("with", "without")


def run(cmd, log_path, timeout) -> tuple[int, float]:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"),
               PYTHONIOENCODING="utf-8")
    log_path.parent.mkdir(parents=True, exist_ok=True)
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


def _read(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _jsonl(path: Path) -> list[dict]:
    out = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    except OSError:
        pass
    return out


def plan_stage_usage(arm: Path) -> dict:
    rows = _jsonl(arm / "api_log.jsonl")
    return {
        "tokens_in_miss": sum(int(r.get("prompt_tokens") or 0) for r in rows
                              if r.get("api") == "chat"),
        "tokens_out": sum(int(r.get("completion_tokens") or 0) for r in rows
                          if r.get("api") == "chat"),
        "search_calls": sum(1 for r in rows if r.get("api") == "search"
                            and r.get("results")),
        "chat_calls": sum(1 for r in rows if r.get("api") == "chat"),
    }


def collect(arm: Path, brief_path: Path) -> dict:
    plan = _read(arm / "plan.json") or {}
    ranked = _read(arm / "plan-ranked.json") or {}
    delivery = _read(arm / "run" / "DELIVERY.json") or {}
    state = _read(arm / "run" / "state.json") or {}
    summary = delivery.get("user_delivery", {}).get("summary") or {}
    mon = delivery.get("monitoring") or {}
    pool = plan.get("pool") or {}
    cands = plan.get("candidates") or []
    assets = state.get("assets") or {}
    with_img = sum(1 for _, p in assets.items()
                   if any((v or []) for v in (p or {}).values()))
    pu = plan_stage_usage(arm)
    return {
        "slots": ((_read(brief_path) or {}).get("request", {})
                  .get("page_budget", {}).get("vehicle_slots")),
        "plan_candidates": len(cands),
        "plan_queries": len(plan.get("queries") or []),
        "plan_search_results": plan.get("search_results"),
        "pool_required": pool.get("required"),
        "pool_ok": pool.get("ok"),
        "dropped_no_source": plan.get("dropped_without_valid_source"),
        "dropped_invalid": plan.get("dropped_invalid_sources"),
        "topup": (plan.get("topup") or {}).get("kept"),
        "ranked_primary": (ranked.get("ranking") or {}).get("primary"),
        "ranked_backup": (ranked.get("ranking") or {}).get("backup"),
        "targets": len(state.get("targets") or {}),
        "with_images": with_img,
        "delivered": summary.get("delivered"),
        "required": summary.get("required"),
        "backup": len(delivery.get("user_delivery", {}).get("backup") or []),
        "backup_required": int((((_read(brief_path) or {}).get("request") or {})
                                .get("page_budget") or {}).get("backup_slots") or 4),
        "degraded": summary.get("degraded"),
        "citation_only": summary.get("citation_only"),
        "status": summary.get("status"),
        "downloads": mon.get("downloads") or {},
        "elapsed_s": round((mon.get("elapsed_ms") or 0) / 1000, 1),
        "cost_peak": (mon.get("cost_cny") or {}).get("peak", {}).get("total"),
        "cost_off": (mon.get("cost_cny") or {}).get("off_peak", {}).get("total"),
        "usage": mon.get("usage") or {},
        "plan_stage": pu,
        "plan_stage_cost_peak": round(pricing.estimate(pu, peak=True)["total"], 4),
        "plan_stage_cost_off": round(pricing.estimate(pu, peak=False)["total"], 4),
        "models": [c.get("model") for c in cands],
    }


def query_diff(brief: dict) -> dict:
    a = planning.build_query_plan(brief, use_negative=True)
    b = planning.build_query_plan(brief, use_negative=False)
    strip = re.compile(r' -"[^"]*"')
    rows = []
    ok = True
    for x, y in zip(a, b):
        left = strip.sub("", x["query"]).strip()
        same = left == y["query"].strip()
        ok = ok and same and x["query_id"] == y["query_id"]
        rows.append({"query_id": x["query_id"], "with": x["query"],
                     "without": y["query"], "suffix_only": same})
    return {"ok": ok and len(a) == len(b), "n": len(a), "rows": rows}


def fmt(x, nd=2):
    return "—" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def render(rows: list[dict]) -> str:
    rows = [r for r in rows if all(isinstance(r.get(a), dict)
                                   and "error" not in r[a] for a in ARMS)]
    lines = [
        "# negative A/B（同一 brief，唯一变量：查询是否追加 -\"短词\"）",
        "",
        "> brief 复用 delivery-20261112-clean（API 生成，冻结）；"
        "with/without 同 case 内先后紧邻执行；loop 均用固定 ranked plan。",
        "",
        "## 1. 查询差异校验",
        "",
        "| case | 查询数 | 仅后缀差异 |",
        "|---|---:|---|",
    ]
    for r in rows:
        qd = r["query_diff"]
        lines.append(f"| {r['case']} | {qd['n']} | {'是' if qd['ok'] else '**否**'} |")
    lines += [
        "",
        "## 2. 结果对照",
        "",
        "| case | 臂 | 候选 | 池需 | 发现 | 有图 | 交付 | 备选 | degraded | 下载成功 | 成本¥(峰) | 耗时s |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        for arm in ARMS:
            m = r[arm]
            d = m["downloads"]
            lines.append(
                f"| {r['case']} | {arm} | {m['plan_candidates']} | {m['pool_required']} | "
                f"{m['targets']} | {m['with_images']} | {m['delivered']}/{m['required']} | "
                f"{m['backup']}/4 | {m['degraded']} | {d.get('gate_pass')} | "
                f"{fmt(m['cost_peak'], 3)} | {m['elapsed_s']:.0f} |")
    lines += ["", "## 3. 差值（without − with）", "",
              "| case | 候选 | 有图 | 交付 | 备选 | 成本¥(峰) | 耗时s | 候选重合 |",
              "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        a, b = r["with"], r["without"]
        sa, sb = set(a["models"]), set(b["models"])
        jac = (len(sa & sb) / len(sa | sb)) if (sa | sb) else 1.0
        lines.append(
            f"| {r['case']} | {b['plan_candidates'] - a['plan_candidates']:+d} | "
            f"{b['with_images'] - a['with_images']:+d} | "
            f"{(b['delivered'] or 0) - (a['delivered'] or 0):+d} | "
            f"{b['backup'] - a['backup']:+d} | "
            f"{(b['cost_peak'] or 0) - (a['cost_peak'] or 0):+.3f} | "
            f"{b['elapsed_s'] - a['elapsed_s']:+.0f} | {jac:.2f} |")
    lines += ["", "## 4. 汇总", ""]
    for arm in ARMS:
        rows_a = [r[arm] for r in rows]
        delivered = sum(int(m["delivered"] or 0) for m in rows_a)
        required = sum(int(m["required"] or 0) for m in rows_a)
        backup = sum(int(m["backup"] or 0) for m in rows_a)
        backup_req = sum(int(m["backup_required"] or 0) for m in rows_a)
        cost = sum(float(m["cost_peak"] or 0) for m in rows_a)
        secs = sum(float(m["elapsed_s"] or 0) for m in rows_a)
        cand = sum(int(m["plan_candidates"] or 0) for m in rows_a)
        lines.append(f"- **{arm}**：候选 {cand}，交付 {delivered}/{required}，"
                     f"备选 {backup}/{backup_req}，峰值成本 ¥{cost:.3f}，"
                     f"循环耗时 {secs/60:.1f} min")
    if len(rows) and rows[0]["with"]["plan_candidates"] is not None:
        lines += ["", "判定规则（预先写死，避免事后挑指标）：", "",
                  "- 准入：`without` 不得让候选池跌破 `pool.required`；",
                  "- 收益：交付数为主，备选数为辅；成本变化 > ¥0.15/5 case 才计入；",
                  "- 若 without 交付不降且成本不升 → 删除 negative；",
                  "- 若 without 交付下降或池跌破下限 → 保留 negative + 现有护栏；",
                  "- 若结果持平 → 保留（默认不改生产），记录为“未证实收益”。"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--source", default=str(ROOT / "data-test" / "runs"
                                            / "delivery-20261112-clean"))
    ap.add_argument("--only", default="", help="逗号分隔 case 名，调试用")
    args = ap.parse_args(argv)
    base = Path(args.base)
    source = Path(args.source)
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    base.mkdir(parents=True, exist_ok=True)
    results_path = base / "AB.json"
    rows: list[dict] = _read(results_path) or []

    for name, klass, slots in CASES:
        if only and name not in only:
            continue
        src_brief = source / name / "brief.json"
        if not src_brief.exists():
            raise SystemExit(f"missing frozen brief: {src_brief}")
        brief = _read(src_brief)
        qd = query_diff(brief)
        (base / name).mkdir(parents=True, exist_ok=True)
        (base / name / "QUERY-DIFF.json").write_text(
            json.dumps(qd, ensure_ascii=False, indent=1), encoding="utf-8")
        if not qd["ok"]:
            raise SystemExit(f"{name}: query diff is not suffix-only")

        rec = {"case": name, "class": klass, "slots": slots, "query_diff": qd}
        for arm in ARMS:
            d = base / name / arm
            d.mkdir(parents=True, exist_ok=True)
            for f in ("brief.json", "brief.json.meta.json"):
                p = source / name / f
                if p.exists():
                    (d / f).write_text(p.read_text(encoding="utf-8"),
                                       encoding="utf-8")
            plan_cmd = [PY, "scripts/plan_candidates.py",
                        "--brief", str(src_brief), "--out", str(d / "plan.json")]
            if arm == "without":
                plan_cmd.append("--no-negative")
            rc, sec = run(plan_cmd, d / "1-plan.log", 1200)
            print(f"[{name}/{arm}] plan rc={rc} {sec}s", flush=True)
            if rc != 0:
                rec[arm] = {"error": f"plan rc={rc}"}
                continue
            rc, sec = run([PY, "scripts/rank_plan.py", "--plan", str(d / "plan.json"),
                           "--brief", str(src_brief), "--out", str(d / "plan-ranked.json")],
                          d / "2-rank.log", 600)
            print(f"[{name}/{arm}] rank rc={rc} {sec}s", flush=True)
            if rc != 0:
                rec[arm] = {"error": f"rank rc={rc}"}
                continue
            rc, sec = run([PY, "-m", "equiplens.retrieval_engine",
                           "--brief", str(src_brief), "--web-only",
                           "--plan", str(d / "plan-ranked.json"),
                           "--run-root", str(d), "--run-id", "run",
                           "--evidence-db", str(d / "run" / "evidence.db")],
                          d / "3-loop.log", 2400)
            print(f"[{name}/{arm}] loop rc={rc} {sec}s", flush=True)
            if rc not in (0, 2):
                rec[arm] = {"error": f"loop rc={rc}"}
                continue
            run([PY, "scripts/render_fetch_audit.py", str(d / "run")], d / "4-audit.log", 300)
            run([PY, "scripts/build_delivery_manifest.py", "--run", str(d / "run"),
                 "--brief", str(src_brief), "--plan", str(d / "plan-ranked.json")],
                d / "5-manifest.log", 300)
            rec[arm] = collect(d, src_brief)
        rows = [x for x in rows if x["case"] != name] + [rec]
        results_path.write_text(json.dumps(rows, ensure_ascii=False, indent=1),
                                encoding="utf-8")
        (base / "AB-SUMMARY.md").write_text(render(rows), encoding="utf-8")
        print(f"=== {name} done; summary updated ===", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
