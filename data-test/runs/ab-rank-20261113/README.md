# rank 小 A/B（2026-11-13）

同一份 plan，只改排序方式：LLM rank vs `rank_plan.py --deterministic`。

- `SUMMARY.md/json`：交付/备选/degraded/成本/耗时/排序重合；
- `<case>/<arm>/`：`plan-ranked.json`、`run/`；
- 结论：2 case 交付完全一致；确定性 rank 省 20–40 s，且无未记账 LLM 成本；
  样本小，生产默认仍 LLM。
