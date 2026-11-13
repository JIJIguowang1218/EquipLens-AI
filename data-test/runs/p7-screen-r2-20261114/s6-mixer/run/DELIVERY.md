# 交付清单：run

> 任务单：`source-expansion-mixer-20261111` · 主 12 台 + 备选 4 台 · 状态 DONE
> 交付 12/12 · degraded 10 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | AXOR 3236 8X4 12 M3 混凝土搅拌车 | primary | 1 | 12 | degraded |
| 2 | Arocs 4142 B 8x4 混凝土搅拌车 | primary | 2 | 20 | degraded |
| 3 | HOWO NX 340Hp 12Cubic Meters Concrete Mixer Truck | primary | 3 | 8 | degraded |
| 4 | 解放 平头柴油混凝土搅拌车（12方规格） | primary | 4 | 8 | degraded |
| 5 | 日野700 8×4 混凝土搅拌车 | primary | 5 | 16 | degraded |
| 6 | Ford GD10FD 8×4 混凝土搅拌车 | primary | 6 | 12 | degraded/citation_only |
| 7 | 江淮 HFC5255GJBLK3 后八轮混凝土搅拌车 | primary | 7 | 12 | degraded |
| 8 | 重汽12方搅拌车 | primary | 8 | 8 | degraded |
| 9 | 陕汽12方搅拌车 | primary | 9 | 8 | — |
| 10 | 福田12方搅拌车 | primary | 10 | 16 | degraded |
| 11 | 富鑫12方搅拌车 | primary | 12 | 16 | — |
| 12 | 联合卡车U380 8X4 混凝土搅拌车 | backup | 13 | 8 | degraded |

**备选（随包）**：

- 1. NX 340Hp 12Cubic Meters 混凝土搅拌车（role=backup，rank=14，12 图）
- 2. 豪瀚 ZZ5315GJBN3063E1B 混凝土搅拌运输车（role=backup，rank=15，24 图）
- 3. 山推建友 CR412-06 混凝土搅拌车（role=backup，rank=16，20 图）
- 4. 豪瀚 ZZ5315GJBN3063E1 混凝土搅拌运输车（role=pool，rank=17，12 图）

## 二、内部监控（不对用户）

- 下载：hits 492 / downloaded 384 / failed 60 / blocked 48 / gate_pass 304
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 8
- 总耗时：208576 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 15996 |
| FETCH | 75921 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 0 |
| FETCH | 17654 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 9157 |
| FETCH | 38066 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 15345 |
| FETCH | 36423 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3524 | ¥0.2 | **¥0.5524** |
| 全空闲 | ¥0.1762 | ¥0.2 | **¥0.3762** |

用量：输入 41426 tokens（按未命中计，偏保守）/ 输出 33693 / Search 8 次 / Fetch 32 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\s6-mixer\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\s6-mixer\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
