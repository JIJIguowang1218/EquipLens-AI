# -*- coding: utf-8 -*-
"""清单校验：schema + 页数/槽位/备选/grounding 不变量。

校验只管"能不能交"——不判断语义对错（那由人审）。
用法: python check_list.py list.json [--schema PATH]
退出码: 0 通过（可有 warning）；1 有 error；2 读文件失败。
"""
from __future__ import annotations

import argparse
import json
import re
import math
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

HERE = Path(__file__).resolve().parent
DEFAULT_SCHEMA = HERE.parent / "schemas" / "association-list.schema.json"
BAD_REASONS = ("相似", "差不多", "类似", "同系列")


def _norm(s: str) -> str:
    t = str(s).lower().replace("×", "x")
    return "".join(ch for ch in t if not ch.isspace() and ch not in "-_*·/()（）")


def _tokens(s: str) -> list[str]:
    return [x for x in re.findall(r"[a-z0-9]+|[一-鿿]+", str(s).lower())
            if len(x) >= 2]


def _model_in_title(models: list[str], title: str) -> bool:
    t = _norm(title)
    for m in models or []:
        toks = _tokens(m)
        if toks and all(tok in t for tok in toks):
            return True
    return False


def _has_grade(ev: list[dict], grades: tuple[str, ...]) -> bool:
    return any(e.get("grade") in grades for e in ev or [])


def _buffer_floor(requested: int) -> int:
    return max(2, math.ceil(0.15 * max(1, requested)))


