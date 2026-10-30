# -*- coding: utf-8 -*-
"""A/B 实图核对评分：两臂的车型在图上的可用性与命中率。

输入：armA3-c01.md、armB3-c01.json、data-test/ab-images/manifest.json、verdicts.csv
输出：data-test/evals/ab-20261031/IMAGE-AB.md
说明：命中率需要人工判定（verdicts.csv 的"人工判定"列：对/部分/错）；
      未填时只报"图覆盖率"，并明确标注待判。
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AB = ROOT / "data-test" / "evals" / "ab-20261031"
IMG = ROOT / "data-test" / "ab-images"


def _norm(s: str) -> str:
    t = str(s).lower().replace("×", "x")
    return "".join(ch for ch in t if not ch.isspace() and ch not in "-_*·/()（）")


def _a_models() -> list[str]:
    out = []
    for line in (AB / "armA3-c01.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| ---") or "序号" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 7 and cells[0].isdigit():
            out.append(cells[1])
    return out


def _b_models() -> list[str]:
    d = json.loads((AB / "armB3-c01.json").read_text(encoding="utf-8"))
    return [" / ".join(t.get("models") or []) for t in d["targets"] if t.get("slots")]


def main() -> int:
    manifest = json.loads((IMG / "manifest.json").read_text(encoding="utf-8"))
    by = {_norm(m["model"]): m for m in manifest}
    verdicts = {}
    vp = IMG / "verdicts.csv"
    if vp.exists():
        for row in csv.DictReader(vp.open(encoding="utf-8-sig")):
            verdicts[_norm(row["清单里的车型"])] = (row.get("人工判定(对/部分/错)") or "").strip()

    def stats(models: list[str]) -> dict:
        rows, hits, labeled = [], 0, 0
        for m in models:
            rec = by.get(_norm(m), {})
            n = len(rec.get("images", []))
            v = verdicts.get(_norm(m), "")
            if v in ("对", "部分", "错"):
                labeled += 1
                hits += {"对": 1, "部分": 0.5, "错": 0}[v]
            rows.append({"model": m, "images": n, "verdict": v})
        return {"n": len(models), "with_images": sum(1 for r in rows if r["images"]),
                "images": sum(r["images"] for r in rows), "rows": rows,
                "labeled": labeled, "hit": hits}

    a, b = stats(_a_models()), stats(_b_models())

    def pct(x, n):
        return f"{x}/{n}" if n else "—"

    md = ["# A/B 实图核对评分（2026-10-31）", "",
          "| 指标 | A（无 skill） | B（skill，已降级） |",
          "|---|---:|---:|",
          f"| 清单车型数 | {a['n']} | {b['n']} |",
          f"| 有图的车型 | {a['with_images']} | {b['with_images']} |",
          f"| 图片总数 | {a['images']} | {b['images']} |",
          f"| 人工已判 | {a['labeled']} | {b['labeled']} |",
          f"| **实图命中率**（对=1/部分=0.5/错=0） | "
          f"**{('%.2f' % (a['hit']/a['n'])) if a['labeled'] else '待判定'}** | "
          f"**{('%.2f' % (b['hit']/b['n'])) if b['labeled'] else '待判定'}** |", "",
          "## 逐车型", "", "| 车型 | A/B | 图数 | 人工判定 |", "|---|---|---:|---|"]
    a_set = {_norm(x) for x in _a_models()}
    b_set = {_norm(x) for x in _b_models()}
    seen = []
    for r in a["rows"] + b["rows"]:
        k = _norm(r["model"])
        if k in seen:
            continue
        seen.append(k)
        tag = ("A+B" if k in a_set and k in b_set else "A" if k in a_set else "B")
        md.append(f"| {r['model']} | {tag} | {r['images']} | {r['verdict'] or '—'} |")
    md += ["", "> 人工判定填 `data-test/ab-images/verdicts.csv`（对/部分/错）后重跑本脚本即可出命中率。"]
    (AB / "IMAGE-AB.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"A": {k: v for k, v in a.items() if k != "rows"},
                      "B": {k: v for k, v in b.items() if k != "rows"}},
                     ensure_ascii=False))
    print(f"→ {AB/'IMAGE-AB.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
