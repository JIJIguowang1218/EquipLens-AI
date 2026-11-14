# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 2 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 东方红-1604/1804大马力轮式拖拉机 | primary | 1 | 30 | degraded/citation_only |
| 2 | John Deere 6170R AP轮式拖拉机 | primary | 2 | 30 | — |
| 3 | 五征雷诺曼 PH2304 | primary | 3 | 20 | — |
| 4 | 凯斯 OPTUM2704 | primary | 4 | 15 | degraded/citation_only |
| 5 | 丰疆智能 FJ2004 | primary | 5 | 15 | — |
| 6 | KAT2204 | primary | 6 | 25 | — |
| 7 | 潍坊泰山TT1604（G4）轮式拖拉机 | primary | 7 | 15 | — |
| 8 | 骥驰 JC2104 | primary | 8 | 25 | — |
| 9 | 飞驰 FB1804 | primary | 9 | 25 | — |
| 10 | 鲁拖 LT1804 | primary | 10 | 15 | — |

**备选（随包）**：

- 1. 天拖 TN1454（role=backup，rank=11，20 图）
- 2. 雷木1604（role=pool，rank=15，30 图）
- 3. John Deere 6190 R轮式拖拉机（role=pool，rank=16，20 图）
- 4. 骥驰 JC1804(G4)（role=backup，rank=12，5 图）

## 二、内部监控（不对用户）

- 下载：hits 510 / downloaded 460 / failed 50 / blocked 0 / gate_pass 380
- 缺图归因：not_delivered 7
- 总耗时：150179 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 12865 |
| FETCH | 39924 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 30915 |
| FETCH | 13665 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 18868 |
| FETCH | 33932 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2877 | ¥0.18 | **¥0.4677** |
| 全空闲 | ¥0.1438 | ¥0.18 | **¥0.3238** |

用量：输入 30390 tokens（按未命中计，偏保守）/ 输出 28360 / Search 6 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c3-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
