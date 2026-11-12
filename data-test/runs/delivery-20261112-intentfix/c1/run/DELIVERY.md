# 交付清单：run

> 任务单：`auto-20261112-185607` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 6 · citation_only 1 · 备选 3 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | HOWO 6×6 油田专用全驱牵引车（TAZ4922，泰安五岳） | — | — | 5 | degraded/citation_only |
| 2 | 东风 6×6 沙漠卡车（400 马力 25 吨级） | — | — | 10 | degraded |
| 3 | H6066 6×6 特种运输车 | — | — | 10 | — |
| 4 | Titan 重型沙漠越野卡车（油田用重型越野车） | — | — | 30 | degraded |
| 5 | TGS 6×6 油田用车 | — | — | 30 | degraded |
| 6 | EQ2220 6×6 越野卡车底盘 | — | — | 15 | — |
| 7 | ZZ2257W4357C5 6×6 沙漠越野货车 | — | — | 5 | degraded |
| 8 | Zetros 4051 AS 6×6 多用途牵引车 | — | — | 30 | degraded |
| 9 | DFV5253TSMGP6D 沙漠车（东风六驱沙漠卡车/六驱越野载货车） | — | — | 30 | — |
| 10 | ND5250TSMZ04 沙漠车 | — | — | 25 | — |

**备选（随包）**：

- 1. HF 8066 6×6（role=—，rank=—，30 图）
- 2. K-65959（6×6 牵引/专用底盘）（role=—，rank=—，20 图）
- 3. X3000 6×6沙漠越野车（role=—，rank=—，30 图）

## 二、内部监控（不对用户）

- 下载：hits 355 / downloaded 285 / failed 38 / blocked 25 / gate_pass 280
- 缺图归因：all_download_failed 1 / no_hits 4 / not_delivered 3
- 总耗时：526422 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 9205 |
| FETCH | 181685 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 36519 |
| FETCH | 232481 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1666 |
| FETCH | 37929 |
| VERIFY | 8 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1075 |
| FETCH | 25835 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 14 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2392 | ¥0.22 | **¥0.4592** |
| 全空闲 | ¥0.1196 | ¥0.22 | **¥0.3396** |

用量：输入 39359 tokens（按未命中计，偏保守）/ 输出 20060 / Search 8 次 / Fetch 36 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q12\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-intentfix\c1\plan.json`
- 审核页：`data-test\runs\delivery-20261112-intentfix\c1\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-intentfix\c1\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
