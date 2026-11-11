# -*- coding: utf-8 -*-
"""离线评估通用车身/吨位 guard：只对已 gate-pass 的 funnel 行生效。

不针对品牌/车型；类别词表来自 brief.class，吨位只比较同单位数值。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

BODY = {
    "mixer": ["搅拌车", "搅拌运输车", "混凝土搅拌"],
    "dump": ["自卸车", "矿用自卸", "宽体自卸", "矿用卡车", "dump truck"],
    "aerial": ["高空作业车", "高空作业平台", "臂架", "作业斗"],
    "tractor": ["牵引车", "牵引头", "tractor"],
    "cargo": ["载货车", "栏板", "厢式", "仓栅"],
    "bus": ["客车", "公交"],
    "loader": ["装载机", "铲车"],
    "excavator": ["挖掘机"],
}
ALL = [(k, t) for k, ts in BODY.items() for t in ts]


def target_body(brief: dict) -> str:
    c = ((brief.get("request") or {}).get("class") or "")
    for key, terms in BODY.items():
        if any(t in c for t in terms):
            return key
    return ""


def title_bodies(title: str) -> set[str]:
    t = (title or "").lower()
    return {k for k, terms in BODY.items() if any(x.lower() in t for x in terms)}


def tonnes(text: str, model: str = "") -> list[float]:
    s = f"{text} {model}"
    vals = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(?:t|吨)(?![a-z])", s, re.I):
        try:
            vals.append(float(m.group(1)))
        except ValueError:
            pass
    return vals


MIXED = ("认证", "类型", "卡车", "货车", "专用车", "工程车", "车辆",
         "系列", "级别", "大吨位", "车型")


def guard(brief: dict, model: str, title: str) -> tuple[bool, str]:
    tb = target_body(brief)
    if not tb:
        return True, ""
    bodies = title_bodies(title)
    # 只在“标题明确、单一、非泛称/认证页、且没有目标类型”时硬拒；
    # 吨位先只 warning，不硬拒（同系列 150T/70T 文章会误杀）。
    if (bodies and tb not in bodies and len(bodies) == 1
            and not any(x in (title or "") for x in MIXED)):
        return False, f"wrong_body:{sorted(bodies)}"
    tv = tonnes((brief.get("request") or {}).get("configuration") or "", model)
    if tv and title:
        hv = tonnes(title)
        if hv and not any(abs(x - y) <= max(3.0, 0.1 * y) for x in hv for y in tv):
            return True, f"tonnage_warning:title={hv},target={tv}"
    return True, ""


def main() -> int:
    funnel = json.loads((ROOT / "data-test/runs/source-expansion-funnel-20261111/funnel.json").read_text(encoding="utf-8"))
    review = json.loads((ROOT / "data-test/evals/source-expansion-funnel-pending-review-20261111/review-data.json").read_text(encoding="utf-8"))
    ann = json.loads((ROOT / "data-test/evals/source-expansion-funnel-pending-review-20261111/annotations.json").read_text(encoding="utf-8"))
    m = {r["url"]: ann.get(f"v{i}", "") for i, r in enumerate(review, 1)}
    briefs = {}
    for name, path in {
        "M1": "data-test/evals/task-briefs-20261109/brief-m1-desert.json",
        "M1B": "data-test/evals/task-briefs-20261109/brief-m1b-global.json",
        "A-mining": "data-test/evals/source-expansion-briefs-20261111/mining-dump.json",
        "B-mixer": "data-test/evals/source-expansion-briefs-20261111/mixer.json",
        "C-aerial": "data-test/evals/source-expansion-briefs-20261111/aerial.json",
    }.items():
        briefs[name] = json.loads((ROOT / path).read_text(encoding="utf-8"))
    rows = []
    for r in funnel["images"]:
        label = r.get("human_label") or ""
        if r["url"] in m:
            label = m[r["url"]]
        if not r.get("accepted"):
            continue
        ok, why = guard(briefs[r["brief"]], r["model"], r.get("title", ""))
        rows.append({**r, "human_label": label, "guard_accept": ok, "guard_reason": why})
    old = [r for r in rows if r["accepted"]]
    new = [r for r in rows if r["guard_accept"]]
    def prec(rs):
        good = sum(1 for r in rs if r["human_label"] == "是目标车")
        return good, len(rs), round(good / max(len(rs), 1), 3)
    out = {"old": prec(old), "new": prec(new),
           "rejected": [r for r in rows if not r["guard_accept"]]}
    path = ROOT / "data-test/evals/source-expansion-funnel-pending-review-20261111/BODY-GUARD.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"old": out["old"], "new": out["new"], "rejected": len(out["rejected"])}, ensure_ascii=False))
    for r in out["rejected"]:
        print("REJECT", r["brief"], r["model"][:25], r["guard_reason"], r["human_label"], repr(r.get("title", "")[:60]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
