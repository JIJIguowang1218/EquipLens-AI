# -*- coding: utf-8 -*-
"""批量分析：选车 → 取图 → 分析 → 缺部位补证 → 落 JSON。

用法:
  PYTHONPATH=src python scripts/analyze_batch.py \
      --vehicles JH6,银河,汕德卡C7H --out data-test/analysis-20261031
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import analysis  # noqa: E402

SLOTS = ["grille", "bumper", "side_guard", "wheel_arch", "step"]
HERO_VIEWS = ("hero_lf", "hero_rf", "hero_45")
SIDE_VIEWS = ("side_l", "side")


def pick_assets(conn, model: str) -> tuple[dict, list[dict]]:
    conn.row_factory = sqlite3.Row
    v = conn.execute(
        "select id, brand, model_name, category from vehicles where model_name=?",
        (model,)).fetchone()
    if not v:
        raise SystemExit(f"找不到车型：{model}")
    rows = conn.execute(
        "select id, file_path, view_angle, width, height from assets "
        "where vehicle_id=? and file_path is not null", (v["id"],)).fetchall()
    if not rows:
        raise SystemExit(f"{model} 没有素材")

    def best(views):
        cand = [r for r in rows if r["view_angle"] in views]
        cand.sort(key=lambda r: r["width"] * r["height"], reverse=True)
        return cand[0] if cand else None

    hero = best(HERO_VIEWS) or best(("side", "side_l", "front"))
    side = best(SIDE_VIEWS)
    return dict(v), [dict(hero) if hero else None, dict(side) if side else None]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vehicles", required=True, help="逗号分隔的 model_name")
    ap.add_argument("--data-dir", default="data-test")
    ap.add_argument("--out", required=True)
    ap.add_argument("--force", action="store_true", help="已存在也重跑")
    ap.add_argument("--overrides", help="JSON: {model: {hero: path, side: path}}")
    args = ap.parse_args()

    models = [m.strip() for m in args.vehicles.split(",") if m.strip()]
    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    cfg = analysis.load_config()
    if not cfg.get("LLM_API_KEY"):
        raise SystemExit("缺 LLM_API_KEY（.env 或环境变量）")
    provider = analysis.ApiProvider(cfg)
    vocab = analysis.load_vocab()
    tax = analysis.load_taxonomy()
    ledger = analysis.TagLedger(vocab)

    overrides = json.loads(Path(args.overrides).read_text(encoding="utf-8"))         if args.overrides else {}
    data_root = ROOT / args.data_dir
    conn = sqlite3.connect(data_root / "equiplens.db")
    summary = []

    for i, model in enumerate(models, 1):
        target = outdir / f"{i:02d}-{model}.json"
        if target.exists() and not args.force:
            data = json.loads(target.read_text(encoding="utf-8"))
        else:
            v, (hero, side) = pick_assets(conn, model)
            ov = overrides.get(model, {})
            if ov.get("hero"):
                hero = dict(hero, file_path=ov["hero"])
            if "side" in ov:
                side = (dict(side or {"view_angle": "side"},
                             file_path=ov["side"],
                             view_angle=ov.get("side_view", "side"))
                        if ov["side"] else None)
            used = list(ledger.used)
            data = analysis.analyze(provider, f"{v['brand']} {model}", data_root / hero["file_path"],
                                    SLOTS, used, vocab, tax, view_tag=hero["view_angle"])
            data["assets"] = {"hero": hero["file_path"],
                              "side": side["file_path"] if side else None,
                              "hero_view": hero["view_angle"],
                              "side_view": side["view_angle"] if side else None}

            weak = [p["slot"] for p in data.get("parts", [])
                    if p.get("visible") != "full"]
            if weak and side and side["file_path"] != hero["file_path"]:
                supp = analysis.analyze_supp(provider, f"{v['brand']} {model}",
                                             data_root / side["file_path"], weak, vocab, tax)
                if supp.get("parts"):
                    data = analysis.merge_views(
                        data, {"parts": supp["parts"]}, view_tag=side["view_angle"])
                data["supplement"] = {"slots": weak, "errors": supp.get("_errors", [])}
            else:
                data["supplement"] = {"slots": weak, "errors": [],
                                      "skipped": "无副图或无需补证"}
            data["vehicle"] = {"brand": v["brand"], "model": model,
                               "category": v["category"]}
            target.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                              encoding="utf-8")

        tags = [t["tag"] for t in (data.get("unit") or {}).get("style_tags", [])]
        if tags and not any(t in ledger.used for t in tags):
            ledger.take(tags)
        vis = {p["slot"]: p.get("visible") for p in data.get("parts", [])}
        ok = "OK" if not (data.get("_meta") or {}).get("status") == "needs_review" else "REVIEW"
        print(f"[{i}/{len(models)}] {model}: {tags} {vis} {ok}")
        summary.append({"model": model, "tags": tags, "visible": vis,
                        "needs_review": (data.get("_meta") or {}).get("status") == "needs_review"})

    (outdir / "_summary.json").write_text(json.dumps(
        {"vehicles": summary, "used_tags": ledger.used,
         "cluster_balance": ledger.balance(),
         "cluster_count": ledger.cluster_count,
         "tokens": provider.tokens, "calls": provider.calls},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n共 {len(models)} 台；API 调用 {provider.calls} 次，{provider.tokens} tokens；"
          f"簇均衡差 {ledger.balance()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
