# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 4 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | TT1600（G4） | primary | 1 | 10 | degraded/citation_only |
| 2 | KAT2204 | primary | 2 | 25 | — |
| 3 | JC1804（G4） | primary | 3 | 10 | — |
| 4 | 雷木1604 | primary | 4 | 30 | — |
| 5 | 五征雷诺曼PH2304轮式拖拉机 | primary | 5 | 15 | — |
| 6 | 雷沃TG系列M1654-G拖拉机 | primary | 6 | 25 | degraded |
| 7 | 潍坊泰山TT1604（G4）轮式拖拉机 | backup | 11 | 15 | — |
| 8 | 东方红-1604/1804 | backup | 12 | 15 | degraded/citation_only |
| 9 | 悍沃1654轮式拖拉机 | backup | 13 | 25 | degraded |
| 10 | 丰疆智能 FJ2004 | pool | 15 | 15 | — |

**备选（随包）**：

- 1. 飞驰 FB1804（role=pool，rank=16，25 图）
- 2. John Deere 6170R（role=pool，rank=19，30 图）
- 3. 雷泰 LT1604/LT1404（role=pool，rank=20，30 图）
- 4. 骥驰JC2104轮式拖拉机（role=pool，rank=21，20 图）

## 二、内部监控（不对用户）

- 下载：hits 615 / downloaded 485 / failed 75 / blocked 11 / gate_pass 400
- 缺图归因：all_download_failed 2 / not_delivered 9
- 总耗时：251659 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 52214 |
| FETCH | 56959 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 36294 |
| FETCH | 47615 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7758 |
| FETCH | 50800 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 5 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2591 | ¥0.2 | **¥0.4591** |
| 全空闲 | ¥0.1296 | ¥0.2 | **¥0.3296** |

用量：输入 30453 tokens（按未命中计，偏保守）/ 输出 24779 / Search 6 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\c3-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
