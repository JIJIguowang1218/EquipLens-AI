# -*- coding: utf-8 -*-
"""A3 探针：第二段“英文档”是否比现有查询键更有效（不引入类目翻译表）。

对比三档（同一 target、同一时刻）：
  current  = WebWorld.normalize_query(model)
  en_latin = 拉丁词/型号 + 构型 + "truck"
  en_code  = 型号码 + "truck"
只做图片搜索（不下载），统计命中数 + 标题含车型 token 的比例。
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import imagesearch  # noqa: E402
from equiplens.retrieval_engine.web import WebWorld  # noqa: E402


def pick(limit: int = 24) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for p in sorted((ROOT / "data-test" / "runs").rglob("state.json")):
        try:
            s = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for _tid, t in (s.get("targets") or {}).items():
            m = t.get("model") or ""
            if not re.search(r"[A-Za-z][A-Za-z\-]{2,}", m) or m in seen:
                continue
            seen.add(m)
            out.append({"case": p.parent.parent.name, "model": m})
    # 按 case 轮转抽样，避免集中在一个案例
    by_case: dict[str, list[dict]] = {}
    for r in out:
        by_case.setdefault(r["case"].split("-")[0], []).append(r)
    picked: list[dict] = []
    while len(picked) < limit and any(by_case.values()):
        for k in list(by_case):
            if by_case[k] and len(picked) < limit:
                picked.append(by_case[k].pop(0))
    return picked


def tokens(model: str) -> list[str]:
    return [t for t in re.findall(r"[A-Za-z]{3,}", model) if t.lower() not in
            {"truck", "trucks", "lorry", "container", "terminal", "series"}]


def code_of(model: str) -> str:
    m = re.search(r"[A-Z]{1,4}\d{3,}[A-Z0-9]*", model)
    return m.group(0) if m else ""


def hit_relevant(hits: list[dict], model: str) -> int:
    toks = [t.lower() for t in tokens(model)] + ([code_of(model).lower()] if code_of(model) else [])
    n = 0
    for h in hits:
        text = f"{h.get('title','')} {h.get('url','')}".lower()
        if toks and any(t in text for t in toks):
            n += 1
    return n


def main() -> int:
    limit = int(sys.argv[sys.argv.index("--cases") + 1]) if "--cases" in sys.argv else 24
    rows = pick(limit)
    agg = {"n": 0}
    for r in rows:
        model = r["model"]
        latin = " ".join(tokens(model)[:2])
        conf = next((c for c in ("6x6", "8x8", "4x4") if c in model.lower().replace("×", "x")), "")
        code = code_of(model)
        variants = {
            "current": WebWorld.normalize_query(model),
            "en_latin": " ".join(x for x in (latin, conf, "truck") if x),
            "en_code": " ".join(x for x in (code, conf, "truck") if x) if code else "",
        }
        rec = {"case": r["case"], "model": model[:40], "v": {}}
        for name, q in variants.items():
            if not q:
                continue
            try:
                hits, _ = imagesearch.search_images_hd(q, limit=6, model=model, hd=False)
            except Exception as e:  # noqa: BLE001
                rec["v"][name] = {"q": q[:44], "hits": -1, "err": type(e).__name__}
                continue
            rec["v"][name] = {"q": q[:44], "hits": len(hits), "rel": hit_relevant(hits, model)}
            print(f"{r['case'][:14]:14s} {model[:24]:26s} {name:9s} hits={len(hits):2d} "
                  f"rel={rec['v'][name]['rel']:2d} q={q[:40]}")
        agg["n"] += 1
        # 粗统计
        for name in ("current", "en_latin", "en_code"):
            v = rec["v"].get(name)
            if v and v.get("hits", 0) > 0:
                agg[name + "_hit"] = agg.get(name + "_hit", 0) + 1
            if v and v.get("rel", 0) > 0:
                agg[name + "_rel"] = agg.get(name + "_rel", 0) + 1
        r.update(rec)
    dest = ROOT / "data-test" / "evals" / "english-query-probe-20261114.json"
    dest.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nAGG", agg)
    print("out:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
