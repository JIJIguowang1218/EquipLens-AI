# 交付清单：run

> 任务单：`auto-20261112-185607` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 8/10 · degraded 4 · citation_only 0 · 备选 1 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | TAZ4922 6×6 油田专用牵引车 | primary | 1 | 30 | degraded |
| 2 | Zetros 4051 AS 6×6 | primary | 2 | 30 | degraded |
| 3 | HF 8066（H6066）6×6 重型沙漠运输车/越野底盘 | primary | 4 | 5 | — |
| 4 | H6066 6×6 特种运输车 | primary | 5 | 10 | — |
| 5 | X3000 6×6沙漠越野车 | primary | 7 | 30 | — |
| 6 | 6×6 沙漠卡车（400 马力，25 吨级） | backup | 12 | 20 | degraded |
| 7 | 东风 6×6 沙漠卡车（400 马力 25 吨级） | backup | 13 | 10 | degraded |
| 8 | ND5250TSMZ04 沙漠车 | primary | 9 | 30 | — |

**备选（随包）**：

- 1. 6×6沙漠卡车（role=backup，rank=14，5 图）

## 二、内部监控（不对用户）

- 下载：hits 235 / downloaded 180 / failed 41 / blocked 0 / gate_pass 175
- 缺图归因：all_download_failed 2 / no_hits 3 / not_delivered 1
- 总耗时：236609 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 87315 |
| FETCH | 85661 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 977 |
| FETCH | 30209 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 862 |
| FETCH | 31571 |
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
| 全高峰 | ¥0.2872 | ¥0.18 | **¥0.4672** |
| 全空闲 | ¥0.1436 | ¥0.18 | **¥0.3236** |

用量：输入 40555 tokens（按未命中计，偏保守）/ 输出 25755 / Search 8 次 / Fetch 28 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q12\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q12\c1-desert-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q12\c1-desert-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q12\c1-desert-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
