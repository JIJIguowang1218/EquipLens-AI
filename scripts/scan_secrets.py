# -*- coding: utf-8 -*-
"""密钥/敏感标识扫描（提交前自检）。

背景：2026-11-12 GitHub 告警 commit 340ae47 泄露 Tencent WeChat API App ID——
实际是第三方 CDN 图片 URL 里的 `wx<16 hex>`（AppID 是公开标识，不是密钥），
但仍按“不在公开仓库留标识”处理：历史已改写，并加本扫描防复发。

用法:
  python scripts/scan_secrets.py            # 扫 git 跟踪文件（CI/提交前）
  python scripts/scan_secrets.py --fix      # 把 wx AppID 替换为 wx-REDACTED（谨慎）
  python scripts/scan_secrets.py --paths a.json b.json
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERNS = [
    ("wechat_appid", re.compile(r"wx[0-9a-f]{16}")),
    ("llm_api_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("github_pat", re.compile(r"ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}")),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


def scan_text(text: str) -> list[tuple[str, str, int]]:
    """返回 [(kind, match, line_no)]。"""
    hits = []
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            hits.append((kind, m.group(0), line))
    return hits


def tracked_files() -> list[Path]:
    try:
        out = subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True)
    except Exception:  # noqa: BLE001
        return []
    return [ROOT / x for x in out.splitlines() if x]


def scan_paths(paths: list[Path]) -> list[tuple[Path, str, str, int]]:
    found = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for kind, match, line in scan_text(text):
            found.append((p, kind, match, line))
    return found


def fix_paths(paths: list[Path]) -> int:
    changed = 0
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        new = PATTERNS[0][1].sub("wx-REDACTED", text)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*", default=None)
    ap.add_argument("--fix", action="store_true", help="把 wx AppID 替换为 wx-REDACTED")
    args = ap.parse_args(argv)
    paths = [Path(x) for x in args.paths] if args.paths else tracked_files()
    if args.fix:
        n = fix_paths(paths)
        print(f"redacted {n} file(s)")
        return 0
    found = scan_paths(paths)
    for p, kind, match, line in found:
        rel = p.relative_to(ROOT) if p.is_relative_to(ROOT) else p
        print(f"{rel}:{line}: {kind}: {match[:8]}***")
    print(f"scanned {len(paths)} file(s), {len(found)} hit(s)")
    return 0 if not found else 1


if __name__ == "__main__":
    raise SystemExit(main())
