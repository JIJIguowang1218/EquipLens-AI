# -*- coding: utf-8 -*-
"""把 data-test/ui-fixtures/*.json 转成高保真页可直接用的 data.js。

file:// 下 fetch 会被 CORS 拦，所以把 fixture 内联成 JS 全局变量。
图片路径改写成相对 docs/ui-hifi/ 的路径。

用法：python scripts/build_hifi_data.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data-test" / "ui-fixtures"
OUT = ROOT / "docs" / "ui-hifi" / "data.js"
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PREFIX = "data-test/ab-images/"


def rel(p: str) -> str:
    return "../../" + p if p.startswith(PREFIX) else p


def main() -> int:
    s1 = json.loads((FIX / "s1-retrieval.json").read_text(encoding="utf-8"))
    s2 = json.loads((FIX / "s2-analysis.json").read_text(encoding="utf-8"))
    s3 = json.loads((FIX / "s3-report.json").read_text(encoding="utf-8"))

    for c in s1["cards"]:
        c["images"] = [rel(x) for x in c["images"]]
        folder = (c["images"][0].split("/")[-2] if c["images"] else "")
        brand = ""
        for key, name in (("德龙", "陕汽"), ("豪沃", "重汽"), ("HOWO", "重汽"),
                          ("汕德卡", "重汽"), ("解放", "一汽"), ("JH6", "一汽"),
                          ("红岩", "上汽红岩"), ("北奔", "北奔"), ("三一", "三一"),
                          ("东风", "东风"), ("H6066", "陕汽"), ("重汽", "重汽")):
            if key.lower() in c["model"].lower():
                brand = name
                break
        cfg = re.search(r"(\d)[xX×](\d)", folder)
        c["brand"] = brand
        c["config"] = f"{cfg.group(1)}×{cfg.group(2)}" if cfg else ""
        c["label"] = " · ".join(x for x in (c["config"], brand) if x)
    for v in s2["vehicles"]:
        for w in v["views"]:
            w["image"] = rel(w["image"])
    for p in s3["pages"]:
        for b in p.get("blocks", []):
            if b.get("kind") == "image":
                b["src"] = rel(b["src"])

    payload = {"s1": s1, "s2": s2, "s3": s3}
    body = json.dumps(payload, ensure_ascii=False, indent=1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "/* 自动生成，勿手改：python scripts/build_hifi_data.py\n"
        "   来源：data-test/ui-fixtures/*.json（模拟数据） */\n"
        "window.HIFI = " + body + ";\n", encoding="utf-8")
    print(f"[ok] {OUT.relative_to(ROOT)}  s1={len(s1['cards'])} "
          f"s2={len(s2['vehicles'])} s3={len(s3['pages'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
