# 交付清单：run

> 任务单：`auto-20261114-024559` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 7 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 五十铃700P QL1110ANKAY 4×2水罐/泡沫消防车 | primary | 1 | 24 | degraded |
| 2 | HOWO 泡沫消防车 HXF5200GXFPM80（程力威牌上装） | primary | 3 | 18 | degraded/citation_only |
| 3 | 曼恩 TGM18.290B6 4x2 泡沫/水罐消防车（QHV5170GXFPM60/M6、QHV5160GXFSG60/M6） | primary | 4 | 36 | — |
| 4 | 中联重科ZLJ5160GXFPM40泡沫水罐消防车 | primary | 5 | 30 | degraded |
| 5 | 中国重汽HOWO 266马力4X2泡沫消防车（上格牌） | backup | 9 | 36 | degraded |
| 6 | 五十铃GIGA 8立方米水泡沫消防车 | backup | 10 | 36 | degraded |
| 7 | CSC5160GXFSG/PM70/E6 水罐/泡沫消防车 | backup | 11 | 24 | degraded/citation_only |
| 8 | Sinotruk HOWO 4X2 8cbm 泡沫消防车 | pool | 13 | 36 | degraded |

**备选（随包）**：

- 1. 中国重汽 HOWO 266马力 4X2 消防车（SGX5191GXFPM80）（role=pool，rank=14，18 图）
- 2. Shacman 4X2 水罐/泡沫罐消防车（role=pool，rank=15，30 图）
- 3. 克洛威 3500升 4*2 泡沫水罐消防车（role=pool，rank=16，12 图）
- 4. 4000L 4*2 水和泡沫罐消防车（role=pool，rank=17，12 图）

## 二、内部监控（不对用户）

- 下载：hits 426 / downloaded 396 / failed 26 / blocked 0 / gate_pass 324
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / not_delivered 4
- 总耗时：129507 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2798 |
| FETCH | 35137 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 9334 |
| FETCH | 27187 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 14331 |
| FETCH | 40711 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2947 | ¥0.17 | **¥0.4647** |
| 全空闲 | ¥0.1474 | ¥0.17 | **¥0.3174** |

用量：输入 31665 tokens（按未命中计，偏保守）/ 输出 28922 / Search 6 次 / Fetch 28 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\h1-fire\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\h1-fire\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
