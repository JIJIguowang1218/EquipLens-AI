# -*- coding: utf-8 -*-
"""把冒烟报告里“下载成功”的图全部重新落盘（含门卫未通过），并生成 gallery。

用法:
  PYTHONPATH=src python scripts/export_smoke_images.py \
      data-test/runs/web-smoke-20261109 data-test/runs/web-smoke-hd-20261109
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens.imagesearch import CHANNEL_REFERERS, UA  # noqa: E402


def slug(s: str) -> str:
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "-", str(s)).strip("-")
    return s[:36] or "x"


def fetch_one(job: dict) -> dict:
    row = job["row"]
    out = dict(job)
    out.update({"gate_pass": bool(row.get("gate_pass")),
                "view": row.get("view", ""),
                "scene": row.get("scene", ""),
                "margin": row.get("margin", 0),
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "channel": row.get("channel", "")})
    out["status"] = "skipped"
    out["image"] = ""
    out["error"] = ""
    if not row.get("download_ok") or not row.get("url"):
        out["error"] = row.get("error") or "download_failed"
        return out
    referer = CHANNEL_REFERERS.get(row.get("channel", ""),
                                   "https://image.so.com/")
    try:
        r = requests.get(row["url"], headers={"User-Agent": UA,
                                              "Referer": referer},
                         timeout=25)
        if r.status_code != 200:
            out["error"] = f"http:{r.status_code}"
            return out
        img = Image.open(BytesIO(r.content)).convert("RGB")
        name = (f"{job['q_idx']:02d}-{slug(job['model'])}-"
                f"{job['r_idx']:02d}-{'pass' if row.get('gate_pass') else 'fail'}.jpg")
        img.save(job["out_dir"] / name, "JPEG", quality=88)
        out.update({"status": "saved", "image": f"all-downloads/{name}",
                    "width": img.size[0], "height": img.size[1]})
        return out
    except Exception as e:  # noqa: BLE001
        out["error"] = f"{type(e).__name__}: {e}"[:120]
        return out


def render_gallery(batch: Path, rows: list[dict]) -> str:
    cards = []
    for r in rows:
        if r["status"] != "saved":
            continue
        badge = "PASS" if r.get("gate_pass") else "FAIL"
        cls = "pass" if r.get("gate_pass") else "fail"
        cards.append(
            f"<figure class='{cls}'><img src='{html.escape(r['image'])}' loading='lazy'>"
            f"<figcaption><span class='badge'>{badge}</span> "
            f"<b>{html.escape(r['query'])}</b><br>"
            f"{html.escape(str(r.get('view','')))} · {r.get('width',0)}×{r.get('height',0)}<br>"
            f"{html.escape(str(r.get('title',''))[:90])}</figcaption></figure>")
    return f"""<!doctype html><meta charset="utf-8">
<title>{html.escape(batch.name)} · all downloads</title>
<style>
body{{font:14px/1.5 system-ui;margin:24px;background:#111;color:#eee}}
h1{{font-size:18px}} .meta{{color:#aaa;margin-bottom:16px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px}}
figure{{margin:0;background:#1b1b1b;border:1px solid #333;border-radius:8px;overflow:hidden}}
figure.pass{{border-color:#3a5f3a}} figure.fail{{border-color:#5f3a3a}}
img{{width:100%;height:180px;object-fit:cover;display:block}}
figcaption{{padding:8px;font-size:12px;color:#bbb}}
.badge{{display:inline-block;padding:1px 5px;border-radius:3px;font-size:10px;
        background:#333;color:#ddd}} figure.pass .badge{{background:#2e5a2e;color:#b8f0b8}}
figure.fail .badge{{background:#5a2e2e;color:#f0b8b8}}
</style>
<h1>{html.escape(batch.name)} · 全部下载成功图</h1>
<div class="meta">共 {sum(1 for r in rows if r['status']=='saved')} 张（含门卫未通过）；PASS=门卫通过，FAIL=门卫未通过</div>
<div class="grid">{''.join(cards)}</div>"""


def export_batch(batch: Path) -> None:
    report = json.loads((batch / "report.json").read_text(encoding="utf-8"))
    out_dir = batch / "all-downloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = []
    for qi, q in enumerate(report["queries"], 1):
        for ri, row in enumerate(q["rows"], 1):
            jobs.append({"q_idx": qi, "r_idx": ri, "query": q["query"],
                         "model": q["model"], "row": row, "out_dir": out_dir})
    with ThreadPoolExecutor(max_workers=4) as ex:
        rows = list(ex.map(fetch_one, jobs))
    (batch / "all-downloads.json").write_text(
        json.dumps({"batch": batch.name,
                    "rows": [{k: v for k, v in r.items() if k != "out_dir"}
                             for r in rows]},
                   ensure_ascii=False, indent=2), encoding="utf-8")
    (batch / "all-downloads.html").write_text(render_gallery(batch, rows),
                                              encoding="utf-8")
    saved = sum(1 for r in rows if r["status"] == "saved")
    print(f"{batch.name}: saved {saved}/{len(rows)} -> {out_dir}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("batches", nargs="+")
    args = parser.parse_args(argv)
    for b in args.batches:
        export_batch(Path(b))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
