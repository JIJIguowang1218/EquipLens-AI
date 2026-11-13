# -*- coding: utf-8 -*-
"""给已生成的 plan 加“意向排序”：N primary（brief 的 vehicle_slots）+ 4 backup + 其余 pool。

只基于文本（用户请求、候选来源/reason），**不看图片**；因此它只是抓取/占槽的先验，
最终仍由门卫/核验/用户决定。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens.planning import pool_requirement, pool_warning  # noqa: E402

KEY_FILE = Path.home() / ".equiplens" / "deepseek.env"


def load_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key and KEY_FILE.exists():
        for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        raise SystemExit("no DEEPSEEK_API_KEY")
    return key


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--brief", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--pin", default="", help="逗号分隔关键词，强制 primary")
    ap.add_argument("--slots", type=int, default=None,
                    help="主交付台数；默认取 brief.request.page_budget.vehicle_slots")
    ap.add_argument("--backup", type=int, default=4, help="备选台数（默认 4）")
    ap.add_argument("--model", default="deepseek-flash")
    ap.add_argument("--deterministic", action="store_true",
                    help="A/B 用：不调 LLM，按来源数/维度/身份做确定性排序")
    args = ap.parse_args(argv)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    cands = plan.get("candidates") or []
    if not cands:
        raise SystemExit("plan 没有 candidates")
    pins = [x.strip().lower() for x in args.pin.split(",") if x.strip()]
    # 主交付台数由用户输入决定（brief），不写死 12
    slots = args.slots or int(((brief.get("request") or {}).get("page_budget") or {})
                              .get("vehicle_slots") or 0)
    if slots <= 0:
        slots = sum(int(u.get("quota") or 0) for u in (brief.get("research_units") or []))
    if slots <= 0:
        raise SystemExit("brief 没有 vehicle_slots/quota，无法确定主交付台数；用 --slots 指定")
    backup = max(0, int(args.backup))
    warn = pool_warning(len(cands), slots, backup)
    if warn:
        print("WARN " + warn, file=sys.stderr)
    compact = [{
        "model": c.get("model"), "identity_kind": c.get("identity_kind"),
        "reason": (c.get("reason") or "")[:160],
        "source_queries": [q.get("query") for q in (c.get("source_queries") or [])][:3],
    } for c in cands]

    if args.deterministic:
        # A/B 基线：不调 LLM。用“被几条查询共同发现 + 来源维度 + 身份类型”排序，
        # 只作为 rank 的对照，不改变 plan 内容。
        dim_rank = {"base": 0, "model": 1, "unit": 2, "environment": 3, "english": 4}
        kind_rank = {"code": 0, "series": 1, "generic": 2}

        def _key(c):
            dims = c.get("dimensions") or []
            d = min([dim_rank.get(x, 9) for x in dims] or [9])
            return (0 if any(p and p in c["model"].lower() for p in pins) else 1,
                    -int(c.get("source_count") or 0), d,
                    kind_rank.get(c.get("identity_kind"), 3), c["model"])

        order = sorted(cands, key=_key)
        ranking = []
        for i, c in enumerate(order, 1):
            role = "primary" if i <= slots else ("backup" if i <= slots + backup else "pool")
            band = "must" if i <= slots else ("strong" if i <= slots + backup else "weak")
            c["intent_band"] = band
            c["intent_reason"] = "确定性排序：来源数/维度/身份"
            c["role"] = "primary" if c.get("pinned") else role
            c["intent_rank"] = i
            ranking.append({"model": c["model"], "band": band,
                            "reason": c["intent_reason"], "role": c["role"]})
        plan["candidates"] = order
        plan["pool"] = {"count": len(cands),
                        "required": pool_requirement(slots, backup),
                        "ok": not warn, "warning": warn}
        plan["ranking"] = {"method": "deterministic", "pins": pins,
                           "slots": slots, "backup": backup,
                           "primary": sum(1 for c in order if c.get("role") == "primary"),
                           "backup": sum(1 for c in order if c.get("role") == "backup"),
                           "rows": ranking}
        out = Path(args.out or Path(args.plan).with_name("plan-ranked.json"))
        out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({"out": str(out), "method": "deterministic",
                          "candidates": len(order),
                          "primary": plan["ranking"]["primary"],
                          "backup": plan["ranking"]["backup"]}, ensure_ascii=False))
        return 0

    prompt = (
        "你是工程车设计检索的规划助手。下面是一个任务单和候选车型（只有文本信息，"
        "没有图片）。请只依据文本，给候选排序，选出最值得优先抓图/交付的车型。\n"
        "要求：\n"
        "1) 只从给出的候选里选，model 必须与列表完全一致；\n"
        "2) 排序依据：与用户设计问题/工况的匹配、关系轴、代表性、差异性；\n"
        "3) 不要因为“型号代码更完整”就排前面；generic 也可以 must；\n"
        "4) 不要编造候选，不要用图片质量/分辨率（你还没看到图）；\n"
        "5) 输出 JSON：{\"ranking\":[{\"model\":\"\",\"band\":\"must|strong|possible|weak\","
        "\"reason\":\"为什么值得先看，引用候选的文本信息\",\"role\":\"primary|backup|pool\"}]}；\n"
        f"   前 {slots} 个 primary，接着 {backup} 个 backup，其余 pool。\n\n"
        f"任务单：{json.dumps(brief.get('request', {}), ensure_ascii=False)}\n"
        f"候选：{json.dumps(compact, ensure_ascii=False)}"
    )
    r = requests.post("https://api.deepseek.com/chat/completions",
                      headers={"Authorization": f"Bearer {load_key()}",
                               "Content-Type": "application/json"},
                      json={"model": args.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "response_format": {"type": "json_object"},
                            "temperature": 0}, timeout=180)
    r.raise_for_status()
    got = json.loads(r.json()["choices"][0]["message"]["content"])
    by_model = {c["model"]: c for c in cands}
    order, seen = [], set()
    for row in got.get("ranking") or []:
        m = row.get("model")
        if m not in by_model or m in seen:
            continue
        seen.add(m)
        c = by_model[m]
        c["intent_band"] = row.get("band") if row.get("band") in ("must", "strong", "possible", "weak") else "possible"
        c["intent_reason"] = str(row.get("reason") or "")[:300]
        c["role"] = row.get("role") if row.get("role") in ("primary", "backup", "pool") else "pool"
        order.append(c)
    # 未排到的放最后
    for c in cands:
        if c["model"] not in seen:
            c.setdefault("intent_band", "weak")
            c.setdefault("intent_reason", "LLM 未排序，放到 pool")
            c["role"] = "pool"
            order.append(c)
    # pinned 强制到最前
    for c in order:
        if any(p and p in c["model"].lower() for p in pins):
            c["pinned"] = True
            c["role"] = "primary"
    order.sort(key=lambda c: (0 if c.get("pinned") else 1,
                              {"primary": 0, "backup": 1}.get(c.get("role"), 2)))
    for i, c in enumerate(order, 1):
        c["intent_rank"] = i
        # 按名次确定角色，保证与 brief 的台数一致（pinned 不降级）
        if c.get("pinned"):
            c["role"] = "primary"
        elif i <= slots:
            c["role"] = "primary"
        elif i <= slots + backup:
            c["role"] = "backup"
        else:
            c["role"] = "pool"
    plan["candidates"] = order
    plan["pool"] = {"count": len(cands), "required": pool_requirement(slots, backup),
                    "ok": not warn, "warning": warn}
    plan["ranking"] = {"model": args.model, "pins": pins,
                       "slots": slots, "backup": backup,
                       "primary": sum(1 for c in order if c.get("role") == "primary"),
                       "backup": sum(1 for c in order if c.get("role") == "backup")}
    out = Path(args.out or Path(args.plan).with_name("plan-ranked.json"))
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(out), "candidates": len(order),
                      "primary": plan["ranking"]["primary"],
                      "backup": plan["ranking"]["backup"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
