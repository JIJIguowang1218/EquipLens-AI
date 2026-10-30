"""域名基准与发现通道：同一组查询跨站点对照，产出域名排行榜。

目的（T18-roster 结论的后续）：
- 把 source_registry 的信任等级从"观察性先验"升级为"可验证数据"；
- 发现新域名：不受 site: 限制的泛搜结果聚类，按小样本产出决定晋升/降级；
- 指标：正文量、抓取成功率、A 档设计文本产出（每千字）、robots 合规。

不引入新依赖；SERP 走 Crawl4AI（百度，被拦落 Bing RSS），抓取复用 webchannel 纪律。

用法：
  python -m equiplens domain-bench tmp/domain-bench-queries.json --out data-test/evals/domain-bench
  （加 --apply 把达标域名写回 data/source_registry.json）
"""

from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

from . import corpus, passage, webchannel
from .roster import _baidu_serp_url

SKIP_DOMAINS = {"b2b.baidu.com", "docin.com", "baike.baidu.com"}
DESIGN_TERMS = ["造型", "设计", "设计语言", "家族化", "外观", "工业设计", "CMF"]


def classify_trust(a_share: float) -> str:
    """按 A 档占正文比例给信任等级（阈值来自 T13-T18 实测经验）。"""
    if a_share >= 0.05:
        return "high"
    if a_share >= 0.02:
        return "medium"
    if a_share >= 0.005:
        return "low"
    return "none"


def summarize(domain: str, pages: list[dict]) -> dict:
    """单域名指标汇总。pages: [{url, title, body_chars, a_chars, status, channel}]"""
    ok = [p for p in pages if p.get("status") == "saved"]
    body = sum(p["body_chars"] for p in ok)
    a_chars = sum(p["a_chars"] for p in ok)
    saved = len(ok)
    robots_denied = sum(1 for p in pages if p.get("status") == "robots_denied")
    fetch_failed = sum(1 for p in pages
                       if str(p.get("status", "")).startswith(("fetch_error",
                                                               "fetch_failed")))
    a_share = a_chars / body if body else 0.0
    # 信任分级只采信百度通道样本；Bing 兜底结果偏官网/商品页，仅作参考
    baidu_ok = [p for p in ok if p.get("channel") == "baidu"]
    b_body = sum(p["body_chars"] for p in baidu_ok)
    b_a = sum(p["a_chars"] for p in baidu_ok)
    trust_suggested = (classify_trust(b_a / b_body) if b_body
                       else "unknown")
    return {
        "domain": domain, "pages": len(pages), "saved": saved, "body_chars": body,
        "a_chars": a_chars, "a_share": round(a_share, 4),
        "a_per_kchar": round(a_chars / body * 1000, 2) if body else 0.0,
        "fetch_ok_rate": round(saved / len(pages), 4) if pages else 0.0,
        "robots_denied": robots_denied, "fetch_failed": fetch_failed,
        "channels": sorted({p.get("channel", "?") for p in ok}),
        "baidu_pages": len(baidu_ok), "baidu_a_share": round(b_a / b_body, 4)
        if b_body else None,
        "trust_suggested": trust_suggested,
        "samples": [{"url": p["url"], "title": p.get("title", "")[:50],
                     "a_chars": p["a_chars"], "channel": p.get("channel")}
                    for p in ok if p["a_chars"] > 0][:3],
        "urls": [p["url"] for p in ok][:5],
    }


def _norm_host(host: str) -> str:
    return host[4:] if host.startswith("www.") else host


def _match_registry(host: str, known: dict) -> dict | None:
    """注册表匹配：仅同域（去 www）视为同一来源。

    mp.weixin.qq.com / news.qq.com 不等于 qq.com——子域可能是不同产品，
    不做后缀归并，避免把微信/新闻频道误当门户本体。
    """
    h = _norm_host(host)
    for d, src in known.items():
        if _norm_host(d) == h:
            return src
    return None


