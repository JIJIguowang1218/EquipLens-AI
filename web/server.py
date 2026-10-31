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
        hero = v["hero"]
        if str(hero).startswith("http"):
            import urllib.request as _u
            dl = out / f"{i:02d}-hero.jpg"
            try:
                _u.urlretrieve(hero, dl)
                img = dl
            except Exception:
                emit(job, model, "fail", "主图下载失败")
                continue
        else:
            img = DATA / hero
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


CAND: dict[str, dict] = {}


def _reason_fallback(c: dict, category: str = "") -> dict:
    srcs = c.get("sources") or []
    title = (srcs[0].get("title") or "") if srcs else ""
    rel = "同类目"
    for kw, tag in (("沙漠", "环境特化"), ("越野", "环境特化"), ("6x6", "同平台"),
                    ("6X6", "同平台"), ("底盘", "同平台")):
        if kw in title:
            rel = tag
            break
    reason = (f"《{title[:16]}…》提到该型号" if title else
              f"{c.get('mentions',0)} 篇文章提及")
    return {"relation": rel, "reason": reason[:40], "evidence": title}


def _reasons_llm(category: str, parts: list[str], cands: list[dict]) -> list[dict]:
    """一次模型调用，为候选清单写关联理由（必须能由来源标题或车型本身看出）。"""
    NL = chr(10)
    cfg = analysis.load_config()
    lines = []
    for i, c in enumerate(cands, 1):
        srcs = (c.get("sources") or [])[:2]
        titles = " / ".join((s.get("title") or "")[:40] for s in srcs) or "（无标题）"
        lines.append(f"{i}. {c.get('brand','')} {c.get('model','')}｜提及 {c.get('mentions',0)} 次｜来源标题：{titles}")
    prompt = NL.join([
        f"类目：{category}；关注部位：{'、'.join(parts) or '前脸'}",
        "下面是检索到的候选车型与来源标题。为每个候选写一条「关联理由」，",
        "必须能从来源标题或车型本身看出来，不要编造事实。",
        "relation 只能取：同类目 / 邻近类目 / 同平台 / 环境特化。",
        "reason 不超过 28 字，说清为什么该进这份清单。",
        '只输出 JSON 数组：[{"i":1,"relation":"同类目","reason":"..."}]',
        "",
        NL.join(lines),
    ])
    payload = {"model": cfg.get("LLM_MODEL") or cfg["LLM_VISION_MODEL"],
               "reasoning_effort": "low", "max_tokens": 3000,
               "messages": [{"role": "user", "content": prompt}]}
    import urllib.request
    req = urllib.request.Request(cfg["LLM_BASE_URL"].rstrip("/") + "/chat/completions",
                                 data=json.dumps(payload).encode(),
                                 headers={"Authorization": f"Bearer {cfg['LLM_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = json.load(r)["choices"][0]["message"]["content"] or ""
    import re as _re
    m = _re.search(r"\[.*\]", raw, _re.S)
    out = []
    if m:
        try:
            for item in json.loads(m.group(0)):
                out.append({"relation": item.get("relation", "同类目"),
                            "reason": (item.get("reason") or "")[:40]})
        except Exception:
            out = []
    while len(out) < len(cands):
        out.append(_reason_fallback(cands[len(out)], category))
    return out


def _gen_candidates(job_id: str, category: str, parts: list[str]):
    job = CAND[job_id]
    try:
        from equiplens import roster
        job["stage"] = "检索中（真实网页搜索，约 30–60 秒）"
        res = roster.generate_roster(category, DATA, max_articles=6, top_n=12)
        cands = res.get("candidates") or []
        if not cands:
            job.update(status="fail", error="没有检索到候选，可能被拦截，请重试")
            return
        job["stage"] = "生成关联理由"
        reasons = None
        for attempt in (1, 2):
            try:
                reasons = _reasons_llm(category, parts, cands)
                break
            except Exception as e:  # noqa: BLE001
                job["reason_error"] = str(e)[:160]
                time.sleep(1)
        if not reasons:
            reasons = [_reason_fallback(c, category) for c in cands]
        items = []
        for c, r in zip(cands, reasons):
            srcs = c.get("sources") or []
            items.append({"brand": c.get("brand", ""), "model": c.get("model", ""),
                          "mentions": c.get("mentions", 0),
                          "relation": r.get("relation", "同类目"),
                          "reason": r.get("reason", ""),
                          "evidence": (srcs[0].get("title", "") if srcs else ""),
                          "evidence_url": (srcs[0].get("url", "") if srcs else ""),
                          "n_sources": len(srcs)})
        job.update(status="done", candidates=items, articles=len(res.get("articles") or []))
    except Exception as e:  # noqa: BLE001
        job.update(status="fail", error=str(e)[:200])


@app.post("/api/candidates")
def api_candidates(payload: dict):
    category = (payload.get("category") or "").strip()
    if not category:
        raise HTTPException(400, "缺类目")
    job_id = uuid.uuid4().hex[:8]
    CAND[job_id] = {"status": "running", "stage": "排队", "candidates": [],
                    "category": category}
    threading.Thread(target=_gen_candidates, args=(job_id, category, payload.get("parts") or []),
                     daemon=True).start()
    return {"job_id": job_id}


@app.get("/api/candidates/{job_id}")
def api_candidates_status(job_id: str):
    job = CAND.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return job


@app.get("/api/heroes")
def api_heroes(model: str):
    """先查库内素材；没有就实时搜图（真实网页图片搜索）。"""
    cands = hero_candidates(model)
    if cands:
        return {"model": model, "source": "library", "candidates": cands}
    try:
        from equiplens import imagesearch
        res, status = imagesearch.search_model_images(model, limit=6)
        out = [{"url": r.get("url"), "file_path": None, "view_angle": "web",
                "width": r.get("width") or 0, "height": r.get("height") or 0,
                "title": (r.get("title") or "")[:60]} for r in res if r.get("url")]
        return {"model": model, "source": "web", "status": status, "candidates": out}
    except Exception as e:  # noqa: BLE001
        return {"model": model, "source": "web", "error": str(e)[:120], "candidates": []}


@app.post("/api/run")
def api_run(payload: dict):
    vehicles = payload.get("vehicles") or []
    if not vehicles:
        raise HTTPException(400, "没有选择车型")
    raw_parts = payload.get("parts") or SLOTS
    slots = []
    for s in raw_parts:
        s = str(s).strip()
        if not s:
            continue
        if s not in slots:
            slots.append(s)
    slots = slots[:8] or SLOTS
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
