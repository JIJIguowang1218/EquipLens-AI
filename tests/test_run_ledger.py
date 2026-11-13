# -*- coding: utf-8 -*-
"""运行台账生成器测试（离线；依赖仓库内真实 run 目录作为夹具）。"""
import importlib.util
import json
import sys
import tempfile
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


def _tmp_run(summary=None, run_json=None):
    td = tempfile.TemporaryDirectory()
    p = Path(td.name)
    if summary is not None:
        (p / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    if run_json is not None:
        (p / "RUN.json").write_text(json.dumps(run_json), encoding="utf-8")
    return td, p


def test_auto_conclusion_keeps_needs_review():
    """机器摘要不能自证已复核：没有人工结论时 needs_review 必须为 True。"""
    td, p = _tmp_run(summary={"state": "DONE",
                              "delivery": {"required": 12, "delivered": 12, "degraded": 8}})
    try:
        rec = ledger.build_record(p)
        assert rec["conclusion"] == "", rec
        assert rec["auto_conclusion"].startswith("DONE 12/12"), rec
        assert rec["needs_review"] is True, rec
        assert rec["conclusion_source"] == "auto", rec
    finally:
        td.cleanup()


def test_manual_conclusion_clears_needs_review():
    td, p = _tmp_run(summary={"state": "DONE"},
                     run_json={"conclusion": "人工复核：12/12 可用"})
    try:
        rec = ledger.build_record(p)
        assert rec["conclusion"] == "人工复核：12/12 可用", rec
        assert rec["needs_review"] is False, rec
        assert rec["conclusion_source"] == "stored", rec
    finally:
        td.cleanup()


def test_legacy_auto_conclusion_migrates():
    """旧版 RUN.json 里的机器摘要要迁移到 auto_conclusion，并重新标待复核。"""
    td, p = _tmp_run(
        summary={"state": "DONE",
                 "delivery": {"required": 12, "delivered": 12, "degraded": 8}},
        run_json={"conclusion": "DONE 12/12（degraded=8）", "needs_review": False})
    try:
        rec = ledger.build_record(p)
        assert rec["conclusion"] == "", rec
        assert rec["auto_conclusion"] == "DONE 12/12（degraded=8）", rec
        assert rec["needs_review"] is True, rec
    finally:
        td.cleanup()


def test_run_date_and_commit_are_preserved():
    """重建索引时不得把历史 run 的 date/git_commit 改写成“生成时的 HEAD/mtime”。"""
    td, p = _tmp_run(summary={"state": "DONE"},
                     run_json={"date": "2026-11-02", "git_commit": "abc1234"})
    try:
        rec = ledger.build_record(p)
        assert rec["date"] == "2026-11-02", rec
        assert rec["git_commit"] == "abc1234", rec
    finally:
        td.cleanup()


if __name__ == "__main__":
    check("阶段映射", test_stage_mapping)
    check("run 记录含指标/结论", test_run_record_has_metrics_and_conclusion)
    check("plan-set 记录", test_plan_set_record)
    check("索引覆盖所有非空 run", test_index_complete)
    check("机器摘要不抵人工结论", test_auto_conclusion_keeps_needs_review)
    check("人工结论关闭待复核", test_manual_conclusion_clears_needs_review)
    check("旧机器结论迁移", test_legacy_auto_conclusion_migrates)
    check("run 日期/提交不被重写", test_run_date_and_commit_are_preserved)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"run_ledger: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
