# -*- coding: utf-8 -*-
"""交付清单生成测试（离线，用仓库内真实 run 作为夹具）。"""
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
    "build_delivery_manifest", ROOT / "scripts" / "build_delivery_manifest.py")
man = importlib.util.module_from_spec(spec)
spec.loader.exec_module(man)

RUN = ROOT / "data-test" / "runs" / "verify-yield3-20261112"
BRIEF = ROOT / "data-test" / "evals" / "task-briefs-20261109" / "brief-m1-desert.json"
PLAN = ROOT / "data-test" / "runs" / "plan-ab4-20261111" / "A2" / "plan-ranked.json"

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def test_manifest_sections():
    m = man.build_manifest(RUN, BRIEF, PLAN)
    for key in ("user_delivery", "monitoring", "reusable"):
        assert key in m, key
    assert m["user_delivery"]["summary"]["delivered"] == 12, m["user_delivery"]["summary"]
    assert len(m["user_delivery"]["backup"]) == 4, len(m["user_delivery"]["backup"])


def test_images_and_cost():
    m = man.build_manifest(RUN, BRIEF, PLAN)
    first = m["user_delivery"]["delivered"][0]
    assert first["images"] is not None, first
    # images/ 是 gitignore 的：换机器/新 clone 时文件不存在，
    # 此时只能校验结构；有图片文件时才校验数量。
    images_dir = RUN / "images"
    has_files = images_dir.exists() and any(images_dir.rglob("*.jpg"))
    if has_files:
        assert sum(len(v) for v in first["images"].values()) > 0, first
    c = m["monitoring"]["cost_cny"]
    assert c["peak"]["total"] >= c["off_peak"]["total"] > 0, c
    assert "timings" in m["monitoring"], m["monitoring"]


def test_render_md_has_three_sections():
    md = man.render_md(man.build_manifest(RUN, BRIEF, PLAN))
    for title in ("一、用户交付物", "二、内部监控", "三、可复用中间产物"):
        assert title in md, title


if __name__ == "__main__":
    check("三块结构", test_manifest_sections)
    check("图片与成本", test_images_and_cost)
    check("Markdown 三节", test_render_md_has_three_sections)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"delivery_manifest: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
