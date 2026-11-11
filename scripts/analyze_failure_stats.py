# -*- coding: utf-8 -*-
"""统计 run 的失败原因与初始下载阶梯成功率（只读 run 目录）。"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "data-test" / "runs"


def rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def err_kind(err: str) -> str:
    e = (err or "").lower()
    if "403" in e:
        return "http_403"
    if "404" in e:
        return "http_404"
    if "timeout" in e or "timed out" in e:
        return "timeout"
    if "redirect" in e:
        return "redirect_loop"
    if "connection" in e:
        return "connection"
    return (err or "unknown")[:40]


def run_stats(name: str) -> dict:
    d = RUNS / name
    fetch = rows(d / "fetch_log.jsonl")
    ok = [r for r in fetch if r.get("ok")]
    gate = [r for r in ok if r.get("gate_pass")]
    state = {}
    try:
        state = json.loads((d / "state.json").read_text(encoding="utf-8"))
    except Exception:
        pass
    targets = state.get("targets") or {}
    assets = state.get("assets") or {}
    accepted = {t for u in (state.get("units") or {}).values()
                for t in (u.get("accepted_targets") or [])}
    verifs = state.get("verifications") or {}
    no_assets = [t for t in targets if not any((assets.get(t) or {}).values())]
    unknown = sum(1 for v in verifs.values() if v.get("identity") == "unknown")
    defects = Counter(x for v in verifs.values() for x in (v.get("defects") or []))
    ladder = Counter()
    for r in fetch:
        if r.get("tries") is None:
            continue
        key = ("ok_try_" if r.get("gate_pass") else "fail_try_") + str(r["tries"])
        ladder[key] += 1
    return {
        "run": name,
        "fetch_rows": len(fetch),
        "download_ok": len(ok),
        "gate_pass_rows": len(gate),
        "unique_images": len({r.get("sha1") for r in ok}),
        "download_errors": Counter(err_kind(r.get("error")) for r in fetch if not r.get("ok")).most_common(8),
        "prefilter": Counter(x for r in ok for x in (r.get("pre_reasons") or [])).most_common(8),
        "gate_drops": Counter(r.get("drop_label") for r in ok
                              if not r.get("gate_pass")).most_common(8),
        "targets": len(targets),
        "delivered": len(accepted),
        "no_asset_targets": len(no_assets),
        "no_asset_names": no_assets[:10],
        "citation_false": sum(1 for t in targets.values() if not t.get("citation_ok")),
        "verification_unknown": unknown,
        "verification_defects": defects.most_common(6),
        "ladder": ladder.most_common(10),
        "ladder_instrumented": bool(ladder),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="*", default=[
        "loop-intent-test3-20261111", "loop-generic-test-20261111",
        "loop-m1b-global-v2", "loop-c01-plan9"])
    ap.add_argument("--out", default="data-test/evals/failure-stats-20261111")
    args = ap.parse_args(argv)
    stats = [run_stats(n) for n in args.runs]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    (out.with_suffix(".json")).write_text(json.dumps(stats, ensure_ascii=False, indent=1),
                                          encoding="utf-8")
    lines = ["# 失败原因 / 初始阶梯统计", "",
             "> 旧 run 的 fetch_log 没有 `tries`，只能统计失败原因；新 run 才有阶梯次数。", ""]
    for s in stats:
        lines += [f"## {s['run']}", "",
                  f"- fetch {s['fetch_rows']} / ok {s['download_ok']} / 过门卫 {s['gate_pass_rows']}"
                  f" / 唯一图 {s['unique_images']}",
                  f"- 目标 {s['targets']} / 交付 {s['delivered']} / 无图目标 {s['no_asset_targets']}"
                  f" / citation_false {s['citation_false']}",
                  f"- 下载失败原因：{s['download_errors']}",
                  f"- 门卫拒绝：{s['gate_drops']}",
                  f"- 核验 unknown/缺陷：{s['verification_unknown']} / {s['verification_defects']}",
                  f"- 阶梯：{s['ladder'] or '未采集（旧日志无 tries）'}", ""]
        if s["no_asset_names"]:
            lines.append("- 无图目标示例：" + "、".join(s["no_asset_names"][:5]))
    (out.with_suffix(".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(out.with_suffix(".md")), "runs": len(stats)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
