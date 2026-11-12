# 交付清单：run

> 任务单：`auto-20261112-164301` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 9/10 · degraded 6 · citation_only 1 · 备选 1 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 泰安五岳 油田专用全驱牵引车（6×6） | primary | 1 | 25 | degraded |
| 2 | HOWO 6×6 全驱牵引车（TX/TH7/T7H 系列，如 ZZ4257V455GF1） | primary | 3 | 30 | degraded |
| 3 | SHACMAN F3000 6×6 牵引车 | primary | 4 | 20 | — |
| 4 | Zetros 4051 AS 6×6牵引车 | primary | 5 | 30 | degraded |
| 5 | SHACMAN X3000 6×6 牵引车头 | primary | 6 | 25 | — |
| 6 | FAW J6P 6×6 重型牵引车 | primary | 7 | 10 | degraded/citation_only |
| 7 | 陕汽通力 6×6 全驱沙漠车（可改装油田专用车） | backup | 11 | 20 | degraded |
| 8 | HOWO 6×6全驱牵引车 | primary | 8 | 25 | — |
| 9 | Zetros 6×6 tractor-head | primary | 9 | 25 | degraded |

**备选（随包）**：

- 1. J6P 6×6 重型牵引车（role=backup，rank=12，25 图）

## 二、内部监控（不对用户）

- 下载：hits 300 / downloaded 265 / failed 35 / blocked 0 / gate_pass 240
- 缺图归因：no_hits 2 / not_delivered 1
- 总耗时：216687 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 27568 |
| FETCH | 99098 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 14331 |
| FETCH | 34075 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1695 |
| FETCH | 39910 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 8 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2251 | ¥0.14 | **¥0.3651** |
| 全空闲 | ¥0.1125 | ¥0.14 | **¥0.2525** |

用量：输入 28066 tokens（按未命中计，偏保守）/ 输出 21119 / Search 6 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112\c1-desert-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112\c1-desert-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112\c1-desert-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
