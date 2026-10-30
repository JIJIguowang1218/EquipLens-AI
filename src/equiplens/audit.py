"""误杀抽样检测：用分层抽样 + 模型重判估计"被规则误杀的可用文本"。

背景：T18-roster 中 C 档占 74.8%，产品负责人无法全量审核。本模块把"全量审核"
替换为：
1) 强语汇护栏（确定性、零成本）：C 档里含设计语汇/型号锚点的段落进"复核队列"，
   不直接丢弃；
2) 分层抽样（域×长度）：每层抽 n 条，交模型重判；
3) 加权估计：按层规模外推漏杀率（estimated_miss_rate），并输出置信区间；
4) 审核包：抽样条目 + 护栏队列，人工只抽看这两类。

用法（CLI）：
  python -m equiplens audit-batch data-test/corpus/batch-* --out data-test/evals/audit
  python -m equiplens audit-apply data-test/evals/audit/audit-sheet.json <verdicts.json>
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from urllib.parse import urlparse

from . import passage

# 强语汇护栏：命中即进复核队列（宁可多审，不可错杀）
GUARD_RE = re.compile(
    r"家族化|家族式|设计语言|造型设计|外观设计|设计风格|涂装|特征线|型面|脸谱"
    r"|前脸|格栅|大灯|腰线|比例|姿态|CMF|体量")
MODEL_CODE_RE = re.compile(r"XGC\d{4,5}|SAC\d{4,5}|ZTC\d{3,4}|QAY\d{2,3}"
                           r"|QY\d{2,3}K\w*|XCT\d{1,3}L?\d?|STC\d{3,4}C?\d?"
                           r"|FTC\d{2,3}X\d|JH6|J6G|J6L|ZZ425|K3000|X5000E|FMX"
                           r"|BJ5311JSQ|X3000|F3000")

STRONG_WORDS = ["造型", "设计", "前脸", "格栅", "大灯", "保险杠", "线条", "曲面",
                "轮廓", "比例", "姿态", "体量", "家族化", "设计语言", "涂装",
                "色彩", "材质", "工艺", "后视镜", "导流罩", "遮阳板", "轮眉"]


def _saved_docs(batch_dir: Path) -> list[dict]:
    idx = json.loads((batch_dir / "index.json").read_text(encoding="utf-8"))
    out, seen = [], set()
    for r in idx["index"]:
        if r["status"] != "saved" or r["url"] in seen:
            continue
        seen.add(r["url"])
        out.append(r)
    return out


def collect_c_passages(batch_dir: str | Path, registry: dict,
                       max_chars: int = 300) -> list[dict]:
    """批内所有被判 C 的段落（用于抽样与护栏）。"""
    batch_dir = Path(batch_dir)
    rows: list[dict] = []
    for doc in _saved_docs(batch_dir):
        trust = passage.trust_for_url(doc["url"], registry)
        if passage.LOW_TITLE_RE.search(doc.get("title", "")):
            trust = "low"
        body = passage._split_doc(batch_dir / doc["file"])
        g = passage.grade_text(body, trust)
        host = (urlparse(doc["url"]).hostname or "").lower()
        for p in g["passages"]:
            if p["label"] != "C":
                continue
            rows.append({
                "id": f"{batch_dir.name[:14]}-{len(rows):04d}",
                "batch": batch_dir.name,
                "title": doc.get("title", "")[:60],
                "url": doc["url"], "domain": host,
                "chars": p["chars"], "text": p["text"][:max_chars],
                "strong": sum(1 for w in STRONG_WORDS if w in p["text"]),
            })
    return rows


def _domain_class(domain: str) -> str:
    if "autohome" in domain:
        return "autohome"
    if "volvocars" in domain:
        return "volvo"
    if any(d in domain for d in ("163.com", "sina", "qq.com")):
        return "portal"
    return "other"


def _size_bucket(chars: int) -> str:
    if chars < 60:
        return "short"
    if chars < 200:
        return "mid"
    return "long"


def guard_hits(row: dict) -> bool:
    """强语汇/型号护栏：命中即进复核队列。"""
    if MODEL_CODE_RE.search(row["text"]):
        return True
    if GUARD_RE.search(row["text"]) and row["strong"] >= 1:
        return True
    return row["strong"] >= 2


def build_sheet(rows: list[dict], sample_per_stratum: int = 2,
                seed: int = 20261030) -> dict:
    """分层（域×长度）抽样，返回判定表 + 护栏队列。"""
    strata: dict[str, list[dict]] = {}
    for r in rows:
        key = f"{_domain_class(r['domain'])}/{_size_bucket(r['chars'])}"
        strata.setdefault(key, []).append(r)
    rng = random.Random(seed)
    sheet = {"population": len(rows), "strata": [], "guard_queue": []}
    for key, items in sorted(strata.items()):
        n = min(sample_per_stratum, len(items))
        sheet["strata"].append({
            "stratum": key, "size": len(items),
            "samples": rng.sample(items, n)})
    for r in rows:
        if guard_hits(r):
            sheet["guard_queue"].append(r)
    sheet["guard_count"] = len(sheet["guard_queue"])
    return sheet


def _wilson_upper(k: int, n: int, z: float = 1.96) -> float | None:
    """Wilson 95% 上界（0 命中时给出"rule of three"式的风险上界）。"""
    if n <= 0:
        return None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return round(min(1.0, centre + half), 4)


def apply_verdicts(sheet: dict, verdicts: dict) -> dict:
    """按层规模加权估计漏杀率；verdicts: {id: "V|P|G|C"}。"""
    total = sum(s["size"] for s in sheet["strata"])
    est, judged, hits, detail = 0.0, 0, 0, []
    for s in sheet["strata"]:
        got = [verdicts.get(x["id"], "C") for x in s["samples"]]
        misses = sum(1 for t in got if t != "C")
        rate = misses / len(got) if got else 0.0
        est += s["size"] * rate
        judged += len(got)
        hits += misses
        detail.append({"stratum": s["stratum"], "size": s["size"],
                       "samples": len(got), "misses": misses,
                       "miss_rate": round(rate, 4)})
    miss_rate = est / total if total else 0.0
    # 护栏队列的"可疑率"（抽查部分）
    g_total = sheet.get("guard_count", 0)
    g_judged = [verdicts.get(g["id"], "C") for g in sheet.get("guard_queue", [])
                if g["id"] in verdicts]
    g_hits = sum(1 for t in g_judged if t != "C")
    return {
        "population": total, "judged": judged,
        "estimated_miss_rate": round(miss_rate, 4),
        "estimated_miss_count": round(est, 1),
        "ci95_upper": _wilson_upper(hits, judged),
        "strata": detail,
        "guard_count": g_total, "guard_judged": len(g_judged),
        "guard_miss_rate": round(g_hits / len(g_judged), 4) if g_judged else None,
        "note": "漏杀率=被规则判 C、模型重判为 V/P/G 的比例（按层加权）；"
                "ci95_upper 为抽样命中的 95% 上界",
    }


def render_report(result: dict) -> str:
    guard = ("无" if result["guard_miss_rate"] is None
             else f"{result['guard_miss_rate']*100:.1f}%")
    ci = ("—" if result.get("ci95_upper") is None
          else f"{result['ci95_upper']*100:.1f}%")
    lines = ["# 误杀抽样检测报告", "",
             f"- 总体（C 档段落）：{result['population']} 段，抽样判定 "
             f"{result['judged']} 段",
             f"- **估计漏杀率：{result['estimated_miss_rate']*100:.1f}%**"
             f"（约 {result['estimated_miss_count']:.0f} 段；95% 上界 {ci}）",
             f"- 强语汇护栏队列：{result['guard_count']} 段；抽查可疑率：{guard}",
             "", "## 分层明细", "",
             "| 层（域/长度） | 规模 | 抽样 | 漏杀 | 漏杀率 |",
             "|---|---:|---:|---:|---:|"]
    for d in result["strata"]:
        lines.append(f"| {d['stratum']} | {d['size']} | {d['samples']} | "
                     f"{d['misses']} | {d['miss_rate']*100:.0f}% |")
    lines.append("")
    return "\n".join(lines)
