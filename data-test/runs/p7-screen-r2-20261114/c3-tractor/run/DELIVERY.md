# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 5 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 东方红-1604/1804 | primary | 1 | 15 | degraded/citation_only |
| 2 | 凯斯OPTUM2704 | primary | 2 | 15 | degraded/citation_only |
| 3 | 骥驰JC2104 | primary | 4 | 25 | — |
| 4 | 潍坊泰山TT1604（G4） | primary | 5 | 25 | — |
| 5 | KAT2204拖拉机 | primary | 6 | 20 | — |
| 6 | 悍沃1654轮式拖拉机 | primary | 7 | 25 | degraded |
| 7 | 雷木1604轮式拖拉机 | backup | 11 | 30 | degraded |
| 8 | 丰疆智能FJ2004 | backup | 12 | 15 | — |
| 9 | 东方红LX2204 | backup | 13 | 25 | — |
| 10 | John Deere 6170R AP | backup | 14 | 25 | degraded |

**备选（随包）**：

- 1. 骥驰JC2104轮式拖拉机（role=pool，rank=16，10 图）
- 2. 东方红LX2004（role=pool，rank=18，25 图）
- 3. 飞驰FB1804（role=pool，rank=19，25 图）
- 4. 昊田1504大马力轮式拖拉机（role=pool，rank=20，30 图）

## 二、内部监控（不对用户）

- 下载：hits 630 / downloaded 540 / failed 60 / blocked 8 / gate_pass 475
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 1 / not_delivered 9
- 总耗时：186164 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 17957 |
| FETCH | 45132 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 26078 |
| FETCH | 41808 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 10890 |
| FETCH | 44286 |
| VERIFY | 5 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3142 | ¥0.2 | **¥0.5142** |
| 全空闲 | ¥0.1571 | ¥0.2 | **¥0.3571** |

用量：输入 30192 tokens（按未命中计，偏保守）/ 输出 31726 / Search 6 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c3-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
