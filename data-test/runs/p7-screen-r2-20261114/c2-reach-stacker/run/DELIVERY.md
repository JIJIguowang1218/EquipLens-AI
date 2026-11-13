# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 5 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 合力 RSH4532-Vo 正面吊运机 | primary | 1 | 30 | — |
| 2 | 海斯特 RS45（B921） | primary | 2 | 5 | degraded |
| 3 | 卡尔玛 Essential系列正面吊 DRU450-570 | primary | 3 | 20 | — |
| 4 | 科尼 SMV 4542 TB4 BH | primary | 4 | 30 | degraded |
| 5 | 龙工 LG420FC4 | primary | 6 | 30 | — |
| 6 | Kalmar DRD420-65S6 正面吊运机 | primary | 7 | 15 | degraded/citation_only |
| 7 | Hyster RS45 正面吊 | backup | 11 | 10 | degraded |
| 8 | HCS46 | backup | 12 | 5 | — |
| 9 | XCMG集装箱正面吊 | backup | 14 | 10 | degraded |
| 10 | RSH4528-VO2 | pool | 15 | 5 | — |

**备选（随包）**：

- 1. 三一（SANY）集装箱正面吊（role=pool，rank=17，25 图）
- 2. 利勃海尔（Liebherr）集装箱正面吊（role=pool，rank=18，25 图）
- 3. 科尼（Konecranes）集装箱正面吊（role=pool，rank=19，20 图）
- 4. TOMAC（通玛科）正面吊（role=pool，rank=21，5 图）

## 二、内部监控（不对用户）

- 下载：hits 530 / downloaded 410 / failed 100 / blocked 20 / gate_pass 345
- 缺图归因：gate_or_verify_rejected 3 / not_delivered 8
- 总耗时：238069 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4507 |
| FETCH | 52596 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2751 |
| FETCH | 90683 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 3224 |
| FETCH | 84298 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.283 | ¥0.21 | **¥0.493** |
| 全空闲 | ¥0.1415 | ¥0.21 | **¥0.3515** |

用量：输入 39812 tokens（按未命中计，偏保守）/ 输出 25420 / Search 8 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c2-reach-stacker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
