# 交付清单：run

> 任务单：`source-expansion-mixer-20261111` · 主 12 台 + 备选 4 台 · 状态 DONE
> 交付 12/12 · degraded 10 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | AXOR 3236/8X4 12 M3 混凝土搅拌车 | primary | 1 | 12 | degraded |
| 2 | NX 340Hp 12Cubic Meters 混凝土搅拌车 | primary | 3 | 12 | degraded |
| 3 | 日野700 8×4 混凝土搅拌车 | primary | 4 | 16 | degraded |
| 4 | Ford GD10FD 混凝土搅拌车 | primary | 5 | 12 | degraded/citation_only |
| 5 | Arocs 4142 B 8x4 混凝土搅拌车 | primary | 6 | 20 | degraded |
| 6 | 重汽 12方混凝土搅拌车 | primary | 7 | 8 | degraded |
| 7 | 联合卡车 U系 QCC5312GJBD656N 混凝土搅拌车 | primary | 8 | 24 | degraded/citation_only |
| 8 | 利勃海尔 混凝土搅拌运输车（ZZ1317N306GD1B底盘） | backup | 13 | 24 | degraded/citation_only |
| 9 | 徐工XZS5310GJBBM1Z混凝土搅拌运输车 | primary | 9 | 24 | — |
| 10 | 凌宇CLY5316GJB30E55混凝土搅拌运输车 | primary | 10 | 24 | — |
| 11 | 山推建友CR412-06混凝土搅拌车 | primary | 11 | 20 | degraded |
| 12 | 解放CA5250GJBP66K22L1T1E平头柴油混凝土搅拌汽车 | backup | 14 | 20 | degraded |

**备选（随包）**：

- 1. 奔驰 Actros 搅拌车底盘（role=backup，rank=16，12 图）
- 2. HOWO NX 340马力 12方混凝土搅拌车（role=primary，rank=2，12 图）
- 3. JGC5271GJB混凝土搅拌输送车（role=primary，rank=12，20 图）
- 4. 沃尔沃 FM 搅拌车底盘（role=backup，rank=15，24 图）

## 二、内部监控（不对用户）

- 下载：hits 360 / downloaded 328 / failed 32 / blocked 0 / gate_pass 288
- 缺图归因：not_delivered 4
- 总耗时：208889 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 26234 |
| FETCH | 94050 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 10172 |
| FETCH | 28727 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 19130 |
| FETCH | 30563 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3365 | ¥0.19 | **¥0.5265** |
| 全空闲 | ¥0.1683 | ¥0.19 | **¥0.3583** |

用量：输入 41294 tokens（按未命中计，偏保守）/ 输出 31743 / Search 8 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\s6-mixer\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\s6-mixer\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
