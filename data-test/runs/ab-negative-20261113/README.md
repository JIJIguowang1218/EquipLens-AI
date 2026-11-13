# ab-negative-20261113 目录说明

negative A/B + 交付/耗时审计的实验目录（2026-11-13）。

## 结构

```
AB.json / AB-SUMMARY.md      # 5 brief × with/without 的汇总
SEARCH-LEVEL.json            # 30 条查询“加/不加负词”的搜索层回放
DELIVERY-AUDIT.json          # 每次 run 的 规划/有图/交付/缺口 统计
AUDIT-DELIVERY-TIMING.md     # 交付缺口根因 + 各阶段耗时分析
c1..c5/
  QUERY-DIFF.json            # 两臂查询“仅后缀不同”的校验
  with/  without/
    brief.json               # 冻结的任务单（复用 clean baseline）
    plan.json / plan-ranked.json
    api_log.jsonl            # plan 阶段的 search/chat 用量
    run/                     # loop 产物：state/summary/DELIVERY/audit/fetch_log
```

## 约定

- `images/` 不入库（`data-test/runs/**/images/` 已在 .gitignore）；
- 结论以 `AB-SUMMARY.md` 和 `AUDIT-DELIVERY-TIMING.md` 为准；
- 该目录是实验集，不是单次 run，`run_ledger.py` 不会把它当 run 索引；
  实验索引见 `docs/EXPERIMENTS-INDEX.md`（E38/E39）。
