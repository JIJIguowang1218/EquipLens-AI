# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 8 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 泰安五岳 TAZ4922 油田专用全驱牵引车 | primary | 1 | 25 | degraded |
| 2 | 奔驰 Zetros 4051 AS 6×6 重型牵引车 | primary | 3 | 30 | degraded |
| 3 | MOL HF8066 6x6 重型沙漠运输车 | primary | 4 | 25 | — |
| 4 | MOL H6066 6x6 特种运输车 | primary | 5 | 25 | — |
| 5 | HOWO 6×6 全驱牵引车 | primary | 7 | 20 | degraded |
| 6 | OTTC 460马力 6×6 牵引头 | backup | 11 | 5 | degraded |
| 7 | 豪沃TH7 6×6 牵引车 | backup | 13 | 25 | degraded |
| 8 | HOWO 6×6 371HP 全驱越野牵引车 | backup | 14 | 25 | degraded |
| 9 | TBH280 (6×6) 牵引车 | pool | 16 | 20 | degraded/citation_only |
| 10 | 德国 Titan 沙漠用重型越野运输车 | pool | 17 | 30 | degraded |

**备选（随包）**：

- 1. 豪沃TX 6×6 牵引车 ZZ4257V455GF1（role=primary，rank=2，25 图）
- 2. 重汽五岳特种牵引车（油田/井场搬迁用）（role=primary，rank=6，15 图）
- 3. 豪沃TX 6×6 牵引车（role=backup，rank=12，25 图）
- 4. OTTC 越野 460 马力 6×6 牵引头（role=pool，rank=15，5 图）

## 二、内部监控（不对用户）

- 下载：hits 370 / downloaded 345 / failed 25 / blocked 0 / gate_pass 310
- 缺图归因：not_delivered 4
- 总耗时：178288 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 74993 |
| FETCH | 42738 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 12715 |
| FETCH | 47835 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3627 | ¥0.16 | **¥0.5227** |
| 全空闲 | ¥0.1814 | ¥0.16 | **¥0.3414** |

用量：输入 40472 tokens（按未命中计，偏保守）/ 输出 35223 / Search 8 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c1-desert-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
