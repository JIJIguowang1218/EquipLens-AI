# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 6 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 安徽合力 RSH4532-Vo 正面吊运机 | primary | 1 | 20 | — |
| 2 | 卡尔玛 Essential 系列正面吊 DRU450-570 | primary | 2 | 25 | — |
| 3 | 海斯特 RS45（B921） | primary | 3 | 5 | degraded |
| 4 | 科尼 SMV 4542 TB4 BH 正面吊 | primary | 4 | 30 | degraded |
| 5 | XCMG 集装箱正面吊 45 吨级 | primary | 5 | 10 | degraded |
| 6 | 龙工 LG420FC4 集装箱正面吊 | primary | 6 | 5 | degraded/citation_only |
| 7 | 大连叉车 CRS450Z5 集装箱正面吊运机 | primary | 7 | 15 | — |
| 8 | HCS46 | primary | 8 | 5 | — |
| 9 | 临晟 CRS450 集装箱正面吊 | primary | 9 | 10 | degraded/citation_only |
| 10 | 柳工正面吊（未给具体型号码） | primary | 10 | 20 | degraded/citation_only |

**备选（随包）**：

- 1. TOMAC 通玛科 集装箱正面吊（role=backup，rank=12，5 图）
- 2. RSH4528-VO2（role=backup，rank=13，5 图）
- 3. Hyster RS45 正面吊（role=pool，rank=17，10 图）
- 4. Kalmar DRD420-65S6 正面吊运机（role=backup，rank=11，15 图）

## 二、内部监控（不对用户）

- 下载：hits 370 / downloaded 270 / failed 95 / blocked 5 / gate_pass 200
- 缺图归因：gate_or_verify_rejected 2 / not_delivered 5
- 总耗时：276713 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 8520 |
| FETCH | 125029 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 4673 |
| FETCH | 30201 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5240 |
| FETCH | 103043 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.292 | ¥0.18 | **¥0.472** |
| 全空闲 | ¥0.146 | ¥0.18 | **¥0.326** |

用量：输入 39875 tokens（按未命中计，偏保守）/ 输出 26534 / Search 8 次 / Fetch 28 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c2-reach-stacker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
