# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 3 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 骥驰 JC2104 | primary | 2 | 25 | — |
| 2 | 五征雷诺曼 PH2304 | primary | 5 | 20 | — |
| 3 | 东方红 LX2204 | primary | 6 | 30 | — |
| 4 | 丰疆智能FJ2004 | primary | 7 | 15 | — |
| 5 | 东方红-1604/1804 | backup | 11 | 10 | degraded/citation_only |
| 6 | KAT2204 | backup | 12 | 25 | — |
| 7 | 骥驰 JC1804(G4) | backup | 13 | 5 | degraded/citation_only |
| 8 | 飞驰FB1804 | backup | 14 | 25 | — |
| 9 | John Deere 6190 R | pool | 16 | 20 | degraded |
| 10 | 雷泰LT1604/LT1404 | pool | 17 | 20 | — |

**备选（随包）**：

- 1. 雷木1604（role=pool，rank=18，30 图）
- 2. 天拖TN1454（role=pool，rank=21，20 图）
- 3. 东方红-LX1304（role=pool，rank=23，25 图）
- 4. 潍坊泰山 TT1604（G4）（role=primary，rank=1，20 图）

## 二、内部监控（不对用户）

- 下载：hits 630 / downloaded 525 / failed 75 / blocked 8 / gate_pass 440
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / not_delivered 8
- 总耗时：230729 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 68604 |
| FETCH | 34110 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 35945 |
| FETCH | 33986 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 20393 |
| FETCH | 37683 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3061 | ¥0.22 | **¥0.5261** |
| 全空闲 | ¥0.1531 | ¥0.22 | **¥0.3731** |

用量：输入 30503 tokens（按未命中计，偏保守）/ 输出 30642 / Search 6 次 / Fetch 38 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c3-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
