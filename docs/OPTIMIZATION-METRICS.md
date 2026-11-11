# 持续优化指标：现在能统计什么、缺什么

## 结论

现有文件**足够做“逐实验对比”**，但**不足做一个跨时间的统一提升曲线**。原因是每次实验的样本、query、分母不同，不能直接把 12/12、accepted、precision 相加。

已补一个统一表：`data-test/evals/METRICS.csv`。

## 当前可支持的结论

| 优化 | 证据 | 结论 |
|---|---|---|
| task-brief v2 方法 | T46 v2 vs v1 | 自动断言 10/10 vs 3/10；人工 v2 10 PASS vs v1 6 PASS/3 FAIL/1 NA |
| 12+2 意向排序 | T47 | 12/12；HF8066 rank6 占槽；2 primary 无图 → backup |
| code prefilter | T59 | 12/12 构成不变；accepted 236→224；无误丢目标 |
| P0 交付不变量 | T61 | 12/12 baseline composition；part_only 软标记，未硬解决 |
| Platform union | T57/T58 | 负结果：丢 HF8066，unknown 暴增；不接入 |

## 不够的地方

1. **分母不统一**：T46 是 case，T57/T59 是 run，T56 是 target/image；
2. **没有重复运行/方差**：多数 n=1，不能算置信区间；
3. **人工 precision/recall 只在部分实验有**；
4. **成本/延迟没有统一记录**；
5. **部分 run 图片未同步**，但 state/log/结论在；
6. **没有固定的 baseline 版本**：每次实验 query/plan 可能不同。

## 建议的统一 KPI（下一轮起）

每次正式实验至少记录：

```text
experiment_id, date, code_commit, brief_id, plan_id,
query_mode, platform_mode, sample_size,
delivery, degraded, citation_only, bonus,
verified_accepted, unknown,
human_target_precision, human_target_recall,
cost_usd, latency_sec, notes
```

否则只能做“这次比上次好/坏”的定性判断，不能做持续优化曲线。

## 现有文件是否保留

- `RESULTS.md`、`results.json`、`REVIEW-SUMMARY.md`、`P0-REVIEW.md`、`PLATFORM-*.md`：保留；
- `state.json`/`summary.json`/`fetch_log.jsonl`：保留，供重算；
- 原图/DB：不同步，需要时重新抓。
