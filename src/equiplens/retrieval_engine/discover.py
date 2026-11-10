# -*- coding: utf-8 -*-
"""【已废弃 2026-11-11】候选车型发现（旧 fallback，不再被 WebWorld 调用）。

废弃原因：`BRANDS` 是 18 个国产品牌的硬编码名单，查询也只发国产品牌词；
外国品牌标题在 `_candidate` 里直接匹配不到，会让“实时发现”静默变成
“国产-only”。这与“不设品牌白名单”的产品边界冲突，且 T32/T33 的结果
因此被误读成“360 没有外国车”。

保留文件仅作历史参考；新流程必须是：
  scripts/plan_candidates.py（brief → 查询计划 → Search → LLM 抽取 + 出处校验）
  → engine --plan。
不要再从任何运行路径调用本模块。
"""
from __future__ import annotations

import re
from collections import Counter

from .. import imagesearch

BRANDS = ("豪沃", "汕德卡", "德龙", "陕汽", "解放", "一汽", "北奔", "红岩",
          "东风", "欧曼", "大运", "徐工", "三一", "江淮", "福田", "柳汽",
          "华菱", "重汽")
# 车系名优先于 VIN 型号码（避免把 ZZ4256V395ME1 当成车系）
FAMILIES = ("X3000", "X5000", "M3000", "F3000", "NG80", "C7H", "C9H", "J6P",
            "J6G", "J5M", "J5P", "J7", "JH6", "N9", "EST", "GTL", "杰狮",
            "天龙", "天锦", "华神", "漢風", "格尔发", "乘龙", "悍威", "奥威",
            "大力神", "H6066")
CONFIG_RE = re.compile(r"6\s*[x×]\s*6|六驱|全驱|6wd", re.I)
CODE_RE = re.compile(r"\b([A-Z]{1,3}\d{3,}[A-Z0-9]*)\b")

BASE_QUERIES = ("6x6 牵引车", "6x6 越野卡车", "大件牵引车 6x6",
                "沙漠 越野 卡车", "全驱 载货车", "六驱 越野 底盘")


def _candidate(title: str) -> str | None:
    t = re.sub(r"\s+", " ", title or "")
    up = t.upper()
    brand = next((b for b in BRANDS if b in t), "")
    fam = next((f for f in FAMILIES if f.upper() in up), "")
    if not fam:
        m = CODE_RE.search(up)
        fam = m.group(1) if m else ""
    if fam and brand:
        return f"{brand} {fam}"
    if fam:
        return fam
    return None


def discover_models(scope: str, limit: int = 12,
                    queries: list[str] | None = None,
                    per_query: int = 30) -> list[dict]:
    """返回 [{model, hits, titles, query}]，按命中次数排序。"""
    qs = list(queries or [])
    if not qs:
        qs = [f"{scope} 6x6", *BASE_QUERIES,
              *[f"{b} 6x6 牵引车" for b in BRANDS]]
    counter: Counter = Counter()
    evidence: dict[str, list[str]] = {}
    first_query: dict[str, str] = {}
    for q in qs:
        try:
            hits, _ = imagesearch._search_360(q, per_query)
        except Exception:  # noqa: BLE001
            continue
        for h in hits:
            title = h.get("title", "")
            if not CONFIG_RE.search(title):   # 只要 6×6/六驱/全驱
                continue
            cand = _candidate(title)
            if not cand:
                continue
            counter[cand] += 1
            evidence.setdefault(cand, [])
            if len(evidence[cand]) < 2:
                evidence[cand].append(title[:60])
            first_query.setdefault(cand, q)
    return [{"model": m, "hits": n, "titles": evidence.get(m, []),
             "query": first_query.get(m, "")}
            for m, n in counter.most_common(limit)]
