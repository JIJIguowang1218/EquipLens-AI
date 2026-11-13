# -*- coding: utf-8 -*-
"""下载并发基准：同一批 URL，串行 vs N 路并发（只测下载+门卫，不改生产 loop）。

用法：
  PYTHONPATH=src python scripts/bench_download_concurrency.py \\
      --run data-test/runs/ab-negative-20261113/c5-roller/with/run --n 40
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import imagesearch  # noqa: E402


def load_hits(run: Path, n: int) -> list[dict]:
    seen, hits = set(), []
    try:
        lines = (run / "fetch_log.jsonl").read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    for line in lines:
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        u = r.get("url")
        if u and u not in seen:
            seen.add(u)
            hits.append({"url": u, "title": r.get("title", ""),
                         "channel": r.get("channel", "")})
        if len(hits) >= n:
            break
    return hits


def one(hit: dict) -> dict:
    # 每次用独立 DomainHealth，避免并发下的计数竞争；这里只测吞吐。
    return imagesearch._download_and_gate(hit, imagesearch.DomainHealth())


def run_batch(hits: list[dict], workers: int) -> dict:
    t0 = time.time()
    if workers <= 1:
        res = [one(h) for h in hits]
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            res = list(ex.map(one, hits))
    sec = time.time() - t0
    ok = sum(1 for r in res if r.get("data"))
    gated = sum(1 for r in res if (r.get("gate") or {}).get("pass"))
    errs = sum(1 for r in res if r.get("error"))
    return {"workers": workers, "n": len(hits), "sec": round(sec, 2),
            "ok": ok, "gate_pass": gated, "errors": errs,
            "per_item_ms": round(sec / max(1, len(hits)) * 1000),
            "errors_sample": [str(r.get("error"))[:60] for r in res
                              if r.get("error")][:5]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--workers", default="1,2,4,8")
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)
    hits = load_hits(Path(args.run), args.n)
    if not hits:
        raise SystemExit("no hits in fetch_log")
    # 预热：加载 ONNX 模型，避免把首帧算进第一组
    one(hits[0])
    rows = []
    for w in [int(x) for x in args.workers.split(",") if x.strip()]:
        r = run_batch(hits, w)
        rows.append(r)
        print(json.dumps(r, ensure_ascii=False), flush=True)
    base = next((r for r in rows if r["workers"] == 1), None)
    if base:
        for r in rows:
            r["speedup_vs_serial"] = round(base["sec"] / r["sec"], 2) if r["sec"] else None
    out = Path(args.out) if args.out else Path(args.run).parent.parent / "DOWNLOAD-CONCURRENCY.json"
    out.write_text(json.dumps({"run": str(args.run), "rows": rows},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print("out:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
