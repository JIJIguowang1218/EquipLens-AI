# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 9 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | Zetros 4051 AS 6×6 重型牵引车 | primary | 4 | 30 | degraded |
| 2 | Zetros 6×6 牵引车头（tractor-head） | primary | 5 | 15 | degraded |
| 3 | TX 6×6 牵引车（ZZ4257V455GF1） | backup | 11 | 30 | degraded |
| 4 | HF 8066 6×6 重型越野底盘 | backup | 12 | 30 | degraded |
| 5 | H6066 6×6 特种运输车 | backup | 13 | 10 | — |
| 6 | TRM700-100（6×6）牵引车 | pool | 15 | 30 | degraded/citation_only |
| 7 | HOWO 6×6 全驱牵引车（全驱系列） | pool | 17 | 30 | degraded/citation_only |
| 8 | 中东版 6×6 柴油重卡（Deutz D13 565 马力） | primary | 8 | 15 | degraded/citation_only |
| 9 | OTTC 越野 6×6 牵引头（460 马力） | primary | 10 | 5 | degraded |
| 10 | 东风 6×6 沙漠卡车（400马力 25 吨级高牵引力越野货车） | pool | 18 | 5 | degraded |

**备选（随包）**：

- 1. EQ2102G 六驱沙漠越野卡车（一排半平头）（role=pool，rank=19，25 图）
- 2. ND5250TSMZ04 沙漠车（role=pool，rank=20，30 图）
- 3. 沙漠车（ND5180TSMZ01、ND5140TSMZ02、ND5250TSM 等）（role=pool，rank=21，15 图）
- 4. Titan 沙漠用重型越野卡车（role=pool，rank=23，30 图）

## 二、内部监控（不对用户）

- 下载：hits 385 / downloaded 355 / failed 30 / blocked 0 / gate_pass 335
- 缺图归因：no_hits 9 / not_delivered 6
- 总耗时：371187 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 64911 |
| FETCH | 84428 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22133 |
| FETCH | 67978 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 7793 |
| FETCH | 24809 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5822 |
| FETCH | 16398 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 34871 |
| FETCH | 42025 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 14 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.0 | ¥0.22 | **¥0.22** |
| 全空闲 | ¥0.0 | ¥0.22 | **¥0.22** |

用量：输入 0 tokens（按未命中计，偏保守）/ 输出 0 / Search 0 次 / Fetch 44 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\ab-rank-20261113\c1-desert-tractor\with\llm\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-rank-20261113\c1-desert-tractor\with\llm\plan-ranked.json`
- 审核页：`data-test\runs\ab-rank-20261113\c1-desert-tractor\with\llm\run\audit.html`
- 证据库：`data-test\runs\ab-rank-20261113\c1-desert-tractor\with\llm\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
