# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 8 · citation_only 5 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | TAZ4922 6×6 油田沙漠牵引车 | primary | 1 | 30 | degraded/citation_only |
| 2 | HF 8066 6×6 重型越野底盘 | primary | 3 | 30 | — |
| 3 | H6066 6×6 特种运输车 | primary | 4 | 25 | — |
| 4 | 沙漠越野重型牵引车（康明斯+艾利逊运输底盘） | primary | 5 | 10 | degraded/citation_only |
| 5 | Zetros 4051 AS 6×6 重型牵引车 | primary | 7 | 30 | degraded |
| 6 | 豪沃6×6全驱越野牵引车 371HP | backup | 11 | 30 | degraded |
| 7 | Middle East 6X6 柴油重卡（Deutz D13 动力） | backup | 12 | 5 | degraded/citation_only |
| 8 | 雷诺 TBH280 6×6 牵引车 | backup | 13 | 25 | degraded/citation_only |
| 9 | KAMAZ K-65959 | backup | 14 | 25 | degraded/citation_only |
| 10 | HOWO 6×6 全驱牵引车 | pool | 15 | 10 | degraded |

**备选（随包）**：

- 1. 6×6越野牵引车头（460马力）（role=pool，rank=16，10 图）
- 2. 豪沃 TX 6×6 牵引车 ZZ4257V455GF1（role=primary，rank=2，25 图）
- 3. 重汽五岳 特种牵引车（油田/井场搬迁用）（role=primary，rank=6，15 图）
- 4. OTTC 460马力 6×6 越野牵引头（role=pool，rank=17，5 图）

## 二、内部监控（不对用户）

- 下载：hits 365 / downloaded 315 / failed 50 / blocked 0 / gate_pass 290
- 缺图归因：not_delivered 4
- 总耗时：177722 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 48747 |
| FETCH | 43317 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 29201 |
| FETCH | 56446 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.0 | ¥0.13 | **¥0.13** |
| 全空闲 | ¥0.0 | ¥0.13 | **¥0.13** |

用量：输入 0 tokens（按未命中计，偏保守）/ 输出 0 / Search 0 次 / Fetch 26 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\verify-identity-20261114\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\verify-identity-20261114\c1-desert-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
