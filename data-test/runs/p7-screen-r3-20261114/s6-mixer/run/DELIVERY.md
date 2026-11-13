# 交付清单：run

> 任务单：`source-expansion-mixer-20261111` · 主 12 台 + 备选 4 台 · 状态 DONE
> 交付 12/12 · degraded 11 · citation_only 2 · 备选 3 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | AXOR 3236/8X4-E4 12 M3 CONCRETE MIXER | primary | 1 | 16 | degraded/citation_only |
| 2 | HOWO NX 340Hp 12Cubic Meters 混凝土搅拌车 | primary | 2 | 20 | degraded |
| 3 | Arocs 4142 B 8x4 concrete mixer truck | primary | 3 | 16 | degraded |
| 4 | 日野700 8×4 混凝土搅拌车 | primary | 4 | 16 | degraded |
| 5 | Ford GD10FD 8x4 混凝土搅拌车 | primary | 5 | 8 | degraded |
| 6 | 重汽12方搅拌车 | primary | 6 | 8 | degraded |
| 7 | 山推建友 CR412-06 混凝土搅拌车 | primary | 7 | 20 | degraded |
| 8 | 联合卡车U系 QCC5312GJBD656N 混凝土搅拌车 | primary | 8 | 24 | degraded/citation_only |
| 9 | 陕汽德龙 F2000 搅拌车 | primary | 10 | 20 | — |
| 10 | 汕德卡牌 SITRAK 混凝土搅拌运输车 | primary | 11 | 20 | degraded |
| 11 | 解放 CA5250GJBP66K22L1T1E 平头柴油混凝土搅拌汽车 | primary | 12 | 20 | degraded |
| 12 | 奔驰 Actros 搅拌车底盘 | backup | 13 | 12 | degraded |

**备选（随包）**：

- 1. 利勃海尔牌混凝土搅拌运输车（ZZ1317N306GD1B底盘）（role=backup，rank=15，12 图）
- 2. JGC5271GJB 混凝土搅拌输送车（role=primary，rank=9，24 图）
- 3. 沃尔沃 FM12 搅拌车底盘（role=backup，rank=14，24 图）

## 二、内部监控（不对用户）

- 下载：hits 328 / downloaded 288 / failed 36 / blocked 4 / gate_pass 268
- 缺图归因：not_delivered 3
- 总耗时：170012 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5343 |
| FETCH | 70382 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 2116 |
| FETCH | 69767 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1136 |
| FETCH | 21255 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3613 | ¥0.19 | **¥0.5513** |
| 全空闲 | ¥0.1807 | ¥0.19 | **¥0.3707** |

用量：输入 41426 tokens（按未命中计，偏保守）/ 输出 34807 / Search 8 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\s6-mixer\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\s6-mixer\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
