# -*- coding: utf-8 -*-
"""任务单生成（L1.5 的最小实现）：用户输入 → LLM 解析 → 校验 → brief。

设计原则（2026-11-11，回应“brief 不能手工代工”）：
- LLM 只负责**理解用户输入**：类目/工况/构型/部件/视角/机制/假设；
- 页槽、配额、预算、tiers、strategy_ref 由代码规则生成，LLM 不许编；
- 所有推断必须出现在 `assumptions`，并在 `brief_meta.json` 留 raw input / prompt 版本；
- 输出必须同时通过 `validate_brief` 与 `schemas/task-brief-v3.schema.json`。

用法见 `scripts/build_brief.py`。
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / "skills" / "task-brief" / "SKILL.md"
TAXONOMY_PATH = ROOT / "data" / "part_taxonomy.json"
SCHEMA_PATH = ROOT / "schemas" / "task-brief-v3.schema.json"

ALLOWED_VIEWS = ("front", "hero_45", "side", "rear", "interior", "detail")
ALLOWED_AXES = ("form_gesture", "proportion", "structure", "cmf",
                "function_ergonomics", "environment_protection",
                "regulation", "manufacturing")
REGION_VIEWS = {"front_face": ["front", "hero_45"], "side": ["side", "hero_45"],
                "rear": ["rear", "side"], "roof": ["side", "hero_45"]}
DEFAULT_NEGATIVE = ("客车", "SUV", "房车", "多车拼图", "内饰", "模型")
SKILL_VERSION = "task-brief@v2"
FORMAT_ONLY_PROMPT = """你是工程车检索任务单解析器。只输出 JSON，不要解释。
字段：request{class, environment, base_platform, configuration, design_questions[]}；
regions[{region, label, views[], design_axes[]}]；
parts[{part, label, kind, location, part_family, taxonomy_status, relation_axis,
       design_axes[], views[], design_relevance, accept, mechanism[], why}]；
