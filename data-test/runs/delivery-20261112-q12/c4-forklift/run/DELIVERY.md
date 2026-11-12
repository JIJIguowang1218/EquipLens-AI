# 交付清单：run

> 任务单：`auto-20261112-192102` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CPD18FVD | primary | 3 | 10 | degraded/citation_only |
| 2 | J1.6-2.0XN | primary | 4 | 25 | degraded/citation_only |
| 3 | CPD-25 | backup | 7 | 25 | — |
| 4 | ERP15-35UX | backup | 9 | 10 | degraded/citation_only |
| 5 | EL25 | primary | 6 | 5 | — |
| 6 | 7系列 四轮电动叉车 | pool | 11 | 5 | degraded |

**备选（随包）**：

- 1. FE4P25N（role=backup，rank=10，30 图）
- 2. MXS series（role=pool，rank=12，5 图）
- 3. 7系列 1.5-1.8吨四轮电动叉车（role=pool，rank=16，10 图）
- 4. FB16CN2-FB20N2（role=pool，rank=14，30 图）

## 二、内部监控（不对用户）

- 下载：hits 355 / downloaded 295 / failed 60 / blocked 0 / gate_pass 165
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 4 / no_hits 1 / not_delivered 4
- 总耗时：226862 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1790 |
| FETCH | 67710 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2986 |
| FETCH | 65576 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1412 |
| FETCH | 13263 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1158 |
| FETCH | 17357 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2065 |
| FETCH | 53526 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 18 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2038 | ¥0.18 | **¥0.3838** |
| 全空闲 | ¥0.1019 | ¥0.18 | **¥0.2819** |

用量：输入 30361 tokens（按未命中计，偏保守）/ 输出 17889 / Search 6 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q12\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q12\c4-forklift\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q12\c4-forklift\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q12\c4-forklift\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
