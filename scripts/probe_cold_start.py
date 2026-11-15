# -*- coding: utf-8 -*-
"""冷启动探针：LLM 凭参数化知识列车型，再用检索验证是否真实存在。

目的（2026-11-15）：回答“DeepSeek 能不能做领域知识冷启动”这一决策问题。
方法：
  1) 对 10 个类目，让模型列 8 个“真实存在、可检索到”的具体车型（品牌+型号+构型）；
  2) 每个车型发一条搜索（品牌+型号+类目），看结果标题/摘要里是否出现该型号的
     主码或品牌+车系 token（复用 identity 归一化）；
  3) 与三轮真实检索（p8-idmatch r1/r2/r3）的 grounded 候选池比对覆盖率。

用法:
  PYTHONPATH=src python scripts/probe_cold_start.py --out data-test/evals/cold-start-probe-20261115.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equiplens.identity import primary_code  # noqa: E402

API = "https://api.deepseek.com"
KEY_FILE = Path.home() / ".equiplens" / "deepseek.env"
MODEL = "deepseek-flash"


def load_key() -> str:
    import os
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("DEEPSEEK_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no DEEPSEEK_API_KEY")


def chat(key: str, prompt: str) -> dict:
    r = requests.post(f"{API}/chat/completions",
                      headers={"Authorization": f"Bearer {key}",
                               "Content-Type": "application/json"},
                      json={"model": MODEL,
                            "messages": [{"role": "user", "content": prompt}],
                            "response_format": {"type": "json_object"},
                            "temperature": 0},
                      timeout=180)
    r.raise_for_status()
    return json.loads(r.json()["choices"][0]["message"]["content"])


def search(key: str, query: str, count: int = 10) -> list[dict]:
    r = requests.post(f"{API}/v1/tools/search",
                      headers={"Authorization": f"Bearer {key}",
                               "Content-Type": "application/json"},
                      json={"query": query, "count": count}, timeout=60)
    r.raise_for_status()
    return r.json().get("results", [])


def norm(s: str) -> str:
    return re.sub(r"[^A-Z0-9\u4e00-\u9fff]", "", (s or "").upper())


def supported(model: str, results: list[dict]) -> bool:
    tok = primary_code(model)
    texts = [(r.get("title") or "") + " " + (r.get("summary") or r.get("snippet") or "")
             for r in results]
    if tok:
        flat = tok.cores[0].replace(".", "")
        pat = re.compile(r"(?<![A-Z0-9])" + re.escape(flat) + r"(?![0-9])")
        return any(pat.search(t.upper().replace("×", "X")) for t in texts)
    # 没有码：退化为“车名前两个中文/拉丁 token 同时出现”
    toks = [t for t in re.findall(r"[A-Za-z0-9\u4e00-\u9fff]{2,}", model)
            if t.lower() not in {"卡车", "牵引车", "搅拌车", "叉车", "压路机"}][:2]
    return any(all(t.lower() in x.lower() for t in toks) for x in texts)


def grounded_models() -> dict[str, set[str]]:
    """三轮真实 plan 的候选（归一化 token），作为“检索可达”的参照。"""
    out: dict[str, set[str]] = {}
    roots = ["p8-idmatch-20261114", "p8-idmatch-r2-20261114", "p8-idmatch-r3-20261114"]
    for root in roots:
        for plan in (ROOT / "data-test" / "runs" / root).glob("*/plan.json"):
            d = json.loads(plan.read_text(encoding="utf-8"))
            case = plan.parent.name
            bag = out.setdefault(case, set())
            for c in d.get("candidates") or []:
                tok = primary_code(c.get("model") or "")
                if tok:
                    bag.add(tok.cores[0].replace(".", ""))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=8)
    ap.add_argument("--out", default="data-test/evals/cold-start-probe-20261115.json")
    args = ap.parse_args(argv)
    key = load_key()

    cases = {
        "c1-desert-tractor": "沙漠牵引车",
        "c2-reach-stacker": "正面吊",
        "c3-tractor": "轮式拖拉机",
        "c4-forklift": "电动叉车",
        "c5-roller": "单钢轮压路机",
        "s6-mixer": "混凝土搅拌运输车",
        "h1-fire": "泡沫消防车",
        "h2-wrecker": "清障车",
        "h3-sweeper": "扫路车",
        "h4-crane-truck": "随车起重运输车",
    }
    grounded = grounded_models()
    rows = []
    for case, klass in cases.items():
        prompt = (
            f"你是工程车辆行业专家。请列出中国市场**真实存在、能在公开网页检索到**的"
            f"「{klass}」具体车型，最多 {args.per} 个。\n"
            "要求：\n"
            "1) 必须给品牌 + 具体型号/型号码（字母数字，如 X3000、CPD50、TGM18.290），不要只写品类；\n"
            "2) 不要编造型号；不确定就不要列；\n"
            "3) 输出 JSON：{\"models\":[{\"brand\":\"\",\"model\":\"\",\"config\":\"\",\"why\":\"\"}]}"
        )
        payload = chat(key, prompt)
        models = payload.get("models") or []
        for m in models[: args.per]:
            model = (str(m.get("brand") or "") + " " + str(m.get("model") or "")).strip()
            q = f"{model} {klass}"[:100]
            t0 = time.time()
            try:
                results = search(key, q, count=10)
            except Exception as e:  # noqa: BLE001
                results = []
                err = str(e)[:100]
            tok = primary_code(model)
            hit = supported(model, results)
            rows.append({
                "case": case, "class": klass, "brand": m.get("brand"), "model": m.get("model"),
                "query": q, "results": len(results), "supported": hit,
                "code": tok.full if tok else "",
                "grounded": bool(tok and tok.cores[0].replace(".", "") in grounded.get(case, set())),
                "ms": round((time.time() - t0) * 1000),
            })
            print(f"{'OK ' if hit else 'MISS'} {case:<20} {model[:40]:<42} results={len(results)}", flush=True)

    total = len(rows)
    sup = sum(1 for r in rows if r["supported"])
    grounded_hit = sum(1 for r in rows if r["grounded"])
    summary = {
        "created_at": "2026-11-15",
        "model": MODEL,
        "per_category": args.per,
        "categories": len(cases),
        "proposed": total,
        "supported": sup,
        "supported_rate": round(sup / max(1, total), 3),
        "in_grounded_pool": grounded_hit,
        "in_grounded_rate": round(grounded_hit / max(1, total), 3),
        "grounded_pool_size": {k: len(v) for k, v in grounded.items()},
    }
    Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
