# -*- coding: utf-8 -*-
"""P0 探针：0 命中（no_hits）候选的查询变体回放。

只做检索回放，不改任何生产数据：对历史 no_hits 目标，用不同的查询写法
各搜一次，比较命中数与标题是否仍指向同一车型。

用法:
  PYTHONPATH=src python scripts/probe_query_fallback.py --cases 12
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


def strip_6x6(q: str) -> str:
    return re.sub(r"\s*6\s*[×x]\s*6\s*", " ", q or "", flags=re.I).strip()


def model_tokens(model: str) -> list[str]:
    s = re.sub(r"[（(][^）)]*[）)]", " ", model or "")
    codes = re.findall(r"[A-Z]{1,5}\d{3,}[A-Z0-9-]*", s, flags=re.I)
    brands = re.findall(r"[一-鿿]{2,4}", s)
    return [c.lower() for c in codes] + [b for b in brands if len(b) >= 2][:2]


def relevant_hits(hits: list[dict], model: str) -> int:
    toks = model_tokens(model)
    if not toks:
        return 0
    n = 0
    for h in hits:
        text = f"{h.get('title','')} {h.get('url','')}".lower()
        if any(t in text for t in toks):
            n += 1
    return n


def collect(n: int) -> list[dict]:
    out: list[dict] = []
    for st in sorted(pathlib.Path(ROOT / "data-test" / "runs").rglob("state.json")):
        run = st.parent
        sm = run / "summary.json"
        if not sm.exists():
            continue
        try:
            s = json.load(open(sm, encoding="utf-8"))
            stt = json.load(open(st, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(s, dict):
            continue
        tg = stt.get("targets") or {}
        for u in (s.get("delivery") or {}).get("unavailable") or []:
            if u.get("reason") != "no_hits":
                continue
            model = u.get("model") or ""
            t = tg.get(model) or {}
            if not t:
                continue
            out.append({"case": run.parent.name, "model": model,
                        "query": t.get("query") or "",
                        "kind": t.get("identity_kind") or ""})
            if len(out) >= n:
                return out
    return out


def main() -> int:
    lim = 12
    if "--cases" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--cases") + 1])
    targets = collect(lim)
    print(f"no_hits targets: {len(targets)}")
    rows = []
    for t in targets:
        model, cur = t["model"], t["query"]
        variants = {
            "current": cur,
            "no_6x6": strip_6x6(cur),
            "full_model": model,
            "alias": imagesearch.alias_query(model),
        }
        if variants["no_6x6"] == cur:
            variants.pop("no_6x6")
        rec = {"case": t["case"], "model": model[:34], "kind": t["kind"], "v": {}}
        for name, q in variants.items():
            try:
                hits, _diag = imagesearch.search_images_hd(q, limit=6, model=model,
                                                           hd=False)
            except Exception as e:  # noqa: BLE001
                rec["v"][name] = {"q": q[:40], "hits": -1, "err": type(e).__name__}
                continue
            rec["v"][name] = {"q": q[:40], "hits": len(hits),
                              "relevant": relevant_hits(hits, model)}
            print(f"  {t['case'][:16]:16s} {model[:26]:28s} {name:10s} "
                  f"hits={len(hits):2d} rel={rec['v'][name]['relevant']:2d}  q={q[:38]}")
        rows.append(rec)
    out = ROOT / "data-test" / "evals" / "query-fallback-probe-20261113.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    recovered = sum(1 for r in rows if r["v"].get("no_6x6", {}).get("hits", 0) > 0)
    print(f"\nno_6x6 recovered hits: {recovered}/{len(rows)}")
    print("out:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
