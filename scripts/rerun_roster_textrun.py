# -*- coding: utf-8 -*-
"""全名录复测（验证 1+2：查询分层 + 信源定向 + 配置行过滤）。

每类目取锁定名录前 6 个车型，用 textrun 新计划跑一轮（max_queries 16 以容纳
site: 定向查询，max_fetch 6），与 T18-roster 首测对比 A 产出。

用法: PYTHONPATH=src python tmp/rerun_roster_textrun.py
输出: data-test/runs/run-roster2-<cat>/（summary/audit/report）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equiplens import textrun  # noqa: E402

CATEGORIES = {
    "沙漠牵引车": ["陕汽重卡德龙6X6", "陕汽重卡德龙", "陕汽重卡德龙F3000",
                   "东风天锦", "陕汽重卡德龙X3000", "一汽解放JH6"],
    "重型吊车": ["徐工XGC88000", "三一SAC16000S", "中联重科ZTC250", "徐工QY35K5",
                 "徐工QY25K5C", "徐工XCT25"],
    "轻型吊车": ["徐工QY25K5C", "徐工XCT8L4", "雷萨FTC25X5", "三一STC800C6",
                 "雷萨FTC55X5", "徐工QY16KC"],
    "翻斗铲车": ["福田金刚", "福田金刚3", "福田金刚C", "沃尔沃FMX",
                 "一汽解放J6L", "陕汽重卡德龙K3000"],
}


def main() -> int:
    tmp = ROOT / "tmp"
    out = []
    for cat, models in CATEGORIES.items():
        intent = {
            "task_type": "text_design_scan",
            "category": cat,
            "models": models,
            "target_content": "design_analysis",
            "budget": {"max_queries": 16, "max_fetch": 6, "max_rounds": 1},
            "serp_channel": "auto",
        }
        ip = tmp / f"intent-roster2-{cat}.json"
        ip.write_text(json.dumps(intent, ensure_ascii=False, indent=1),
                      encoding="utf-8")
        try:
            s = textrun.run(ip, ROOT / "data-test", run_root=ROOT / "data-test" / "runs",
                            run_id=f"run-roster2b-{cat}", do_replan=False)
            m = s["metrics"]
            out.append({"category": cat, "articles": m["articles"],
                        "a_chars": m["a_chars"], "a_share": m["a_share"],
                        "audit": s["summary"].get("audit")})
            print(f"[{cat}] 文章 {m['articles']} / A {m['a_chars']} "
                  f"({m['a_share']*100:.1f}%)", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"[{cat}] FAILED: {type(e).__name__}: {e}", flush=True)
            out.append({"category": cat, "error": str(e)[:200]})
    (ROOT / "data-test" / "runs" / "roster2-summary.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE", out, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
