# -*- coding: utf-8 -*-
"""EquipLens Web 壳：五步流程（立项 → 清单 → 素材 → 分析 → 导出）。

启动:
  PYTHONPATH=src python web/server.py --port 8770
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equiplens import analysis  # noqa: E402

DATA = ROOT / "data-test"
RUNS = ROOT / "data" / "web-runs"
UI = Path(__file__).resolve().parent / "ui"

SLOTS = ["grille", "bumper", "side_guard", "wheel_arch", "step"]
SLOT_CN = {"grille": "进气格栅", "bumper": "保险杠", "side_guard": "侧防护栏",
           "wheel_arch": "前轮轮拱", "step": "登车踏步"}
HERO_VIEWS = ("hero_lf", "hero_rf", "hero_45", "side_l", "side", "front")

app = FastAPI(title="EquipLens")
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()


# ---------------------------------------------------------------- 数据

def conn():
    c = sqlite3.connect(DATA / "equiplens.db")
    c.row_factory = sqlite3.Row
    return c


def catalog() -> dict:
    c = conn()
    cats = [dict(r) for r in c.execute(
        "select category, count(*) n from vehicles where category is not null "
        "group by category order by n desc")]
    vehicles = [dict(r) for r in c.execute(
        """select v.id, v.brand, v.model_name, v.category,
                  count(a.id) assets
           from vehicles v left join assets a on a.vehicle_id = v.id
           group by v.id order by assets desc""")]
    c.close()
    return {"categories": cats, "vehicles": vehicles}


def hero_candidates(model: str) -> list[dict]:
    c = conn()
    rows = c.execute(
        """select a.file_path, a.view_angle, a.width, a.height
           from assets a join vehicles v on v.id = a.vehicle_id
           where v.model_name = ? and a.file_path is not null
             and a.view_angle in ('hero_lf','hero_rf','hero_45','side_l','side','front')
           order by a.width*a.height desc""", (model,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- 任务

def emit(job: dict, model: str, state: str, msg: str = ""):
    job["progress"].append({"model": model, "state": state, "msg": msg,
                            "t": time.strftime("%H:%M:%S")})


def run_pipeline(run_id: str, vehicles: list[dict], slots: list[str] | None = None):
    job = JOBS[run_id]
    out = RUNS / run_id
    out.mkdir(parents=True, exist_ok=True)
    cfg = analysis.load_config()
    provider = analysis.ApiProvider(cfg)
    vocab = analysis.load_vocab()
    tax = analysis.load_taxonomy()
    ledger = analysis.TagLedger(vocab)
    job["status"] = "running"

    total = len(vehicles)
    for i, v in enumerate(vehicles, 1):
        model = v["model_name"]
        emit(job, model, "run", f"正在分析 {model}（{i}/{total}）")
        img = DATA / v["hero"]
        try:
            data = analysis.analyze(provider, f"{v['brand']} {model}", img, slots or SLOTS,
                                    list(ledger.used), vocab, tax, view_tag="hero")
            data["vehicle"] = {"brand": v["brand"], "model": model,
                               "category": v.get("category", "")}
            data["assets"] = {"hero": v["hero"], "side": None}
            tags = [t["tag"] for t in (data.get("unit") or {}).get("style_tags", [])]
            if tags:
                ledger.take(tags)
            (out / f"{i:02d}-{model}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            subprocess.run([sys.executable, str(ROOT / "scripts" / "build_report_page.py"),
                            "--analysis", str(out / f"{i:02d}-{model}.json"),
                            "--out", str(out / "pages"),
                            "--page", str(i), "--total", str(total),
                            "--brand-rule", v.get("category", ""),
                            "--dump-blocks"],
                           check=True, capture_output=True, env={**dict(__import__("os").environ),
                                                                 "PYTHONPATH": str(ROOT / "src")})
            page = out / "pages" / f"{model}.html"
            if page.exists():
                import re as _re
                txt = page.read_text(encoding="utf-8")
                txt = _re.sub(r"(?:\.\./)+data-test/", "/", txt)
                page.write_text(txt, encoding="utf-8")
            job["pages"].append({"model": model, "brand": v["brand"],
                                 "file": f"pages/{model}.html",
                                 "json": f"{i:02d}-{model}.json"})
            emit(job, model, "ok", "完成")
        except Exception as e:  # noqa: BLE001
            emit(job, model, "fail", str(e)[:160])

    job["status"] = "done"
    emit(job, "-", "done", f"共 {len(job['pages'])} 页")


def export_pptx(run_id: str) -> Path:
    out = RUNS / run_id / "pages"
    target = RUNS / run_id / f"EquipLens-{run_id[:6]}.pptx"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "export_pptx.py"),
                    "--blocks", str(out), "--out", str(target)],
                   check=True, capture_output=True,
                   env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "src")})
    return target


# ---------------------------------------------------------------- 路由

@app.get("/", response_class=HTMLResponse)
def index():
    return (UI / "index.html").read_text(encoding="utf-8")


@app.get("/api/catalog")
def api_catalog():
    return catalog()


@app.get("/api/heroes")
def api_heroes(model: str):
    return {"model": model, "candidates": hero_candidates(model)}


@app.post("/api/run")
def api_run(payload: dict):
    vehicles = payload.get("vehicles") or []
    if not vehicles:
        raise HTTPException(400, "没有选择车型")
    slots = [s for s in (payload.get("parts") or SLOTS) if s in SLOTS] or SLOTS
    with LOCK:
        run_id = uuid.uuid4().hex[:8]
        JOBS[run_id] = {"id": run_id, "status": "queued", "progress": [],
                        "pages": [], "vehicles": vehicles}
        threading.Thread(target=run_pipeline, args=(run_id, vehicles, slots),
                         daemon=True).start()
    return {"run_id": run_id}


@app.get("/api/run/{run_id}")
def api_status(run_id: str):
    job = JOBS.get(run_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return job


@app.post("/api/export/{run_id}")
def api_export(run_id: str):
    if run_id not in JOBS:
        raise HTTPException(404, "任务不存在")
    try:
        f = export_pptx(run_id)
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, (e.stderr or b"")[-400:].decode("utf-8", "replace"))
    return {"file": f"/files/{run_id}/{f.name}", "name": f.name}


@app.get("/assets/{path:path}")
def assets(path: str):
    f = DATA / "assets" / path
    if not f.exists():
        raise HTTPException(404, "no file")
    return FileResponse(f)


@app.get("/files/{run_id}/{path:path}")
def files(run_id: str, path: str):
    f = RUNS / run_id / path
    if not f.exists():
        raise HTTPException(404, "no file")
    return FileResponse(f)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8770)
    a = ap.parse_args()
    RUNS.mkdir(parents=True, exist_ok=True)
    print(f"EquipLens Web: http://127.0.0.1:{a.port}")
    uvicorn.run(app, host="127.0.0.1", port=a.port, log_level="warning")
