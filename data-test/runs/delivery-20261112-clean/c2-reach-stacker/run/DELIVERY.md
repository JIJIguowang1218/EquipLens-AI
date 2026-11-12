# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 6 · citation_only 0 · 备选 2 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | XCS4531K2 | primary | 2 | 30 | — |
| 2 | CRS450Z5 | primary | 3 | 20 | — |
| 3 | HCS46 | primary | 4 | 5 | — |
| 4 | LG420FC4 集装箱正面吊 | primary | 5 | 20 | degraded |
| 5 | RS45（B921）正面吊 | primary | 7 | 25 | degraded |
| 6 | DRU450-570 Essential系列正面吊 | backup | 11 | 10 | degraded |
| 7 | XCMG 集装箱正面吊（45吨级） | backup | 12 | 10 | degraded |
| 8 | SMV 4542 TB4 BH 正面吊 | primary | 8 | 25 | degraded |
| 9 | ZRS4531 集装箱正面吊运机 | primary | 9 | 10 | degraded |
| 10 | 集装箱正面吊 | primary | 10 | 10 | — |

**备选（随包）**：

- 1. RSH4532-Vo 正面吊运机（role=backup，rank=14，25 图）
- 2. RSH4531-VO5（role=pool，rank=16，15 图）

## 二、内部监控（不对用户）

- 下载：hits 380 / downloaded 300 / failed 58 / blocked 0 / gate_pass 235
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / no_hits 1 / not_delivered 2
- 总耗时：315151 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 36647 |
| FETCH | 137542 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 49916 |
| FETCH | 53204 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 13458 |
| FETCH | 24372 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 9 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2372 | ¥0.19 | **¥0.4272** |
| 全空闲 | ¥0.1186 | ¥0.19 | **¥0.3086** |

用量：输入 38902 tokens（按未命中计，偏保守）/ 输出 19927 / Search 8 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-clean\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-clean\c2-reach-stacker\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-clean\c2-reach-stacker\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-clean\c2-reach-stacker\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
