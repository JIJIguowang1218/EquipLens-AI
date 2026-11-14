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
import hashlib
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = ROOT / "skills" / "task-brief" / "SKILL.md"
SCHEMA_PATH = ROOT / "schemas" / "task-brief-v3.schema.json"
# 区域分析输出的固定字段（schema 常量，不是部件/类目词表）
ANALYSIS_FIELDS = ("gesture", "proportion", "character_lines", "cmf", "judgement")

ALLOWED_VIEWS = ("front", "hero_45", "side", "rear", "interior", "detail")
ALLOWED_AXES = ("form_gesture", "proportion", "structure", "cmf",
                "function_ergonomics", "environment_protection",
                "regulation", "manufacturing")
REGION_VIEWS = {"front_face": ["front", "hero_45"], "side": ["side", "hero_45"],
                "rear": ["rear", "side"], "roof": ["side", "hero_45"]}
DEFAULT_NEGATIVE = ("客车", "SUV", "房车", "多车拼图", "内饰", "广告")
SKILL_VERSION = "task-brief@v2"
FORMAT_ONLY_PROMPT = """你是工程车检索任务单解析器。只输出 JSON，不要解释。
字段：request{class, environment, base_platform, configuration, design_questions[]}；
regions[{region, label, views[], design_axes[]}]；
parts[{part, label, kind, location, part_family, taxonomy_status, relation_axis,
       design_axes[], views[], design_relevance, accept, mechanism[], why}]；
assumptions[{field, value, why, confidence}]；negative[]：
  **只能写不超过 6 个字的排除词**（如 客车/SUV/多车拼图/内饰/广告），
  不得写句子、规则或说明；不要写“模型/品牌/车型”这类会误伤的词。
views 只能取 front/hero_45/side/rear/interior/detail；
design_axes 只能取 form_gesture/proportion/structure/cmf/function_ergonomics/
environment_protection/regulation/manufacturing。
不要输出 page_budget/research_units/quota/tiers/budget/strategy_ref。"""


def build_prompt(raw: str, *, class_hint: str = "",
                 part_hints: list[str] | None = None,
                 use_skill: bool = True,
                 prompt_mode: str = "v2") -> str:
    """LLM 的系统提示 = skill 文件；用户提示 = 原始输入 + 约束。

    不再向模型提供任何部件/类目词表（2026-11-14 口径：词表不得进入主体代码）。
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
    hints = {
        "raw": raw,
        "class_hint": class_hint,
        "part_hints": part_hints or [],
        "no_vocabulary_note": "不要引用任何部件/类目词表；只按用户原话写 label 与 part",
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


def _part_slug(label: str) -> str:
    """词表外部件 → 可读 key 片段（保留中文/字母/数字，截断 16 字）。"""
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", label or "").strip("_")[:16]
    if s:
        return s
    return hashlib.sha1((label or "").encode("utf-8")).hexdigest()[:8]


def assemble_brief(payload: dict, raw: str, *, slots: int = 12,
                   brief_id: str = "", class_hint: str = "",
                   now: str | None = None) -> dict:
    """把 LLM 输出补成完整 brief；规则字段在这里生成。

    不读取任何部件/类目词表（2026-11-14）：part 若是 ascii snake 键就保留，
    否则用可读的 `custom_<slug>`；label 永远保留原词。
    """
    request = payload.get("request")
    if not isinstance(request, dict):
        request = {}
    klass = _clean(request.get("class")) or _clean(class_hint)
    if not klass:
        raise ValueError("无法确定 request.class：用户输入里没有车型类别，也没有 --class 兜底")

    regions_out: list[dict] = []
    seen_regions: set[str] = set()
    for item in _as_list(payload.get("regions")):
        if not isinstance(item, dict):
            continue
        key = _clean(item.get("region"))
        if not key or key in seen_regions:
            continue
        seen_regions.add(key)
        views = [v for v in _as_list(item.get("views")) if v in ALLOWED_VIEWS]
        if not views:
            views = REGION_VIEWS.get(key, ["hero_45"])
        fields = [f for f in _as_list(item.get("fields")) if f in ANALYSIS_FIELDS]
        regions_out.append({
            "region": key,
            "label": _clean(item.get("label")) or key,
            "fields": fields or list(ANALYSIS_FIELDS),
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
        if not raw_key and not raw_label:
            continue
        # 只认“写法”，不查词表：ascii snake 键保留，其余从 label 派生可读 key
        if raw_key.startswith("custom_"):
            key, known = raw_key, False
        elif re.fullmatch(r"[a-z][a-z0-9_]*", raw_key or ""):
            key, known = raw_key, True
        else:
            key, known = "custom_" + _part_slug(raw_label or raw_key), False
            new_parts.append(raw_label or raw_key)
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
            "label": raw_label or key,
            "kind": _clean(item.get("kind")) or "part",
            "location": _clean(item.get("location")),
            "part_family": _clean(item.get("part_family")),
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
                            "why": "未使用词表；未知部件保留为可读 custom_* 并保留原词",
                            "confidence": 0.6})
    if any(not _as_list(p.get("views")) for p in payload.get("parts") or []):
        assumptions.append({"field": "views", "value": "hero_45",
                            "why": "LLM 未给合法视角，回落 hero_45",
                            "confidence": 0.5})
    assumptions.append({"field": "page_budget", "value": slots,
                        "why": f"规则：exact {exact_quota} + environment {env_quota}",
                        "confidence": 1.0})

    # negative 只允许短排除词：LLM 容易写成整句规则，拼进 query 会让搜索 0 结果
    from .planning import negative_terms as _neg_terms
    negative: list[str] = []
    for x in list(_as_list(payload.get("negative"))) + list(DEFAULT_NEGATIVE):
        for t in _neg_terms({"negative": [x]}):
            if t not in negative:
                negative.append(t)

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
                   model: str = "deepseek-flash",
                   chat_fn=None, use_skill: bool = True,
                   prompt_mode: str = "v2") -> dict:
    """真实调用：一次 LLM 解析；校验失败时用错误信息重试一次。"""
    prompt = build_prompt(raw, class_hint=class_hint,
                          part_hints=part_hints, use_skill=use_skill,
                          prompt_mode=prompt_mode)
    result = (chat_fn or chat)(prompt, api_key, model)
    last_error = ""
    for attempt in range(2):
        try:
            brief = assemble_brief(result["payload"], raw, slots=slots, brief_id=brief_id,
                                   class_hint=class_hint)
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