def build_proposals(leaderboard: list[dict], registry: dict) -> dict:
    """对比现有注册表，给出晋升/降级/新增建议（不自动写）。

    新增门槛：≥2 页成功、正文字数 ≥5,000、有百度通道样本——单页小样本
    （如 1 页 4K 字）只进观察，不进注册表。
    """
    known = {s["domain"]: s for s in registry.get("sources", [])}
    proposals = {"promote": [], "demote": [], "add": [], "keep": []}
    for row in leaderboard:
        d = row["domain"]
        suggested = row["trust_suggested"]
        if suggested in (None, "unknown"):  # 无百度通道样本，无法判定
            proposals["keep"].append({"domain": d,
                                      "reason": "无百度通道样本（仅 Bing 兜底）"})
            continue
        cur = _match_registry(d, known)
        enough = (row["saved"] >= 2 and row["body_chars"] >= 5000
                  and (row.get("baidu_pages") or 0) >= 1)
        cur_trust = cur.get("trust", "medium") if cur else None
        if cur is None:
            if suggested in ("high", "medium") and enough:
                proposals["add"].append({
                    "domain": d, "trust": suggested,
                    "design_yield": suggested,
                    "evidence": {"a_share": row["a_share"],
                                 "a_per_kchar": row["a_per_kchar"],
                                 "saved": row["saved"],
                                 "body_chars": row["body_chars"]},
                    "notes": "domain-bench 发现，小样本验证通过"})
            elif suggested in ("high", "medium"):
                proposals["keep"].append({"domain": d,
                                          "reason": "样本不足（单页/正文过短）"})
            else:
                proposals["keep"].append({"domain": d, "reason": "新域名产出不足"})
            continue
        if suggested == "high" and cur_trust != "high" and enough:
            proposals["promote"].append({"domain": d, "from": cur_trust,
                                         "to": "high",
                                         "a_share": row["a_share"]})
        elif (suggested == "none" and cur_trust in ("high", "medium")
              and row["saved"] >= 3 and row["body_chars"] >= 15000
              and (row.get("baidu_pages") or 0) >= 2):
            proposals["demote"].append({"domain": d, "from": cur_trust,
                                        "to": "low",
                                        "a_share": row["a_share"]})
        else:
            proposals["keep"].append({"domain": d,
                                      "registry_trust": cur_trust,
                                      "bench": suggested})
    return proposals


def render_report(leaderboard: list[dict], proposals: dict,
                  meta: dict) -> str:
    lines = ["# 域名基准与发现报告", "",
             f"- 生成：{meta['generated_at']} ｜ 查询 {meta['queries']} 条 ｜ "
             f"抓取页 {meta['pages']} 个 ｜ 域名 {len(leaderboard)} 个",
             f"- SERP 被拦并退 Bing：{len(meta.get('blocked_queries', []))} 查询"
             + ("（" + "、".join(meta["blocked_queries"][:3]) + "…）"
                if meta.get("blocked_queries") else ""),
             "- 口径：A 档设计文本产出 = A 字数 / 正文字数；"
             "信任分级只采信百度通道样本，Bing 兜底样本仅参考", "",
             "## 排行榜（按 A 产出/千字）", "",
             "| 域名 | 页数 | 成功 | 正文 | A 字 | A/千字 | 建议 | 现注册表 |",
             "|---|---:|---:|---:|---:|---:|---|---|"]
    for r in sorted(leaderboard, key=lambda x: -x["a_per_kchar"]):
        lines.append(f"| {r['domain']} | {r['pages']} | {r['saved']} | "
                     f"{r['body_chars']:,} | {r['a_chars']:,} | "
                     f"{r['a_per_kchar']} | {r['trust_suggested']} | "
                     f"{r['registry_trust'] if 'registry_trust' in r else '新'} |")
    lines += ["", "## 建议动作", ""]
    for k, label in (("promote", "晋升"), ("demote", "降级"),
                     ("add", "新增"), ("keep", "保持/观察")):
        rows = proposals.get(k, [])
        lines.append(f"### {label}（{len(rows)}）")
        for p in rows:
            lines.append(f"- {p.get('domain')}: " + json.dumps(
                {kk: vv for kk, vv in p.items() if kk != 'domain'},
                ensure_ascii=False))
        lines.append("")
    return "\n".join(lines)


