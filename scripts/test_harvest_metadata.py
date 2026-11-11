# -*- coding: utf-8 -*-
"""A/B：同一批 harvest 图，旧 title='' vs 新页面 title/alt，对核验的影响。

只测试 harvest 路径，不改 normal search；输入从 run 的无图 target + plan query 派生，
不做品牌/车型特判。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
from equiplens import imagesearch  # noqa: E402
from equiplens.retrieval_engine.contracts import Asset, PartRequirement  # noqa: E402
from equiplens.retrieval_engine.web import RuleVerifier  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="data-test/runs/loop-intent-test3-20261111")
    ap.add_argument("--plan", default="data-test/runs/plan-ab4-20261111/A2/plan-ranked.json")
    ap.add_argument("--brief", default="data-test/evals/task-briefs-20261109/brief-m1-desert.json")
    ap.add_argument("--out", default="data-test/evals/harvest-metadata-ab-20261111.json")
    ap.add_argument("--limit", type=int, default=8)
    args = ap.parse_args(argv)
    run = ROOT / args.run
    state = json.loads((run / "state.json").read_text(encoding="utf-8"))
    plan = json.loads((ROOT / args.plan).read_text(encoding="utf-8"))
    brief = json.loads((ROOT / args.brief).read_text(encoding="utf-8"))
    by = {c["model"]: c for c in plan.get("candidates") or []}
    reqs = {p["part"]: PartRequirement(part=p["part"], label=p.get("label", ""),
                                       views=tuple(p.get("views") or []))
            for p in brief.get("part_requirements") or []}
    part = next(iter(reqs))
    ver = RuleVerifier(reqs, min_width=1200)
    targets = [t for t in state.get("targets") or {}
               if not any((state.get("assets", {}).get(t) or {}).values())]
    rows = []
    for model in targets:
        c = by.get(model, {})
        qs = []
        for q in (c.get("query") or model, imagesearch.alias_query(model)):
            if q and q not in qs:
                qs.append(q)
        for q in qs:
            hits, diag = imagesearch.search_images_hd(q, limit=args.limit, harvest=2)
            for h in hits:
                res = imagesearch._download_and_gate(h)
                gate = bool((res.get("gate") or {}).get("pass"))
                if not gate:
                    continue
                w = (res.get("prefilter") or {}).get("width", 0)
                hgt = (res.get("prefilter") or {}).get("height", 0)
                out = {"target": model, "query": q, "url": h.get("url", ""),
                       "source": h.get("source_url", ""), "page_title": h.get("page_title", ""),
                       "alt": h.get("alt", ""), "new_title": h.get("title", ""),
                       "gate": True, "width": w, "height": hgt,
                       "old_identity": "", "new_identity": "",
                       "old_accepted": False, "new_accepted": False}
                for key, title in (("old", ""), ("new", h.get("title", ""))):
                    a = Asset(asset_id="x", target_id=model, part=part,
                              width=w, height=hgt, url=h.get("url", ""),
                              title=title, model=model)
                    v = ver.verify(a, part)
                    out[f"{key}_identity"] = v.identity
                    out[f"{key}_accepted"] = v.accepted
                rows.append(out)
    out = Path(args.out)
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    old = sum(1 for r in rows if r["old_accepted"])
    new = sum(1 for r in rows if r["new_accepted"])
    print(json.dumps({"out": str(out), "gate_pass": len(rows),
                      "old_accepted": old, "new_accepted": new,
                      "targets": len(targets)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
