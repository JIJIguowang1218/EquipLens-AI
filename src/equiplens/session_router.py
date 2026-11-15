# -*- coding: utf-8 -*-
"""S0-05 Session Router：LLM 提议 + 规则守卫（M3）。

四层：LLM 语义提议 → context digest → 确定性守卫 → 歧义提问。
不写领域同义词表；targets 只取动作 schema（见 ACTIONS）。
"""
from __future__ import annotations

import json
import re

from .session import ALLOWED_TARGETS, DESTRUCTIVE_TARGETS, HARD_TARGETS, classify_text

ACTIONS = {
    "fetch.filters.views": "换/加拍摄角度（正脸、侧面、45 度、车尾、顶部）",
    "fetch.filters.quality": "清晰度/水印/分辨率要求",
    "fetch.parts": "指定部件细节（格栅、保险杠、吊臂、支腿、踏步等）",
    "fill.quota": "给**现有型号/现有 target** 加图或加数量",
    "plan.add_targets": "增加**新品牌/新车型/新车系**到检索范围",
    "plan.negative": "排除品牌/挂车/内饰/配件等（硬约束）",
    "verify.blacklist": "单张图/单个资产判错，标黑名单",
    "fill.replace": "用新图替换错误图",
    "scope.ratio": "改精确/邻近比例或任务范围",
    "plan.quantity": "改总交付台数",
    "plan.configuration": "改驱动/构型（6x6/4x2/8x4 等）",
    "session.reset": "整批重来/重新选（重大调整）",
    "delivered.remove": "从交付中移除某张/某型号（降级，不物理删除）",
    "delivered.replace": "替换已交付的某张图",
    "session.pause": "暂停当前 run",
    "session.resume": "继续/恢复",
}

PROMPT = """你是工程车辆检索会话的“修改动作分类器”。用户会对当前任务追加一句话要求。
只输出 JSON：
{"hard":bool,"targets":[...],"destructive":bool,"confirm":bool,"enforce":"hard|soft",
 "confidence":0.0,"evidence":"","reason":""}

判定规则：
1) hard=true 只用于改变任务定义：范围/类目（scope.ratio）、数量（plan.quantity）、
   构型（plan.configuration）、整批重置（session.reset）、暂停（session.pause）；
2) 排除项（plan.negative）是**硬约束**（enforce=hard），但 hard=false（不重排）；
3) 视角/质量/部件/加图/加品牌/纠错 → hard=false；
4) “只要/仅限 + 类目/环境” → scope.ratio（hard），不是 plan.negative；
   “再加/再补 N 台”（未说“数量/总量”）→ plan.quantity（hard）；只有“同款/这个型号再来 N 张”才是 fill.quota；
5) destructive=true 只用于“删/换**已交付**内容”；
   - 文本明确“第 N 张”或具体型号码 → confirm=false（直接降级，不删除）；
   - 目标不明确（“删掉一张”“换掉那个”）→ confirm=true（先问）；
6) “全部/全都/整批 + 重来/换” → session.reset, hard=true, destructive=true, confirm=true；
7) targets 只能从下面的动作里选（可多选，最多 3 个）；无法判断就空数组；
8) evidence 必须引用用户原话片段；confidence 0–1。

动作定义：
{actions}

会话上下文（可能为空）：
{context}

用户这句话：
{text}
"""

EXAMPLES = [
    ("全要正面", "fetch.filters.views", False, False, False, False),
    ("同款再来三张", "fill.quota", False, False, False, False),
    ("把重汽加进来", "plan.add_targets", False, False, False, False),
    ("不要挂车，不要内饰", "plan.negative", False, False, False, True),
    ("数量加到 14 台", "plan.quantity", True, False, False, True),
    ("只要沙漠版，别的都不要", "scope.ratio", True, False, False, True),
    ("删掉第 2 张", "delivered.remove", False, True, False, True),
    ("删掉一张", "delivered.remove", False, True, True, True),
    ("全部重来", "session.reset", True, True, True, True),
]


