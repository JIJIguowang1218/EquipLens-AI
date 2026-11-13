# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 9 · citation_only 4 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 豪沃 6×6 油田牵引车（豪沃驾驶室油田专用牵引车） | primary | 1 | 5 | degraded/citation_only |
| 2 | 泰安五岳 TAZ4922 油田专用全驱牵引车 | primary | 2 | 25 | degraded |
| 3 | 豪沃 6×6 371HP 全驱越野牵引车 | primary | 3 | 25 | degraded |
| 4 | Zetros 6×6 牵引车头 | primary | 5 | 30 | degraded |
| 5 | Zetros 4051 AS 6×6 重型牵引车 | primary | 6 | 15 | degraded |
| 6 | MOL HF 8066 | primary | 7 | 20 | — |
| 7 | TRM700-100（6×6）牵引车 | backup | 11 | 30 | degraded/citation_only |
| 8 | HOWO 6×6 全驱牵引车 | backup | 12 | 20 | degraded |
| 9 | DFV5253TSMGP6D 6×6 沙漠车 | backup | 13 | 25 | degraded/citation_only |
| 10 | EQ2102G 6X6 沙漠越野卡车 | backup | 14 | 30 | degraded/citation_only |

**备选（随包）**：

- 1. 豪沃TX 6×6牵引车 ZZ4257V455GF1（role=primary，rank=4，20 图）
- 2. OTTC 460马力 6×6 越野牵引头（role=pool，rank=15，5 图）
- 3. 豪沃TX 6×6牵引车（role=pool，rank=16，25 图）
- 4. 6×6 越野牵引头（460马力）（role=pool，rank=17，20 图）

## 二、内部监控（不对用户）

- 下载：hits 395 / downloaded 360 / failed 35 / blocked 0 / gate_pass 315
- 缺图归因：not_delivered 4
- 总耗时：135184 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 27096 |
| FETCH | 47813 |
| VERIFY | 8 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 13990 |
| FETCH | 46270 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2203 | ¥0.14 | **¥0.3603** |
| 全空闲 | ¥0.1101 | ¥0.14 | **¥0.2501** |

用量：输入 30475 tokens（按未命中计，偏保守）/ 输出 19913 / Search 6 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c1-desert-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
