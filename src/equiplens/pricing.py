# -*- coding: utf-8 -*-
"""DeepSeek 官方定价（人民币）与峰谷时段计算。

来源：https://api-docs.deepseek.com/zh-cn/quick_start/pricing/
（2026-11 抓取；价格变动以官网为准）

deepseek-flash：
  输入（缓存未命中）  峰 ¥2   / 谷 ¥1   每百万 tokens
  输入（缓存命中）    峰 ¥0.04/ 谷 ¥0.02 每百万 tokens
  输出                峰 ¥8   / 谷 ¥4   每百万 tokens
Search / Fetch：¥5 / 1000 次成功请求（按次，不分峰谷）

峰时段：北京时间周一至周五（不含中国法定节假日）9:00–12:00、14:00–18:00；
其余（含周末、法定节假日全天）为空闲时段。空闲价 = 峰价的一半。
法定节假日不在本模块内置（需要时传入 holiday 日期集合）。
"""
from __future__ import annotations

from datetime import datetime, time, timedelta, timezone

CNY = "CNY"
CN_TZ = timezone(timedelta(hours=8))

# 每百万 tokens（人民币）
PRICE = {
    "flash": {
        "in_miss": {"peak": 2.0, "off": 1.0},
        "in_hit": {"peak": 0.04, "off": 0.02},
        "out": {"peak": 8.0, "off": 4.0},
    },
    "v4-pro": {
        "in_miss": {"peak": 9.0, "off": 4.5},
        "in_hit": {"peak": 0.30, "off": 0.15},
        "out": {"peak": 27.0, "off": 13.5},
    },
}

# 每 1000 次成功请求（人民币）
SEARCH_CNY_PER_1K = 5.0
FETCH_CNY_PER_1K = 5.0

PEAK_WINDOWS = ((time(9, 0), time(12, 0)), (time(14, 0), time(18, 0)))


def is_peak(when: datetime | None = None,
            holidays: set[str] | None = None) -> bool:
    """是否处于高峰时段（按北京时间）。holidays 用 'YYYY-MM-DD'。"""
    dt = when or datetime.now(CN_TZ)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=CN_TZ)
    dt = dt.astimezone(CN_TZ)
    if dt.weekday() >= 5:          # 周六/周日全天空闲
        return False
    if holidays and dt.strftime("%Y-%m-%d") in holidays:
        return False
    t = dt.time()
    return any(start <= t < end for start, end in PEAK_WINDOWS)


def chat_cost(tokens_in_miss: int = 0, tokens_in_hit: int = 0,
              tokens_out: int = 0, *, peak: bool, model: str = "flash") -> float:
    """一次/一批 chat 调用的费用（人民币）。"""
    table = PRICE.get(model) or PRICE["flash"]
    tier = "peak" if peak else "off"
    return (tokens_in_miss / 1_000_000 * table["in_miss"][tier]
            + tokens_in_hit / 1_000_000 * table["in_hit"][tier]
            + tokens_out / 1_000_000 * table["out"][tier])


def call_cost(search_calls: int = 0, fetch_calls: int = 0) -> float:
    """Search / Fetch 按成功请求次数计费（人民币）。"""
    return (search_calls / 1000 * SEARCH_CNY_PER_1K
            + fetch_calls / 1000 * FETCH_CNY_PER_1K)


def estimate(usage: dict, *, peak: bool, model: str = "flash") -> dict:
    """把一次 run 的用量折算成人民币。

    usage = {
      "tokens_in_miss", "tokens_in_hit", "tokens_out",   # chat
      "search_calls", "fetch_calls",                      # 按次
    }
    返回 {"chat", "api_calls", "total", "peak", "model"}。
    """
    chat = chat_cost(int(usage.get("tokens_in_miss") or 0),
                     int(usage.get("tokens_in_hit") or 0),
                     int(usage.get("tokens_out") or 0),
                     peak=peak, model=model)
    calls = call_cost(int(usage.get("search_calls") or 0),
                      int(usage.get("fetch_calls") or 0))
    return {"chat": round(chat, 4), "api_calls": round(calls, 4),
            "total": round(chat + calls, 4),
            "peak": peak, "model": model}


def both_cases(usage: dict, model: str = "flash") -> dict:
    """峰/谷两个口径（同一份用量）。"""
    return {"peak": estimate(usage, peak=True, model=model),
            "off_peak": estimate(usage, peak=False, model=model)}
