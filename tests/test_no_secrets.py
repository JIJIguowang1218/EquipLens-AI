# -*- coding: utf-8 -*-
"""仓库密钥卫生测试（不联网）。

1) 模式自检：构造字符串避免把真实值写进测试文件；
2) 全仓扫描：git 跟踪文件里不允许出现 WeChat AppID / sk- / GitHub PAT / AWS key / 私钥头。
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

spec = importlib.util.spec_from_file_location(
    "scan_secrets", ROOT / "scripts" / "scan_secrets.py")
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

results = []


def check(name, fn):
    try:
        fn()
        results.append((name, "PASS", ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, "FAIL", str(e)[:200]))


def test_patterns():
    appid = "wx" + "0123456789abcdef"
    key = "sk-" + "a" * 24
    text = f"url https://x/wxmpup/{appid}/a.jpg\ntoken={key}\n"
    kinds = {k for k, _, _ in scan.scan_text(text)}
    assert "wechat_appid" in kinds, kinds
    assert "llm_api_key" in kinds, kinds
    assert scan.scan_text("https://img.example/a.jpg") == []


def test_repo_is_clean():
    found = scan.scan_paths(scan.tracked_files())
    assert not found, [f"{p}:{line} {k}" for p, k, _, line in found[:5]]


if __name__ == "__main__":
    check("敏感模式识别", test_patterns)
    check("仓库无敏感标识", test_repo_is_clean)
    fails = [r for r in results if r[1] == "FAIL"]
    for name, status, err in results:
        print(f"  [{status}] {name}" + (f" — {err}" if err else ""))
    print(f"secrets: {len(results) - len(fails)}/{len(results)} 通过")
    sys.exit(1 if fails else 0)
