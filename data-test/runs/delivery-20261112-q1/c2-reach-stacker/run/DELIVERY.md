# 交付清单：run

> 任务单：`auto-20261112-181902` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 4 · citation_only 1 · 备选 1 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | RSH4532-Vo正面吊运机 | primary | 2 | 25 | — |
| 2 | XCMG集装箱正面吊（45吨级，燃油/纯电动产品线） | primary | 3 | 30 | degraded/citation_only |
| 3 | CRS450Z5 | primary | 4 | 20 | — |
| 4 | HCS46 | primary | 5 | 5 | — |
| 5 | 港口正面吊 | primary | 7 | 5 | — |
| 6 | RSH4528-VO2 | backup | 12 | 5 | — |
| 7 | 正面吊（徐工港机） | pool | 15 | 20 | degraded |
| 8 | 柳工正面吊（港口机械） | primary | 8 | 30 | degraded |
| 9 | 正面吊（沃尔华） | primary | 9 | 30 | degraded |
| 10 | 集装箱正面吊 | primary | 10 | 15 | — |

**备选（随包）**：

- 1. 正面吊（role=pool，rank=16，25 图）

## 二、内部监控（不对用户）

- 下载：hits 325 / downloaded 275 / failed 50 / blocked 0 / gate_pass 215
- 缺图归因：gate_or_verify_rejected 3 / no_hits 2 / not_delivered 1
- 总耗时：389509 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 52547 |
| FETCH | 130907 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 28164 |
| FETCH | 131917 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 18161 |
| FETCH | 27800 |
| VERIFY | 0 |
| FILL | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 11 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1841 | ¥0.17 | **¥0.3541** |
| 全空闲 | ¥0.092 | ¥0.17 | **¥0.262** |

用量：输入 28111 tokens（按未命中计，偏保守）/ 输出 15982 / Search 6 次 / Fetch 28 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q1\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q1\c2-reach-stacker\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q1\c2-reach-stacker\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q1\c2-reach-stacker\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
