# -*- coding: utf-8 -*-
"""A/B v3 评分：证据覆盖率、证据有效性、陷阱规避、强/弱分布。

输入：armA3-c01.md（自由格式表）+ armB3-c01.json（schema 清单）
输出：data-test/evals/ab-20261031/EVIDENCE-AB.md
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AB = ROOT / "data-test" / "evals" / "ab-20261031"
INDEX = ROOT / "data-test" / "evals" / "evidence-index-20261031.json"
TRAP = ("XGC88000", "履带")


def _norm(s: str) -> str:
    t = str(s).lower().replace("×", "x")
    return "".join(ch for ch in t if not ch.isspace() and ch not in "-_*·/()（）")


def _tokens(s: str) -> list[str]:
    return [x for x in re.findall(r"[a-z0-9]+|[\u4e00-\u9fff]+", str(s).lower())
            if len(x) >= 2]


def _model_in_title(model: str, title: str) -> bool:
    t = _norm(title)
    toks = _tokens(model)
    return bool(toks) and all(tok in t for tok in toks)


def parse_a3(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("| ---") or "序号" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 7 or not cells[0].isdigit():
            continue
        rows.append({"model": cells[1], "tier": cells[2], "strength": cells[3],
                     "url": cells[4], "title": cells[5], "confidence": cells[6]})
    return rows


def main() -> int:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    by_url = {it["url"]: it for it in index["items"]}

    a_rows = parse_a3(AB / "armA3-c01.md")
    b = json.loads((AB / "armB3-c01.json").read_text(encoding="utf-8"))
    b_rows = [t for t in b["targets"] if t.get("slots")]

    def eval_rows(rows: list[dict], arm: str) -> dict:
        out = []
        for r in rows:
            url = r.get("url") or (r.get("evidence") or [{}])[0].get("url", "")
            title = r.get("title") or (r.get("evidence") or [{}])[0].get("title", "")
            models = [r["model"]] if r.get("model") else (r.get("models") or [])
            hit = by_url.get(url)
            in_index = hit is not None
            title_ok = bool(hit and hit["title"] == title) if hit else False
            # 公平口径：以索引里的型号为准，判断"申报车型是否包含该索引型号"，
            # 而不是要求申报串的每个词（品牌/描述）都出现在标题里。
            claimed = " ".join(models)
            model_ok = (bool(hit)
                        and all(_norm(tok) in _norm(claimed)
                                for tok in _tokens(hit["model"]))
                        and _model_in_title(hit["model"], title))
            trap = any(k in " ".join(models) or k in title for k in TRAP)
            out.append({"model": " / ".join(models), "url": url, "in_index": in_index,
                        "title_matches_index": title_ok, "model_in_title": model_ok,
                        "trap": trap, "strength": r.get("strength") or
                        ("weak" if r.get("relevance_strength") == "weak" else "strong")})
        n = len(out)
        return {"rows": out, "n": n,
                "evidence_present": sum(1 for x in out if x["url"]),
                "valid": sum(1 for x in out if x["in_index"] and x["title_matches_index"]
                             and x["model_in_title"]),
                "strong": sum(1 for x in out if x["strength"].startswith("强")
                              or x["strength"] == "strong"),
                "weak": sum(1 for x in out if x["strength"].startswith("弱")
                            or x["strength"] == "weak"),
                "traps": sum(1 for x in out if x["trap"])}

    a = eval_rows(a_rows, "A")
    b = eval_rows(b_rows, "B")

    def pct(k, n):
        return f"{k}/{n} = {k/n*100:.0f}%" if n else "0/0"

    md = ["# A/B v3：带证据的清单对照（2026-10-31）", "",
          "| 指标 | A（无 skill） | B（skill v0.3） |",
          "|---|---:|---:|",
          f"| 交付车型数 | {a['n']} | {b['n']} |",
          f"| 带证据 | {a['evidence_present']} | {b['evidence_present']} |",
          f"| **证据有效**（URL 在索引内 + 标题逐字一致 + 标题含型号） | "
          f"**{pct(a['valid'], a['n'])}** | **{pct(b['valid'], b['n'])}** |",
          f"| 强关联 / 弱关联 | {a['strong']} / {a['weak']} | {b['strong']} / {b['weak']} |",
          f"| 陷阱车型（履带/4000t 吊） | {a['traps']} | {b['traps']} |", "",
          "## 逐条核对", "",
          "| 臂 | 车型 | 证据在索引 | 标题一致 | 标题含型号 | 判定 |",
          "|---|---|:--:|:--:|:--:|---|"]
    for arm, st in (("A", a), ("B", b)):
        for r in st["rows"]:
            ok = r["in_index"] and r["title_matches_index"] and r["model_in_title"]
            md.append(f"| {arm} | {r['model']} | {'✓' if r['in_index'] else '✗'} | "
                      f"{'✓' if r['title_matches_index'] else '✗'} | "
                      f"{'✓' if r['model_in_title'] else '✗'} | "
                      f"{'✅ 有效' if ok else '⚠️ 不成立'} |")
    (AB / "EVIDENCE-AB.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"A": {k: v for k, v in a.items() if k != "rows"},
                      "B": {k: v for k, v in b.items() if k != "rows"}},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
