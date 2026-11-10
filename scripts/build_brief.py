# -*- coding: utf-8 -*-
"""任务单生成 CLI：用户输入 → DeepSeek Chat → 校验 → brief.json。

用法:
  python scripts/build_brief.py \
    --input "沙漠牵引车，重点看登车踏步、大灯、前轮拱、防护栏、保险杠；沙漠/油田工况；6×6；12 台" \
    --slots 12 --out data-test/briefs/brief-auto.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import briefing  # noqa: E402

KEY_FILE = Path.home() / ".equiplens" / "deepseek.env"


def load_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    if KEY_FILE.exists():
        for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit(
        "no DEEPSEEK_API_KEY：请先提供 key（~/.equiplens/deepseek.env 或环境变量），"
        "本脚本不允许手工代写 brief。")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="", help="用户原话")
    ap.add_argument("--input-file", default="", help="或从文件读用户原话")
    ap.add_argument("--class", dest="klass", default="", help="车型类别（可选的强制值）")
    ap.add_argument("--parts", default="", help="可选：逗号分隔的期望部件（提示，不强制）")
    ap.add_argument("--slots", type=int, default=12)
    ap.add_argument("--out", required=True)
    ap.add_argument("--meta", default="", help="默认 <out>.meta.json")
    ap.add_argument("--brief-id", default="")
    ap.add_argument("--model", default="deepseek-flash")
    args = ap.parse_args(argv)

    raw = args.input.strip()
    if args.input_file:
        raw = Path(args.input_file).read_text(encoding="utf-8").strip()
    if not raw:
        ap.error("需要 --input 或 --input-file")

    key = load_key()
    hints = [x.strip() for x in args.parts.split(",") if x.strip()]
    t0 = time.time()
    try:
        out = briefing.generate_brief(raw, key, slots=args.slots, class_hint=args.klass,
                                      part_hints=hints, brief_id=args.brief_id,
                                      model=args.model)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": type(e).__name__, "message": str(e)[:400]},
                         ensure_ascii=False))
        return 2

    brief = out["brief"]
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(brief, ensure_ascii=False, indent=1), encoding="utf-8")
    meta_path = Path(args.meta) if args.meta else path.with_suffix(path.suffix + ".meta.json")
    meta = {
        "ok": True,
        "source": "deepseek-chat",
        "model": out["response"].get("model") or args.model,
        "skill_version": briefing.SKILL_VERSION,
        "skill_path": "skills/task-brief/SKILL.md",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "raw_input": raw,
        "brief_path": str(path),
        "attempts": out["attempts"],
        "usage": out["response"].get("usage") or {},
        "validation": {"ok": True, "errors": []},
        "llm_payload": out["response"].get("payload") or {},
        "duration_ms": round((time.time() - t0) * 1000),
    }
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "brief_id": brief["brief_id"],
        "class": brief["request"]["class"],
        "parts": [p["part"] for p in brief["part_requirements"]],
        "units": [(u["unit_id"], u["quota"]) for u in brief["research_units"]],
        "assumptions": len(brief["assumptions"]),
        "out": str(path),
        "meta": str(meta_path),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
