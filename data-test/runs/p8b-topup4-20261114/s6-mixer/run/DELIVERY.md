# 交付清单：run

> 任务单：`source-expansion-mixer-20261111` · 主 12 台 + 备选 4 台 · 状态 DONE
> 交付 12/12 · degraded 10 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | AXOR 3236/8X4-E4-12 M3 CONCRETE MIXER | primary | 1 | 16 | degraded/citation_only |
| 2 | HOWO NX 340Hp 12Cubic Meters混凝土搅拌车 | primary | 2 | 20 | degraded |
| 3 | 解放 平头柴油混凝土搅拌车（12立方规格） | primary | 3 | 24 | degraded |
| 4 | 重汽12方搅拌车 | primary | 4 | 8 | degraded |
| 5 | Ford GD10FD 搅拌车 | primary | 6 | 12 | degraded/citation_only |
| 6 | 日野700 混凝土搅拌车 | primary | 7 | 16 | degraded |
| 7 | CR412-06混凝土搅拌车 | primary | 8 | 20 | degraded |
| 8 | 联合卡车U380 8X4混凝土搅拌车 | backup | 13 | 8 | degraded |
| 9 | ZLJ5312GJBHT5E | backup | 14 | 24 | degraded/citation_only |
| 10 | ZLJ5310GJBHTE | backup | 15 | 16 | — |
| 11 | 陕汽德龙F3000 搅拌车底盘 | backup | 16 | 12 | — |
| 12 | 奔驰Actros 搅拌车底盘 | pool | 18 | 12 | degraded |

**备选（随包）**：

- 1. 江淮 JAC 重卡后八轮混凝土搅拌车 HFC5255GJBLK3（role=primary，rank=9，16 图）
- 2. 解放 CA5250GJBP66K22L1T1E 平头柴油混凝土搅拌汽车（role=primary，rank=11，12 图）
- 3. 乘龙H7 LNG渣土车（role=pool，rank=19，24 图）
- 4. 福田瑞沃工程自卸车（金刚/大金刚ES/骁运）（role=pool，rank=20，20 图）

## 二、内部监控（不对用户）

- 下载：hits 436 / downloaded 384 / failed 52 / blocked 0 / gate_pass 344
- 缺图归因：no_hits 1 / not_delivered 7
- 总耗时：214657 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4896 |
| FETCH | 98060 |
| VERIFY | 7 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 12146 |
| FETCH | 61366 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1606 |
| FETCH | 36568 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.5406 | ¥0.22 | **¥0.7606** |
| 全空闲 | ¥0.2703 | ¥0.22 | **¥0.4903** |

用量：输入 50833 tokens（按未命中计，偏保守）/ 输出 54864 / Search 10 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\evals\source-expansion-briefs-20261111\mixer.json`（分析模块输入）
- 优先级先验：`data-test\runs\p8b-topup4-20261114\s6-mixer\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
