# -*- coding: utf-8 -*-
"""离线重评冒烟批次：对已落盘的图跑新分层判定，产出新旧口径对照。

不联网；输入是 data-test/runs/<batch>/all-downloads.json + all-downloads/*.jpg。
用途：验证门卫标签集 v3 + assess_image 对同一批图的影响（不需要重跑 360）。

用法:
  PYTHONPATH=src python scripts/reassess_smoke.py \\
      --out data-test/runs/web-reassess-20261109
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from equiplens import gate  # noqa: E402

BATCHES = ["data-test/runs/web-smoke-20261109",
           "data-test/runs/web-smoke-hd-20261109"]
EXTERIOR = set(gate.EXTERIOR_VIEWS)


def old_usable(row: dict) -> bool:
    """旧口径：门卫通过 + ≥1200 + 视角属外观（视角当硬门槛）。"""
    return (bool(row.get("gate_pass")) and int(row.get("width") or 0) >= 1200
            and row.get("view") in EXTERIOR)


def collect(batches: list[str]) -> list[dict]:
    out, seen = [], set()
    for batch in batches:
        p = ROOT / batch / "all-downloads.json"
        if not p.exists():
            print(f"skip missing batch: {batch}")
            continue
        for row in json.loads(p.read_text(encoding="utf-8"))["rows"]:
            if row.get("status") != "saved":
                continue
            key = row.get("url") or (row.get("title"), row.get("width"))
            if key in seen:
                continue
            seen.add(key)
            img = ROOT / batch / row["image"]
            if not img.exists():
                continue
            out.append({"batch": Path(batch).name, "image": img,
                        "rel": row["image"], "row": row})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="离线重评冒烟图")
    ap.add_argument("--batches", nargs="*", default=BATCHES)
    ap.add_argument("--out", default="data-test/runs/web-reassess-20261109")
    args = ap.parse_args(argv)

    t0 = time.time()
    items = collect(args.batches)
    # 旧口径重算用 v2 标签集（keep + BASE_DROP），与 v3 在同一批字节上对照
    base_labels = {f"k{i}": t for i, t in enumerate(gate.KEEP_LABELS)}
    base_labels.update({f"d{i}": t for i, t in enumerate(gate.BASE_DROP_LABELS)})
    keep_keys = [f"k{i}" for i in range(len(gate.KEEP_LABELS))]
    base_drop_keys = [f"d{i}" for i in range(len(gate.BASE_DROP_LABELS))]
    rows = []
    for it in items:
        data = it["image"].read_bytes()
        a = gate.assess_image(data)
        sc = gate.classify_labels(data, base_labels)
        old_margin = round(max(sc[k] for k in keep_keys)
                           - max(sc[k] for k in base_drop_keys), 4)
        old = it["row"]
        rows.append({
            "image": f"{it['batch']}/{it['rel']}",
            "title": old.get("title", "")[:80],
            "url": old.get("url", ""),
            "batch_old_pass": bool(old.get("gate_pass")),
            "old_pass_recalc": old_margin >= 0,
            "old_margin_recalc": old_margin,
            "old_view": old.get("view", ""),
            "old_usable": old_usable(old),
            "old_margin": old.get("margin"),
            "new_pass": a["pass"],
            "new_margin": a["margin"],
            "new_scene": a["scene"],
            "new_view": a["view"],
            "new_gap": a["view_gap"],
            "drop_label": a["drop_label"],
            "overview_ok": a["overview_candidate"],
            "part_ok": a["part_candidate"],
            "exterior_hint": a["exterior_hint"],
            "reasons": a["reasons"],
            "hints": a["hints"],
            "width": a["width"], "height": a["height"],
        })
        print(".", end="", flush=True)
    print()

    newly_rejected = [r for r in rows
                      if r["old_pass_recalc"] and not r["new_pass"]]
    borderline = [r for r in newly_rejected if abs(r["new_margin"] or 0) < 0.01]
    summary = {
        "batches": [b for b in args.batches],
        "images": len(rows),
        # 同一批字节上重算：v2 标签集 vs v3 标签集（严格 A/B）
        "old_pass_recalc": sum(1 for r in rows if r["old_pass_recalc"]),
        "new_pass": sum(1 for r in rows if r["new_pass"]),
        # 批次记录里的 PASS（当次跑批、原始字节，仅作参照）
        "batch_old_pass": sum(1 for r in rows if r["batch_old_pass"]),
        "old_usable": sum(1 for r in rows if r["old_usable"]),
        "overview_ok": sum(1 for r in rows if r["overview_ok"]),
        "part_ok": sum(1 for r in rows if r["part_ok"]),
        "part_with_exterior_hint": sum(1 for r in rows
                                       if r["part_ok"] and r["exterior_hint"]),
        "newly_rejected": len(newly_rejected),
        "borderline_rejections": len(borderline),
        "seconds": round(time.time() - t0, 1),
    }

    out_dir = ROOT / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.json").write_text(json.dumps(
        {"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    (out_dir / "report.md").write_text(
        render_md(summary, rows, newly_rejected), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    print(f"out: {out_dir}")
    return 0


def render_md(summary: dict, rows: list[dict], rejected: list[dict]) -> str:
    s = summary
    lines = [
        "# 冒烟图离线重评（门卫 v3 + 分层口径）", "",
        f"- 批次：{', '.join(Path(b).name for b in s['batches'])}",
        f"- 去重后图片：{s['images']}；耗时：{s['seconds']}s",
        "- 口径变化：旧 = 门卫 v2 + ≥1200 + 视角属外观（视角硬门槛）；"
        "新 = 门卫 v3 + 分层（视角只作提示）", "",
        "| 指标 | 数量 |", "|---|---:|",
        f"| 旧门卫通过（v2 标签集，同字节重算） | {s['old_pass_recalc']} |",
        f"| 新门卫通过（v3 标签集，同字节重算） | {s['new_pass']} |",
        f"| 批次记录里的旧 PASS（当次原始字节，仅参照） | {s['batch_old_pass']} |",
        f"| 旧口径可用（≥1200+外观） | {s['old_usable']} |",
        f"| **概览可用**（≥800，非拼图） | {s['overview_ok']} |",
        f"| **部件可用**（≥1200，非拼图） | {s['part_ok']} |",
        f"| 部件可用且外观提示 | {s['part_with_exterior_hint']} |",
        f"| 新旧门卫由通过变拒绝 | {s['newly_rejected']} |",
        f"| 其中边界拒绝（|新 margin| < 0.01） | {s['borderline_rejections']} |", "",
        "## 由通过变拒绝的图（v2→v3，同字节）", "",
        "| 图 | 尺寸 | 旧视角 | 旧 margin | 新 margin | 新 drop 标签 | 标题 |",
        "|---|---:|---|---:|---:|---|---|",
    ]
    for r in rejected:
        mark = " ⚠️边界" if abs(r["new_margin"] or 0) < 0.01 else ""
        lines.append(f"| {r['image'].split('/', 1)[-1]} | {r['width']}×{r['height']} "
                     f"| {r['old_view']} | {r['old_margin_recalc']} "
                     f"| {r['new_margin']}{mark} | "
                     f"{r['drop_label'][:40]} | {r['title']} |")

    lines += ["", "## 部件可用（≥1200）明细", "",
              "| 图 | 尺寸 | 新视角(gap) | 外观提示 | 否决理由 | 标题 |",
              "|---|---:|---|---|---|---|"]
    for r in rows:
        if not r["part_ok"]:
            continue
        lines.append(
            f"| {r['image'].split('/', 1)[-1]} | {r['width']}×{r['height']} | "
            f"{r['new_view']}({r['new_gap']}) | "
            f"{'是' if r['exterior_hint'] else '否'} | "
            f"{','.join(r['reasons']) or '-'} | {r['title'][:50]} |")

    lines += ["", "## 说明", "",
              "- 输入是 export 重存的 JPEG（质量 88），与原图字节不完全一致；"
              "分数会有 ±0.001 级差异。",
              "- **边界拒绝**说明单标签 verdict 不稳定：同一图重编码就可能翻转；"
              "门卫阈值应做扫掠（像 T18 那样给放行率×精确率曲线），不要靠加标签硬调。",
              "- 视角 top1−top2 中位数 ~0.003，因此 `外观提示` 只当提示，"
              "不再作为可用门槛。",
              "- 本表只说明“同一批图的筛选口径变化”，不代表源已扩、分辨率已够。"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
