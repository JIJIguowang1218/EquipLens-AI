# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 5 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 东方红 LX2204 大马力轮式拖拉机 | primary | 1 | 30 | — |
| 2 | 雷沃欧豹 M1654 | primary | 2 | 30 | — |
| 3 | 五征雷诺曼 PH2304 | primary | 3 | 20 | — |
| 4 | 凯斯 OPTUM2704 | primary | 4 | 15 | degraded/citation_only |
| 5 | John Deere 6170R | primary | 5 | 30 | — |
| 6 | 骥驰 JC2104 | primary | 6 | 25 | — |
| 7 | 悍沃1654轮式拖拉机 | primary | 7 | 25 | degraded |
| 8 | 潍坊泰山 TT1600（G4） | primary | 8 | 10 | degraded/citation_only |
| 9 | 东方红-1604/1804 | primary | 9 | 15 | degraded/citation_only |
| 10 | 天拖TN1454型大马力轮式拖拉机 | primary | 10 | 30 | degraded |

**备选（随包）**：

- 1. 东方红-LX2004（role=backup，rank=11，15 图）
- 2. KAT2204拖拉机（role=backup，rank=13，20 图）
- 3. 丰疆智能 FJ2004（role=backup，rank=14，15 图）
- 4. 东方红-LX2204系列（role=pool，rank=16，25 图）

## 二、内部监控（不对用户）

- 下载：hits 510 / downloaded 465 / failed 45 / blocked 0 / gate_pass 395
- 缺图归因：not_delivered 7
- 总耗时：127267 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4195 |
| FETCH | 47505 |
| VERIFY | 11 |
| FILL | 2 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1882 |
| FETCH | 19539 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 9661 |
| FETCH | 44466 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2375 | ¥0.18 | **¥0.4175** |
| 全空闲 | ¥0.1187 | ¥0.18 | **¥0.2987** |

用量：输入 30429 tokens（按未命中计，偏保守）/ 输出 22080 / Search 6 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c3-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
