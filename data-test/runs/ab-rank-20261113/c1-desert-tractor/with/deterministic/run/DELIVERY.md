# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 9 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | Zetros 6×6 牵引车头（tractor-head） | primary | 4 | 30 | degraded |
| 2 | HOWO 6×6 全驱牵引车（全驱系列） | primary | 5 | 30 | degraded/citation_only |
| 3 | OTTC 460马力 6×6 越野牵引头 | primary | 6 | 5 | degraded |
| 4 | K-65959 6×6 | primary | 7 | 5 | degraded/citation_only |
| 5 | TX 6×6 牵引车（ZZ4257V455GF1） | backup | 11 | 30 | degraded |
| 6 | OTTC 越野 6×6 牵引头（460 马力） | backup | 12 | 5 | degraded |
| 7 | 中东版 6×6 柴油重卡（Deutz D13 565 马力） | backup | 13 | 15 | degraded/citation_only |
| 8 | 东风 6×6 沙漠卡车（400马力 25 吨级高牵引力越野货车） | primary | 8 | 5 | degraded |
| 9 | H6066 6×6 特种运输车 | primary | 9 | 10 | — |
| 10 | HF 8066 6×6 重型越野底盘 | primary | 10 | 30 | degraded |

**备选（随包）**：

- 1. Zetros 4051 AS 6×6 重型牵引车（role=pool，rank=16，15 图）
- 2. 沙漠车（ND5180TSMZ01、ND5140TSMZ02、ND5250TSM 等）（role=pool，rank=21，25 图）
- 3. EQ2102G 六驱沙漠越野卡车（一排半平头）（role=pool，rank=25，25 图）
- 4. ND5250TSMZ04 沙漠车（role=pool，rank=26，20 图）

## 二、内部监控（不对用户）

- 下载：hits 445 / downloaded 415 / failed 30 / blocked 0 / gate_pass 385
- 缺图归因：no_hits 9 / not_delivered 6
- 总耗时：241262 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 3810 |
| FETCH | 74447 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4731 |
| FETCH | 53487 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1542 |
| FETCH | 17751 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2229 |
| FETCH | 61408 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1106 |
| FETCH | 20735 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 13 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.0 | ¥0.21 | **¥0.21** |
| 全空闲 | ¥0.0 | ¥0.21 | **¥0.21** |

用量：输入 0 tokens（按未命中计，偏保守）/ 输出 0 / Search 0 次 / Fetch 42 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\ab-rank-20261113\c1-desert-tractor\with\deterministic\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-rank-20261113\c1-desert-tractor\with\deterministic\plan-ranked.json`
- 审核页：`data-test\runs\ab-rank-20261113\c1-desert-tractor\with\deterministic\run\audit.html`
- 证据库：`data-test\runs\ab-rank-20261113\c1-desert-tractor\with\deterministic\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
