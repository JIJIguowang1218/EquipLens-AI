# -*- coding: utf-8 -*-
"""扩源 pilot：对候选先做 base，再对失败 target 做 alias+harvest；记录所有过门卫图。

不做品牌/车型规则；query 只来自 plan source_query / 通用 alias。
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

CASES = [
    ("M1", "data-test/evals/task-briefs-20261109/brief-m1-desert.json",
     "data-test/runs/plan-ab4-20261111/A2/plan-ranked.json"),
    ("M1B", "data-test/evals/task-briefs-20261109/brief-m1b-global.json",
     "data-test/runs/plan-m1b-global/plan.json"),
    ("A-mining", "data-test/evals/source-expansion-briefs-20261111/mining-dump.json",
     "data-test/runs/source-expansion-briefs-20261111/mining-dump/plan.json"),
    ("B-mixer", "data-test/evals/source-expansion-briefs-20261111/mixer.json",
     "data-test/runs/source-expansion-briefs-20261111/mixer/plan.json"),
    ("C-aerial", "data-test/evals/source-expansion-briefs-20261111/aerial.json",
     "data-test/runs/source-expansion-briefs-20261111/aerial/plan.json"),
]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data-test/runs/source-expansion-probe-20261111")
    ap.add_argument("--per-brief", type=int, default=6)
    ap.add_argument("--base-hits", type=int, default=4)
    ap.add_argument("--exp-hits", type=int, default=6)
    args = ap.parse_args(argv)
    out = ROOT / args.out
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    rows, targets = [], []
    for name, bpath, ppath in CASES:
        brief = json.loads((ROOT / bpath).read_text(encoding="utf-8"))
        plan = json.loads((ROOT / ppath).read_text(encoding="utf-8"))
        reqs = {p["part"]: PartRequirement(part=p["part"], label=p.get("label", ""),
                                           views=tuple(p.get("views") or []))
                for p in brief.get("part_requirements") or []}
        part = next(iter(reqs))
        ver = RuleVerifier(reqs, min_width=1200)
        cands = [c for c in plan.get("candidates") or [] if c.get("model")][:args.per_brief]
        for c in cands:
            model = c["model"]
            base_q = c.get("source_query") or model
            base_hits = imagesearch.search_images_hd(base_q, limit=args.base_hits)[0]
            base_rows = []
            failed = True
            for h in base_hits:
                res = imagesearch._download_and_gate(h)
                if not (res.get("gate") or {}).get("pass"):
                    continue
                w = (res.get("prefilter") or {}).get("width", 0)
                hh = (res.get("prefilter") or {}).get("height", 0)
                a = Asset(asset_id="x", target_id=model, part=part, width=w, height=hh,
                          url=h.get("url", ""), title=h.get("title", ""), model=model)
                v = ver.verify(a, part)
                base_rows.append({"title": h.get("title", ""), "url": h.get("url", ""),
                                  "source": h.get("source_url", ""), "identity": v.identity,
                                  "accepted": v.accepted, "w": w, "h": hh})
                if v.accepted:
                    failed = False
                    break
            if not failed:
                targets.append({"brief": name, "model": model, "failed": False,
                                "base_accepted": True, "exp_accepted": False})
                continue
            exp_q = imagesearch.alias_query(model) or model
            exp_hits, diag = imagesearch.search_images_hd(exp_q, limit=args.exp_hits, harvest=2)
            exp_acc = False
            n_gate = 0
            for h in exp_hits:
                res = imagesearch._download_and_gate(h)
                if not (res.get("gate") or {}).get("pass"):
                    continue
                n_gate += 1
                w = (res.get("prefilter") or {}).get("width", 0)
                hh = (res.get("prefilter") or {}).get("height", 0)
                a = Asset(asset_id="x", target_id=model, part=part, width=w, height=hh,
                          url=h.get("url", ""), title=h.get("title", ""), model=model)
                v = ver.verify(a, part)
                local = ""
                try:
                    data = imagesearch._fetch_image(h.get("url", ""), h.get("referer") or "https://image.so.com/")
                    if data:
                        local = f"images/{len(rows):03d}.jpg"
                        (out / local).write_bytes(data)
                except Exception:  # noqa: BLE001
                    pass
                rows.append({"brief": name, "model": model, "phase": "expansion",
                             "query": exp_q, "title": h.get("title", ""),
                             "url": h.get("url", ""), "source": h.get("source_url", ""),
                             "channel": h.get("channel", ""), "image": local,
                             "identity": v.identity, "accepted": v.accepted,
                             "w": w, "h": hh})
                if v.accepted:
                    exp_acc = True
                    break
            targets.append({"brief": name, "model": model, "failed": True,
                            "base_accepted": False, "exp_accepted": exp_acc,
                            "exp_query": exp_q, "base_query": base_q,
                            "base_gate": len(base_rows), "exp_gate": n_gate})
            print(name, model[:36], "FAILED", "exp_acc", exp_acc, "exp_gate", n_gate, flush=True)
    (out / "targets.json").write_text(json.dumps(targets, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "images.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    failed = sum(1 for x in targets if x["failed"])
    recovered = sum(1 for x in targets if x["failed"] and x["exp_accepted"])
    print(json.dumps({"targets": len(targets), "failed": failed, "recovered": recovered,
                      "images": len(rows), "out": str(out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
