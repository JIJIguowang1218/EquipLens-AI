# -*- coding: utf-8 -*-
"""bbox 精修：只重新定位部件框，不动文字。

分析阶段的 bbox 是"大致区域"，会带到相邻部件；这里单独问一次紧贴轮廓。

用法:
  PYTHONPATH=src python scripts/relocate_parts.py --analysis <json> [--dry]
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

SLOT_CN = {"grille": "进气格栅", "bumper": "保险杠", "side_guard": "侧防护栏",
           "wheel_arch": "前轮轮拱", "step": "登车踏步"}

PROMPT = """这张图里有一台卡车。请给出下列每个部件**紧贴其外轮廓**的边界框。

规则（重要）：
- 框只包含该部件本身，不要带上相邻的部件或车身大面积
- 框的宽度一般不超过整车可见宽度的 30%，高度不超过 25%
- 若该部件被挡住或看不出边界，visible 写 false，bbox 写 null
- 坐标用 0-1000 归一化：[x1,y1,x2,y2]，左上为原点

部件：{slots}

只输出 JSON：{{"parts":[{{"slot":"","visible":true,"bbox":[0,0,0,0],"note":""}}]}}"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--data-dir", default="data-test")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    cfg = {}
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()

    src = ROOT / args.analysis
    data = json.loads(src.read_text(encoding="utf-8"))
    hero = ROOT / args.data_dir / data["assets"]["hero"]
    slots = [p["slot"] for p in data.get("parts", []) if p.get("visible") != "not_visible"]
    prompt = PROMPT.format(slots="、".join(f"{s}（{SLOT_CN.get(s, s)}）" for s in slots))

    b64 = base64.b64encode(hero.read_bytes()).decode()
    mime = "image/png" if hero.suffix.lower() == ".png" else "image/jpeg"
    payload = {"model": cfg["LLM_VISION_MODEL"], "reasoning_effort": "low",
               "max_tokens": 6000,
               "messages": [{"role": "user", "content": [
                   {"type": "text", "text": prompt},
                   {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}]}]}
    req = urllib.request.Request(cfg["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {cfg['LLM_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.load(r)
    text = d["choices"][0]["message"]["content"] or ""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        print("[FATAL] 无 JSON:\n", text[:800])
        return 1
    got = json.loads(m.group(0))

    changed = 0
    for p in data.get("parts", []):
        loc = next((g for g in got.get("parts", []) if g.get("slot") == p.get("slot")), None)
        if not loc:
            continue
        if not loc.get("visible") or not loc.get("bbox"):
            continue
        old = p.get("bbox")
        p["bbox"] = loc["bbox"]
        if old != loc["bbox"]:
            changed += 1
        print(f"  {p['slot']:12s} {old} → {loc['bbox']}  {loc.get('note','')[:20]}")
    if not args.dry:
        src.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[ok] 更新 {changed} 个框 → {src}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
