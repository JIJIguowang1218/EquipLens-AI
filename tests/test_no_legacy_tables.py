# -*- coding: utf-8 -*-
"""词表守卫：主体代码不得引用 legacy 领域词表（见 docs/vocabulary-policy.md）。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def test_main_code_has_no_legacy_names():
    """主体代码（src/）不得出现任何旧词表名：它们已删除（2026-11-14）。"""
    banned = ("part_taxonomy", "category_profiles", "brand_aliases",
              "ENABLE_LEGACY", "data/legacy")
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for name in banned:
            assert name not in text, f"{path.relative_to(ROOT)} 仍引用 {name}"


def test_brand_table_silent_by_default():
    from equiplens import imagesearch
    assert imagesearch.BRAND_GROUPS == (), "品牌表必须为空（表已删除，无 legacy 开关）"


def test_legacy_tables_deleted():
    for name in ("part_taxonomy.json", "category_profiles.json", "brand_aliases.json"):
        assert not (ROOT / "data" / "legacy" / name).exists(), f"{name} 应已删除"


LEGACY_MODULES = ("textrun", "l3gate", "passage", "audit", "roster",
                  "corpus", "domainbench", "strategy")


def test_main_chain_imports_no_legacy_modules():
    """主链不得顺着 import 图把旧链路词表拉回来（policy §6）。"""
    for path in (ROOT / "src" / "equiplens" / "retrieval_engine").glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for mod in LEGACY_MODULES:
            bad = (f"from ..{mod} import" in text
                   or f"from .. import {mod}" in text
                   or f"import equiplens.{mod}" in text)
            assert not bad, f"{path.name} 引用了旧链路模块 {mod}"


if __name__ == "__main__":
    check("主体代码无旧词表名", test_main_code_has_no_legacy_names)
    check("品牌表默认空", test_brand_table_silent_by_default)
    check("legacy 文件已删除", test_legacy_tables_deleted)
    check("主链不 import 旧链路", test_main_chain_imports_no_legacy_modules)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"vocabulary_guard: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
