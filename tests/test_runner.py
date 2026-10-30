# -*- coding: utf-8 -*-
"""runner 测试：契约判定/重试/降级链/断点续跑（全离线，collect 用假实现）。"""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import runner  # noqa: E402

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:160]))


def make_report(td: Path, saved: int, failed: int, batch: str) -> dict:
    outdir = td / batch
    outdir.mkdir(parents=True, exist_ok=True)
    index = [{"status": "saved"}] * saved + [{"status": "fetch_failed"}] * failed
    (outdir / "index.json").write_text(json.dumps({"index": index}),
                                       encoding="utf-8")
    return {"batch_id": batch, "outdir": str(outdir), "index": index,
            "summary": {}}


def test_success_first_attempt():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        calls = []

        def collect(plan):
            calls.append(plan.get("serp_channel"))
            return make_report(td, 3, 0, "b1")

        res = runner.run_unit(
            runner.Unit("u1", {"batch_id": "b1"}), collect=collect,
            grade=lambda d: {"docs": [{"a_count": 2}], "metrics": {}},
            data_dir=td, state_root=td / "state", sleep=lambda s: None)
        assert res.status == "ok", res
        assert res.attempts == 1 and res.channel == "auto", res
        assert res.saved == 3 and res.candidates == 2, res


def test_blocked_then_bing_fallback():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        calls = []

        def collect(plan):
            ch = plan["serp_channel"]
            calls.append(ch)
            if ch == "auto":
                return make_report(td, 0, 5, "b-auto")
            return make_report(td, 3, 0, "b-bing")

        res = runner.run_unit(
            runner.Unit("u2", {"batch_id": "b2"}), collect=collect,
            grade=lambda d: {"docs": [{"a_count": 1}], "metrics": {}},
            data_dir=td, state_root=td / "state", sleep=lambda s: None)
        assert res.status == "ok", res
        assert res.attempts == 2 and res.channel == "bing", res
        assert calls == ["auto", "bing"], calls


def test_all_channels_fail():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)

        def collect(plan):
            return make_report(td, 0, 5, "b-fail")

        res = runner.run_unit(
            runner.Unit("u3", {"batch_id": "b3"}), collect=collect,
            grade=lambda d: {"docs": [], "metrics": {}},
            data_dir=td, state_root=td / "state", sleep=lambda s: None)
        assert res.status == "failed", res
        assert res.blockers, res


def test_low_yield_degrades_then_retries():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        calls = []

        def collect(plan):
            calls.append(plan["serp_channel"])
            return make_report(td, 1, 0, "b-low")  # 1 < min_saved 2

        res = runner.run_unit(
            runner.Unit("u4", {"batch_id": "b4"},
                        contract=runner.Contract(min_saved=2)),
            collect=collect,
            grade=lambda d: {"docs": [{"a_count": 0}], "metrics": {}},
            data_dir=td, state_root=td / "state", sleep=lambda s: None)
        assert res.status == "degraded", res
        assert any("low_yield" in b for b in res.blockers), res
        # 2 次尝试 × 2 个通道（auto/bing）
        assert len(calls) == 4, calls


def test_resume_skips_done_unit():
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        first = []

        def collect_ok(plan):
            first.append(1)
            return make_report(td, 3, 0, "b-ok")

        res1 = runner.run_unit(
            runner.Unit("u5", {"batch_id": "b-ok"}), collect=collect_ok,
            grade=lambda d: {"docs": [{"a_count": 1}], "metrics": {}},
            data_dir=td, state_root=td / "state", sleep=lambda s: None)
        assert res1.status == "ok"

        def boom(plan):
            raise AssertionError("resume 后不应再次采集")

        res2 = runner.run_unit(
            runner.Unit("u5", {"batch_id": "b-ok"}), collect=boom,
            grade=lambda d: {"docs": [{"a_count": 1}], "metrics": {}},
            data_dir=td, state_root=td / "state", sleep=lambda s: None)
        assert res2.status == "ok", res2
        assert len(first) == 1, first


def test_retry_backoff():
    p = runner.RetryPolicy(max_attempts=3, initial_ms=1000, backoff=2.0)
    assert [p.delay_ms(i) for i in (1, 2, 3)] == [1000, 2000, 4000]


if __name__ == "__main__":
    check("首轮成功即 ok", test_success_first_attempt)
    check("被拦后换 Bing 降级链", test_blocked_then_bing_fallback)
    check("全通道失败 → failed + blockers", test_all_channels_fail)
    check("低产出 → degraded 并重试", test_low_yield_degrades_then_retries)
    check("断点续跑跳过已完成单元", test_resume_skips_done_unit)
    check("重试退避序列", test_retry_backoff)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"runner: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
