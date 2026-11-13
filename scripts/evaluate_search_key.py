# -*- coding: utf-8 -*-
"""C 验证：抽取阶段 search_key 的质量 + 第二段命中对照（只搜不下载）。

用法:
  PYTHONPATH=src python scripts/evaluate_search_key.py --cases data-test/runs/p3-searchkey-20261114 --probe 30
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import imagesearch  # noqa: E402
from equiplens.retrieval_engine.web import WebWorld  # noqa: E402


def model_tokens(model: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z]{3,}|\d{3,}", model)]


def relevant(hits: list[dict], model: str) -> int:
    toks = model_tokens(model)
    n = 0
    for h in hits:
        text = f"{h.get('title','')} {h.get('url','')}".lower()
        if toks and any(t in text for t in toks):
            n += 1
    return n


def main() -> int:
    base = ROOT / "data-test" / "runs" / "p3-searchkey-20261114"
    if "--cases" in sys.argv:
        base = ROOT / sys.argv[sys.argv.index("--cases") + 1]
    probe_n = int(sys.argv[sys.argv.index("--probe") + 1]) if "--probe" in sys.argv else 30
    qstats = Counter()
    rows: list[dict] = []
    for p in sorted(base.glob("*/plan.json")):
        j = json.load(open(p, encoding="utf-8"))
        for c in j.get("candidates") or []:
            model = c.get("model") or ""
            sk = (c.get("search_key") or "").strip()
            nq = WebWorld.normalize_query(model)
            qstats["n"] += 1
            qstats["has_key"] += bool(sk)
            qstats["differs"] += bool(sk) and sk != nq
            if sk:
                qstats["key_len"] += len(sk)
                if re.search(r"[A-Z]{1,4}\d{3,}", model) and re.search(r"[A-Z]{1,4}\d{3,}", sk):
                    qstats["key_has_code"] += 1
                if re.search(r"[A-Z]{1,4}\d{3,}", model):
                    qstats["model_has_code"] += 1
                qstats["extra_tokens"] += bool(set(sk.lower().split()) - set(nq.lower().split()))
    qstats["avg_key_len"] = round(qstats["key_len"] / max(1, qstats["has_key"]), 1)
    print("quality:", dict(qstats))

    # 第二段对照：每个 case 抽样
    picks: list[tuple[str, dict]] = []
    per = max(1, probe_n // 5)
    for p in sorted(base.glob("*/plan.json")):
        j = json.load(open(p, encoding="utf-8"))
        cands = [c for c in (j.get("candidates") or []) if c.get("search_key")]
        for c in cands[:per]:
            picks.append((p.parent.name, c))
    agg = Counter()
    for case, c in picks:
        model, sk = c["model"], c["search_key"]
        nq = WebWorld.normalize_query(model)
        rec = {"case": case, "model": model[:40], "search_key": sk, "normalized": nq}
        for name, q in (("normalized", nq), ("search_key", sk)):
            try:
                hits, _ = imagesearch.search_images_hd(q, limit=6, model=model, hd=False)
            except Exception as e:  # noqa: BLE001
                rec[name] = {"hits": -1, "err": type(e).__name__}
                continue
            rec[name] = {"hits": len(hits), "rel": relevant(hits, model)}
        a, b = rec["normalized"], rec["search_key"]
        agg["n"] += 1
        if b["hits"] > a["hits"]:
            agg["key_more_hits"] += 1
        elif b["hits"] < a["hits"]:
            agg["key_fewer_hits"] += 1
        if b["rel"] > a["rel"]:
            agg["key_more_rel"] += 1
        elif b["rel"] < a["rel"]:
            agg["key_less_rel"] += 1
        rows.append(rec)
        print(f"{case[:14]:14s} {model[:26]:28s} norm={a['hits']}/{a['rel']} key={b['hits']}/{b['rel']} | {sk[:34]}")
    dest = ROOT / "data-test" / "evals" / "search-key-eval-20261114.json"
    dest.write_text(json.dumps({"quality": dict(qstats), "probe": dict(agg), "rows": rows},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    print("probe:", dict(agg))
    print("out:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
