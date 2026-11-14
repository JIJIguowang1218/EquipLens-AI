# 交付清单：run

> 任务单：`source-expansion-mixer-20261111` · 主 12 台 + 备选 4 台 · 状态 DONE
> 交付 12/12 · degraded 10 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 富鑫 12方 8*4 混凝土搅拌车（重汽底盘） | primary | 1 | 20 | degraded |
| 2 | Mercedes-Benz AXOR 3236 8×4 12m³ 混凝土搅拌车 | primary | 2 | 8 | degraded |
| 3 | HOWO NX 340Hp 12Cubic Meters 混凝土搅拌车 | primary | 3 | 20 | degraded |
| 4 | 解放平头柴油混凝土搅拌车（12立方规格） | primary | 4 | 20 | degraded/citation_only |
| 5 | 山推建友CR412-06混凝土搅拌车 | primary | 5 | 20 | degraded |
| 6 | 日野700 8x4 混凝土搅拌车 | primary | 6 | 16 | degraded |
| 7 | Mercedes-Benz Arocs 4142 B 8×4 混凝土搅拌车 | primary | 7 | 4 | degraded |
| 8 | Ford GD10FD 8x4 混凝土搅拌车 | primary | 8 | 8 | degraded |
| 9 | 陕汽F3000 16方混凝土搅拌车 | primary | 9 | 24 | — |
| 10 | 中国重汽豪泺 HOWO 混凝土搅拌运输车 | primary | 11 | 20 | degraded |
| 11 | 中国重汽汕德卡 SITRAK 混凝土搅拌运输车 | primary | 12 | 4 | degraded |
| 12 | 豪瀚ZZ5315GJBN3063E1B混凝土搅拌运输车 | backup | 13 | 24 | — |

**备选（随包）**：

- 1. 豪瀚ZZ5315GJBN3063E1混凝土搅拌运输车（role=backup，rank=14，4 图）
- 2. 中联 QDZ5313GJBZDC30F1 混凝土搅拌车（role=backup，rank=16，24 图）
- 3. 仁拓博歌 ZBG5312GJB30F7 混凝土搅拌车（role=pool，rank=17，24 图）
- 4. 奔驰 Actros 工程版搅拌车底盘（role=pool，rank=19，12 图）

## 二、内部监控（不对用户）

- 下载：hits 532 / downloaded 444 / failed 80 / blocked 8 / gate_pass 408
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 10
- 总耗时：299080 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 11580 |
| FETCH | 70336 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 22398 |
| FETCH | 95841 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 24521 |
| FETCH | 23909 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 13290 |
| FETCH | 37196 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.4712 | ¥0.25 | **¥0.7212** |
| 全空闲 | ¥0.2356 | ¥0.25 | **¥0.4856** |

用量：输入 41282 tokens（按未命中计，偏保守）/ 输出 48575 / Search 8 次 / Fetch 42 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\s6-mixer\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\s6-mixer\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
