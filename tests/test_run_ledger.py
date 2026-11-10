# -*- coding: utf-8 -*-
"""运行台账生成器测试（离线；依赖仓库内真实 run 目录作为夹具）。"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

spec = importlib.util.spec_from_file_location("run_ledger", ROOT / "scripts" / "run_ledger.py")
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def test_stage_mapping():
    assert ledger._stage("loop-ab4-a2-20261111") == "loop"
    assert ledger._stage("plan-ab4-20261111") == "plan"
    assert ledger._stage("web-smoke-v5-20261109") == "search"
    assert ledger._stage("filter-98-20261109") == "gate"


def test_run_record_has_metrics_and_conclusion():
    rec = ledger.build_record(ROOT / "data-test" / "runs" / "loop-ab4-a2-20261111")
    assert rec["kind"] == "run", rec
    assert rec["status"] == "DONE", rec
    assert rec["metrics"].get("delivery") == "12/12", rec["metrics"]
    assert rec["conclusion"], rec
    assert rec["report"] == "" and rec["audit"].endswith("audit.html"), rec


def test_plan_set_record():
    rec = ledger.build_record(ROOT / "data-test" / "runs" / "plan-ab4-20261111")
    assert rec["kind"] == "plan-set", rec
    assert len(rec.get("plans") or []) == 6, rec


def test_index_complete():
    idx = json.loads((ROOT / "data-test" / "runs" / "INDEX.json").read_text(encoding="utf-8"))
    assert idx["counts"]["all"] == len(idx["records"])
    for rec in idx["records"]:
        if rec["kind"] in ("empty", "archived"):
            continue
        assert (ROOT / "data-test" / "runs" / rec["run_id"] / "RUN.json").exists(), rec["run_id"]
    assert (ROOT / "data-test" / "runs" / "README.md").exists()


if __name__ == "__main__":
    check("阶段映射", test_stage_mapping)
    check("run 记录含指标/结论", test_run_record_has_metrics_and_conclusion)
    check("plan-set 记录", test_plan_set_record)
    check("索引覆盖所有非空 run", test_index_complete)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"run_ledger: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