def check(doc: dict, schema: dict | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []

    if schema is not None:
        if jsonschema is None:
            warnings.append("jsonschema 未安装，跳过 schema 校验")
        else:
            try:
                jsonschema.validate(instance=doc, schema=schema)
            except jsonschema.ValidationError as e:
                errors.append(f"schema: {'/'.join(map(str, e.absolute_path))}: {e.message}")

    pb = doc.get("page_budget", {})
    total = int(pb.get("total", 0))
    fixed = int(pb.get("fixed_pages", 0))
    vslots = int(pb.get("vehicle_slots", 0))
    pslots = int(pb.get("part_page_slots", 0))
    if total and fixed + vslots + pslots > total:
        errors.append(f"页数超限: {fixed}+{vslots}+{pslots} > {total}")

    targets = doc.get("targets", [])
    holders = [t for t in targets
               if t.get("status") in ("recommended", "provisional")]
    rec = [t for t in targets if t.get("status") == "recommended"]
    slots = [s for t in holders for s in (t.get("slots") or [])]
    vused = [s for s in slots if s.startswith("vehicle:")]
    if len(vused) != len(set(vused)):
        errors.append(f"槽位重复: {sorted(vused)}")
    if vslots and len(set(vused)) > vslots:
        errors.append(f"推荐槽数 {len(set(vused))} > vehicle_slots {vslots}")

    for t in targets:
        status = t.get("status")
        models = t.get("models") or []
        ev = t.get("evidence") or []
        if status not in ("recommended", "provisional") and t.get("slots"):
            errors.append(f"{t.get('id')}: 非推荐/非 provisional 项不得占槽 {t['slots']}")
        if status in ("recommended", "provisional"):
            if not models:
                errors.append(f"{t.get('id')}: 占槽必须有具体车型名（纯方向改放 next_action）")
            if status == "recommended":
                if not _has_grade(ev, ("E3",)):
                    errors.append(f"{t.get('id')}: recommended 必须带 E3 证据（详情页/专文，标题含型号）")
                elif not any(e.get("grade") == "E3"
                             and _model_in_title(models, e.get("title", "")) for e in ev):
                    errors.append(f"{t.get('id')}: E3 证据标题里没有该型号，证据不成立")
            if status == "provisional":
                if not (t.get("verify_by") or "").strip():
                    warnings.append(f"{t.get('id')}: 建议写 verify_by（转正动作）")
                if not _has_grade(ev, ("E1", "E2", "E3")):
                    errors.append(f"{t.get('id')}: provisional 至少要有 E1 证据（SERP 命中）")
            if t.get("relevance_strength") == "weak" and not (t.get("weak_reason") or "").strip():
                warnings.append(f"{t.get('id')}: 弱关联建议写 weak_reason")
        if t.get("kind") == "exclude" and status != "blocked":
            errors.append(f"{t.get('id')}: exclude 必须 status=blocked")
        if t.get("relation") == "cross_vehicle" and not doc.get("allow_cross_vehicle"):
            warnings.append(f"{t.get('id')}: cross_vehicle 未开 allow_cross_vehicle（借用证据需标注）")
        reason = str(t.get("reason", ""))
        if any(w in reason for w in BAD_REASONS):
            warnings.append(f"{t.get('id')}: 理由含空话词（{'/'.join(BAD_REASONS)}）")

    blocking = [c for c in doc.get("needs_confirmation", []) if c.get("blocking")]
    full_block = [c for c in blocking if c.get("blocking_scope", "all") == "all"]
    if full_block and holders:
        errors.append(f"阻断式确认(all)存在时不得占槽，当前占槽 {len(holders)} 个")
    elif blocking and holders:
        warnings.append(f"部分阻断（{len(blocking)} 条）下占槽 {len(holders)} 个，"
                        "需确认阻断范围确实不覆盖这些目标")

    cov = doc.get("coverage") or {}
    filled = int(cov.get("slots_filled", len(set(vused))))
    want = int(cov.get("slots_requested", vslots))
    if want and filled < want and not cov.get("gap_kind"):
        warnings.append(f"缺口 {want - filled} 槽但未写 coverage.gap_kind")

    parts_req = doc.get("parts_requested") or []
    mentioned = {p.get("part") for t in targets for p in (t.get("parts") or [])}
    missing = [p for p in parts_req if p not in mentioned]
    if missing:
        warnings.append(f"请求部件未被任何目标覆盖: {missing}")

    requested = int(doc.get("buffer", {}).get("requested") or doc.get("requested") or 0)
    extra = int(doc.get("buffer", {}).get("extra", 0))

    # 硬要求：必须交付 requested 台"带车型名"的目标（弱关联可接受，但必须有名字）
    named_slots = {s for t in holders if t.get("models") for s in (t.get("slots") or [])}
    if requested and len(named_slots) < requested:
        errors.append(f"必须交付 {requested} 台可开爬车型，当前 {len(named_slots)}"
                      f"（缺 {requested - len(named_slots)}；可弱关联但必须有车型名+证据）")
    if requested and extra < _buffer_floor(requested):
        warnings.append(f"缓冲 {extra} < 建议 {_buffer_floor(requested)}")

    if not doc.get("decisions") and any(int(t.get("tier", 1)) >= 2 for t in targets):
        warnings.append("出现 tier≥2 的目标但没有 decisions 记录（放闸不可审计）")
    if not doc.get("run_meta"):
        warnings.append("缺 run_meta（model_id/prompt_version/evidence_index_version/run_at）")

    stats = {
        "targets": len(targets),
        "recommended": len(rec),
        "provisional": sum(1 for t in targets if t.get("status") == "provisional"),
        "backup": sum(1 for t in targets if t.get("status") == "backup"),
        "blocked": sum(1 for t in targets if t.get("status") == "blocked"),
        "slots_used": len(set(vused)),
        "slots_available": vslots,
        "named_slots": len(named_slots),
        "fill_rate": round(len(set(vused)) / vslots, 3) if vslots else 0.0,
        "named_fill": round(len(named_slots) / requested, 3) if requested else 0.0,
        "evidence_e3": sum(1 for t in holders if t.get("models")
                           and _has_grade(t.get("evidence") or [], ("E3",))),
        "parts_missing": missing,
    }
    return {"ok": not errors, "errors": errors, "warnings": warnings, "stats": stats}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="关联清单校验（schema + 页槽/备选/grounding）")
    ap.add_argument("list_json")
    ap.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    a = ap.parse_args(argv)
    try:
        doc = json.loads(Path(a.list_json).read_text(encoding="utf-8"))
        schema = (json.loads(Path(a.schema).read_text(encoding="utf-8"))
                  if Path(a.schema).exists() else None)
    except (OSError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    if schema is None:
        print(json.dumps({"ok": False, "error": f"schema 不存在: {a.schema}"},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    res = check(doc, schema)
    print(json.dumps(res, ensure_ascii=False, indent=1))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
