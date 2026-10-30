# -*- coding: utf-8 -*-
"""T18-roster 判定协议：三分类 + 指向性机制（规则层）。

三分类（产品负责人 2026-10-30 定义）：
- V 指向车型的整体描述：整车级风格/姿态/比例/CMF，落点是可唯一识别的具体产品
- P 部件及描述：部件构型/造型设计描述（指向车型的部件优先，通用部件构型也可入此档）
- G 非指向参考：宏观设计分析/企业设计语言/行业观察，不指向具体车型，作定调参考
- C 剔除：跑题/空洞/错类型（毕设代做/竞赛攻略/经销商报价/新闻通稿）

指向性机制（对象锚定，两层）：
1. 规则层（本脚本，确定性）：
   a. 显式锚点——名录车型名/型号代码（XCT25、JH6、德龙X3000…）出现在段落内；
   b. 文档主语继承——标题/URL 锚定单一车型时，正文代词段（"该车/这款/其前脸"）
      继承该主语（subject inheritance）；
   c. 反向锚点——段落主语是行业/企业/类目泛词（"工程机械/专用车/该类车型"）
      且无显式锚点 → 非指向。
2. 模型层（对话模型扮演 judge）：语义判定主语能否解析到唯一具体产品；
   处理对比文（多车型）、经销商页（标题有型号正文空洞→仍按 C 剔）、
   承前省略、企业级设计语言（→G）等规则不可形式化的情形。

规则先杀（可形式化的直接判 C，不进模型）：
- 主题类型排除：毕设/代做/竞赛/报名/评分策略/报价/促销/经销商联系页
- 空壳：negative_terms 密度超限、数字占比超限（沿用 passage.score_passage）

用法: PYTHONPATH=src python tmp/roster_judge_sheet.py
输出: data-test/evals/roster-judge-sheet-20261030.md + .json
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from equiplens import passage  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data-test" / "corpus"
OUT_DIR = ROOT / "data-test" / "evals"

BATCHES = [
    "batch-corpus-roster-沙漠牵引车-20261030",
    "batch-corpus-roster-重型吊车-20261030",
    "batch-corpus-roster-轻型吊车-20261030",
    "batch-corpus-roster-翻斗铲车-20261030",
]

# ── 主题类型排除（L3 评测集 v1 教训：竞赛攻略/毕设代做/经销商页）──
TOPIC_KILL = re.compile(
    r"毕设|毕业设计|代做|建模服务|设计竞赛|设计比赛|大赛|参赛|组队|评分|答辩"
    r"|选题|招新|报名|学费|培训|就业|课程"
    r"|批发|采购|多少钱|询价|价格表|厂家直销|联系电话|微信同号", re.I)

# ── 显式锚点：名录车型 + 代表车型 + 品牌型号模式 ──
ROSTER_MODELS = [
    "陕汽重卡德龙6X6", "陕汽重卡德龙F3000", "陕汽重卡德龙X3000", "陕汽重卡德龙",
    "东风天锦", "一汽解放JH6", "中国重汽ZZ425", "中国重汽汕德卡C7H",
    "中国重汽HOWO", "中国重汽MAX", "东风龙H5", "一汽解放J6G",
    "徐工XGC88000", "三一SAC16000S", "中联重科ZTC250", "徐工QY35K5",
    "徐工QY25K5C", "徐工XCT25", "中联重科QAY25", "三一STC500", "福田BJ5311JSQ",
    "徐工XCT8L4", "雷萨FTC25X5", "三一STC800C6", "雷萨FTC55X5", "徐工QY16KC",
    "三一QY25C", "三一STC550C5", "三一STC1300C8", "徐工QY25K5F", "中联重科ZTC250A",
    "福田金刚3", "福田金刚C", "福田金刚", "沃尔沃FMX", "一汽解放J6L",
    "陕汽重卡德龙K3000", "陕汽重卡德龙X5000E",
    # 档案代表车型（category_profiles.json）
    "汕德卡C9H", "解放J7", "黄河X7", "豪沃V7-X", "徐工 XCT25", "三一 STC250",
    "中联 ZTC250", "柳工 856H", "临工 L956F", "龙工 855N", "豪沃 6X6", "H6066",
]
# 型号代码（短，需品牌共现或全大写数字模式）：单独出现也算锚点的高置信代码
MODEL_CODE = re.compile(
    r"XGC\d{4,5}|SAC\d{4,5}|ZTC\d{3,4}|QAY\d{2,3}|QY\d{2,3}K\w*|XCT\d{1,3}L?\d?"
    r"|STC\d{3,4}C?\d?|FTC\d{2,3}X\d|JH6|J6G|J6L|ZZ425|K3000|X5000E|FMX"
    r"|BJ5311JSQ|X3000|F3000|6X6|6x6")
BRANDS = ["徐工", "三一", "中联", "重汽", "解放", "陕汽", "东风", "雷萨",
          "沃尔沃", "福田", "柳工", "临工", "龙工", "程力", "虎6G", "豪沃"]
# 非指向主语（段落级反向锚点）
GENERIC_SUBJ = re.compile(
    r"工程机械|专用车|商用车|该类车型|这类车型|同类车型|一般来说|通常情况下"
    r"|我国.{0,4}行业|国内.{0,6}市场|行业整体|企业.{0,4}设计|品牌.{0,4}基因")

SUBJ_INHERIT = re.compile(r"该车|这款车|此车|该机型|这款|其(?:前脸|驾驶室|外观|造型)")


def doc_anchor(title: str, url: str) -> str | None:
    """文档级主语锚定：标题或 URL 命中的车型（最长优先）。"""
    hay = title + " " + url
    for m in sorted(ROSTER_MODELS, key=len, reverse=True):
        if m in hay or m.replace(" ", "") in hay:
            return m
    code = MODEL_CODE.search(title)
    if code and any(b in hay for b in BRANDS):
        return code.group(0)
    return None


def passage_pointing(text: str, doc_subject: str | None) -> dict:
    """段落级指向性（规则层证据，供模型层参考，不单独定案）。"""
    explicit = None
    for m in sorted(ROSTER_MODELS, key=len, reverse=True):
        if m in text or m.replace(" ", "") in text:
            explicit = m
            break
    if not explicit:
        c = MODEL_CODE.search(text)
        if c:
            explicit = c.group(0)
    inherit = bool(doc_subject and SUBJ_INHERIT.search(text))
    generic = bool(GENERIC_SUBJ.search(text))
    pointing = bool(explicit) or (inherit and not generic)
    return {"explicit_anchor": explicit, "subject_inheritance": inherit,
            "generic_subject": generic, "rule_pointing": pointing}


def main() -> int:
    registry = json.loads(
        (ROOT / "data" / "source_registry.json").read_text(encoding="utf-8"))
    import hashlib
    sheet_items = []
    seen_fp: set[str] = set()
    for batch in BATCHES:
        bdir = CORPUS / batch
        if not bdir.exists():
            print(f"SKIP（未落盘）: {batch}")
            continue
        idx = json.loads((bdir / "index.json").read_text(encoding="utf-8"))
        cat = idx["batch_id"].split("roster-")[1].rsplit("-", 1)[0]
        seen_urls: set[str] = set()
        for r in idx["index"]:
            if r["status"] != "saved" or not r.get("file"):
                continue
            if r["url"] in seen_urls:  # 同 URL 多次落盘（SERP 重复锚点）只算一次
                continue
            seen_urls.add(r["url"])
            subject = doc_anchor(r["title"], r["url"])
            killed = bool(TOPIC_KILL.search(r["title"]))
            trust = passage.trust_for_url(r["url"], registry)
            if passage.LOW_TITLE_RE.search(r.get("title", "")):
                trust = "low"
            full = passage._split_doc(bdir / r["file"])
            g = passage.grade_text(full, trust)
            for p in g["passages"]:
                if p["label"] == "C":
                    continue
                if TOPIC_KILL.search(p["text"][:60]) or killed:
                    continue
                pid = f"{cat[:2]}-{hashlib.sha1(p['text'].encode()).hexdigest()[:8]}"
                if pid in seen_fp:  # 跨文档同文（汽车之家首页多次落盘）只算一次
                    continue
                seen_fp.add(pid)
                sheet_items.append({
                    "id": pid,
                    "category": cat, "title": r["title"], "url": r["url"],
                    "doc_subject": subject, "rule_label": p["label"],
                    "rule_score": p["score"], "chars": p["chars"],
                    "dims": p["dims"], "text": p["text"][:420],
                    **passage_pointing(p["text"], subject)})

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jp = OUT_DIR / "roster-judge-sheet-20261030.json"
    jp.write_text(json.dumps({"total": len(sheet_items),
                              "items": sheet_items},
                             ensure_ascii=False, indent=1), encoding="utf-8")

    md = ["# T18-roster 判定工作表 2026-10-30",
          "",
          f"候选段落 {len(sheet_items)} 条（确定性 A/B，已排除主题类型与短段）。",
          "模型层判定输出三分类：V 指向车型整体 / P 部件 / G 非指向参考 / C 剔除。",
          ""]
    cur = None
    for it in sheet_items:
        if it["category"] != cur:
            cur = it["category"]
            md.append(f"\n## {cur}\n")
        ev = []
        if it["explicit_anchor"]:
            ev.append(f"锚:{it['explicit_anchor']}")
        if it["subject_inheritance"]:
            ev.append("承题")
        if it["generic_subject"]:
            ev.append("泛主语")
        md.append(f"- **{it['id']}** [{it['rule_label']}/{it['rule_score']}] "
                  f"{it['title'][:36]} | 主题:{it['doc_subject'] or '-'} "
                  f"| {' '.join(ev) or '无锚'} | {it['chars']}字")
        md.append(f"  > {it['text']}")
    (OUT_DIR / "roster-judge-sheet-20261030.md").write_text(
        "\n".join(md), encoding="utf-8")
    print(f"判定表: {len(sheet_items)} 条 → {jp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
