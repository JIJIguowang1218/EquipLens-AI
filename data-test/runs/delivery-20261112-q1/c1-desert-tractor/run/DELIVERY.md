# 交付清单：run

> 任务单：`auto-20261112-181236` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 7/10 · degraded 6 · citation_only 0 · 备选 1 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 泰安五岳 6×6油田专用全驱牵引车（6X6油田沙漠重型牵引车） | primary | 1 | 30 | degraded |
| 2 | HOWO 6×6 全驱牵引车 | primary | 5 | 25 | degraded |
| 3 | ZETROS 3643 6X6 | primary | 7 | 25 | degraded |
| 4 | 豪沃T7H 6×6牵引车系列 | backup | 11 | 25 | degraded |
| 5 | 沙豹 DFV5253GP6DJ | backup | 13 | 20 | degraded |
| 6 | HF8066 6×6 重型沙漠运输车 | primary | 9 | 10 | — |
| 7 | 豪沃TH7 6×6牵引车系列 | primary | 10 | 25 | degraded |

**备选（随包）**：

- 1. 豪沃TX 6×6牵引车（ZZ4257V455GF1）（role=primary，rank=4，25 图）

## 二、内部监控（不对用户）

- 下载：hits 225 / downloaded 195 / failed 23 / blocked 0 / gate_pass 190
- 缺图归因：all_download_failed 1 / no_hits 4 / not_delivered 1
- 总耗时：164629 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5912 |
| FETCH | 86351 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 9606 |
| FETCH | 28252 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 914 |
| FETCH | 33582 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 10 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2656 | ¥0.12 | **¥0.3856** |
| 全空闲 | ¥0.1328 | ¥0.12 | **¥0.2528** |

用量：输入 30317 tokens（按未命中计，偏保守）/ 输出 25623 / Search 6 次 / Fetch 18 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q1\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q1\c1-desert-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q1\c1-desert-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q1\c1-desert-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
