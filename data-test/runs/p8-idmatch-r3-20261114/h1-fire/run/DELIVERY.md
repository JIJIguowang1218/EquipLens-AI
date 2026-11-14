# 交付清单：run

> 任务单：`auto-20261114-024559` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 6 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | PM75多功能水罐泡沫消防车 | primary | 1 | 30 | degraded/citation_only |
| 2 | 斯堪尼亚城市主战消防车 P310 | primary | 2 | 36 | degraded |
| 3 | 曼恩 TGM18.290B6 4×2 泡沫/水罐消防车（QHV5170GXFPM60/M6） | primary | 3 | 36 | — |
| 4 | 东风 4×2 水罐消防车 SLS5160（6000L，双排驾驶室） | primary | 4 | 18 | degraded |
| 5 | 五十铃GIGA 8立方米水泡沫消防车 | backup | 10 | 36 | degraded |
| 6 | 川消牌 SXF5090GXFPM35 泡沫消防车（东风底盘，4×2） | backup | 11 | 24 | degraded |
| 7 | CLW5090GXFP40 | backup | 12 | 12 | degraded/citation_only |
| 8 | PM50 | pool | 13 | 12 | — |

**备选（随包）**：

- 1. HOWO 4×2 8cbm 泡沫消防车（role=pool，rank=14，24 图）
- 2. 豪沃 8吨 水罐泡沫消防车（4×2）（role=pool，rank=15，36 图）
- 3. 3500升 4*2 泡沫水罐消防车（role=pool，rank=17，12 图）
- 4. 克洛威 3500升 4×2 泡沫水罐消防车（role=pool，rank=16，12 图）

## 二、内部监控（不对用户）

- 下载：hits 450 / downloaded 372 / failed 50 / blocked 0 / gate_pass 312
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 1 / not_delivered 5
- 总耗时：198723 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 13100 |
| FETCH | 74104 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 26822 |
| FETCH | 32530 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1484 |
| FETCH | 50670 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3023 | ¥0.15 | **¥0.4523** |
| 全空闲 | ¥0.1511 | ¥0.15 | **¥0.3011** |

用量：输入 31712 tokens（按未命中计，偏保守）/ 输出 29859 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\h1-fire\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\h1-fire\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
