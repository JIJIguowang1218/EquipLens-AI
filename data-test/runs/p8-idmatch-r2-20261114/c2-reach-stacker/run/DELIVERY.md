# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 3 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | RSH4532-Vo 正面吊运机 | primary | 1 | 25 | — |
| 2 | DRU450-570 | primary | 3 | 5 | — |
| 3 | SMV 4542 TB4 BH | primary | 4 | 30 | degraded/citation_only |
| 4 | LG420FC4 | primary | 5 | 20 | degraded/citation_only |
| 5 | CRS450Z5 | primary | 6 | 20 | — |
| 6 | HCS46 | primary | 7 | 5 | — |
| 7 | RSH4528-VO2 | backup | 11 | 5 | — |
| 8 | RS45 正面吊 | backup | 13 | 20 | — |
| 9 | Liebherr 利勃海尔 正面吊 | backup | 14 | 30 | degraded |
| 10 | 正面吊 | pool | 16 | 25 | — |

**备选（随包）**：

- 1. Konecranes 科尼 正面吊（role=pool，rank=17，25 图）
- 2. Taylor Machine Works 集装箱正面吊（role=pool，rank=18，20 图）
- 3. Sitrak 480HP 集装箱码头牵引车（role=pool，rank=19，25 图）
- 4. 700 集装箱运输底盘车（role=pool，rank=20，15 图）

## 二、内部监控（不对用户）

- 下载：hits 470 / downloaded 390 / failed 80 / blocked 0 / gate_pass 285
- 缺图归因：gate_or_verify_rejected 3 / not_delivered 5
- 总耗时：312391 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 13827 |
| FETCH | 119373 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 23587 |
| FETCH | 91791 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 30865 |
| FETCH | 32941 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2737 | ¥0.19 | **¥0.4637** |
| 全空闲 | ¥0.1369 | ¥0.19 | **¥0.3269** |

用量：输入 39761 tokens（按未命中计，偏保守）/ 输出 24276 / Search 8 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c2-reach-stacker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