def build_prompt(text: str, context: dict | None) -> str:
    ex = "\n".join(
        f"- “{t}” → target={a}, hard={h}, destructive={d}, confirm={c}, enforce={'hard' if e else 'soft'}"
        for t, a, h, d, c, e in EXAMPLES)
    return (PROMPT.replace("{actions}", json.dumps(ACTIONS, ensure_ascii=False, indent=1))
            .replace("{context}", json.dumps(context or {}, ensure_ascii=False))
            .replace("{text}", text)
            + "\n\n参考示例（只学语义，不要照抄 target 之外的内容）：\n" + ex)


def propose(text: str, context: dict | None, api_key: str, *,
            model: str = "deepseek-flash", chat_fn=None) -> dict:
    from .briefing import chat
    res = (chat_fn or chat)(build_prompt(text, context), api_key, model)
    return res.get("payload") or {}


def _clear_target(text: str) -> bool:
    return bool(re.search(r"第\s*\d+\s*张", text)) or bool(re.search(r"[A-Za-z]{2,}\d{2,}", text))


def guard(text: str, proposal: dict) -> dict:
    """确定性守卫：白名单、hard/enforce 强制、destructive 确认、歧义提问。"""
    out = {"intent": "modify", "hard": False, "targets": [], "destructive": False,
           "confirm": False, "enforce": "soft", "confidence": 0.7, "clarify": False,
           "evidence": "", "reason": ""}
    if not isinstance(proposal, dict):
        return out
    targets = [t for t in (proposal.get("targets") or []) if t in ALLOWED_TARGETS]
    # 去重、最多 3 个；超出视为歧义
    seen, uniq = set(), []
    for t in targets:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    out["targets"] = uniq[:3]
    out["confidence"] = float(proposal.get("confidence") or 0.0)
    out["evidence"] = str(proposal.get("evidence") or "")[:120]
    out["reason"] = str(proposal.get("reason") or "")[:160]
    if len(uniq) > 3:
        out["clarify"] = True
        out["targets"] = uniq[:3]
        return out
    if not uniq:
        out["clarify"] = True
        return out

    hard_targets = [t for t in out["targets"] if t in HARD_TARGETS]
    out["hard"] = bool(proposal.get("hard")) or bool(hard_targets)
    if any(t in ("scope.ratio", "plan.quantity", "plan.configuration", "session.reset")
           for t in out["targets"]):
        out["hard"] = True
    if "session.pause" in out["targets"]:
        out["hard"] = True

    # 排除项：约束硬、打断软
    if "plan.negative" in out["targets"]:
        out["enforce"] = "hard"
        if not hard_targets:
            out["hard"] = False

    # 交付编辑
    dest = [t for t in out["targets"] if t in DESTRUCTIVE_TARGETS]
    if dest:
        out["destructive"] = True
        out["hard"] = False
        out["enforce"] = "hard"
        out["confirm"] = not _clear_target(text)
        if "session.reset" in dest:
            out["hard"] = True
            out["confirm"] = True
    else:
        out["destructive"] = False
        out["confirm"] = False

    # 文本有“删/换/重来”但模型没给交付动作 → 保守提问
    if not dest and any(k in text for k in ("删", "换掉", "重来", "重做")):
        out["clarify"] = True

    # 低置信 / 硬冲突 → 提问
    if out["confidence"] and out["confidence"] < 0.55:
        out["clarify"] = True
    if out["hard"] and out["destructive"] and "session.reset" not in out["targets"]:
        out["confirm"] = True
    return out


def classify(text: str, *, context: dict | None = None, api_key: str = "",
             model: str = "deepseek-flash", chat_fn=None, rules_fallback: bool = True) -> dict:
    """LLM 提议 + 守卫；无 key/失败时回退规则版。"""
    if api_key or chat_fn:
        try:
            return guard(text, propose(text, context, api_key, model=model, chat_fn=chat_fn))
        except Exception:  # noqa: BLE001
            if not rules_fallback:
                raise
    return classify_text(text)
