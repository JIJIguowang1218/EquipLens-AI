# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 6 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 海斯特RS45（B921）正面吊 | primary | 2 | 25 | — |
| 2 | 合力 RSH4532-Vo 正面吊运机 | primary | 3 | 30 | — |
| 3 | 科尼SMV 4542 TB4 BH正面吊 | primary | 4 | 30 | degraded |
| 4 | 大连叉车CRS450Z5集装箱正面吊运机 | primary | 6 | 15 | — |
| 5 | Kalmar Essential DRU450-570 正面吊 | backup | 11 | 30 | degraded/citation_only |
| 6 | Hyster RS45 正面吊 | backup | 12 | 5 | degraded/citation_only |
| 7 | 安徽合力RSH4532-Vo正面吊运机 | backup | 13 | 15 | — |
| 8 | SANY 集装箱正面吊 | primary | 8 | 30 | degraded |
| 9 | Liebherr 集装箱正面吊 | primary | 9 | 30 | degraded |
| 10 | TOMAC 通玛科 集装箱正面吊 | primary | 10 | 5 | degraded |

**备选（随包）**：

- 1. 合力 RSH4528-VO2 重型正面吊（role=backup，rank=14，20 图）
- 2. Taylor Machine Works 集装箱正面吊（role=pool，rank=17，20 图）
- 3. 卡尔玛Essential系列正面吊DRU450-570（role=primary，rank=1，15 图）
- 4. 龙工LG420FC4集装箱正面吊（role=primary，rank=5，10 图）

## 二、内部监控（不对用户）

- 下载：hits 430 / downloaded 370 / failed 55 / blocked 5 / gate_pass 350
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 1 / not_delivered 5
- 总耗时：246196 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 38427 |
| FETCH | 86822 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 19599 |
| FETCH | 50100 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 13489 |
| FETCH | 37740 |
| VERIFY | 8 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1486 | ¥0.15 | **¥0.2986** |
| 全空闲 | ¥0.0743 | ¥0.15 | **¥0.2243** |

用量：输入 29134 tokens（按未命中计，偏保守）/ 输出 11293 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c2-reach-stacker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