async def run_bench(queries: list[str], *, max_anchors_per_query: int = 8,
                    max_pages_per_domain: int = 2, max_pages_total: int = 40,
                    serp_channel: str = "auto") -> list[dict]:
    """执行基准：SERP → 锚点 → 按域名取样抓取 → 分级 → 指标。"""
    from crawl4ai import AsyncWebCrawler

    async with AsyncWebCrawler(headless=True, verbose=False) as browser:
        serp: dict[str, str] = {}

        async def one(q: str) -> tuple[str, str]:
            try:
                r = await browser.arun(url=_baidu_serp_url(q))
                md = r.markdown if isinstance(r.markdown, str) else str(r.markdown)
                return q, md if getattr(r, "success", False) else ""
            except Exception:  # noqa: BLE001
                return q, ""

        for q, md in await asyncio.gather(*[one(q) for q in queries]):
            serp[q] = md
        # 被拦查询：先重试一次（间隔 2s），仍拦则换 Bing 并在报告中标明通道
        blocked = [q for q in queries if corpus.serp_looks_blocked(serp[q])]
        if blocked:
            await asyncio.sleep(2)
            for q, md in await asyncio.gather(*[one(q) for q in blocked]):
                serp[q] = md
        blocked = [q for q in queries if corpus.serp_looks_blocked(serp[q])]
        if blocked:
            serp.update(await asyncio.to_thread(corpus._bing_serps, blocked))

        seen: set[str] = set()
        by_domain: dict[str, list[dict]] = {}
        for q in queries:
            terms = DESIGN_TERMS + [q.split()[0]] if q.split() else DESIGN_TERMS
            for a in corpus.pick_anchors(serp.get(q, ""), max_anchors_per_query,
                                         seen, relevant_terms=terms):
                seen.add(a["url"])
                real = corpus.resolve_redirect(a["url"])
                host = (urlparse(real).hostname or "").lower()
                if any(host == d or host.endswith("." + d) for d in SKIP_DOMAINS):
                    continue
                slots = by_domain.setdefault(host, [])
                if len(slots) >= max_pages_per_domain:
                    continue
                slots.append({"url": real, "title": a["title"], "query": q,
                              "channel": "bing" if q in blocked else "baidu",
                              "status": "", "body_chars": 0, "a_chars": 0})
                if sum(len(v) for v in by_domain.values()) >= max_pages_total:
                    break

        for host, pages in sorted(by_domain.items()):
            for p in pages:
                if not webchannel.robots_allows(p["url"]):
                    p["status"] = "robots_denied"
                    continue
                time.sleep(webchannel.SLEEP_SECONDS)
                try:
                    r = await browser.arun(url=p["url"])
                except Exception as e:  # noqa: BLE001
                    p["status"] = f"fetch_error: {type(e).__name__}"
                    continue
                if not getattr(r, "success", False):
                    p["status"] = "fetch_failed"
                    continue
                body = r.markdown if isinstance(r.markdown, str) else str(r.markdown)
                p["body_chars"] = len(body)
                g = passage.grade_text(body, "medium")
                p["a_chars"] = g["a_chars"]
                p["status"] = "saved"
    rows = [summarize(h, pages) for h, pages in sorted(by_domain.items())]
    meta = {"queries": len(queries), "pages": sum(r["pages"] for r in rows),
            "blocked_queries": blocked,
            "channel_note": "百度；重试后仍被拦的查询退 Bing（样本标 channel=bing）"}
    return {"rows": rows, "meta": meta}
