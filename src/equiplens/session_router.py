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
    "plan.quantity": "改总交付台数/总量",
    "plan.quantity_per_model": "把每个车型的图片数量补到 N 张（条件扩张）",
    "plan.configuration": "改驱动/构型（6x6/4x2/8x4 等）",
    "session.reset": "整批重来/重新选（重大调整）",
    "delivered.remove": "从交付中移除某张/某型号（降级，不物理删除）",
    "delivered.replace": "替换已交付的某张图",
    "delivery.report": "生成/更新报告或 PPT 交付物（不改检索）",
    "session.pause": "暂停当前 run",
    "session.resume": "继续/恢复",
}

PROMPT = """你是工程车辆检索会话的“修改动作分类器”。用户会对当前任务追加一句话要求。
只输出 JSON：
{"hard":bool,"targets":[...],"destructive":bool,"confirm":bool,"enforce":"hard|soft",
 "confidence":0.0,"evidence":"","reason":"","asset_index":null,
 "values":{"<target>":{...}}}

判定规则：
1) hard=true 只用于改变任务定义：范围/类目（scope.ratio）、数量（plan.quantity）、
   构型（plan.configuration）、整批重置（session.reset）、暂停（session.pause）；
2) 排除项（plan.negative）是**硬约束**（enforce=hard），但 hard=false（不重排）；
3) 视角/质量/部件/加图/加品牌/纠错 → hard=false；
4) 数量四义必须分清：
   - 总量（总共/一共/总数/数量改成或调到 N、凑够 N）→ plan.quantity（hard）；
   - 每款/每个车型/每台 + 张数（统一6张、从4调到6）→ plan.quantity_per_model（soft）；
   - 同一台车/同款/这个型号要更多图（无总数）→ fill.quota；
   - 其他“再加/再补 N 台” → plan.quantity；
   “只要/仅限 + 类目/环境” → scope.ratio（hard），不是 plan.negative；
5) destructive=true 只用于“删/换**已交付**内容”；
   - 文本明确“第 N 张”或具体型号码 → confirm=false（直接降级，不删除）；
   - 目标不明确（“删掉一张”“换掉那个”）→ confirm=true（先问）；
6) “全部/全都/整批 + 重来/换” → session.reset, hard=true, destructive=true, confirm=true；
7) targets 只能从下面的动作里选；**一句话有多个独立动作时必须分别列出（最多 3 个，按执行顺序）**，
   不要合并成一个；无法判断就空数组；
   复合示例：“驾驶室要高顶的，平顶的不要” → plan.negative + plan.configuration；
   “杰狮那台多弄几张，顺便总数改成12张” → fill.quota + plan.quantity；
   “再加个徐工，顺便图也多来几张” → plan.add_targets + fill.quota；
8) evidence 必须引用用户原话片段；confidence 0–1。
9) values 可选，给出该 target 的结构化值：fetch.filters.views={"views":["front"|"side"|"45"|"rear"|"roof"]}；
   fetch.filters.quality={"min_width":1200} 或 {"no_watermark":true}；fetch.parts={"parts":["格栅"]}；
   plan.negative={"terms":["北奔"]}；plan.add_targets={"models":["HOWO TX"]}；
   fill.quota={"count":2}；plan.quantity_per_model={"count":6}；
   plan.quantity={"primary":12}；plan.configuration={"value":"8x8"}。
   注意：配置/构型/高顶/平顶/双备胎/涉水喉/驱动 → plan.configuration；
   只有“要格栅/大灯/保险杠等部件的细节图/特写”才是 fetch.parts。

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
    ("每个车型统一按6张来", "plan.quantity_per_model", False, False, False, True),
    ("驾驶室要高顶的，平顶的不要", "plan.negative+plan.configuration", False, False, False, True),
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
            model: str = "deepseek-flash", chat_fn=None, retries: int = 3) -> dict:
    """LLM 提议；网络抖动重试（2026-11-16 实测 httpx.RemoteProtocolError 中断过 loop）。"""
    import time as _time
    from .briefing import chat
    fn = chat_fn or chat
    last = None
    for i in range(max(1, retries)):
        try:
            res = fn(build_prompt(text, context), api_key, model)
            return res.get("payload") or {}
        except Exception as e:  # noqa: BLE001
            last = e
            if i < retries - 1:
                _time.sleep(1.5 * (i + 1))
    raise last


CAPABILITIES = [
    ("remove_watermark", r"水印", "unsupported",
     "去水印/保证无水印暂不支持；可以帮你换一张来源没有水印的图。",
     {"fetch.filters.quality"}),
    ("print_export", r"印刷|打印|DPI|dpi|别压缩|不压缩", "unsupported",
     "印刷级/不压缩导出暂不支持；可以导出原图供你自行处理。",
     {"fetch.filters.quality", "delivery.report"}),
    ("scene_filter", r"车展|工地.{0,6}(实拍|干活|真实)|拍摄场景", "unsupported",
     "按拍摄场景（车展/工地）筛选暂不支持；可以按型号/品牌帮你换图。",
     {"plan.negative", "fetch.filters.quality", "scope.ratio"}),
    ("weather_filter", r"阴天|雨天|天气", "unsupported",
     "按天气筛选暂不支持。", {"plan.negative", "fetch.filters.quality"}),
    ("uncropped", r"原图|未裁|别裁|裁过", "unsupported",
     "保证未裁切/原图暂不支持；可以换一张来源图。", {"fetch.filters.quality"}),
    ("layout_default", r"每款(两|2)页|每台(车)?.*两页|加(个)?封面|换(个)?目录|目录样式|带缩略图",
     "unsupported", "默认一车一页；版式超出默认暂不支持。",
     {"delivery.report", "plan.quantity_per_model"}),
    ("weekly_report", r"周报|日报|月报", "out_of_domain",
     "我只做工程车图检索与交付，不写周报/日报。", {"delivery.report"}),
]


UI_GUIDE = [
    (r"导出.*PPT|PPT.*(导出|在哪|怎么)|导(个|出)?PDF|格式按钮|交付格式|导出按钮",
     "交付格式在界面右上角「导出」里选 PPT/PDF/报告；当前页可直接切换格式预览。"),
    (r"保存.*方案|分享.*同事|重新跑一次|历史记录.*(哪|怎么)",
     "保存/分享/重跑/历史记录在右上角「更多」菜单；重跑会新建一次会话。"),
]


def _ui_guide(text: str):
    for pat, msg in UI_GUIDE:
        if re.search(pat, text):
            return msg
    return None


def _capability(text: str):
    for cid, pat, feas, msg, drop in CAPABILITIES:
        if re.search(pat, text):
            return cid, feas, msg, drop
    return None


def _count(text: str) -> int | None:
    cn = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
          "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    m = re.search(r"(\d+)\s*张", text)
    if m:
        return int(m.group(1))
    m = re.search(r"([一二两三四五六七八九十])\s*张", text)
    return cn.get(m.group(1)) if m else None


def _clarify_for(text: str):
    if any(k in text for k in ("删", "换掉", "重来", "重做")):
        return ("你指哪一张/哪一批？", ["指出第几张（如“第3张”）", "整批重来", "先不操作"])
    if any(k in text for k in ("数量", "台", "张")):
        return ("数量怎么改？", ["同一台车多几张", "改总数量", "每款补到 N 张", "先不操作"])
    return ("你想改哪一部分？", ["改数量", "改视角", "排除品牌/车型", "换图或出报告", "先不操作"])


def _clear_target(text: str) -> bool:
    return bool(re.search(r"第\s*[一二三四五六七八九十\d]+\s*张", text)) or bool(re.search(r"[A-Za-z]{2,}\d{2,}", text))


def guard(text: str, proposal: dict, context: dict | None = None) -> dict:
    """确定性守卫：能力/阶段门 → 白名单/数量语义 → destructive 确认 → 歧义提问。"""
    out = {"intent": "modify", "hard": False, "targets": [], "destructive": False,
           "confirm": False, "enforce": "soft", "confidence": 0.7, "clarify": False,
           "evidence": "", "reason": "", "feasibility": "supported",
           "message": "", "action": "apply", "stage": (context or {}).get("stage") or ""}
    if not isinstance(proposal, dict):
        return out
    targets = [t for t in (proposal.get("targets") or []) if t in ALLOWED_TARGETS]
    # 去重、最多 3 个；超出视为歧义
    seen, uniq = set(), []
    for t in targets:
        if t not in seen:
            seen.add(t)
            uniq.append(t)
    too_many = len(uniq) > 3
    out["targets"] = uniq[:3]
    out["confidence"] = float(proposal.get("confidence") or 0.0)
    try:
        out["asset_index"] = int(proposal.get("asset_index")) if proposal.get("asset_index") else None
    except (TypeError, ValueError):
        out["asset_index"] = None
    out["evidence"] = str(proposal.get("evidence") or "")[:120]
    try:
        out["asset_index"] = int(proposal.get("asset_index")) if proposal.get("asset_index") else None
    except (TypeError, ValueError):
        out["asset_index"] = None
    out["reason"] = str(proposal.get("reason") or "")[:160]
    vals = proposal.get("values") if isinstance(proposal.get("values"), dict) else {}
    out["values"] = {k: v for k, v in vals.items()
                     if k in ALLOWED_TARGETS and isinstance(v, dict)}
    # UI 引导：界面已有功能（导出/格式/保存/分享/重跑），回答在哪操作，不产 patch
    guide_msg = _ui_guide(text)
    if guide_msg:
        out.update({"targets": [], "clarify": False, "action": "guide",
                    "feasibility": "supported", "message": guide_msg})
        return out
    # 能力门：明确做不到/越界的，不伪装成动作
    cap = _capability(text)
    if cap:
        cid, feas, msg, drop = cap
        remaining = [t for t in out["targets"] if t not in drop]
        if remaining:
            out["targets"] = remaining
            out["feasibility"] = "partial"
            out["message"] = msg
            out["capability"] = cid
        else:
            out.update({"targets": [], "clarify": False, "action": "explain",
                        "feasibility": feas, "message": msg, "capability": cid,
                        "hard": False, "destructive": False, "confirm": False})
            return out
    # 阶段门：还没有交付图时，不允许资产级动作
    stage = (context or {}).get("stage") or ""
    if stage in ("pre_run", "running"):
        blocked = {"delivered.remove", "delivered.replace", "verify.blacklist", "fill.replace"}
        hit = [t for t in out["targets"] if t in blocked]
        if hit:
            out["targets"] = [t for t in out["targets"] if t not in blocked]
            out["stage_blocked"] = hit
            out["message"] = "还没有交付图；等交付后再换/删。"
            if not out["targets"]:
                out.update({"clarify": True, "action": "clarify",
                            "question": "还没有交付图；等交付后再换/删。",
                            "options": ["等交付后再改", "先不操作"]})
                return out
    uniq = out["targets"]

    if too_many:
        out["clarify"] = True
        out["targets"] = uniq[:3]
        return out
    if not uniq:
        out["clarify"] = True
        out["action"] = "clarify"
        q, opts = _clarify_for(text)
        out["question"] = q
        out["options"] = opts
        return out

    hard_targets = [t for t in out["targets"] if t in HARD_TARGETS]
    out["hard"] = bool(proposal.get("hard")) or bool(hard_targets)
    if any(t in ("scope.ratio", "plan.quantity", "plan.configuration", "session.reset")
           for t in out["targets"]):
        out["hard"] = True
    if "session.pause" in out["targets"]:
        out["hard"] = True

    # 构型/配置 vs 部件：有配置词且不是“部件细节图”时，纠正成 plan.configuration
    config_kw = any(k in text for k in ("配置", "构型", "驱动", "6x6", "8x8", "4x2",
                                        "双备胎", "涉水喉", "高顶", "平顶", "国六", "国五",
                                        "电动", "左舵", "右舵", "寒区", "爬梯", "排放", "动力"))
    part_kw = any(k in text for k in ("细节图", "特写", "部件图"))
    image_edit = _clear_target(text) and any(
        k in text for k in ("这张", "不能进", "别用", "不是", "另一款", "别家", "认错"))
    if (config_kw and not part_kw and "plan.configuration" not in out["targets"]
            and not image_edit):
        if "fetch.parts" in out["targets"]:
            out["targets"] = [("plan.configuration" if t == "fetch.parts" else t)
                              for t in out["targets"]]
            out["hard"] = True
            out["enforce"] = "hard"
        elif "plan.negative" in out["targets"]:
            out["targets"] = list(dict.fromkeys(out["targets"] + ["plan.configuration"]))
            out["hard"] = True
            out["enforce"] = "hard"

    # 数量四义：总量 / 每款张数 / 同车补图 / 条件扩张
    per_model = any(k in text for k in ("每款", "每个车型", "每台", "各车型", "每种"))
    same_vehicle = (any(k in text for k in ("同款", "这台", "那台", "这个车型", "该车",
                                            "这个型号", "这型号", "这个款", "这款", "这个车",
                                            "这辆车", "这车", "这辆", "这几张", "就这几张",
                                            "该型号", "内饰", "它"))
                    or bool(re.search(r"[A-Za-z]{1,}\d|\d+[A-Za-z]", text)))
    total_cue = bool(re.search(
        r"(总共|一共|总数|总量|合计|凑(够|到)?|要\s*\d+\s*张|数量.{0,4}(改|调|到))", text))
    add_cue = any(k in text for k in ("再加", "再补", "再来", "多来", "多给", "多弄",
                                      "加两", "加几", "凑"))
    if per_model:
        conv = [("plan.quantity_per_model" if t in ("plan.quantity", "fill.quota") else t)
                for t in out["targets"]]
        out["targets"] = list(dict.fromkeys(conv))
        out["hard"] = False
        out["enforce"] = "soft"
        if ("plan.quantity_per_model" in out["targets"]
                and not out["values"].get("plan.quantity_per_model")):
            n = _count(text)
            if n:
                out["values"]["plan.quantity_per_model"] = {"count": n}
    elif total_cue or (add_cue and not same_vehicle):
        conv = [("plan.quantity" if t == "fill.quota" else t) for t in out["targets"]]
        out["targets"] = list(dict.fromkeys(conv))
        if "plan.quantity" in out["targets"]:
            out["hard"] = True
            out["enforce"] = "hard"
            if not out["values"].get("plan.quantity") and _count(text):
                out["values"]["plan.quantity"] = {"primary": _count(text)}
    elif same_vehicle and add_cue and "plan.quantity" in out["targets"]:
        conv = [("fill.quota" if t == "plan.quantity" else t) for t in out["targets"]]
        out["targets"] = list(dict.fromkeys(conv))
        out["hard"] = False
        out["enforce"] = "soft"
    if ("fill.quota" in out["targets"] and not same_vehicle
            and not (context or {}).get("last_model") and not re.search(r"\d", text)):
        out["clarify"] = True
        out["action"] = "clarify"
        out["question"] = "你是要同一台车多几张，还是总数改？"
        out["options"] = ["同一台车多几张", "改总数量", "先不操作"]
    if image_edit and "plan.configuration" in out["targets"]:
        out["targets"] = [t for t in out["targets"] if t != "plan.configuration"]
        if not any(t in ("delivered.remove", "delivered.replace", "verify.blacklist")
                   for t in out["targets"]):
            out["targets"] = list(dict.fromkeys(out["targets"] + ["verify.blacklist"]))
    # 报告里的“每款一张图”是交付格式，不是 per-model 数量
    report_cue = any(k in text for k in ("报告", "PPT", "ppt", "导出", "页面"))
    if report_cue and "plan.quantity_per_model" in out["targets"]:
        out["targets"] = [("delivery.report" if t == "plan.quantity_per_model" else t)
                          for t in out["targets"]]
        out["targets"] = list(dict.fromkeys(out["targets"]))
        out["hard"] = False
        out["enforce"] = "soft"
    # 配置词命中 scope（如“只要国六”）→ 构型配置，不是范围比例
    if "scope.ratio" in out["targets"] and config_kw and not part_kw:
        out["targets"] = [("plan.configuration" if t == "scope.ratio" else t)
                          for t in out["targets"]]
        out["hard"] = True
        out["enforce"] = "hard"
    # 身份错：明确第 N 张 + “不是/别家/认错/不能用” → blacklist，不是普通 remove
    if ("delivered.remove" in out["targets"] and _clear_target(text)
            and any(k in text for k in ("不是", "别家", "认错", "不能用", "不能进", "另一款", "别的车"))):
        out["targets"] = [("verify.blacklist" if t == "delivered.remove" else t)
                          for t in out["targets"]]
    # 画质类表述 + 误判成排除项 → 画质
    if ("plan.negative" in out["targets"]
            and any(k in text for k in ("糊", "清晰", "反光", "分辨率", "灰扑扑", "画质", "翻拍"))
            and not any(k in text for k in ("品牌", "车系", "日系", "进口", "国产"))):
        out["targets"] = [("fetch.filters.quality" if t == "plan.negative" else t)
                          for t in out["targets"]]
        out["enforce"] = "hard"
    # 内饰/车内视角：不是部件细节图
    if ("fetch.parts" in out["targets"]
            and any(k in text for k in ("驾驶室里面", "车内", "内饰"))
            and not any(k in text for k in ("细节图", "特写"))):
        out["targets"] = [("fetch.filters.views" if t == "fetch.parts" else t)
                          for t in out["targets"]]

    # 复合：范围收窄 + “不要” → 同时排除
    if "scope.ratio" in out["targets"] and "plan.negative" not in out["targets"]             and any(k in text for k in ("不要", "排除", "去掉")):
        out["targets"] = list(dict.fromkeys(out["targets"] + ["plan.negative"]))
        out["enforce"] = "hard"
    # 复合：加品牌 + “图也多来几张” → 给新 target 补图，不改总数
    if ("plan.add_targets" in out["targets"] and "plan.quantity" in out["targets"]
            and add_cue and "图" in text and not total_cue):
        out["targets"] = [("fill.quota" if t == "plan.quantity" else t)
                          for t in out["targets"]]
        out["hard"] = False
        out["enforce"] = "soft"
    # 复合：同车补图 + 总数（“顺便/同时”）→ 两个动作都保留
    if (same_vehicle and add_cue and total_cue
            and any(k in text for k in ("顺便", "同时", "另外"))
            and "plan.quantity" in out["targets"]
            and "fill.quota" not in out["targets"]):
        out["targets"] = list(dict.fromkeys(out["targets"] + ["fill.quota"]))
        out["hard"] = True
        out["enforce"] = "hard"

    # 排除项：约束硬、打断软
    if "plan.negative" in out["targets"]:
        out["enforce"] = "hard"
        if not hard_targets:
            out["hard"] = False

    # 画质类表述（高清/水印/清晰度）不是删除/替换：去掉误判的交付编辑
    if (any(k in text for k in ("高清", "水印", "清晰", "分辨率"))
            and not any(k in text for k in ("删", "去掉第", "换掉第"))
            and not (_clear_target(text) and any(k in text for k in ("换", "替换")))):
        out["targets"] = [t for t in out["targets"] if t not in DESTRUCTIVE_TARGETS]

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
        out["action"] = "clarify"
        out["question"] = "你指哪一张/哪一批？"
        out["options"] = ["指出第几张（如“第3张”）", "整批重来", "先不操作"]

    # 低置信 / 硬冲突 → 提问
    if out["confidence"] and out["confidence"] < 0.55:
        out["clarify"] = True
        out["action"] = "clarify"
        q, opts = _clarify_for(text)
        out.setdefault("question", q)
        out.setdefault("options", opts)
    if out["hard"] and out["destructive"] and "session.reset" not in out["targets"]:
        out["confirm"] = True
    return out


def make_router(api_key: str, *, model: str = "deepseek-flash", chat_fn=None):
    """生产入口：返回 Session 可直接注入的 router(text, context)。"""
    def _router(text: str, context: dict | None = None) -> dict:
        return classify(text, context=context, api_key=api_key, model=model, chat_fn=chat_fn)
    return _router


def classify(text: str, *, context: dict | None = None, api_key: str = "",
             model: str = "deepseek-flash", chat_fn=None, rules_fallback: bool = True,
             stage: str | None = None) -> dict:
    """LLM 提议 + 守卫；无 key/失败时回退规则版。"""
    ctx = dict(context or {})
    if stage:
        ctx["stage"] = stage
    if api_key or chat_fn:
        try:
            return guard(text, propose(text, ctx, api_key, model=model, chat_fn=chat_fn),
                         context=ctx)
        except Exception:  # noqa: BLE001
            if not rules_fallback:
                raise
    return classify_text(text)