assumptions[{field, value, why, confidence}]；negative[]。
views 只能取 front/hero_45/side/rear/interior/detail；
design_axes 只能取 form_gesture/proportion/structure/cmf/function_ergonomics/
environment_protection/regulation/manufacturing。
不要输出 page_budget/research_units/quota/tiers/budget/strategy_ref。"""


def load_taxonomy(path: Path | None = None) -> dict:
    return json.loads((path or TAXONOMY_PATH).read_text(encoding="utf-8"))


def reference_parts(taxonomy: dict) -> dict[str, str]:
    return {k: (v.get("label") or k) for k, v in (taxonomy.get("parts") or {}).items()}


def build_prompt(raw: str, taxonomy: dict, *, class_hint: str = "",
                 part_hints: list[str] | None = None,
                 use_skill: bool = True,
                 prompt_mode: str = "v2") -> str:
    """LLM 的系统提示 = skill 文件；用户提示 = 原始输入 + 约束 + 词表。

    `use_skill=False` 只用于必要性 A/B（无方法引导的基线），不是生产路径。
    """
    mode = prompt_mode if prompt_mode in ("v2", "v1", "none") else "v2"
    if not use_skill and mode == "v2":
        mode = "none"
    if mode == "v2":
        skill = SKILL_PATH.read_text(encoding="utf-8")
    elif mode == "v1":
        skill = FORMAT_ONLY_PROMPT
    else:
        skill = ("你是工程车检索任务单解析器。只输出 JSON："
                 "{request, regions, parts, assumptions, negative}。")
    parts = reference_parts(taxonomy)
    hints = {
        "raw": raw,
        "class_hint": class_hint,
        "part_hints": part_hints or [],
        "reference_parts": parts,
        "reference_parts_note": "参考词表，不是准入；用户/新部件可用 custom_*",
        "reference_regions": {k: (v.get("label") or k)
                            for k, v in (taxonomy.get("regions") or {}).items()},
        "allowed_views": list(ALLOWED_VIEWS),
        "allowed_axes": list(ALLOWED_AXES),
        "output": "只输出 JSON：{request, regions, parts, assumptions, negative}",
    }
    return (skill + "\n\n---\n\n## 本次输入\n\n"
            + json.dumps(hints, ensure_ascii=False, indent=1))


def _clean(value) -> str:
    return " ".join(str(value or "").split())


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def assemble_brief(payload: dict, raw: str, *, slots: int = 12,
                   brief_id: str = "", class_hint: str = "",
                   taxonomy: dict | None = None,
                   now: str | None = None) -> dict:
    """把 LLM 输出补成完整 brief；规则字段在这里生成。"""
    taxonomy = taxonomy or load_taxonomy()
    parts_meta = reference_parts(taxonomy)
    request = payload.get("request")
    if not isinstance(request, dict):
        request = {}
    klass = _clean(request.get("class")) or _clean(class_hint)
    if not klass:
        raise ValueError("无法确定 request.class：用户输入里没有车型类别，也没有 --class 兜底")

    regions_meta = taxonomy.get("regions") or {}
    regions_out: list[dict] = []
    for item in _as_list(payload.get("regions")):
        if not isinstance(item, dict):
            continue
        key = _clean(item.get("region"))
        if key not in regions_meta:
            continue
        views = [v for v in _as_list(item.get("views")) if v in ALLOWED_VIEWS]
        if not views:
            views = REGION_VIEWS.get(key, ["hero_45"])
        regions_out.append({
            "region": key,
            "label": regions_meta[key].get("label") or key,
            "fields": list(regions_meta[key].get("writes") or []),
            "views": views,
            "accept": "C",
        })

    parts_out: list[dict] = []
    seen: set[str] = set()
    new_parts: list[str] = []
    for item in _as_list(payload.get("parts")):
        if not isinstance(item, dict):
            continue
        raw_key = _clean(item.get("part"))
        raw_label = _clean(item.get("label")) or raw_key
        by_label = next((k for k, v in parts_meta.items() if v == raw_label), None)
        key = raw_key if raw_key in parts_meta else (by_label or raw_key)
        known = key in parts_meta
        if not known:
            # 用户/LLM 给的是词表外的新部件：保留，不拒绝（词表不是准入）
            if not key.startswith("custom_"):
                import hashlib
                key = "custom_" + hashlib.sha1((raw_label or key).encode("utf-8")).hexdigest()[:8]
            new_parts.append(raw_label)
        if key in seen:
            continue
        seen.add(key)
        views = [v for v in _as_list(item.get("views")) if v in ALLOWED_VIEWS]
        if not views:
            views = ["hero_45"]
        rel = _clean(item.get("design_relevance")) or "conditional"
        if rel not in ("strong", "conditional", "none"):
            rel = "conditional"
        accept = _clean(item.get("accept")) or "B"
        if accept not in ("A", "B", "C"):
            accept = "B"
        axes = [a for a in _as_list(item.get("design_axes")) if a in ALLOWED_AXES]
        if not axes:
            axes = ["form_gesture"]
        parts_out.append({
            "part": key,
            "label": parts_meta[key] if known else raw_label,
            "kind": _clean(item.get("kind")) or ("part" if known else "function"),
            "location": _clean(item.get("location")),
            "part_family": _clean(item.get("part_family"))
                           or ((taxonomy.get("parts") or {}).get(key, {}) or {}).get("default_family", ""),
            "taxonomy_status": "known" if known else "new",
            "relation_axis": _clean(item.get("relation_axis")) or "exact",
            "design_axes": axes,
            "design_relevance": rel,
            "views": views,
            "accept": accept,
            "mechanism": [_clean(x) for x in _as_list(item.get("mechanism")) if _clean(x)][:3],
            "why": _clean(item.get("why")),
        })
    if not parts_out:
        raise ValueError("没有可用部件：LLM 没有返回任何 parts")

    slots = int(slots)
    if slots <= 0:
        raise ValueError("slots 必须 > 0")
    exact_quota = max(1, round(slots * 2 / 3))
    env_quota = max(0, slots - exact_quota)
    config = _clean(request.get("configuration"))
    env = _clean(request.get("environment"))
    units = [{
        "unit_id": "u-exact", "tier": "exact",
        "scope": " ".join(x for x in (klass, config) if x),
        "parts": [p["part"] for p in parts_out],
        "quota": exact_quota,
        "budget": {"max_queries": 6, "max_rounds": 2},
        "stop": f"{exact_quota} 台占满即停",
    }]
    if env_quota:
        units.append({
            "unit_id": "u-env", "tier": "environment",
            "scope": " ".join(x for x in (env or klass, "工程车") if x),
            "parts": [p["part"] for p in parts_out],
            "quota": env_quota,
            "budget": {"max_queries": 4, "max_rounds": 2},
            "stop": f"{env_quota} 台占满即停",
        })

    assumptions = [x for x in _as_list(payload.get("assumptions")) if isinstance(x, dict)]
    if new_parts:
        assumptions.append({"field": "parts.new", "value": new_parts,
                            "why": "词表外的新部件，已保留为 custom_* 并保留原词",
                            "confidence": 0.6})
    if any(not _as_list(p.get("views")) for p in payload.get("parts") or []):
        assumptions.append({"field": "views", "value": "hero_45",
                            "why": "LLM 未给合法视角，回落 hero_45",
                            "confidence": 0.5})
    assumptions.append({"field": "page_budget", "value": slots,
                        "why": f"规则：exact {exact_quota} + environment {env_quota}",
                        "confidence": 1.0})

    negative = []
    for x in _as_list(payload.get("negative")) + list(DEFAULT_NEGATIVE):
        x = _clean(x)
        if x and x not in negative:
            negative.append(x)

    created = now or time.strftime("%Y%m%d-%H%M%S")
    brief = {
        "brief_id": brief_id or f"auto-{created}",
        "request": {
            "raw": raw,
            "class": klass,
            "environment": {"value": env, "confidence": 0.8} if env else None,
            "base_platform": ({"value": _clean(request.get("base_platform")), "confidence": 0.8}
                              if _clean(request.get("base_platform")) else None),
            "configuration": config or None,
            "page_budget": {"total": 20, "vehicle_slots": slots, "part_pages": 2},
        },
        "assumptions": assumptions,
        "region_requirements": regions_out,
        "part_requirements": parts_out,
        "research_units": units,
        "tiers": ["exact"] + (["environment"] if env_quota else []),
        "budget": {"max_queries": 40, "max_rounds": 3, "max_models": slots + 2},
        "stop_rules": {"no_new_after": 3, "max_rounds": 2},
        "negative": negative,
        "strategy_ref": "default@v1",
    }
    errors = validate_brief_json(brief)
    if errors:
        raise ValueError("brief 校验失败: " + "; ".join(errors))
    return brief


def validate_brief_json(data: dict) -> list[str]:
    """契约校验 + JSON Schema 校验；返回错误列表。"""
    from .retrieval_engine.contracts import validate_brief
    import jsonschema

    errors = validate_brief(data)
    try:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"schema: {e.message}")
    except Exception as e:  # noqa: BLE001
        errors.append(f"schema load: {type(e).__name__}")
    return errors


def parse_json_response(text: str) -> dict:
    """LLM 常带 ```json 围栏/前后说明/控制字符；尽量取出第一个 JSON 对象。"""
    import json as _json
    t = (text or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t).strip()
    try:
        return _json.loads(t, strict=False)
    except _json.JSONDecodeError:
        pass
    start = t.find("{")
    if start >= 0:
        try:
            obj, _ = _json.JSONDecoder().raw_decode(t[start:])
            return obj
        except _json.JSONDecodeError:
            pass
    raise ValueError("LLM 返回非 JSON（前 200 字）: " + t[:200])


def chat(prompt: str, api_key: str, model: str = "deepseek-flash") -> dict:
    import requests

    r = requests.post("https://api.deepseek.com/chat/completions",
                      headers={"Authorization": f"Bearer {api_key}",
                               "Content-Type": "application/json"},
                      json={"model": model,
                            "messages": [{"role": "user", "content": prompt}],
                            "response_format": {"type": "json_object"},
                            "temperature": 0},
                      timeout=180)
    r.raise_for_status()
    body = r.json()
    return {
        "payload": parse_json_response(body["choices"][0]["message"]["content"]),
        "usage": body.get("usage") or {},
        "model": model,
    }


def generate_brief(raw: str, api_key: str, *, slots: int = 12, class_hint: str = "",
                   part_hints: list[str] | None = None, brief_id: str = "",
                   model: str = "deepseek-flash", taxonomy: dict | None = None,
                   chat_fn=None, use_skill: bool = True,
                   prompt_mode: str = "v2") -> dict:
    """真实调用：一次 LLM 解析；校验失败时用错误信息重试一次。"""
    taxonomy = taxonomy or load_taxonomy()
    prompt = build_prompt(raw, taxonomy, class_hint=class_hint,
                          part_hints=part_hints, use_skill=use_skill,
                          prompt_mode=prompt_mode)
    result = (chat_fn or chat)(prompt, api_key, model)
    last_error = ""
    for attempt in range(2):
        try:
            brief = assemble_brief(result["payload"], raw, slots=slots, brief_id=brief_id,
                                   class_hint=class_hint, taxonomy=taxonomy)
            return {"brief": brief, "prompt": prompt, "response": result,
                    "attempts": attempt + 1, "use_skill": use_skill,
                    "prompt_mode": prompt_mode}
        except ValueError as e:
            last_error = str(e)
            if attempt == 1:
                break
            repair = (prompt + "\n\n---\n\n上一次输出校验失败：" + last_error
                      + "\n请只修正 JSON，不要解释。")
            result = (chat_fn or chat)(repair, api_key, model)
    raise ValueError(f"brief 生成失败（已重试）: {last_error}")
