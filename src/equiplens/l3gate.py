"""L3 确定性闸门：对象锚定 + 主题类型排除 + 具体性要求。

背景：T18-roster 实测关键词打分 A 档假阳性 40.4%（与 L3 v1 的 43% 一致）。
本模块把"是否值得进入模型判定"形式化为可复现规则：

1. 主题类型排除：毕设/竞赛/代做/经销商/报价/批发/促销/招聘——直接拒绝；
2. 报价配置行：`2024款 … 长轴 高顶 厢货 2座`——直接拒绝（复用 passage.CONFIG_LINE_RE）；
3. 具体性要求：至少 1 个部件词，或 ≥2 个形态/CMF 词；且至少 1 个设计语汇；
   零具体证据的营销话术（"颜值高、大气、科技感"）拒绝；
4. 对象锚定：有显式车型/型号或文档主语继承 → 加分（不作为硬门槛，
   因为 G 档"宏观设计分析"按定义不指向车型）。

输出 pass/reject + 理由列表，便于审计与回写评测集。
"""

from __future__ import annotations

import re

from . import passage

TOPIC_KILL = re.compile(
    r"毕设|毕业设计|代做|建模服务|设计竞赛|设计比赛|大赛|参赛|组队|评分|答辩"
    r"|选题|招新|报名|学费|培训|就业|课程"
    r"|批发|采购|多少钱|询价|价格表|厂家直销|联系电话|微信同号"
    r"|招聘|诚聘|求职|简历", re.I)

# 部件词（构型/造型证据）
PARTS = [
    "前脸", "格栅", "中网", "大灯", "车灯", "灯组", "保险杠", "翼子板", "轮眉",
    "后视镜", "导流罩", "遮阳板", "遮阳罩", "爬梯", "踏板", "踏步", "货厢", "货箱",
    "吊臂", "臂架", "塔臂", "悬挂", "伸缩臂", "支腿", "转台", "回转平台", "配重",
    "驾驶室", "铲斗", "动臂", "座椅", "仪表", "中控", "方向盘", "轮圈", "油箱",
    "储气筒", "储气罐", "大梁", "臂头", "鞍座", "绞盘", "工作台", "拉花", "涂装", "分色",
    "镀铬", "顶棚", "地毯", "密封条", "线束", "底板", "散热风扇", "轴距", "车身",
    "笼式",
]
# 形态/CMF 证据
FORMS = [
    "线条", "曲面", "轮廓", "型面", "比例", "姿态", "体量", "腰线", "肩线",
    "圆润", "硬朗", "方正", "流线", "棱线", "立面", "造型", "曲线", "曲面设计",
    "色彩", "配色", "材质", "质感", "哑光", "光泽", "肌理", "纹理", "熏黑",
    "双透镜", "光源",
]
DESIGN_WORDS = [
    "设计", "造型", "风格", "家族化", "家族式", "设计语言", "美学", "视觉",
    "颜值", "辨识度", "力量感", "科技感", "整体感", "层次感", "人机工程",
    "流线型", "人性化", "组合化", "内饰",
]
# 乘用车口碑/导购（非工程车辆语料）；"购车/家用"过宽，易误伤卡车评测
PASSENGER_RE = re.compile(r"SUV|轿车|MPV|车主|提车|落地价|插混|纯电续航")
ENGINEERING_RE = re.compile(
    r"重卡|卡车|牵引车|吊车|起重机|自卸|翻斗|铲车|装载机|工程机械|专用车|商用车")
# 企业宣传/通稿
ENTERPRISE_RE = re.compile(
    r"专利|智能制造|试点示范|品牌价值|产业链|战略合作|生产基地|绿色工厂|营业收入")
# 广告钩子（出现多个即视为营销页）
AD_RE = re.compile(r"优惠|促销|抢购|限时|到手价|指导价|售价|万元|购车|提车|经销商|福利")
# 宏观设计分析标记（G 档：无部件但有观点/趋势/方法论）
MACRO_RE = re.compile(
    r"行业|趋势|理念|策略|体系|成本|效率|本质|方法论|范式|未来|市场|客户|用户"
    r"|需求|升级|换代|方向|演进|变革")
# 配置清单（无标点堆砌的选装项）
OPTION_WORDS = ["全景天窗", "电动天窗", "电动调节座椅", "ESP", "氙气大灯",
                "GPS导航", "定速巡航", "真皮座椅", "倒车雷达", "全自动空调",
                "多功能方向盘", "LED大灯", "倒车影像", "无钥匙启动", "座椅加热",
                "日间行车灯", "自动泊车", "蓝牙/车载电话"]
