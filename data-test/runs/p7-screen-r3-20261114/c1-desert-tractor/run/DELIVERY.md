# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 8 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 泰安五岳 TAZ4922 6×6 油田专用全驱牵引车 | primary | 1 | 20 | degraded |
| 2 | 奔驰 Zetros 4051 AS 6×6 牵引车 | primary | 3 | 25 | degraded |
| 3 | HOWO 371HP 全驱越野牵引车（6×6） | primary | 4 | 30 | degraded |
| 4 | KAMAZ K-65959 6X6 牵引车 | primary | 5 | 25 | degraded/citation_only |
| 5 | MOL HF 8066 6×6 越野底盘 | primary | 6 | 30 | degraded |
| 6 | MOL H6066 6×6 特种运输车 | primary | 7 | 25 | — |
| 7 | Mercedes-Benz Zetros 6x6 牵引头 | backup | 11 | 20 | degraded |
| 8 | OTTC 460马力 6×6 牵引头 | backup | 12 | 5 | degraded |
| 9 | 北奔沙漠车（ND5180TSMZ01/ND5140TSMZ02/ND5250TSM 系列） | backup | 13 | 30 | — |
| 10 | 沙漠越野重型牵引车（康明斯+艾里逊运输底盘） | pool | 16 | 15 | degraded/citation_only |

**备选（随包）**：

- 1. 豪沃TX 6×6牵引车 ZZ4257V455GF1（role=primary，rank=2，25 图）
- 2. OTTC 越野 460 马力 6×6 牵引头（role=backup，rank=14，5 图）
- 3. 6×6 越野牵引头（460 马力）（role=pool，rank=15，10 图）
- 4. 6X6 油田沙漠重型牵引车（专利 CN206171594U 所述车型）（role=pool，rank=17，25 图）

## 二、内部监控（不对用户）

- 下载：hits 375 / downloaded 330 / failed 45 / blocked 0 / gate_pass 295
- 缺图归因：not_delivered 4
- 总耗时：154226 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 14160 |
| FETCH | 60794 |
| VERIFY | 8 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 25001 |
| FETCH | 54258 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2889 | ¥0.16 | **¥0.4489** |
| 全空闲 | ¥0.1444 | ¥0.16 | **¥0.3044** |

用量：输入 40665 tokens（按未命中计，偏保守）/ 输出 25945 / Search 8 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c1-desert-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
