# 交付清单：run

> 任务单：`auto-20261114-024559` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 6 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | PM75 多功能水罐泡沫消防车 | primary | 1 | 12 | — |
| 2 | CSC5160GXFSG/PM70/E6 水罐/泡沫消防车 | primary | 2 | 30 | degraded/citation_only |
| 3 | 中联重科ZLJ5160GXFPM40泡沫水罐消防车 | primary | 3 | 30 | degraded |
| 4 | 曼恩 TGM18.290B6 4x2 水罐/泡沫消防车（QHV5170GXFPM60/M6） | primary | 4 | 30 | — |
| 5 | 福田瑞沃水罐泡沫消防车 CLW5160GXFSG60 | primary | 5 | 30 | degraded/citation_only |
| 6 | 川消牌 泡沫消防车 SXF5090GXFPM35（东风商用车底盘） | primary | 6 | 36 | degraded |
| 7 | 五十铃 4x2 泡沫消防车 QL1160AMFRY | primary | 7 | 6 | degraded |
| 8 | GIGA 8立方米水泡沫消防车 | primary | 8 | 12 | degraded/citation_only |

**备选（随包）**：

- 1. P310 城市主战消防车（role=backup，rank=9，30 图）
- 2. 中国重汽 泡沫消防车（4×2 可选驱动型式）（role=backup，rank=10，6 图）
- 3. 中国重汽HOWO 4X2泡沫消防车（上格牌）（role=backup，rank=11，36 图）
- 4. 梅赛德斯-奔驰Atego 1330 4×2压缩空气泡沫消防车（role=backup，rank=12，18 图）

## 二、内部监控（不对用户）

- 下载：hits 390 / downloaded 360 / failed 30 / blocked 0 / gate_pass 306
- 缺图归因：not_delivered 5
- 总耗时：166131 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22784 |
| FETCH | 37262 |
| VERIFY | 9 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1865 |
| FETCH | 17424 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 8286 |
| FETCH | 78495 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3045 | ¥0.16 | **¥0.4645** |
| 全空闲 | ¥0.1523 | ¥0.16 | **¥0.3123** |

用量：输入 31540 tokens（按未命中计，偏保守）/ 输出 30181 / Search 6 次 / Fetch 26 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\h1-fire\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\h1-fire\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
