# -*- coding: utf-8 -*-
"""LLM 抽取 TaskSpec（S0-01，生产路径）。

只负责“文本 → 原始 TaskSpec”；规范化/校验在 `taskspec.py`。S0 的正式链路：
`taskspec_llm.parse` → `taskspec.normalize/validate` → `briefing.apply_taskspec`。
旧的一次性 brief 解析仍保留，但只能显式 `--legacy-brief` 触发（静默下线）。
"""
from __future__ import annotations

import json

from . import taskspec

MODEL = "deepseek-flash"

PROMPT = """你是工程车辆设计调研的任务解析器。把用户输入解析成 TaskSpec JSON（只输出 JSON）。

硬规则：
R1 只写输入/上下文里有的；没有就 null/空数组；禁止编造。
R2 class 纯类目；同义归一（沙漠车→沙漠牵引车，随车吊→随车起重运输车，铲车→装载机，
   翻斗车→自卸车）；原词放 class_raw，别名放 class_aliases。
R3 environment 放工况；configuration 放驱动形式（6x6/4x2/8x4/四轮）。
R4 intent：new_task|modify|question；“上次/这批/再加/换掉/改成”=modify；modify 用 quantity.delta，primary=null。
R5 三分，严禁混：
   - “再加/再补 N 台（同型号/同类）” → quantity.delta=N；
   - “备选/备用/备份 N 台” → quantity.backup=N；
   - “参考/同类/对比（N 台）” → scope={mode:"mixed",adjacent:N}；不得进 backup/delta。
R6 硬约束只放这些枚举：quantity, class, brands_include, brands_exclude, models_pinned,
   constraints.exclude, constraints.origin, constraints.powertrain, configuration, environment。
   views/quality/year/tonnage/price/soft_brands/foreign_ratio/brand_quota 只能出现在 soft，
   禁止进 hard。policy.hard/soft 的值必须是上述枚举之一，禁止自由词。
R7 “必须/一定要/只要/至少” → 硬；“最好/希望/优先/有…更好” → soft（preferences.soft_brands）。
R8 品牌配额：输入“至少 N 台 + 品牌A 或 品牌B + 总数M” → preferences.brand_quota=
   {"brands":["A","B"],"min":N,"of":M}；不用提问，不要塞进 foreign_ratio。
R9 foreign_ratio 只在明确比例/台数时给 {min,max}；“你定/看着办” → unknown severity=defaultable，
   proposal 给建议值；纯模糊 → informational。
R10 输入提到“拍的图/截图/型号牌上写着…” → models_provided（image=true），即使未附文件；
    上下文里的车型不要写进 models_provided/models_pinned。
    部件词（前脸格栅/保险杠/吊臂/支腿/踏步/灯具/后视镜/罐体/料斗/机罩/配重/护栏…）放 parts；
    preferences.views 只放 front/45/side/rear/roof。严禁把“前脸格栅”写成 views=front。
R11 “国产/进口” → constraints.origin（domestic/import）；“电动/柴油” → constraints.powertrain；
    两者是硬约束（用户说“必须/只要”时）。
R12 未知项分级：blocking（缺了无法执行）/defaultable（可给默认）/informational；
    questions 最多 1 条，只在 blocking 时给，2–4 个选项 + default。
    类目缺失且输入/上下文没有明确类目 → 必须 blocking + 1 个问题，不得用 defaultable 猜类目。
R13 有 session context 且用户说“上次/这批/再加/换掉” → 使用上下文，session_context_used=true；
    上下文里有的车型/数量不要写 unknown。“同类参考”且有上下文类目 → scope.adjacent；
    无上下文且“加”与“参考”都出现、无法判定 → 1 个 blocking 问题（同型号再加/邻近类目参考）。
R14 evidence 每项给原文依据（逐字可找），找不到留空。

输出结构（严格键名）：
{"intent":"","class":"","class_raw":"","class_aliases":[],"environment":"","configuration":"",
 "quantity":{"primary":null,"backup":null,"delta":null},
 "brands_include":[],"brands_exclude":[],
 "preferences":{"soft_brands":[],"brand_quota":null,"foreign_ratio":null,"views":[],"quality":[],
   "year":null,"tonnage":null,"price":null},
 "models_pinned":[],"models_provided":[],"parts":[],
 "constraints":{"exclude":[],"origin":null,"powertrain":null,"min_width":null},
 "scope":null,"delivery":null,
 "policy":{"hard":[],"soft":[]},
 "unknowns":[{"field":"","text":"","severity":"blocking|defaultable|informational","proposal":""}],
 "assumptions":[],"questions":[{"id":"q1","question":"","options":[""],"default":""}],
 "session_context_used":false,
 "evidence":{"class":"","environment":"","configuration":"","quantity":"","brands":"","models":"","constraints":"","scope":""}}
"""


def build_prompt(text: str, context: dict | None = None) -> str:
    ctx = json.dumps(context, ensure_ascii=False) if context else "（无）"
    return PROMPT + f"\n\nsession context：{ctx}\n\n用户输入：\n{text}\n"


def parse(text: str, api_key: str, *, context: dict | None = None,
          model: str = MODEL, chat_fn=None) -> dict:
    """文本 → 规范化 TaskSpec；校验不过直接抛 ValueError（由调用方重试/报错）。"""
    from .briefing import chat  # 延迟导入，避免循环

    prompt = build_prompt(text, context)
    result = (chat_fn or chat)(prompt, api_key, model)
    spec = taskspec.normalize(result.get("payload") or {})
    issues = taskspec.validate(spec)
    if issues:
        raise ValueError("TaskSpec 校验失败: " + "; ".join(issues[:3]))
    return spec
