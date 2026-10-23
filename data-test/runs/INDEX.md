# 运行台账（data-test/runs）

| run_id | 类目 | 档案 | 文章 | A 字 | A 占比 | A/篇 | 失败总 | 硬失败 | 政策跳过 | SERP被拦 | 轮次 | 决策 | 时长s | token in/out |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---|
| run-suicheche-blind | 随车吊 | - | 4 | 327 | 1.0% | 81.8 | 40 | n/a* | n/a* | 0 | 2 | stop | 45.0 | 66/9 |
| run-suicheche-blind-v2 | 随车吊 | - | 3 | 198 | 1.8% | 66.0 | 35 | n/a* | n/a* | 0 | 2 | stop | 36.2 | 66/9 |
| run-suicheche-blind-v3 | 随车吊 | 随车吊 | 10 | 323 | 0.5% | 32.3 | 43 | n/a* | n/a* | 0 | 2 | stop | 65.2 | 66/11 |
| run-suicheche-profile | 随车吊 | 随车吊 | 10 | 562 | 0.7% | 56.2 | 41 | n/a* | n/a* | 0 | 2 | stop | 64.7 | 66/11 |
| run-gaokong-blind | 高空作业车 | - | 10 | 1894 | 2.9% | 189.4 | 54 | n/a* | n/a* | 0 | 2 | stop | 66.6 | 68/9 |
| run-gaokong-blind-v2 | 高空作业车 | - | 8 | 2438 | 4.5% | 304.8 | 41 | n/a* | n/a* | 0 | 2 | stop | 60.8 | 68/9 |
| run-gaokong-blind-v3 | 高空作业车 | - | 9 | 2670 | 4.5% | 296.7 | 38 | 9 | 29 | 0 | 2 | ok | 62.4 | 68/9 |
| run-gaokong-budget20 | 高空作业车 | - | 3 | 2178 | 19.0% | 726.0 | 34 | 4 | 30 | 0 | 1 | ok | 31.5 | 68/9 |
| run-gaokong-budget20-v2 | 高空作业车 | - | 0 | 0 | 0.0% | 0.0 | 0 | 0 | 0 | 0 | 2 | stop | 4.1 | 68/9 |
| run-budget-q1 | 高空作业车 | - | 0 | 0 | 0.0% | 0.0 | 0 | 0 | 0 | 6 | 1 | stop | 2.2 | 73/9 |
| run-budget-q3 | 高空作业车 | - | 0 | 0 | 0.0% | 0.0 | 0 | 0 | 0 | 6 | 1 | stop | 2.1 | 73/9 |
| run-budget-q6 | 高空作业车 | - | 0 | 0 | 0.0% | 0.0 | 0 | 0 | 0 | 6 | 1 | stop | 2.3 | 73/9 |
| run-budget-q10 | 高空作业车 | - | 0 | 0 | 0.0% | 0.0 | 0 | 0 | 0 | 6 | 1 | stop | 2.0 | 73/9 |
| run-budget-q1-bing | 高空作业车 | - | 0 | 0 | 0.0% | 0.0 | 0 | 0 | 0 | 0 | 1 | stop | 5.4 | 79/9 |

说明：
- 硬失败 = fetch_error/fetch_failed/robots_denied/too_short；政策跳过 = blocked_url/source_skipped；
- `n/a*` = 旧运行未拆分失败口径，只保留失败总数；
- token 为启发式估算（est=true），未接 LLM API；
- 每行对应 `runs/<run_id>/summary.json`、`events.jsonl`、`report.md`。