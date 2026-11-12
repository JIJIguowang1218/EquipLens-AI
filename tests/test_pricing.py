# -*- coding: utf-8 -*-
"""定价（峰/谷）测试：官方价目表 + 时段判定。"""
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import pricing  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def test_peak_windows():
    # 2026-11-12 是周四
    assert pricing.is_peak(datetime(2026, 11, 12, 10, 0)) is True
    assert pricing.is_peak(datetime(2026, 11, 12, 13, 0)) is False   # 午休/谷
    assert pricing.is_peak(datetime(2026, 11, 12, 15, 0)) is True
    assert pricing.is_peak(datetime(2026, 11, 12, 18, 30)) is False
    assert pricing.is_peak(datetime(2026, 11, 14, 10, 0)) is False   # 周六
    assert pricing.is_peak(datetime(2026, 11, 13, 10, 0),
                           holidays={"2026-11-13"}) is False       # 节假日


def test_chat_cost_matches_official_table():
    # 100 万未命中输入 + 100 万输出，峰时：2 + 8 = 10 元
    assert pricing.chat_cost(1_000_000, 0, 1_000_000, peak=True) == 10.0
    assert pricing.chat_cost(1_000_000, 0, 1_000_000, peak=False) == 5.0
    # 缓存命中价
    assert pricing.chat_cost(1_000_000, 1_000_000, 0, peak=True) == 2.04


def test_call_cost():
    assert pricing.call_cost(1000, 0) == pricing.SEARCH_CNY_PER_1K
    assert pricing.call_cost(0, 2000) == 10.0


def test_both_cases_half():
    usage = {"tokens_in_miss": 500_000, "tokens_out": 100_000,
             "search_calls": 6, "fetch_calls": 20}
    both = pricing.both_cases(usage)
    assert both["peak"]["total"] > both["off_peak"]["total"]
    assert abs(both["peak"]["total"] - both["off_peak"]["total"]) > 0


if __name__ == "__main__":
    check("峰/谷时段判定", test_peak_windows)
    check("chat 单价", test_chat_cost_matches_official_table)
    check("Search/Fetch 单价", test_call_cost)
    check("峰谷两口径", test_both_cases_half)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"pricing: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
