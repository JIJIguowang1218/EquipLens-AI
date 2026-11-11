# -*- coding: utf-8 -*-
"""同一批 24 个失败 target 的阶段漏斗：search→download→gate→verify→overview/part。

- 先按车型身份去重；URL 全局去重；
- 不改 query 策略：base 用 plan source_query，expansion 用上一轮 alias_query；
- 记录每阶段计数，供定位 recall 丢失；不是完整 loop。
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="data-test/runs/source-expansion-probe-20261111/targets.json")
    ap.add_argument("--labels", default="data-test/evals/source-expansion-pilot-review-20261111/annotations.json")
    ap.add_argument("--review", default="data-test/evals/source-expansion-pilot-review-20261111/review-data.json")
    ap.add_argument("--out", default="data-test/runs/source-expansion-funnel-20261111")
    ap.add_argument("--hits", type=int, default=4)
    args = ap.parse_args(argv)
    out = ROOT / args.out
    (out / "images").mkdir(parents=True, exist_ok=True)
    failed = [x for x in json.loads((ROOT / args.targets).read_text(encoding="utf-8"))
              if x.get("failed")]
    ann = json.loads((ROOT / args.labels).read_text(encoding="utf-8"))
    rev = json.loads((ROOT / args.review).read_text(encoding="utf-8"))
    url_label = {}
    for i, r in enumerate(rev, 1):
        if r.get("url"):
            url_label[r["url"]] = ann.get(f"v{i}", "")
    briefs = {k: json.loads((ROOT / v).read_text(encoding="utf-8")) for k, v in BRIEFS.items()}
    reqs = {k: {p["part"]: PartRequirement(part=p["part"], label=p.get("label", ""),
                                          views=tuple(p.get("views") or []))
                for p in b.get("part_requirements") or []}
            for k, b in briefs.items()}
    verifiers = {k: RuleVerifier(v, min_width=1200) for k, v in reqs.items()}
    seen_urls, seen_models = set(), set()
    targets, rows = [], []
    for t in failed:
        brief, model = t["brief"], t["model"]
        key = planning.model_identity(model)
        if key in seen_models:
            targets.append({"brief": brief, "model": model, "excluded": "duplicate_model"})
            continue
        seen_models.add(key)
        part = next(iter(reqs[brief]))
        ver = verifiers[brief]
        rec = {"brief": brief, "model": model, "model_key": str(key),
               "base": Counter(), "exp": Counter(), "base_accept": False,
               "exp_accept": False, "overview_accept": False, "part_only": False,
               "urls": []}
        for phase, q, harvest in (("base", t.get("base_query") or model, 0),
                                  ("exp", t.get("exp_query") or imagesearch.alias_query(model) or model, 2)):
            hits, _diag = imagesearch.search_images_hd(q, limit=args.hits, harvest=harvest)
            rec[phase]["hits"] = len(hits)
            for h in hits:
                u = h.get("url", "")
                if not u:
                    continue
                if u in seen_urls:
                    rec[phase]["dup"] += 1
                    continue
                seen_urls.add(u)
                rec[phase]["unique"] += 1
                res = imagesearch._download_and_gate(h)
                if not res.get("data"):
                    rec[phase]["download_fail"] += 1
                    continue
                rec[phase]["download_ok"] += 1
                if not (res.get("gate") or {}).get("pass"):
                    rec[phase]["gate_fail"] += 1
                    continue
                rec[phase]["gate_pass"] += 1
                scene = (res.get("gate") or {}).get("scene", "")
                w = (res.get("prefilter") or {}).get("width", 0)
                hh = (res.get("prefilter") or {}).get("height", 0)
                a = Asset(asset_id="x", target_id=model, part=part, width=w, height=hh,
                          url=u, title=h.get("title", ""), model=model)
                v = ver.verify(a, part)
                rec[phase]["verified_unknown"] += 0 if v.accepted else 1
                if v.accepted:
                    rec[phase]["accepted"] += 1
                    if phase == "base":
                        rec["base_accept"] = True
                    else:
                        rec["exp_accept"] = True
                    if scene == "single_vehicle" and w >= 800:
                        rec["overview_accept"] = True
                    elif scene == "part":
                        rec["part_only"] = True
                if phase == "exp":
                    local = ""
                    try:
                        data = imagesearch._fetch_image(u, h.get("referer") or "https://image.so.com/")
                        if data:
                            local = f"images/{len(rows):03d}.jpg"
                            (out / local).write_bytes(data)
                    except Exception:  # noqa: BLE001
                        pass
                    rows.append({"brief": brief, "model": model, "url": u,
                                 "title": h.get("title", ""), "query": q,
                                 "scene": scene, "width": w, "height": hh,
                                 "identity": v.identity, "accepted": v.accepted,
                                 "human_label": url_label.get(u, "pending"),
                                 "image": local})
        targets.append(rec)
        print(brief, model[:32], "base", dict(rec["base"]), "exp", dict(rec["exp"]), flush=True)
    (out / "funnel.json").write_text(json.dumps({"targets": targets, "images": rows},
                                                ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"targets": len(targets), "unique_models": len(seen_models),
                      "failed": len([x for x in targets if not x.get("excluded")]),
                      "base_accept": sum(1 for x in targets if x.get("base_accept")),
                      "exp_accept": sum(1 for x in targets if x.get("exp_accept")),
                      "overview": sum(1 for x in targets if x.get("overview_accept")),
                      "rows": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
