# -*- coding: utf-8 -*-
"""换机器自检：Python / 依赖 / API key / 门卫模型 / 测试文件是否就绪。

用法:
  python scripts/check_env.py
不打印 key 明文，不联网。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def ok(label: str, extra: str = "") -> None:
    print(f"  [OK]   {label}" + (f" — {extra}" if extra else ""))


def warn(label: str, extra: str = "") -> None:
    print(f"  [WARN] {label}" + (f" — {extra}" if extra else ""))


def bad(label: str, extra: str = "") -> None:
    print(f"  [FAIL] {label}" + (f" — {extra}" if extra else ""))


def main() -> int:
    fails = 0
    print("EquipLens-AI 环境自检")
    v = sys.version_info
    if (v.major, v.minor) == (3, 11):
        ok("Python", f"{v.major}.{v.minor}.{v.micro}")
    else:
        warn("Python", f"{v.major}.{v.minor}.{v.micro}（项目验证 3.11）")

    for mod in ("PIL", "jsonschema", "requests"):
        if importlib.util.find_spec(mod):
            ok(f"依赖 {mod}")
        else:
            bad(f"依赖 {mod}", "pip install -r requirements.txt")
            fails += 1
    for mod, optional in (("uform", False), ("torch", True)):
        if importlib.util.find_spec(mod):
            ok(f"依赖 {mod}")
        elif optional:
            warn(f"依赖 {mod}", "跑当前 loop 非必须；Chinese-CLIP 探针才需要")
        else:
            bad(f"依赖 {mod}", "pip install -r requirements.txt")
            fails += 1

    key_file = Path.home() / ".equiplens" / "deepseek.env"
    if not key_file.exists():
        bad("DeepSeek key 文件", f"缺少 {key_file}；新会话先向用户要 key")
        fails += 1
    else:
        text = key_file.read_text(encoding="utf-8", errors="ignore")
        line = next((x for x in text.splitlines() if x.startswith("DEEPSEEK_API_KEY=")), "")
        val = line.split("=", 1)[1].strip() if line else ""
        if val.startswith("sk-") and len(val) > 20:
            ok("DeepSeek key", f"{key_file}（sk-***{val[-4:]}）")
        else:
            bad("DeepSeek key", f"{key_file} 里没有有效的 DEEPSEEK_API_KEY=sk-...")
            fails += 1

    model = (Path.home() / ".cache" / "huggingface" / "hub"
             / "models--unum-cloud--uform3-image-text-english-small")
    if model.exists():
        ok("门卫模型缓存", str(model))
    else:
        warn("门卫模型缓存", "首次跑 test_gate 会自动下载约 59MB（HF_ENDPOINT 已设镜像）")

    checks = [
        "tests/test_gate.py", "tests/test_imagesearch.py",
        "tests/test_retrieval_engine.py",
        "data-test/evals/task-briefs-20261109/brief-m1b-global.json",
        "data-test/evals/image-gate-52-20261109.json",
    ]
    for rel in checks:
        if (ROOT / rel).exists():
            ok(f"文件 {rel}")
        else:
            bad(f"文件 {rel}")
            fails += 1

    print("\n下一步：")
    print("  PYTHONPATH=src python tests/test_retrieval_engine.py   # 40/40")
    print("  PYTHONPATH=src python tests/test_imagesearch.py        # 14/14")
    print("  PYTHONPATH=src python tests/test_planning.py           # 14/14")
    print("  PYTHONPATH=src python tests/test_gate.py               # 11/11")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
