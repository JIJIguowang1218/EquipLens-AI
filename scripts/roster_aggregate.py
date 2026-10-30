# -*- coding: utf-8 -*-
"""T18-roster 判定结果聚合：三类占比（V/P/G/C）× 类目拆解 + 报告生成。

输入:
- data-test/evals/roster-judge-sheet-20261030.json（候选段）
- data-test/evals/roster-verdicts-20261030.json（模型层逐段判定: {id: {tier, note}}）
- data-test/corpus/batch-corpus-roster-*-20261030/index.json（漏斗基数）

输出:
- data-test/evals/roster-eval-20261030.json（明细+汇总）
- data-test/runs/T18-ROSTER-20261030.md（报告）

占比口径：以"确定性 A/B 候选段总字数"为分母（即规则粗筛后的设计相关文本），
另报"占全部落盘正文"的口径（规则粗筛前），两个口径都写清楚。
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "data-test" / "evals"
CORPUS = ROOT / "data-test" / "corpus"
RUNS = ROOT / "data-test" / "runs"

TIERS = {"V": "指向车型的整体描述", "P": "部件构型及造型描述",
         "G": "非指向参考（宏观/企业设计语言）", "C": "剔除"}


def main() -> int:
    sheet = json.loads(
        (EVALS / "roster-judge-sheet-20261030.json").read_text(encoding="utf-8"))
    verdicts = json.loads(
        (EVALS / "roster-verdicts-20261030.json").read_text(encoding="utf-8"))

    # 漏斗基数：各批次落盘正文总字数
    funnel = {}
    for bdir in sorted(CORPUS.glob("batch-corpus-roster-*-20261030")):
        idx = json.loads((bdir / "index.json").read_text(encoding="utf-8"))
        cat = idx["batch_id"].split("roster-")[1].rsplit("-", 1)[0]
        saved = [r for r in idx["index"] if r["status"] == "saved"]
        funnel[cat] = {"articles": len(saved),
                       "body_chars": sum(r["chars"] for r in saved)}

    by_tier = defaultdict(lambda: {"chars": 0, "count": 0})
    by_cat = defaultdict(lambda: defaultdict(lambda: {"chars": 0, "count": 0}))
    unknown = []
    items_out = []
    cand_chars = 0

    for it in sheet["items"]:
        v = verdicts.get(it["id"])
        if not v:
            unknown.append(it["id"])
            continue
        tier = v["tier"]
        cand_chars += it["chars"]
        by_tier[tier]["chars"] += it["chars"]
        by_tier[tier]["count"] += 1
        by_cat[it["category"]][tier]["chars"] += it["chars"]
        by_cat[it["category"]][tier]["count"] += 1
        items_out.append({**{k: it[k] for k in
                             ("id", "category", "title", "url", "doc_subject",
                              "rule_label", "chars", "explicit_anchor")},
                          "tier": tier, "note": v.get("note", "")})

    total_by_tier = {t: {**by_tier[t],
                         "char_share": round(by_tier[t]["chars"] / cand_chars, 4)
                         if cand_chars else 0.0}
                     for t in TIERS}
    per_cat = {}
    for cat, tiers in by_cat.items():
        cat_cand = sum(d["chars"] for d in tiers.values())
        body = funnel.get(cat, {})
        per_cat[cat] = {
            "candidate_chars": cat_cand,
            "body_chars": body.get("body_chars", 0),
            "tiers": {t: {**tiers.get(t, {"chars": 0, "count": 0}),
                          "share_of_candidates": round(
                              tiers.get(t, {"chars": 0})["chars"] / cat_cand, 4)
                          if cat_cand else 0.0}
                      for t in TIERS},
        }

    eval_out = {
        "eval_id": "roster-triage-v1", "date": "2026-10-30",
        "protocol": {"V": TIERS["V"], "P": TIERS["P"], "G": TIERS["G"],
                     "C": TIERS["C"],
                     "pointing": "规则锚点（名录车型/型号代码）+ 文档主语继承 + "
                                 "模型层语义判定（唯一产品落点）"},
        "funnel": funnel,
        "candidate_passages": sheet["total"],
        "judged": len(items_out),
        "unjudged_ids": unknown,
        "candidate_chars": cand_chars,
        "body_chars_total": sum(f["body_chars"] for f in funnel.values()),
        "articles_total": sum(f["articles"] for f in funnel.values()),
        "tiers": total_by_tier,
        "per_category": per_cat,
        "items": items_out,
    }
    (EVALS / "roster-eval-20261030.json").write_text(
        json.dumps(eval_out, ensure_ascii=False, indent=1), encoding="utf-8")

    # 报告
    L = ["# T18-roster 全名录文本筛选测试报告（2026-10-30）", "",
         "## 0. 测试目的与口径", "",
         "产品负责人 2026-10-30 指令：用 T13–T15 锁定名录的全部车型做一次大规模"
         "文本爬取-筛选测试，同时检验①筛选能力（指向性识别）②各车型设计文本的真实"
         "储备。三分类：V 指向车型的整体描述 / P 部件构型及造型描述 / G 非指向参考。",
         "",
         "指向性机制（本轮实现）：规则层=名录锚点+型号代码正则+文档主语继承"
         "（标题锚定车型时代词段继承主语）+泛主语反向锚点；模型层=语义判定"
         "「描述能否落到唯一具体产品」，规则不可形式化的情形（对比文/承前省略/"
         "企业级设计语言）由模型裁决。", "",
         "## 1. 漏斗", "",
         "| 类目 | 落盘文章 | 正文总字数 | A/B 候选段字数 |",
         "|---|---|---|---|"]
    for cat, f in funnel.items():
        cand = per_cat.get(cat, {}).get("candidate_chars", 0)
        L.append(f"| {cat} | {f['articles']} | {f['body_chars']:,} | {cand:,} |")
    L += ["| **合计** | {} | {} | {} |".format(
        eval_out["articles_total"],
        f"{eval_out['body_chars_total']:,}",
        f"{cand_chars:,}"), "",
          "## 2. 三类占比（分母=候选段字数）", "",
          "| 类别 | 篇段数 | 字数 | 占候选比 | 占全部正文比 |",
          "|---|---|---|---|---|"]
    body_total = eval_out["body_chars_total"] or 1
    for t in ("V", "P", "G", "C"):
        d = total_by_tier[t]
        L.append(f"| {t} {TIERS[t]} | {d['count']} | {d['chars']:,} | "
                 f"{d['char_share']*100:.1f}% | "
                 f"{d['chars']/body_total*100:.1f}% |")
    L += ["", "## 3. 按类目拆解（占该类目候选段字数比）", "",
          "| 类目 | V | P | G | C |",
          "|---|---|---|---|---|"]
    for cat, d in per_cat.items():
        t = d["tiers"]
        L.append("| {} | {:.1f}% | {:.1f}% | {:.1f}% | {:.1f}% |".format(
            cat, *[t[x]["share_of_candidates"] * 100 for x in ("V", "P", "G", "C")]))
    (RUNS / "T18-ROSTER-20261030.md").write_text("\n".join(L) +
                                                 "\n", encoding="utf-8")
    print(json.dumps({"judged": len(items_out), "unjudged": unknown,
                      "tiers": {t: total_by_tier[t]["char_share"]
                                for t in TIERS}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
