"""段落级清洗与设计相关性评估（L3 的确定性基线）。

目标：把“整篇文章”拆成“可用设计段”，给人审和后续 LLM 质检一个可复现的起点。
启发式只做初筛，不做最终事实判断；label=A/B/C 是 provisional，LLM/人工可覆盖。
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

STRONG = [
    "造型", "设计", "前脸", "格栅", "中网", "大灯", "灯组", "保险杠", "翼子板",
    "轮眉", "线条", "曲面", "轮廓", "比例", "姿态", "型面", "体量", "特征线",
    "家族化", "家族式", "设计语言", "风格", "视觉", "颜值", "美感", "犀利",
    "圆润", "硬朗", "动感", "精致", "力量感", "稳重", "大气", "流线", "涂装",
    "分色", "材质", "工艺", "色彩", "质感", "镀铬", "哑光", "覆盖件", "踏板",
    "后视镜", "遮阳板", "脸谱", "造型设计", "外观设计", "设计感", "设计风格",
    "导流罩", "扰流板", "轮拱", "A柱", "腰线", "肩线", "灯组签名", "格栅图形",
]
WEAK = ["风阻", "外观", "审美", "辨识度", "肌肉感", "层次", "整体感", "科技感",
        "年轻化", "传承", "品牌基因"]
NEGATIVE = ["油耗", "马力", "扭矩", "变速箱", "发动机", "配置", "报价", "优惠",
            "促销", "保养", "维修", "参数", "经销商", "询价", "裸车价", "试驾",
            "续航", "电池", "充电", "载重", "轴距", "排放"]
DIMENSIONS = {
    "形态": ["前脸", "格栅", "中网", "大灯", "灯组", "保险杠", "翼子板", "轮眉",
             "线条", "曲面", "轮廓", "型面", "体量", "特征线", "踏板", "后视镜",
             "遮阳板", "导流罩", "扰流板", "轮拱"],
    "CMF": ["材质", "工艺", "色彩", "涂装", "分色", "质感", "镀铬", "哑光",
            "闪粒", "肌理", "漆"],
    "比例/姿态": ["比例", "姿态", "A柱", "倾角", "宽体", "短车头", "长头",
                 "平头", "高顶", "低趴"],
    "意图": ["设计意图", "为了", "营造", "彰显", "强调", "辨识度", "力量感",
             "年轻化", "家族化", "传承", "品牌基因", "视觉", "气场", "科技感"],
}
NAV_MARKERS = ["版权", "登录", "注册", "下载APP", "微信扫一扫", "网站地图",
               "相关推荐", "热门推荐", "最新问答", "车系推荐", "经销商",
               "营业执照", "经营许可证", "分享到", "扫码", "App", "首页"]
IMG_RE = re.compile(r"^!\[[^\]]*\]\([^)]*\)\s*$")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
LOW_TITLE_RE = re.compile(r"有限公司|销售|报价|价格|促销|厂家|批发|多少钱|询价")


def _domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def trust_for_url(url: str, registry: dict | None) -> str:
    """按域名后缀匹配来源注册表；未知来源默认 medium。"""
    if not registry:
        return "medium"
    host = _domain(url)
    for src in registry.get("sources", []):
        d = src.get("domain", "").lower()
        if host == d or host.endswith("." + d):
            return src.get("trust", "medium")
    return "medium"


def clean_lines(body: str) -> list[str]:
    """去导航/推荐/图片轮播，保留可用于判读的正文行。"""
    out = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or IMG_RE.match(line):
            continue
        if line.count("](") >= 3:  # 推荐位/导航：一行塞满链接
            continue
        if any(m in line for m in NAV_MARKERS) and line.count("](") >= 1:
            continue
        line = LINK_RE.sub(r"\1", line)
        line = BOLD_RE.sub(r"\1", line).lstrip("#").strip()
        if len(line) < 20:
            continue
        out.append(line)
    return out


def split_passages(lines: list[str], min_chars: int = 20) -> list[str]:
    return [x for x in lines if len(x) >= min_chars]


def score_passage(text: str, source_trust: str = "medium") -> dict:
    strong = [w for w in STRONG if w in text]
    weak = [w for w in WEAK if w in text]
    neg = [w for w in NEGATIVE if w in text]
    dims = [name for name, words in DIMENSIONS.items() if any(w in text for w in words)]
    digits = sum(1 for ch in text if ch.isdigit())
    numeric_ratio = digits / max(1, len(text))
    trust_bonus = {"high": 1, "medium": 0, "low": -1, "exclude": -3}.get(source_trust, 0)
    score = (len(strong) * 2 + len(dims) * 2 + len(weak)
             - len(neg) * 2 - (4 if numeric_ratio > 0.2 else 0) + trust_bonus)
    if source_trust == "exclude":
        label = "C"
    elif len(text) >= 20 and len(strong) >= 2 and len(neg) == 0 \
            and numeric_ratio < 0.15 and source_trust != "low":
        label = "A"
    elif len(text) >= 20 and (len(strong) >= 1 or len(dims) >= 1) and len(neg) <= 1:
        label = "B"
    else:
        label = "C"
    return {"label": label, "score": score, "strong": strong, "weak": weak,
            "negative": neg, "dims": dims, "numeric_ratio": round(numeric_ratio, 3),
            "source_trust": source_trust, "chars": len(text)}


def grade_text(text: str, source_trust: str = "medium") -> dict:
    lines = clean_lines(text)
    passages = []
    for p in split_passages(lines):
        rec = score_passage(p, source_trust)
        rec["text"] = p
        passages.append(rec)
    total = sum(len(p["text"]) for p in passages)
    a = [p for p in passages if p["label"] == "A"]
    b = [p for p in passages if p["label"] == "B"]
    return {
        "passages": passages,
        "total_chars": total,
        "a_chars": sum(p["chars"] for p in a),
        "b_chars": sum(p["chars"] for p in b),
        "a_count": len(a), "b_count": len(b), "c_count": len(passages) - len(a) - len(b),
        "a_share": round(sum(p["chars"] for p in a) / total, 4) if total else 0.0,
        "dims": sorted({d for p in a for d in p["dims"]}),
    }


def _split_doc(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n\n(.*)$", text, re.S)
    return m.group(2) if m else text


def grade_batch(batch_dir: Path, registry: dict | None = None) -> dict:
    batch_dir = Path(batch_dir)
    idx = json.loads((batch_dir / "index.json").read_text(encoding="utf-8"))
    docs = []
    totals = {"total_chars": 0, "a_chars": 0, "b_chars": 0, "a_count": 0}
    for r in idx["index"]:
        if r["status"] != "saved":
            continue
        trust = trust_for_url(r["url"], registry)
        if LOW_TITLE_RE.search(r.get("title", "")):
            trust = "low"  # 经销商/报价/厂家页：即使域名未知也降权
        g = grade_text(_split_doc(batch_dir / r["file"]), trust)
        doc = {"title": r["title"], "url": r["url"], "source_type": r["source_type"],
               "chars": g["total_chars"], "a_chars": g["a_chars"],
               "a_count": g["a_count"], "a_share": g["a_share"],
               "dims": g["dims"], "source_trust": trust,
               "top_passages": [p["text"][:200] for p in g["passages"]
                                if p["label"] == "A"][:3]}
        docs.append(doc)
        for k in totals:
            totals[k] += g[k]
    failed = [r for r in idx["index"] if r["status"] != "saved"]
    hard_statuses = ("fetch_error", "fetch_failed", "robots_denied", "too_short")
    hard_failed = sum(1 for r in failed
                      if any(str(r["status"]).startswith(s) for s in hard_statuses))
    policy_skipped = sum(1 for r in failed
                         if r["status"] in ("blocked_url", "source_skipped"))
    metrics = {
        "articles": len(docs),
        "articles_with_a": sum(1 for d in docs if d["a_count"] > 0),
        "total_chars": totals["total_chars"],
        "a_chars": totals["a_chars"],
        "b_chars": totals["b_chars"],
        "a_share": round(totals["a_chars"] / totals["total_chars"], 4)
        if totals["total_chars"] else 0.0,
        "a_per_article": round(totals["a_chars"] / len(docs), 1) if docs else 0.0,
        "source_types": sorted({d["source_type"] for d in docs}),
        "failed": len(failed),
        "hard_failed": hard_failed,
        "policy_skipped": policy_skipped,
        "blocked_url": sum(1 for r in failed if r["status"] == "blocked_url"),
        "robots_denied": sum(1 for r in failed if r["status"] == "robots_denied"),
        "dims": sorted({d for doc in docs for d in doc["dims"]}),
    }
    return {"batch_id": idx.get("batch_id"), "docs": docs, "metrics": metrics,
            "failed": [{"title": r["title"], "status": r["status"], "url": r["url"]}
                       for r in failed]}


def format_report(report: dict, top: int = 5) -> str:
    m = report["metrics"]
    lines = [f"### {report['batch_id']}",
             f"- 文章 {m['articles']} / 有 A 段 {m['articles_with_a']} / "
             f"A {m['a_chars']} 字（{m['a_share']*100:.1f}%）/ 单篇 {m['a_per_article']} 字",
             f"- 维度 {', '.join(m['dims']) or '无'} / 来源类型 {', '.join(m['source_types'])}",
             f"- 失败 {m['failed']}（硬失败 {m.get('hard_failed', 0)} / "
             f"政策跳过 {m.get('policy_skipped', 0)} / blocked_url {m['blocked_url']} / "
             f"robots {m['robots_denied']}）"]
    for d in report["docs"][:top]:
        lines.append(f"  - [{d['source_trust']}] {d['title'][:40]} · A {d['a_chars']} 字")
    return "\n".join(lines)
