# 交付清单：run

> 任务单：`auto-20261114-024559` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 7 · citation_only 5 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 3500升 4*2 泡沫水罐消防车 | primary | 1 | 12 | degraded |
| 2 | PM75多功能水罐泡沫消防车 | primary | 2 | 30 | degraded/citation_only |
| 3 | GIGA 8立方米水泡沫消防车 | primary | 3 | 12 | degraded/citation_only |
| 4 | CSC5160GXFSG/PM70/E6 水罐/泡沫消防车 | primary | 4 | 30 | degraded/citation_only |
| 5 | P310城市主战消防车 | primary | 5 | 36 | — |
| 6 | 曼恩 TGM18.290B6 4x2 泡沫消防车（QHV5170GXFPM60/M6） | primary | 6 | 30 | degraded |
| 7 | 福田瑞沃水罐泡沫消防车（CLW5160GXFSG60） | primary | 7 | 30 | degraded/citation_only |
| 8 | 4X2 Water & Foam Fire Engine | primary | 8 | 6 | degraded/citation_only |

**备选（随包）**：

- 1. 五十铃700P 4吨水罐/泡沫消防车（QL1110ANKAY）（role=backup，rank=9，36 图）
- 2. 中国重汽 HOWO 266马力 4X2 消防车（上格牌 SGX5191GXFPM80）（role=backup，rank=10，30 图）
- 3. 川消牌 SXF5090GXFPM35 泡沫消防车（东风商用车底盘）（role=backup，rank=11，24 图）
- 4. 中联重科 ZLJ5160GXFPM40 泡沫水罐消防车（role=backup，rank=12，30 图）

## 二、内部监控（不对用户）

- 下载：hits 408 / downloaded 342 / failed 66 / blocked 0 / gate_pass 318
- 缺图归因：not_delivered 5
- 总耗时：142948 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 12916 |
| FETCH | 56151 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 10319 |
| FETCH | 21174 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6234 |
| FETCH | 36142 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2874 | ¥0.15 | **¥0.4374** |
| 全空闲 | ¥0.1437 | ¥0.15 | **¥0.2937** |

用量：输入 31579 tokens（按未命中计，偏保守）/ 输出 28030 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\h1-fire\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\h1-fire\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
