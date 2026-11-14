# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 4 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 凯斯 OPTUM2704 | primary | 1 | 15 | degraded/citation_only |
| 2 | 五征雷诺曼 PH2304 | primary | 2 | 20 | — |
| 3 | 东方红 LX2204 | primary | 3 | 30 | — |
| 4 | Claas Arion 4 Cmatic | primary | 4 | 30 | degraded |
| 5 | John Deere 6170R | primary | 5 | 30 | — |
| 6 | John Deere 6190 R | backup | 11 | 20 | degraded |
| 7 | 丰疆智能 FJ2004 | backup | 12 | 15 | — |
| 8 | 骥驰 JC1804(G4)/JC1854 | backup | 13 | 25 | degraded/citation_only |
| 9 | 鲁拖 LT1804 | backup | 14 | 15 | — |
| 10 | 天拖 TN1454 | pool | 15 | 20 | — |

**备选（随包）**：

- 1. 飞驰 FB1804（role=pool，rank=16，25 图）
- 2. 雷木1604（role=pool，rank=18，30 图）
- 3. 潍坊泰山 TT1604(G4)（role=primary，rank=7，20 图）
- 4. 悍沃 1654（role=pool，rank=17，25 图）

## 二、内部监控（不对用户）

- 下载：hits 630 / downloaded 515 / failed 63 / blocked 8 / gate_pass 435
- 缺图归因：all_download_failed 2 / not_delivered 9
- 总耗时：356402 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 32918 |
| FETCH | 37258 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 103907 |
| FETCH | 38541 |
| VERIFY | 10 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 61148 |
| FETCH | 82610 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2824 | ¥0.22 | **¥0.5024** |
| 全空闲 | ¥0.1412 | ¥0.22 | **¥0.3612** |

用量：输入 30588 tokens（按未命中计，偏保守）/ 输出 27657 / Search 6 次 / Fetch 38 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c3-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
