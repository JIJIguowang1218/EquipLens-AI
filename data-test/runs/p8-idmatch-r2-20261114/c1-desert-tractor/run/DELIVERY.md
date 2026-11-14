# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 8 · citation_only 4 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 泰安五岳 TAZ4922 6×6 油田专用牵引车 | primary | 1 | 25 | degraded/citation_only |
| 2 | 奔驰 Zetros 4051 AS 6×6 重型牵引车 | primary | 2 | 30 | degraded |
| 3 | MOL H6066 6x6 特种运输车 | primary | 3 | 25 | — |
| 4 | Zetros 6x6 牵引车头（tractor-head） | primary | 5 | 30 | degraded |
| 5 | OTTC 460马力 6×6 越野牵引头 | primary | 6 | 5 | degraded/citation_only |
| 6 | HOWO 371HP 全驱越野牵引车 | primary | 7 | 30 | degraded |
| 7 | 雷诺 TBH280（6×6）牵引车 / TRM 1200 T | backup | 11 | 25 | degraded/citation_only |
| 8 | MOL HF 8066 6×6 越野底盘 | backup | 12 | 30 | — |
| 9 | 东风 6×6 沙漠卡车（400马力） | backup | 13 | 30 | degraded |
| 10 | 济南重汽 HOWO 6×6全驱牵引车 | pool | 15 | 30 | degraded/citation_only |

**备选（随包）**：

- 1. 北奔沙漠车 ND5180TSMZ01（role=primary，rank=8，15 图）
- 2. 豪沃TH7 6×6全驱牵引车（role=primary，rank=10，25 图）
- 3. 北奔 沙漠车 ND5250TSMZ04（role=pool，rank=16，30 图）
- 4. 豪沃TX 6×6牵引车 ZZ4257V455GF1（role=primary，rank=4，25 图）

## 二、内部监控（不对用户）

- 下载：hits 460 / downloaded 445 / failed 15 / blocked 0 / gate_pass 405
- 缺图归因：not_delivered 6
- 总耗时：142897 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6735 |
| FETCH | 50171 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2857 |
| FETCH | 40587 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 23809 |
| FETCH | 18728 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.385 | ¥0.18 | **¥0.565** |
| 全空闲 | ¥0.1925 | ¥0.18 | **¥0.3725** |

用量：输入 40621 tokens（按未命中计，偏保守）/ 输出 37974 / Search 8 次 / Fetch 28 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c1-desert-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
