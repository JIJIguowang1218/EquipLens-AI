# -*- coding: utf-8 -*-
"""收集批量编辑器下载的 *-boxes.json，校验后落到指定目录。

用法:
  PYTHONPATH=src python scripts/collect_boxes.py --src ~/Downloads --out data-test/edit-batch
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def valid(item: dict) -> bool:
    parts = item.get("parts")
    if not isinstance(parts, list) or not parts:
        return False
    for p in parts:
        b = p.get("bbox")
        if not (isinstance(b, list) and len(b) == 4):
            return False
        if not all(isinstance(x, (int, float)) and 0 <= x <= 1000 for x in b):
            return False
        if b[2] - b[0] < 8 or b[3] - b[1] < 8:
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(Path.home() / "Downloads"))
    ap.add_argument("--out", default="data-test/edit-batch")
    ap.add_argument("--model", help="只收指定车型（可选）")
    args = ap.parse_args()

    src = Path(args.src).expanduser()
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    got, bad = 0, 0
    for f in sorted(src.glob("*-boxes.json")):
        try:
            item = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            bad += 1
            continue
        slug = item.get("slug")
        if not slug or (args.model and slug != args.model) or not valid(item):
            bad += 1
            continue
        target = outdir / f"{slug}-boxes.json"
        target.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
        got += 1
        print(f"[ok] {f.name} → {target.name}  parts={len(item['parts'])}")

    print(f"\n收录 {got} 个，跳过 {bad} 个；目录 {outdir}")
    return 0 if got else 1


if __name__ == "__main__":
    sys.exit(main())
