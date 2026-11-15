# -*- coding: utf-8 -*-
"""换机器 / 换环境后的主体代码检查（不联网）。

用法:
  PYTHONPATH=src python scripts/check_machine.py          # 默认：轻量检查
  PYTHONPATH=src python scripts/check_machine.py --full   # 加跑引擎/图片/分析测试
  PYTHONPATH=src python scripts/check_machine.py --json   # 机器可读

检查：状态机入口 → S0/S1/S2 相关单测 → 台账完整性 → 密钥扫描。
失败时退出码 1；不打印任何密钥明文。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

LIGHT = [
    ("状态机", ["scripts/check_stages.py"]),
    ("S0 任务单", ["tests/test_taskspec.py"]),
    ("S0 brief 接入", ["tests/test_briefing.py"]),
    ("标识归一", ["tests/test_identity.py"]),
    ("查询规划", ["tests/test_planning.py"]),
    ("台账脚本", ["tests/test_run_ledger.py"]),
    ("词表守卫", ["tests/test_no_legacy_tables.py"]),
    ("台账完整性", ["scripts/run_ledger.py", "--check"]),
    ("密钥扫描", ["scripts/scan_secrets.py"]),
]
FULL = [
    ("检索引擎", ["tests/test_retrieval_engine.py"]),
    ("图片检索", ["tests/test_imagesearch.py"]),
    ("分析模块", ["tests/test_analysis.py"]),
]


def run_one(name: str, args: list[str]) -> dict:
    t0 = time.time()
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    try:
        p = subprocess.run([PY, *args], cwd=ROOT, env=env, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=180)
        out = (p.stdout or "") + (p.stderr or "")
        tail = [x for x in out.strip().splitlines() if x.strip()][-1:] or [""]
        return {"name": name, "ok": p.returncode == 0, "code": p.returncode,
                "tail": tail[0][:160], "ms": round((time.time() - t0) * 1000)}
    except Exception as e:  # noqa: BLE001
        return {"name": name, "ok": False, "code": -1, "tail": str(e)[:160],
                "ms": round((time.time() - t0) * 1000)}


def context() -> dict:
    active = []
    try:
        data = json.loads((ROOT / "docs" / "stages.json").read_text(encoding="utf-8"))
        active = [f"{s['id']}={s.get('version') or s['status']}" for s in data.get("stages", [])
                  if s.get("status") == "active"]
    except Exception:  # noqa: BLE001
        pass
    return {"python": sys.version.split()[0], "cwd": str(ROOT), "active_stages": active}


def main(argv: list[str]) -> int:
    full = "--full" in argv
    as_json = "--json" in argv
    checks = LIGHT + (FULL if full else [])
    ctx = context()
    results = [run_one(name, args) for name, args in checks]
    ok = all(r["ok"] for r in results)
    if as_json:
        print(json.dumps({"ok": ok, "context": ctx, "results": results},
                         ensure_ascii=False, indent=1))
        return 0 if ok else 1
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    print("EquipLens-AI 主体代码检查")
    print(f"  Python {ctx['python']} · {ctx['cwd']}")
    print(f"  正式阶段：{' / '.join(ctx['active_stages']) or '（未读到 stages.json）'}")
    print()
    for r in results:
        flag = "PASS" if r["ok"] else "FAIL"
        print(f"  [{flag}] {r['name']:<12} {r['ms']:>5}ms  {r['tail']}")
    print()
    print("结果：" + ("全部通过" if ok else "存在失败；先看上面的 FAIL，再对照 docs/STAGES.md"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
