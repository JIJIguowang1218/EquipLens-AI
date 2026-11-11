# -*- coding: utf-8 -*-
"""Platform 层 A/B：同一 query、同一 target，比较 360/Baidu/Bing/union。

不改正常 run；直接调用 imagesearch 的通道函数。
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
from equiplens import imagesearch, planning  # noqa: E402
from equiplens.retrieval_engine.contracts import Asset, PartRequirement  # noqa: E402
from equiplens.retrieval_engine.web import RuleVerifier  # noqa: E402

BRIEFS = {
    "M1": "data-test/evals/task-briefs-20261109/brief-m1-desert.json",
    "M1B": "data-test/evals/task-briefs-20261109/brief-m1b-global.json",
    "A-mining": "data-test/evals/source-expansion-briefs-20261111/mining-dump.json",
    "B-mixer": "data-test/evals/source-expansion-briefs-20261111/mixer.json",
    "C-aerial": "data-test/evals/source-expansion-briefs-20261111/aerial.json",
}
PLATFORMS = {"360": imagesearch._search_360, "baidu": imagesearch._search_baidu,
             "bing": imagesearch._search_bing}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="data-test/runs/source-expansion-probe-20261111/targets.json")
    ap.add_argument("--out", default="data-test/runs/platform-probe-20261111")
    ap.add_argument("--hits", type=int, default=6)
    ap.add_argument("--query-mode", choices=["base", "class"], default="base")
    args = ap.parse_args(argv)
    out = ROOT / args.out
    (out / "images").mkdir(parents=True, exist_ok=True)
    failed = [x for x in json.loads((ROOT / args.targets).read_text(encoding="utf-8"))
              if x.get("failed")]
    briefs = {k: json.loads((ROOT / p).read_text(encoding="utf-8")) for k, p in BRIEFS.items()}
    reqs = {k: {p["part"]: PartRequirement(part=p["part"], label=p.get("label", ""),
                                          views=tuple(p.get("views") or []))
                for p in b.get("part_requirements") or []}
            for k, b in briefs.items()}
    vers = {k: RuleVerifier(v, min_width=1200) for k, v in reqs.items()}
    labels = {}
    for revdir in ("data-test/evals/source-expansion-pilot-review-20261111",
                   "data-test/evals/source-expansion-funnel-pending-review-20261111",
                   "data-test/evals/source-expansion-class-review-20261111"):
        rp = ROOT / revdir / "review-data.json"
        apath = ROOT / revdir / "annotations.json"
        if rp.exists() and apath.exists():
            rr = json.loads(rp.read_text(encoding="utf-8"))
            aa = json.loads(apath.read_text(encoding="utf-8"))
            for i, r in enumerate(rr, 1):
                if r.get("url"):
                    labels[r["url"]] = aa.get(f"v{i}", "")
    seen_models = set()
    targets, rows = [], []
    for t in failed:
        brief, model = t["brief"], t["model"]
        key = planning.model_identity(model)
        if key in seen_models:
            continue
        seen_models.add(key)
        if args.query_mode == "class":
            cls = briefs[brief].get("request", {}).get("class", "")
            term = next((v for k, v in (("搅拌", "搅拌车"), ("自卸", "矿用自卸车"),
                                        ("高空作业", "高空作业车"), ("牵引", "牵引车"))
                         if k in cls), cls[:12])
            core = model.split("（")[0].split("(")[0][:30]
            q = f"{term} {core}".strip()
        else:
            q = t.get("base_query") or model
        part = next(iter(reqs[brief]))
        ver = vers[brief]
        rec = {"brief": brief, "model": model, "query": q, "platforms": {}}
        gate_cache = {}
        union_hits = {}
        for pname, fn in PLATFORMS.items():
            try:
                hits, status = fn(q, args.hits)
            except Exception as e:  # noqa: BLE001
                hits, status = [], f"error:{type(e).__name__}"
            rec["platforms"][pname] = {"hits": len(hits), "status": str(status),
                                       "unique": 0, "download_ok": 0, "gate_pass": 0,
                                       "unknown": 0, "accepted": 0}
            for h in hits:
                u = h.get("url", "")
                if not u:
                    continue
                union_hits[u] = h
                if u in gate_cache:
                    res = gate_cache[u]
                else:
                    res = imagesearch._download_and_gate(h)
                    gate_cache[u] = res
                st = rec["platforms"][pname]
                st["unique"] += 1
                if not res.get("data"):
                    continue
                st["download_ok"] += 1
                if not (res.get("gate") or {}).get("pass"):
                    continue
                st["gate_pass"] += 1
                w = (res.get("prefilter") or {}).get("width", 0)
                hh = (res.get("prefilter") or {}).get("height", 0)
                a = Asset(asset_id="x", target_id=model, part=part, width=w, height=hh,
                          url=u, title=h.get("title", ""), model=model)
                v = ver.verify(a, part)
                if v.accepted:
                    st["accepted"] += 1
                else:
                    st["unknown"] += 1
        # union dedupe + verify
        rec["union"] = {"hits": len(union_hits), "accepted": 0, "overview": 0,
                        "unknown": 0, "gate_pass": 0}
        for u, h in union_hits.items():
            res = gate_cache.get(u) or imagesearch._download_and_gate(h)
            if not res.get("data") or not (res.get("gate") or {}).get("pass"):
                continue
            rec["union"]["gate_pass"] += 1
            w = (res.get("prefilter") or {}).get("width", 0)
            hh = (res.get("prefilter") or {}).get("height", 0)
            a = Asset(asset_id="x", target_id=model, part=part, width=w, height=hh,
                      url=u, title=h.get("title", ""), model=model)
            v = ver.verify(a, part)
            if v.accepted:
                rec["union"]["accepted"] += 1
                if (res.get("gate") or {}).get("scene") == "single_vehicle" and w >= 800:
                    rec["union"]["overview"] += 1
            else:
                rec["union"]["unknown"] += 1
            local = ""
            try:
                data = imagesearch._fetch_image(u, h.get("referer") or "https://image.so.com/")
                if data:
                    local = f"images/{len(rows):03d}.jpg"
                    (out / local).write_bytes(data)
            except Exception:  # noqa: BLE001
                pass
            rows.append({"brief": brief, "model": model, "query": q, "url": u,
                         "title": h.get("title", ""), "channel": h.get("channel", ""),
                         "gate": True, "unknown": not v.accepted,
                         "accepted": v.accepted, "image": local,
                         "human_label": labels.get(u, "pending")})
        targets.append(rec)
        print(brief, model[:28], {k: v["accepted"] for k, v in rec["platforms"].items()},
              "union", rec["union"]["accepted"], flush=True)
    (out / "platform.json").write_text(json.dumps({"targets": targets, "images": rows},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"targets": len(targets), "images": len(rows),
                      "accepted": sum(1 for r in targets if r["union"]["accepted"]),
                      "overview": sum(1 for r in targets if r["union"]["overview"]),
                      "pending": sum(1 for r in rows if r["human_label"] == "pending")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
