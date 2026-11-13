# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 4 · citation_only 1 · 备选 0 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | RSH4528-VO2 | primary | 1 | 5 | — |
| 2 | DRU450-570（Essential系列正面吊） | primary | 3 | 15 | — |
| 3 | LG420FC4 | primary | 5 | 20 | degraded/citation_only |
| 4 | CRS450Z5 | primary | 6 | 20 | — |
| 5 | RSH4532-Vo | backup | 11 | 5 | — |
| 6 | RS45 | backup | 12 | 25 | — |
| 7 | G系列（Gloria）正面吊 | pool | 15 | 15 | degraded |
| 8 | HCS46 集装箱正面吊运起重机 | primary | 8 | 10 | degraded |
| 9 | 柳工正面吊 | primary | 10 | 20 | — |
| 10 | XCMG集装箱正面吊 | pool | 16 | 10 | degraded |

## 二、内部监控（不对用户）

- 下载：hits 345 / downloaded 250 / failed 73 / blocked 0 / gate_pass 145
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 3 / no_hits 2
- 总耗时：257109 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4753 |
| FETCH | 116834 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1591 |
| FETCH | 115088 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1276 |
| FETCH | 17554 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 12 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.0 | ¥0.12 | **¥0.12** |
| 全空闲 | ¥0.0 | ¥0.12 | **¥0.12** |

用量：输入 0 tokens（按未命中计，偏保守）/ 输出 0 / Search 0 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\ab-rank-20261113\c2-reach-stacker\with\llm\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-rank-20261113\c2-reach-stacker\with\llm\plan-ranked.json`
- 审核页：`data-test\runs\ab-rank-20261113\c2-reach-stacker\with\llm\run\audit.html`
- 证据库：`data-test\runs\ab-rank-20261113\c2-reach-stacker\with\llm\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
