# -*- coding: utf-8 -*-
"""死图床监测（只统计，不参与生产判断）。

背景：403 / DNS 死链是 2026-11-10 起已知问题（E20/T48），结论是"同 URL 重试无收益"。
当前生产只在**单轮 run 内**临时拉黑（imagesearch.DomainHealth），跨 run 不复用。
本脚本把历次 run 的 `fetch_log.jsonl` 汇总成长期观测表，供以后决定是否要做
持久化黑名单/换源；**生产代码不读取本脚本的输出**。

用法:
  PYTHONPATH=src python scripts/monitor_bad_domains.py
  PYTHONPATH=src python scripts/monitor_bad_domains.py --runs data-test/runs \
      --out data-test/evals/bad-domains-monitor
输出:
  data-test/evals/bad-domains-monitor.json   全量聚合
  data-test/evals/bad-domains-monitor.md     人读 Top 表
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


def classify(error: str) -> str:
    """把下载错误归一成有限几类，便于跨 run 聚合。"""
    e = (error or "").lower()
    if not e:
        return "unknown"
    if e == "domain_blocked":
        return "blocked"
    if "http 403" in e or " 403" in e:
        return "http_403"
    if "http 404" in e:
        return "http_404"
    if "getaddrinfo" in e or "nameresolution" in e or "name resolution" in e:
        return "dns"
    if "redirect" in e:
        return "redirect"
    if "timed out" in e or "timeout" in e:
        return "timeout"
    if "connection" in e or "pool" in e:
        return "connection"
    if "ssl" in e:
        return "ssl"
    return "other"


def host_of(url: str) -> str:
    try:
        return (urlparse(url or "").hostname or "").lower()
    except ValueError:
        return ""


def summarize(records: list[dict]) -> list[dict]:
    """records: [{host, error, run, date, url}] → 按 host 聚合。"""
    agg: dict[str, dict] = {}
    for r in records:
        host = r.get("host") or host_of(r.get("url", ""))
        if not host:
            continue
        a = agg.setdefault(host, {"host": host, "total_failures": 0,
                                  "by_class": Counter(), "runs": set(),
                                  "first_seen": "", "last_seen": "",
                                  "examples": []})
        a["total_failures"] += 1
        a["by_class"][classify(r.get("error", ""))] += 1
        if r.get("run"):
            a["runs"].add(r["run"])
        date = str(r.get("date") or "")
        if date:
            a["first_seen"] = min(filter(None, [a["first_seen"], date]))
            a["last_seen"] = max(filter(None, [a["last_seen"], date]))
        if len(a["examples"]) < 2 and r.get("url"):
            a["examples"].append(r["url"])
    rows = []
    for a in agg.values():
        rows.append({
            "host": a["host"],
            "total_failures": a["total_failures"],
            "by_class": dict(a["by_class"].most_common()),
            "runs": len(a["runs"]),
            "first_seen": a["first_seen"],
            "last_seen": a["last_seen"],
            "examples": a["examples"],
        })
    rows.sort(key=lambda x: (-x["total_failures"], x["host"]))
    return rows


def scan(runs_root: Path) -> tuple[list[dict], dict]:
    records: list[dict] = []
    runs = 0
    rows = 0
    for d in sorted(Path(runs_root).iterdir()):
        log = d / "fetch_log.jsonl"
        if not d.is_dir() or not log.exists():
            continue
        runs += 1
        m = re.search(r"(20\d{6})", d.name)
        date = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}" if m else ""
        try:
            with log.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    rows += 1
                    if rec.get("ok"):
                        continue
                    url = rec.get("url") or ""
                    records.append({"host": host_of(url), "url": url,
                                    "error": str(rec.get("error") or ""),
                                    "run": d.name, "date": date})
        except OSError:
            continue
    return summarize(records), {"runs_scanned": runs, "rows_scanned": rows}


def render_md(hosts: list[dict], meta: dict, generated_at: str) -> str:
    lines = [
        "# 死图床监测（只统计，不参与生产）",
        "",
        f"> 生成：{generated_at} · 扫描 {meta['runs_scanned']} 个 run / "
        f"{meta['rows_scanned']} 行 fetch_log · 失败 {sum(h['total_failures'] for h in hosts)} 行",
        "",
        "用途：长期积累 403/DNS 的分布，供以后决定是否做持久化黑名单或换源。",
        "生产侧仍只在单轮 run 内临时拉黑（`imagesearch.DomainHealth`），**不读本表**。",
        "",
        "| # | host | 失败次数 | 分类 | 涉及 run | 首次 | 最近 |",
        "|---|---|---:|---|---:|---|---|",
    ]
    for i, h in enumerate(hosts[:30], 1):
        by = " / ".join(f"{k} {v}" for k, v in h["by_class"].items())
        lines.append(f"| {i} | `{h['host']}` | {h['total_failures']} | {by} | "
                     f"{h['runs']} | {h['first_seen']} | {h['last_seen']} |")
    lines += ["", "## 说明", "",
              "- `blocked` = 单轮内已被拉黑后跳过的行（不是新失败）；",
              "- `dns` 多为已死域名；`http_403` 多为防盗链/反爬；",
              "- 同一 host 跨 run 反复出现，才值得考虑持久化或换源。", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(ROOT / "data-test" / "runs"))
    ap.add_argument("--out", default=str(ROOT / "data-test" / "evals" / "bad-domains-monitor"))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    hosts, meta = scan(Path(args.runs))
    import time
    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": now, **meta, "hosts": hosts}
    out.with_suffix(".json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    out.with_suffix(".md").write_text(render_md(hosts, meta, now), encoding="utf-8")
    summary = {"runs": meta["runs_scanned"], "hosts": len(hosts),
               "failures": sum(h["total_failures"] for h in hosts),
               "top": [(h["host"], h["total_failures"]) for h in hosts[:5]]}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
