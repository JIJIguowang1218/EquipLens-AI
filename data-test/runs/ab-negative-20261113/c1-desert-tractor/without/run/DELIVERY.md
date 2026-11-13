# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 9/10 · degraded 8 · citation_only 1 · 备选 2 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | H6066 6×6 特种运输车 | primary | 2 | 10 | — |
| 2 | HF 8066 6×6 重型越野底盘 | primary | 3 | 30 | degraded |
| 3 | Zetros 4051 AS 6×6 重型牵引车 | primary | 6 | 30 | degraded |
| 4 | HOWO 6×6 全驱牵引车（运输/自卸/牵引系列中的牵引型） | backup | 12 | 30 | degraded/citation_only |
| 5 | Zetros 6×6 牵引车头 | backup | 13 | 15 | degraded |
| 6 | 越野 6×6 牵引头（460 马力，3900mm 轴距） | pool | 15 | 30 | degraded |
| 7 | OTTC 460马力 6×6 越野牵引头（鞍式牵引车） | pool | 16 | 5 | degraded |
| 8 | OTTC 越野 6×6 牵引头（460 马力） | primary | 9 | 5 | degraded |
| 9 | 豪沃 TH7 6×6 牵引车 | primary | 10 | 30 | degraded |

**备选（随包）**：

- 1. 6×6 371HP All Wheel Drive Off Road Vehicle Tractor（role=pool，rank=17，15 图）
- 2. 豪沃 TX 6×6 牵引车（ZZ4257V455GF1）（role=primary，rank=5，25 图）

## 二、内部监控（不对用户）

- 下载：hits 260 / downloaded 255 / failed 5 / blocked 0 / gate_pass 240
- 缺图归因：no_hits 6 / not_delivered 2
- 总耗时：215655 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 15136 |
| FETCH | 79138 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2267 |
| FETCH | 85756 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 407 |
| FETCH | 32940 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 9 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2929 | ¥0.16 | **¥0.4529** |
| 全空闲 | ¥0.1464 | ¥0.16 | **¥0.3064** |

用量：输入 39181 tokens（按未命中计，偏保守）/ 输出 26813 / Search 8 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c1-desert-tractor\without\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c1-desert-tractor\without\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c1-desert-tractor\without\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
