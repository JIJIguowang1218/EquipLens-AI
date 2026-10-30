# -*- coding: utf-8 -*-
"""证据索引：给"推荐车型"提供可核对的出处（URL + 标题 + 证据级）。

- `--build`  从已落盘 corpus 的真实文章索引建库（标题含型号 → E3）
- `--lookup 型号`  查某型号有哪些证据（给规划员用）
- `--check list.json`  校验清单里每条占槽目标的证据是否成立
- `--index PATH`  指定索引文件（默认 data-test/evals/evidence-index-20261031.json）

证据级：E3=详情页/专文（标题含型号，URL 非图片搜索）；E1=仅 SERP 命中；E0=无。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INDEX = ROOT / "data-test" / "evals" / "evidence-index-20261031.json"
BAD_URL = ("image.baidu.com", "image.so.com", "pic.sogou.com")


def _norm(s: str) -> str:
    t = str(s).lower().replace("×", "x")
    return "".join(ch for ch in t if not ch.isspace() and ch not in "-_*·/()（）")


def _models_from_rosters() -> list[str]:
    out: set[str] = set()
    for f in (ROOT / "data-test").glob("roster-*.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for c in d.get("candidates", []):
            m = c.get("model")
            if m and len(_norm(m)) >= 3:
                out.add(m)
    return sorted(out)


def _corpus_articles() -> list[tuple[str, str]]:
    arts: list[tuple[str, str]] = []
    for f in (ROOT / "data-test" / "corpus").glob("batch-*/index.json"):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for r in d.get("index", []):
            url, title = r.get("url", ""), r.get("title", "")
            if not url.startswith("http") or not title:
                continue
            if any(b in url for b in BAD_URL):
                continue
            arts.append((url, title))
    return arts


def build(index_path: Path) -> dict:
    models = _models_from_rosters()
    arts = _corpus_articles()
    items = []
    for model in models:
        for url, title in arts:
            if _norm(model) in _norm(title):
                items.append({"model": model, "url": url, "title": title,
                              "grade": "E3", "source": "corpus"})
    data = {"built_at": "2026-10-31", "models": len(models),
            "articles": len(arts), "items": items}
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"models": len(models), "articles": len(arts),
                      "evidence": len(items), "path": str(index_path)},
                     ensure_ascii=False))
    return data


def _load(index_path: Path) -> dict:
    if not index_path.exists():
        raise SystemExit(f"索引不存在：{index_path}（先跑 --build）")
    return json.loads(index_path.read_text(encoding="utf-8"))


def lookup(index: dict, model: str) -> list[dict]:
    key = _norm(model)
    return [it for it in index["items"] if key and key in _norm(it["model"])]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="车型证据索引：建库/查询/校验")
    ap.add_argument("--index", default=str(DEFAULT_INDEX))
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--lookup")
    ap.add_argument("--check")
    ap.add_argument("--limit", type=int, default=5)
    a = ap.parse_args(argv)
    idx_path = Path(a.index)

    if a.build:
        build(idx_path)
        return 0
    index = _load(idx_path)
    if a.lookup:
        hits = lookup(index, a.lookup)
        print(json.dumps({"model": a.lookup, "count": len(hits),
                          "evidence": hits[:a.limit]}, ensure_ascii=False, indent=1))
        return 0
    if a.check:
        doc = json.loads(Path(a.check).read_text(encoding="utf-8"))
        bad, ok = [], 0
        for t in doc.get("targets", []):
            if not t.get("slots"):
                continue
            models = t.get("models") or []
            got = [e for e in (t.get("evidence") or [])
                   if e.get("grade") == "E3"
                   and any(_norm(m) in _norm(e.get("title", "")) for m in models)]
            if got:
                ok += 1
            else:
                bad.append({"id": t.get("id"), "models": models,
                            "evidence_in_list": len(t.get("evidence") or []),
                            "index_hits": sum(len(lookup(index, m)) for m in models)})
        print(json.dumps({"ok": not bad, "checked": ok + len(bad),
                          "with_e3": ok, "problems": bad},
                         ensure_ascii=False, indent=1))
        return 0 if not bad else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
