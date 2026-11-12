# 交付清单：run

> 任务单：`auto-20261112-185607` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 8/10 · degraded 5 · citation_only 1 · 备选 0 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 豪沃 6×6 油田专用牵引车（TAZ4922） | — | — | 15 | degraded |
| 2 | 6×6 沙漠卡车（400 马力，25 吨级） | — | — | 20 | degraded |
| 3 | H6066 6×6 特种运输车 | — | — | 10 | — |
| 4 | Zetros 4051 AS 6×6 | — | — | 30 | degraded |
| 5 | X3000 6×6沙漠越野车 | — | — | 30 | — |
| 6 | 6×6沙漠卡车（DFV5253TSMGP6D 沙漠车） | — | — | 5 | degraded |
| 7 | ND5250TSMZ04 沙漠车 | — | — | 30 | — |
| 8 | HF8066 6×6刚性油田卡车 | — | — | 5 | degraded/citation_only |

## 二、内部监控（不对用户）

- 下载：hits 190 / downloaded 170 / failed 13 / blocked 0 / gate_pass 150
- 缺图归因：all_download_failed 1 / no_hits 2
- 总耗时：100997 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2837 |
| FETCH | 68749 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1224 |
| FETCH | 6178 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 2006 |
| FETCH | 19990 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 12 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2636 | ¥0.16 | **¥0.4236** |
| 全空闲 | ¥0.1318 | ¥0.16 | **¥0.2918** |

用量：输入 40548 tokens（按未命中计，偏保守）/ 输出 22812 / Search 8 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q12\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-mergefix\c1\plan.json`
- 审核页：`data-test\runs\delivery-20261112-mergefix\c1\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-mergefix\c1\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
