# -*- coding: utf-8 -*-
"""判死链离线评估（不联网、不改数据）。

用历史产物（plan.json / state.json / fetch_log.jsonl）重放判定逻辑：
  1) 查询键：旧 normalize_query vs 新（括号内型号码、长查询、6x6 硬拼）
  2) 相关性护栏：旧品牌兜底 vs 新（历史已放行命中是否被新逻辑改判丢弃）
  3) 身份证据：历史 unknown 的资产，用“车系+构型”双证据能救回多少

用法:
  PYTHONPATH=src python scripts/evaluate_kill_chain_offline.py
输出:
  data-test/evals/kill-chain-offline-20261114.json
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

from equiplens import imagesearch  # noqa: E402
from equiplens.retrieval_engine.contracts import Asset  # noqa: E402
from equiplens.retrieval_engine.web import RuleVerifier, WebWorld  # noqa: E402

RUNS = ROOT / "data-test" / "runs"


# ---------------------------------------------------------------- old logic
def old_brand_group(src: str) -> tuple[str, ...]:
    toks = imagesearch._tokens(src)
    for t in toks:
        if t in imagesearch._BRAND_LOOKUP:
            return imagesearch._BRAND_LOOKUP[t]
    for t in toks:
        if not re.search(r"\d", t) and t not in imagesearch.GENERIC and len(t) >= 2:
            return (t,)
    return ()


def old_relevant(query: str, title: str, model: str | None = None) -> bool:
    t = (title or "").lower()
    if not t:
        return False
    if any(w in t for w in imagesearch.NON_VEHICLE):
        return False
    src = model or query
    want = imagesearch._config_set(src)
    have = imagesearch._config_set(t)
    if want and have and not (want & have):
        return False
    codes = imagesearch._distinctive(src)
    if codes and any(c in t for c in codes):
        return True
    group = old_brand_group(src)
    if group:
        if any(imagesearch._alias_in(a, t) for a in group):
            return True
        return False
    return any(w in t for w in imagesearch.VEHICLE_WORDS)


def old_normalize_query(model: str) -> str:
    s = re.sub(r"[（(][^）)]*[）)]", " ", model or "").replace("×", "x").strip()
    code = re.search(r"[A-Z]{1,4}\d{3,}[A-Z0-9]*", s)
    if code:
        brand = re.search(r"[一-鿿]{2,4}", s[:code.start()])
        pre = brand.group(0) if brand else ""
        return f"{pre} {code.group(0)} 6x6".strip()
    words = [w for w in s.split() if w]
    key = " ".join(words[:3]).strip(" /,、;")
    return key if "6x6" in key.lower() else f"{key} 6x6"


# ---------------------------------------------------------------- collect
def models() -> dict[str, str]:
    """model -> identity_kind（来自 plan / state）。"""
    out: dict[str, str] = {}
    for p in RUNS.rglob("plan.json"):
        try:
            j = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for c in (j.get("candidates") or []):
            if c.get("model"):
                out.setdefault(c["model"], c.get("identity_kind") or "")
    for p in RUNS.rglob("state.json"):
        try:
            s = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for _tid, t in (s.get("targets") or {}).items():
            if t.get("model"):
                out.setdefault(t["model"], t.get("identity_kind") or "")
    return out


def main() -> int:
    ms = models()
    q_stats = Counter()
    q_samples = {"paren_code": [], "longer": []}
    for m in ms:
        old = old_normalize_query(m)
        new = WebWorld.normalize_query(m)
        q_stats["models"] += 1
        if old != new:
            q_stats["changed"] += 1
        codes = re.findall(r"[A-Z]{1,4}\d{3,}", m)
        if codes and re.search(r"[（(][^）)]*" + re.escape(codes[0]), m):
            q_stats["paren_code"] += 1
            if "taz4922" in new.lower() or codes[0].lower() in new.lower():
                q_stats["paren_code_fixed"] += 1
            if len(q_samples["paren_code"]) < 8:
                q_samples["paren_code"].append({"model": m[:40], "old": old[:40], "new": new[:40]})
        if len(old) > 14:
            q_stats["old_long"] += 1
            if len(new) < len(old):
                q_stats["new_shorter"] += 1
            if len(q_samples["longer"]) < 8:
                q_samples["longer"].append({"model": m[:40], "old": old[:40], "new": new[:40]})
        if "6x6" in old.lower() and not re.search(r"(?i)6x6|8x8|4x4", m.replace("×", "x")):
            q_stats["hard_6x6"] += 1
        if not imagesearch.alias_query(m):
            q_stats["alias_empty"] += 1

    # 相关性护栏回放（只对历史已放行的命中做一致性检查）
    rel = Counter()
    rejects: list[dict] = []
    for p in RUNS.rglob("fetch_log.jsonl"):
        for line in open(p, encoding="utf-8", errors="ignore"):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:  # noqa: BLE001
                rel["bad_json"] += 1
                continue
            model = r.get("model") or ""
            q = r.get("part_query") or ""
            title = r.get("title") or ""
            if not q or not model:
                rel["skip"] += 1
                continue
            rel["rows"] += 1
            old = old_relevant(q, title, model)
            new = imagesearch._relevant(q, title, model)
            if old and not new:
                rel["old_pass_new_reject"] += 1
                if len(rejects) < 15:
                    rejects.append({"model": model[:30], "title": title[:40], "q": q[:30]})
            elif not old and new:
                rel["old_reject_new_pass"] += 1

    # 身份证据：历史 unknown 的资产能否靠“车系+构型”救回
    verifier = RuleVerifier({})
    ident = Counter()
    flips: list[dict] = []
    for p in RUNS.rglob("state.json"):
        try:
            s = json.load(open(p, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        meta = s.get("asset_meta") or {}
        for key, v in (s.get("verifications") or {}).items():
            aid, _, part = key.partition(":")
            a = meta.get(aid)
            if not a or not a.get("title"):
                continue
            ident["checked"] += 1
            if v.get("identity") != "unknown":
                ident["known"] += 1
                continue
            ident["unknown"] += 1
            try:
                asset = Asset.from_dict(a, target_id=a.get("target_id") or aid, part=part)
                newv = verifier.verify(asset, part)
            except Exception:  # noqa: BLE001
                continue
            if newv.identity != "unknown":
                ident["flip_to_probable"] += 1
                if len(flips) < 10:
                    flips.append({"model": (a.get("model") or "")[:30],
                                  "title": (a.get("title") or "")[:40],
                                  "new_identity": newv.identity})

    out = {
        "generated_at": "2026-11-14",
        "note": "离线重放，不联网；只评估判定层，不等价端到端",
        "query_key": dict(q_stats),
        "query_samples": q_samples,
        "relevance_replay": dict(rel),
        "relevance_new_reject_samples": rejects,
        "identity_replay": dict(ident),
        "identity_flip_samples": flips,
    }
    dest = ROOT / "data-test" / "evals" / "kill-chain-offline-20261114.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1)[:4000])
    print("\nout:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
