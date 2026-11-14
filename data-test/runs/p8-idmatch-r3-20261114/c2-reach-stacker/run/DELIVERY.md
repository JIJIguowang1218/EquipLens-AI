# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 5 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 大连 CRS450Z5 集装箱正面吊运机 | primary | 1 | 15 | — |
| 2 | 海斯特 RS45（B921） | primary | 2 | 5 | — |
| 3 | 卡尔玛 Essential 系列正面吊 DRU450-570 | primary | 3 | 25 | — |
| 4 | 合力 RSH4532-Vo 正面吊运机 | primary | 4 | 30 | — |
| 5 | 龙工 LG420FC4 集装箱正面吊 | primary | 5 | 5 | degraded/citation_only |
| 6 | 科尼 SMV 4542 TB4 BH 正面吊 | primary | 6 | 30 | degraded |
| 7 | RSH4528-VO2 重型正面吊 | primary | 7 | 5 | — |
| 8 | XCMG集装箱正面吊（45吨级） | primary | 8 | 10 | degraded |
| 9 | 杭叉 集装箱正面吊（X系列平台） | primary | 9 | 25 | degraded |
| 10 | HCS46 集装箱正面吊运起重机 | primary | 10 | 10 | degraded/citation_only |

**备选（随包）**：

- 1. RS45 正面吊（role=backup，rank=11，15 图）
- 2. 科尼港口正面吊（role=backup，rank=12，5 图）
- 3. 柳工正面吊（港口机械集装箱搬运设备）（role=backup，rank=13，25 图）
- 4. 重型四轮底盘集装箱正面吊（结构图）（role=backup，rank=14，15 图）

## 二、内部监控（不对用户）

- 下载：hits 440 / downloaded 340 / failed 95 / blocked 5 / gate_pass 245
- 缺图归因：not_delivered 7
- 总耗时：312705 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 43643 |
| FETCH | 49184 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 36023 |
| FETCH | 15591 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 63483 |
| FETCH | 104775 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1726 | ¥0.19 | **¥0.3626** |
| 全空闲 | ¥0.0863 | ¥0.19 | **¥0.2763** |

用量：输入 29231 tokens（按未命中计，偏保守）/ 输出 14266 / Search 6 次 / Fetch 32 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c2-reach-stacker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
