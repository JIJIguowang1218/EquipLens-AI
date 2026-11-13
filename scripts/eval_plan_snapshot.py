# -*- coding: utf-8 -*-
"""F6 最小评估协议：冻结快照 + 指标 + 配对 bootstrap。

用法:
  PYTHONPATH=src python scripts/eval_plan_snapshot.py --freeze data-test/runs/p5-slots-20261114
  PYTHONPATH=src python scripts/eval_plan_snapshot.py --compare A B
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import random
import statistics
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def _sha(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def case_metrics(plan: dict) -> dict:
    cands = plan.get("candidates") or []
    n = len(cands)
    code = sum(1 for c in cands if c.get("identity_kind") == "code")
    generic = sum(1 for c in cands if c.get("identity_kind") == "generic")
    sk = sum(1 for c in cands if c.get("search_key"))
    slots = sum(1 for c in cands
                if (c.get("slots") or {}).get("model_code")
                or (c.get("slots") or {}).get("series"))
    pool = plan.get("pool") or {}
    return {
        "candidates": n,
        "code_share": round(code / n, 3) if n else 0.0,
        "generic_share": round(generic / n, 3) if n else 0.0,
        "search_key_share": round(sk / n, 3) if n else 0.0,
        "slot_share": round(slots / n, 3) if n else 0.0,
        "pool_ok": bool(pool.get("ok")),
        "pool_gap": max(0, int(pool.get("required") or 0) - n),
    }


def load_snapshot(path: pathlib.Path) -> dict:
    out = {}
    for p in sorted(path.glob("*/plan.json")):
        j = json.loads(p.read_text(encoding="utf-8"))
        rec = case_metrics(j)
        rec["queries"] = [q.get("query") for q in (j.get("queries") or [])]
        rec["plan_sha"] = _sha(p.read_text(encoding="utf-8"))
        out[p.parent.name] = rec
    return out


def freeze(path: pathlib.Path) -> dict:
    snap = load_snapshot(path)
    manifest = {"root": str(path.relative_to(ROOT)), "cases": snap}
    dest = path / "SNAPSHOT.json"
    dest.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    return manifest


def compare(a: pathlib.Path, b: pathlib.Path) -> dict:
    sa, sb = load_snapshot(a), load_snapshot(b)
    keys = sorted(set(sa) & set(sb))
    diffs = {}
    for k in keys:
        diffs[k] = {m: round(sb[k][m] - sa[k][m], 3)
                    for m in ("candidates", "code_share", "generic_share",
                              "search_key_share", "slot_share")}
    # 对每个指标，按 case 做配对 bootstrap（n=case 数，区间会很宽，如实报告）
    pooled = {}
    for m in ("candidates", "code_share", "generic_share",
              "search_key_share", "slot_share"):
        vals = [diffs[k][m] for k in keys]
        if not vals:
            continue
        rnd = random.Random(7)
        means = []
        for _ in range(2000):
            sample = [rnd.choice(vals) for _ in vals]
            means.append(statistics.mean(sample))
        means.sort()
        pooled[m] = {
            "mean_delta": round(statistics.mean(vals), 3),
            "ci95": [round(means[int(0.025 * len(means))], 3),
                     round(means[int(0.975 * len(means)) - 1], 3)],
        }
    return {"a": str(a.relative_to(ROOT)), "b": str(b.relative_to(ROOT)),
            "cases": keys, "per_case": diffs, "pooled": pooled}


def main() -> int:
    if "--freeze" in sys.argv:
        path = ROOT / sys.argv[sys.argv.index("--freeze") + 1]
        man = freeze(path)
        print(json.dumps({k: v["candidates"] for k, v in man["cases"].items()},
                         ensure_ascii=False))
        print("frozen:", path / "SNAPSHOT.json")
        return 0
    if "--compare" in sys.argv:
        i = sys.argv.index("--compare")
        a, b = ROOT / sys.argv[i + 1], ROOT / sys.argv[i + 2]
        res = compare(a, b)
        out = ROOT / "data-test" / "evals" / f"snapshot-compare-{a.name}-vs-{b.name}.json"
        out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps(res["pooled"], ensure_ascii=False, indent=1))
        for k in res["cases"]:
            print(k, res["per_case"][k])
        print("out:", out)
        return 0
    print("用法: --freeze <dir> | --compare <dirA> <dirB>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