# 显式车型/型号锚点（短代码）
MODEL_CODE = re.compile(
    r"XGC\d{4,5}|SAC\d{4,5}|ZTC\d{3,4}|QAY\d{2,3}|QY\d{2,3}K\w*|XCT\d{1,3}L?\d?"
    r"|STC\d{3,4}C?\d?|FTC\d{2,3}X\d|JH6|J6G|J6L|ZZ425|K3000|X5000E|FMX"
    r"|BJ5311JSQ|X3000|F3000|6X6|6x6")
SUBJ_INHERIT = re.compile(r"该车|这款车|此车|该机型|这款|其(?:前脸|驾驶室|外观|造型)")
GENERIC_SUBJ = re.compile(
    r"工程机械|专用车|商用车|该类车型|这类车型|同类车型|一般来说|通常情况下"
    r"|我国.{0,4}行业|国内.{0,6}市场|行业整体|企业.{0,4}设计|品牌.{0,4}基因")


def _hits(text: str, words: list[str]) -> list[str]:
    return [w for w in words if w in text]


def evaluate(text: str, *, title: str = "", url: str = "",
             subject: str | None = None) -> dict:
    """返回 {pass: bool, reasons: [...], anchors: {...}}。"""
    reasons: list[str] = []
    if not text or len(text.strip()) < 20:
        return {"pass": False, "reasons": ["too_short"], "anchors": {}}
    if TOPIC_KILL.search(text) or TOPIC_KILL.search(title):
        return {"pass": False, "reasons": ["topic_type"], "anchors": {}}
    if passage.CONFIG_LINE_RE.search(text):
        return {"pass": False, "reasons": ["config_line"], "anchors": {}}
    option_hits = sum(1 for w in OPTION_WORDS if w in text)
    if option_hits >= 6 and "。" not in text:
        return {"pass": False, "reasons": ["option_list"], "anchors": {}}
    if PASSENGER_RE.search(text) and not ENGINEERING_RE.search(text):
        return {"pass": False, "reasons": ["passenger_car"], "anchors": {}}
    if len(ENTERPRISE_RE.findall(text)) >= 3:
        return {"pass": False, "reasons": ["enterprise_pr"], "anchors": {}}
    parts = _hits(text, PARTS)
    forms = _hits(text, FORMS)
    design = _hits(text, DESIGN_WORDS)
    code = MODEL_CODE.search(text) or MODEL_CODE.search(title)
    anchored = bool(subject or code or SUBJ_INHERIT.search(text))
    generic = bool(GENERIC_SUBJ.search(text))

    if not design and not parts and not forms:
        return {"pass": False, "reasons": ["no_design_content"],
                "anchors": {"parts": [], "forms": [], "design": []}}
    if not parts and len(forms) < 2:
        # G 档通道：无部件，但有设计语汇 + 观点/趋势（且非广告）
        macro = (len(design) >= 2 or (len(design) >= 1 and len(forms) >= 1)) \
            and len(text) >= 60 and MACRO_RE.search(text) \
            and not AD_RE.search(text)
        if not macro:
            return {"pass": False,
                    "reasons": ["no_concrete_evidence"],
                    "anchors": {"parts": [], "forms": forms, "design": design}}
        reasons.append("macro_analysis")
    # 营销空话：设计词堆砌但零部件/形态证据已在上面拦掉
    if (generic and not anchored and len(forms) < 3 and len(parts) == 0
            and "macro_analysis" not in reasons):
        reasons.append("generic_no_object")
        return {"pass": False, "reasons": reasons,
                "anchors": {"parts": parts, "forms": forms, "design": design}}
    return {"pass": True, "reasons": reasons,
            "anchors": {"parts": parts, "forms": forms, "design": design,
                        "anchored": anchored, "generic": generic}}


def metrics(rows: list[dict]) -> dict:
    """rows: [{gate_pass, usable}] → 精确率/召回率/假阳性。"""
    tp = sum(1 for r in rows if r["gate_pass"] and r["usable"])
    fp = sum(1 for r in rows if r["gate_pass"] and not r["usable"])
    fn = sum(1 for r in rows if not r["gate_pass"] and r["usable"])
    tn = sum(1 for r in rows if not r["gate_pass"] and not r["usable"])
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4), "false_positive_rate": round(fp / (tp + fp), 4)
            if tp + fp else 0.0}
