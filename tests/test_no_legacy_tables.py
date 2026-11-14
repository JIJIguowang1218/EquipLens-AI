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


def test_main_code_has_no_part_taxonomy():
    for rel in ("src/equiplens/briefing.py", "src/equiplens/analysis.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "part_taxonomy" not in text, rel


def test_brand_table_silent_by_default():
    from equiplens import imagesearch
    assert imagesearch.BRAND_GROUPS == (), "品牌表默认必须为空（用 EQUIPLENS_ENABLE_LEGACY_BRANDS=1 显式开启）"


def test_legacy_files_exist():
    for name in ("part_taxonomy.json", "category_profiles.json", "brand_aliases.json"):
        assert (ROOT / "data" / "legacy" / name).exists(), name


if __name__ == "__main__":
    check("主体代码无 part_taxonomy", test_main_code_has_no_part_taxonomy)
    check("品牌表默认静默", test_brand_table_silent_by_default)
    check("legacy 文件保留", test_legacy_files_exist)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"vocabulary_guard: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
