# 交付清单：run

> 任务单：`source-expansion-mixer-20261111` · 主 12 台 + 备选 4 台 · 状态 DONE
> 交付 12/12 · degraded 12 · citation_only 3 · 备选 2 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | AXOR 3236 8X4 12 M3 CONCRETE MIXER | primary | 1 | 20 | degraded/citation_only |
| 2 | 日野700 8×4 混凝土搅拌车 | primary | 2 | 16 | degraded |
| 3 | Arocs 4142 B 8x4 concrete mixer truck | primary | 3 | 16 | degraded |
| 4 | 山东富鑫 重汽12方搅拌车 | primary | 5 | 16 | degraded |
| 5 | 山推建友 CR412-06 混凝土搅拌车 | primary | 7 | 20 | degraded |
| 6 | 奔驰Actros工程版搅拌车底盘 | primary | 8 | 12 | degraded |
| 7 | 城市猎豹牌 HDL5310GJBJ5GE 混凝土搅拌运输车 | backup | 13 | 20 | degraded |
| 8 | HOWO NX 340马力 12方混凝土搅拌车 | primary | 4 | 12 | degraded/citation_only |
| 9 | 沃尔沃FM系列搅拌车底盘 | primary | 9 | 24 | degraded |
| 10 | 解放 CA5250GJBP66K22L1T1E 平头柴油混凝土搅拌汽车 | primary | 10 | 16 | degraded |
| 11 | 联合卡车 U系 QCC5312GJBD656N 混凝土搅拌车 | primary | 11 | 24 | degraded/citation_only |
| 12 | 三一 SY5255GJB2E 混凝土搅拌车 | primary | 12 | 20 | degraded |

**备选（随包）**：

- 1. HOWO NX 340Hp 12Cubic Meters（role=primary，rank=6，4 图）
- 2. JGC5271GJB 混凝土搅拌输送车（role=backup，rank=14，24 图）

## 二、内部监控（不对用户）

- 下载：hits 312 / downloaded 300 / failed 12 / blocked 0 / gate_pass 256
- 缺图归因：not_delivered 2
- 总耗时：142242 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 25903 |
| FETCH | 56629 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4023 |
| FETCH | 10307 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 27117 |
| FETCH | 18257 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3754 | ¥0.16 | **¥0.5354** |
| 全空闲 | ¥0.1877 | ¥0.16 | **¥0.3477** |

用量：输入 41565 tokens（按未命中计，偏保守）/ 输出 36528 / Search 8 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\s6-mixer\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\s6-mixer\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
