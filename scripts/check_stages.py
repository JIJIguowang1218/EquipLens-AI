# -*- coding: utf-8 -*-
"""状态机检查：确认正式链路入口存在，旧机制标记为 silent。

用法：PYTHONPATH=src python scripts/check_stages.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "stages.json"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    data = json.loads(SPEC.read_text(encoding="utf-8"))
    issues = []
    print(f"{'阶段':<6}{'状态':<10}{'版本':<18}入口")
    for st in data.get("stages", []):
        sid, status, ver = st["id"], st["status"], st.get("version", "")
        entries = st.get("entries") or []
        if status == "active" and not entries:
            issues.append(f"{sid} active 但没有入口")
        names = []
        for e in entries:
            p = ROOT / e["path"]
            if not p.exists():
                issues.append(f"{sid} 入口不存在：{e['path']}")
                continue
            text = p.read_text(encoding="utf-8")
            if e["symbol"] not in text:
                issues.append(f"{sid} 入口符号缺失：{e['path']}::{e['symbol']}")
            names.append(f"{e['path']}::{e['symbol']}")
        for lg in st.get("legacy") or []:
            p = ROOT / lg["path"]
            if not p.exists():
                issues.append(f"{sid} legacy 不存在：{lg['path']}")
            elif lg.get("status") != "silent":
                issues.append(f"{sid} legacy 未标 silent：{lg['path']}")
            else:
                text = p.read_text(encoding="utf-8")
                if lg["symbol"] not in text:
                    issues.append(f"{sid} legacy 符号缺失：{lg['path']}::{lg['symbol']}")
        print(f"{sid:<6}{status:<10}{ver:<18}{'; '.join(names) or '—'}")
    print(f"\n状态机：{len(data.get('stages', []))} 个阶段，{len(issues)} 个问题")
    for x in issues:
        print("  [FAIL]", x)
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
