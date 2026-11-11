# -*- coding: utf-8 -*-
"""同一批失败 target：用类目词 query（而非泛 alias）重跑扩源，比较 precision/recall。

类目词只从 brief.class 推断；model core 去掉括号/配置；不做品牌规则。
"""
from __future__ import annotations

import argparse
import json
import re
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
CLASS_TERMS = (("搅拌", "搅拌车"), ("自卸", "矿用自卸车"),
               ("高空作业", "高空作业车"), ("牵引", "牵引车"))


def class_term(cls: str) -> str:
    for needle, term in CLASS_TERMS:
        if needle in (cls or ""):
            return term
    return re.sub(r"[（(].*", "", cls or "").strip()[:12]


def model_core(model: str) -> str:
    s = re.sub(r"[（(].*?[）)]", " ", model or "")
    s = re.sub(r"\b\d+\s*[x×]\s*\d+\b", " ", s, flags=re.I)
    s = re.sub(r"\b\d+\s*(?:t|吨|方|m3|m³)\b", " ", s, flags=re.I)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:30]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default="data-test/runs/source-expansion-funnel-20261111/targets.json")
    ap.add_argument("--out", default="data-test/runs/source-expansion-class-query-20261111")
    ap.add_argument("--hits", type=int, default=5)
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
    # 旧标签
    labels = {}
    for revdir in ("data-test/evals/source-expansion-pilot-review-20261111",
                   "data-test/evals/source-expansion-funnel-pending-review-20261111"):
        rp = ROOT / revdir / "review-data.json"
        apath = ROOT / revdir / "annotations.json"
        if not rp.exists() or not apath.exists():
            continue
        rr = json.loads(rp.read_text(encoding="utf-8"))
        aa = json.loads(apath.read_text(encoding="utf-8"))
        for i, r in enumerate(rr, 1):
            if r.get("url"):
                labels[r["url"]] = aa.get(f"v{i}", "")
    seen_models, seen_urls = set(), set()
    targets, rows = [], []
    for t in failed:
        brief, model = t["brief"], t["model"]
        key = planning.model_identity(model)
        if key in seen_models:
            continue
        seen_models.add(key)
        part = next(iter(reqs[brief]))
        ver = vers[brief]
        q = f"{class_term(briefs[brief].get('request', {}).get('class', ''))} {model_core(model)}".strip()
        rec = {"brief": brief, "model": model, "query": q, "stage": Counter(),
               "accepted": 0, "target_accept": False, "overview": False, "fallback": ""}
        hits, _ = imagesearch.search_images_hd(q, limit=args.hits, harvest=2)
        if not hits:
            rec["fallback"] = imagesearch.alias_query(model) or ""
            hits, _ = imagesearch.search_images_hd(rec["fallback"], limit=args.hits, harvest=2)
        rec["stage"]["hits"] = len(hits)
        for h in hits:
            u = h.get("url", "")
            if not u:
                continue
            if u in seen_urls:
                rec["stage"]["dup"] += 1
                continue
            seen_urls.add(u)
            rec["stage"]["unique"] += 1
            res = imagesearch._download_and_gate(h)
            if not res.get("data"):
                rec["stage"]["download_fail"] += 1
                continue
            rec["stage"]["download_ok"] += 1
            if not (res.get("gate") or {}).get("pass"):
                rec["stage"]["gate_fail"] += 1
                continue
            rec["stage"]["gate_pass"] += 1
            scene = (res.get("gate") or {}).get("scene", "")
            w = (res.get("prefilter") or {}).get("width", 0)
            hh = (res.get("prefilter") or {}).get("height", 0)
            a = Asset(asset_id="x", target_id=model, part=part, width=w, height=hh,
                      url=u, title=h.get("title", ""), model=model)
            v = ver.verify(a, part)
            rec["stage"]["unknown"] += 0 if v.accepted else 1
            if v.accepted:
                rec["accepted"] += 1
                rec["target_accept"] = True
                if scene == "single_vehicle" and w >= 800:
                    rec["overview"] = True
            local = ""
            try:
                data = imagesearch._fetch_image(u, h.get("referer") or "https://image.so.com/")
                if data:
                    local = f"images/{len(rows):03d}.jpg"
                    (out / local).write_bytes(data)
            except Exception:  # noqa: BLE001
                pass
            rows.append({"brief": brief, "model": model, "query": q,
                         "url": u, "title": h.get("title", ""), "scene": scene,
                         "width": w, "height": hh, "identity": v.identity,
                         "accepted": v.accepted,
                         "human_label": labels.get(u, "pending"), "image": local})
        targets.append(rec)
        print(brief, model[:30], q[:50], dict(rec["stage"]), "acc", rec["accepted"], flush=True)
    (out / "class-funnel.json").write_text(json.dumps({"targets": targets, "images": rows},
                                                      ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"targets": len(targets), "accepted_targets": sum(1 for x in targets if x["target_accept"]),
                      "overview": sum(1 for x in targets if x["overview"]),
                      "images": len(rows), "pending": sum(1 for r in rows if r["human_label"] == "pending")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
