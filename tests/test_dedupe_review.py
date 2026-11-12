# -*- coding: utf-8 -*-
"""去重审核页生成测试（离线）。"""
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

spec = importlib.util.spec_from_file_location(
    "build_dedupe_review", ROOT / "scripts" / "build_dedupe_review.py")
dr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dr)

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


PLAN = {
    "brief_id": "b-test",
    "candidates": [
        {"model": "6×6 沙漠运输车（400马力 25吨级）", "identity_kind": "generic",
         "model_variants": ["6×6 沙漠运输车（400马力 25吨级）"],
         "source_queries": [{"query_id": "q-base", "query": "沙漠 6×6"}],
         "sources": ["https://a.example/1"]},
        {"model": "东风 6×6 沙漠运输车（400 马力 25 吨级）", "identity_kind": "generic",
         "model_variants": ["东风 6×6 沙漠运输车（400 马力 25 吨级）"],
         "source_queries": [{"query_id": "q-env", "query": "沙漠 工程车"}],
         "sources": ["https://b.example/2"]},
        {"model": "Zetros 4051 AS 6×6", "identity_kind": "series",
         "model_variants": ["Zetros 4051 AS 6×6", "Zetros 4051 AS 6×6 牵引车"],
         "source_queries": [], "sources": []},
    ],
    "dedupe": {"input": 5, "unique": 3, "removed": 2},
    "queries": [{}, {}, {}],
}


def test_payload_flags_similar_pairs():
    p = dr.build_payload(PLAN, {"brief_id": "b-test", "request": {"class": "沙漠牵引车"}})
    assert p["stats"]["unique"] == 3, p["stats"]
    assert p["stats"]["variants"] == 4, p["stats"]
    pairs = {(x["a"], x["b"]) for x in p["suggested_pairs"]}
    assert (0, 1) in pairs, p["suggested_pairs"]


def test_html_contains_controls():
    html = dr.render_html(dr.build_payload(PLAN, None))
    for token in ("去重审核", "导出判定 JSON", "合并正确", "应拆分", "dedupe-verdicts.json"):
        assert token in html, token


if __name__ == "__main__":
    check("疑似同款配对", test_payload_flags_similar_pairs)
    check("页面控件", test_html_contains_controls)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"dedupe_review: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
