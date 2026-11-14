# -*- coding: utf-8 -*-
"""离线回放：新的标识匹配（identity.code_in_title）对比旧的子串匹配。

用途：在历史 run 的冻结证据（state.json 的 asset_meta + verifications）上，
不联网、不重跑，评估"code 匹配归一化"带来的 E1 变化与风险。

用法:
  PYTHONPATH=src python scripts/evaluate_identity_match.py \
      --roots data-test/runs/p7-screen-20261114,data-test/runs/p7-screen-r2-20261114,data-test/runs/p7-screen-r3-20261114 \
      --out data-test/evals/identity-match-20261114.json

判定口径:
  - gained: 旧判定不是 confirmed，新匹配命中码 → 会升到 confirmed；
  - lost:   旧判定 confirmed，新匹配不命中 → 需要对每条解释（多半是旧子串误命中）；
  - delivered_flips: 已交付车辆里"因新匹配获得 confirmed 图"的台数（质量变化）。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equiplens.identity import code_in_title  # noqa: E402

OLD_CODE = re.compile(r"[A-Z]{1,4}\d{3,}[A-Z0-9]*")


def _old_hit(model: str, title: str) -> bool:
    m = OLD_CODE.search((model or "").upper())
    return bool(m) and m.group(0).lower() in (title or "").lower()


def _model_in_title(model: str, title: str) -> bool:
    """旧规则里的“车名整串出现在标题”（去多余空格后）。"""
    m = " ".join((model or "").split()).lower()
    t = " ".join((title or "").split()).lower()
    return bool(m) and m in t


def replay_run(run_dir: Path) -> dict:
    state = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
    summary_path = run_dir / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {}
    delivered: set[str] = set()
    for models in (summary.get("accepted_targets") or {}).values():
        delivered.update(models)

    ver = state.get("verifications") or {}
    meta = state.get("asset_meta") or {}
    gained, lost, old_loose = [], [], []
    delivered_flips: dict[str, dict] = {}
    for aid, m in meta.items():
        model = m.get("model") or ""
        title = m.get("title") or ""
        rows = [(k, v) for k, v in ver.items() if k.startswith(f"{aid}:")]
        if not rows:
            continue
        old_conf = any(v.get("identity") == "confirmed" for _, v in rows)
        new_hit = code_in_title(model, title) or _model_in_title(model, title)
        rec = {"asset_id": aid, "target": m.get("target_id"), "model": model, "title": title}
        if new_hit and not old_conf:
            gained.append(rec)
            tid = m.get("target_id")
            if tid in delivered:
                delivered_flips.setdefault(tid, rec)
        elif old_conf and not new_hit:
            lost.append(rec)
        if old_conf and _old_hit(model, title) and not new_hit:
            old_loose.append(rec)
    return {
        "run": run_dir.parent.name,
        "assets": len(meta),
        "old_confirmed_assets": sum(
            1 for aid in meta
            if any(v.get("identity") == "confirmed" for k, v in ver.items() if k.startswith(f"{aid}:"))),
        "gained": gained,
        "lost": lost,
        "old_loose_confirmed": old_loose,
        "delivered_flips": delivered_flips,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", default=",".join([
        "data-test/runs/p7-screen-20261114",
        "data-test/runs/p7-screen-r2-20261114",
        "data-test/runs/p7-screen-r3-20261114"]))
    ap.add_argument("--out", default="data-test/evals/identity-match-20261114.json")
    args = ap.parse_args(argv)

    results = []
    for root in [Path(x) for x in args.roots.split(",") if x.strip()]:
        for run in sorted(root.glob("*/run")):
            if (run / "state.json").exists():
                results.append(replay_run(run))

    gained = [g for r in results for g in r["gained"]]
    lost = [x for r in results for x in r["lost"]]
    loose = [x for r in results for x in r["old_loose_confirmed"]]
    flips = {}
    for r in results:
        for tid, rec in r["delivered_flips"].items():
            flips[tid] = dict(rec, run=r["run"])
    payload = {
        "created_at": "2026-11-14",
        "scope": [str(r["run"]) for r in results],
        "summary": {
            "runs": len(results),
            "assets": sum(r["assets"] for r in results),
            "old_confirmed_assets": sum(r["old_confirmed_assets"] for r in results),
            "gained_assets": len(gained),
            "lost_assets": len(lost),
            "old_loose_confirmed": len(loose),
            "delivered_flips": len(flips),
        },
        "delivered_flips": flips,
        "gained": gained,
        "lost": lost,
        "old_loose_confirmed": loose,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False))
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
