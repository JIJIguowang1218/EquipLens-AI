# -*- coding: utf-8 -*-
"""无提示识别探针：只给图，不给候选名单、不给文件名、不给任何文字线索。

真值来自库内 vehicle 绑定，仅用于打分，不进入 prompt。

用法:
  PYTHONPATH=src python scripts/identify_probe.py --n 20 --out data-test/identify-20261031
"""

from __future__ import annotations

import argparse
import base64
import json
import random
import re
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

VIEWS = ("hero_lf", "hero_rf", "hero_45", "front", "side", "side_l")

PROMPT = """只看这张图，回答：这是什么品牌、什么型号的车辆？
要求：
- 不确定就写 unknown，不要猜；宁可 unknown 也不要编一个近似的
- evidence 写你依据的可见特征（车标/字样/格栅/驾驶室造型），≤25 字
只输出 JSON：{"brand":"","model":"","confidence":0.0,"evidence":""}"""


def norm(s: str) -> str:
    return re.sub(r"[\s\-_·]+", "", (s or "").lower())


def call(cfg: dict, path: Path) -> dict:
    b64 = base64.b64encode(path.read_bytes()).decode()
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    payload = {"model": cfg["LLM_VISION_MODEL"], "reasoning_effort": "low",
               "max_tokens": 3000,
               "messages": [{"role": "user", "content": [
                   {"type": "text", "text": PROMPT},
                   {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]}
    req = urllib.request.Request(cfg["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {cfg['LLM_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    text = d["choices"][0]["message"]["content"] or ""
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {"brand": "PARSE_FAIL", "model": "", "evidence": ""}


def score(truth: dict, got: dict) -> str:
    tb = norm(truth.get("brand"))
    tm = norm(truth.get("model") or truth.get("model_name"))
    gb, gm = norm(got.get("brand")), norm(got.get("model"))
    if gm in ("unknown", "") or gb in ("unknown", ""):
        return "unknown" if not gm else "wrong"
    if (tm and (tm in gm or gm in tm)) or (tm and tm in gb):
        return "exact"
    if tb and (tb in gb or gb in tb):
        return "brand_only"
    return "wrong"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    cfg = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

    conn = sqlite3.connect(ROOT / "data-test/equiplens.db")
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"""select v.id vid, v.brand, v.model_name, v.category, a.file_path,
                   a.view_angle, a.width, a.height
            from assets a join vehicles v on v.id = a.vehicle_id
            where a.file_path is not null and a.view_angle in {VIEWS}""").fetchall()

    best: dict[str, dict] = {}
    for r in rows:
        cur = best.get(r["vid"])
        if not cur or r["width"] * r["height"] > cur["width"] * cur["height"]:
            best[r["vid"]] = dict(r)
    pool = list(best.values())
    random.Random(args.seed).shuffle(pool)
    sample = pool[: args.n]

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    results = []
    for i, r in enumerate(sample, 1):
        path = ROOT / "data-test" / r["file_path"]
        try:
            got = call(cfg, path)
        except Exception as e:  # noqa: BLE001
            got = {"brand": "ERROR", "model": str(e)[:60], "evidence": ""}
        verdict = score(dict(r), got)
        results.append({"truth": {"brand": r["brand"], "model": r["model_name"],
                                  "category": r["category"], "view": r["view_angle"],
                                  "file": r["file_path"]},
                        "got": got, "verdict": verdict})
        print(f"[{i}/{len(sample)}] 真值 {r['brand']} {r['model_name']} "
              f"({r['view_angle']}) → {got.get('brand')} {got.get('model')} "
              f"[{verdict}] {got.get('evidence', '')[:30]}")

    summary = {k: sum(1 for x in results if x["verdict"] == k)
               for k in ("exact", "brand_only", "wrong", "unknown")}
    summary["n"] = len(results)
    (outdir / "results.json").write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print("\n汇总:", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
