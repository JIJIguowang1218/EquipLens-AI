# 交付清单：run

> 任务单：`source-expansion-mixer-20261111` · 主 12 台 + 备选 4 台 · 状态 DONE
> 交付 12/12 · degraded 12 · citation_only 0 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | AXOR 3236 8X4 12 m³ 混凝土搅拌车 | primary | 1 | 12 | degraded |
| 2 | 杰狮 混凝土搅拌车（8X4） | primary | 2 | 8 | degraded |
| 3 | 日野700 8×4 混凝土搅拌车 | primary | 3 | 16 | degraded |
| 4 | Arocs 4142 B 8x4 底盘混凝土搅拌车（IMER Group ORU LT 105EH 上装） | primary | 4 | 20 | degraded |
| 5 | 解放 平头柴油混凝土搅拌车（12立方规格） | primary | 5 | 24 | degraded |
| 6 | 重汽12方搅拌车 | primary | 6 | 8 | degraded |
| 7 | HOWO NX 340Hp 12Cubic Meters Concrete Mixer Truck | primary | 7 | 8 | degraded |
| 8 | 三一 SY5255GJB2E 搅拌车 | backup | 13 | 20 | degraded |
| 9 | CR412-06混凝土搅拌车 | backup | 14 | 20 | degraded |
| 10 | 悍V 混凝土搅拌车（CA5311GJBP1K2L1T4E6A81 / 中联 ZLJ5310GJBJX2F） | backup | 15 | 24 | degraded |
| 11 | 解放 CA5250GJBP66K22L1T1E 平头柴油混凝土搅拌汽车 | backup | 16 | 12 | degraded |
| 12 | 中国重汽 豪泺(HOWO) 混凝土搅拌运输车 | pool | 17 | 16 | degraded |

**备选（随包）**：

- 1. 中国重汽 汕德卡(SITRAK) 混凝土搅拌运输车（role=pool，rank=18，20 图）
- 2. 陕汽底盘12方混凝土搅拌车（role=pool，rank=20，24 图）
- 3. HOWO NX 340Hp 12 m³ 混凝土搅拌车（中联上装）（role=primary，rank=8，4 图）
- 4. JGC5271GJB 混凝土搅拌输送车（role=pool，rank=19，16 图）

## 二、内部监控（不对用户）

- 下载：hits 356 / downloaded 308 / failed 48 / blocked 0 / gate_pass 272
- 缺图归因：not_delivered 4
- 总耗时：159327 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 25340 |
| FETCH | 61068 |
| VERIFY | 13 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 18377 |
| FETCH | 54518 |
| VERIFY | 10 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3671 | ¥0.19 | **¥0.5571** |
| 全空闲 | ¥0.1835 | ¥0.19 | **¥0.3735** |

用量：输入 41438 tokens（按未命中计，偏保守）/ 输出 35524 / Search 8 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\s6-mixer\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\s6-mixer\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
