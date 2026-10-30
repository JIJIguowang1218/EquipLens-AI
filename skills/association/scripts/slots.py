# -*- coding: utf-8 -*-
"""页槽分配与缓冲：把候选目标收敛成「推荐 N + 备选 M」，并分配 vehicle:1..N 槽位。

确定性代码，不做语义判断——判断（选谁、什么轴、什么理由）由模型给。
用法:
    python slots.py --targets candidates.json --slots 12 --requested 12 [--thin]
candidates.json 形如 {"targets": [...]} 或直接数组；每条至少含 id/tier/confidence。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def buffer_size(requested: int, thin: bool = False) -> int:
    """薄类目 25%，常规 max(2, ceil(0.15N))。"""
    n = max(1, int(requested))
    return max(2, math.ceil((0.25 if thin else 0.15) * n))


def allocate(targets: list[dict], *, vehicle_slots: int = 12, requested: int = 12,
             thin: bool = False, max_per_family: int = 2) -> dict:
    """排序 → 同族去重 → 填槽 → 余下进备选。

    - blocked/exclude 不参与分配；
    - 同 family（缺省用 category）最多 max_per_family 个，避免一页版全是兄弟车型；
    - 备选不占槽（slots 为空）。
    """
    pool = [t for t in targets
            if t.get("status") != "blocked" and t.get("kind") != "exclude"]
    # 未验证的"具体型号名"只能当备选（编造风险）；方向级（无 models）可占槽
    eligible, held = [], []
    for t in pool:
        unverified_model = (t.get("grounding") == "inference"
                            and not t.get("verified") and t.get("models"))
        if unverified_model:
            held.append(t)
        else:
            eligible.append(t)
    status_rank = {"recommended": 0, "provisional": 1}
    ranked = sorted(eligible, key=lambda t: (int(t.get("tier", 9)),
                                             status_rank.get(t.get("status"), 2),
                                             not t.get("verified", False),
                                             -float(t.get("confidence", 0.0))))
    picks, seen_family, dropped = [], {}, []
    for t in ranked:
        fam = t.get("family") or t.get("category") or "_"
        if seen_family.get(fam, 0) >= max_per_family:
            dropped.append({"id": t.get("id"), "why": f"同族超过 {max_per_family} 台"})
            continue
        seen_family[fam] = seen_family.get(fam, 0) + 1
        picks.append(t)

    cap = max(0, int(vehicle_slots))
    n_take = min(int(requested), cap, len(picks))
    recommended = picks[:n_take]
    backup = picks[n_take:] + held
    for i, t in enumerate(recommended, 1):
        if t.get("status") != "provisional":  # provisional 保持自身状态，只加槽
            t["status"] = "recommended"
        t["slots"] = [f"vehicle:{i}"]
    for t in backup:
        t["status"] = "backup"
        t["slots"] = []
    return {
        "recommended": [t["id"] for t in recommended],
        "backup": [t["id"] for t in backup],
        "buffer": {"requested": int(requested),
                   "extra": buffer_size(requested, thin), "thin": bool(thin)},
        "slots_used": n_take,
        "dropped": dropped,
        "held": [{"id": t.get("id"), "why": "grounding=inference 且未验证"} for t in held],
        "shortfall": max(0, int(requested) - n_take),
        "targets": [t for t in targets],
    }


def _load(path: str) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["targets"] if isinstance(data, dict) else data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="页槽分配：推荐 N + 备选 M，同族去重")
    ap.add_argument("--targets", required=True, help="候选目标 JSON（数组或 {targets:[]}）")
    ap.add_argument("--slots", type=int, default=12, help="整车页槽数")
    ap.add_argument("--requested", type=int, default=12, help="用户确认的车型数")
    ap.add_argument("--thin", action="store_true", help="薄类目：缓冲 25%%")
    ap.add_argument("--max-per-family", type=int, default=2)
    ap.add_argument("--out", help="写出结果 JSON（默认打印）")
    a = ap.parse_args(argv)
    try:
        res = allocate(_load(a.targets), vehicle_slots=a.slots,
                       requested=a.requested, thin=a.thin,
                       max_per_family=a.max_per_family)
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    text = json.dumps(res, ensure_ascii=False, indent=1)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"→ {a.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
