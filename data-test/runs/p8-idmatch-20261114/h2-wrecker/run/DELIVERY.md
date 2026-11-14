# 交付清单：run

> 任务单：`auto-20261114-024643` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 5 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 重汽豪沃6*4拖吊连体清障车（华通牌） | primary | 1 | 35 | degraded |
| 2 | 重汽豪沃MAX 后双桥托吊连体清障车(CSC5250TQZZT6) | primary | 3 | 7 | degraded |
| 3 | 一汽解放 J6M 320马力 6X4 清障车（程力威牌） | backup | 8 | 28 | degraded |
| 4 | 东风商用车 天龙 260马力 6X4 清障车(江特牌) | backup | 9 | 14 | degraded |
| 5 | FAW 6×4 吊车清障车 CA5250JSQP62K1L7T3E6 | primary | 5 | 14 | degraded/citation_only |
| 6 | 陕汽重卡 德龙新M3000 336马力 6X4 清障车(程力威牌)(CLW5320TQZS5) | primary | 6 | 35 | — |

**备选（随包）**：

- 1. 一汽解放 J6M 320马力 6X4 清障车(程力威牌)(CLW5250TQZC5)（role=pool，rank=12，28 图）
- 2. 重汽豪沃 HOWO-7 6X4 清障车(程力威牌)（role=pool，rank=13，14 图）
- 3. 陕汽重卡 德龙新M3000 6X4 清障车（role=pool，rank=14，21 图）
- 4. HOWO 6x4 30吨重型平板清障车（role=primary，rank=4，28 图）

## 二、内部监控（不对用户）

- 下载：hits 560 / downloaded 322 / failed 130 / blocked 40 / gate_pass 287
- 缺图归因：all_download_failed 2 / gate_or_verify_rejected 1 / not_delivered 5
- 总耗时：302858 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 11806 |
| FETCH | 67294 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 11578 |
| FETCH | 77015 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1150 |
| FETCH | 23084 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5469 |
| FETCH | 105447 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2789 | ¥0.13 | **¥0.4089** |
| 全空闲 | ¥0.1395 | ¥0.13 | **¥0.2695** |

用量：输入 29862 tokens（按未命中计，偏保守）/ 输出 27403 / Search 6 次 / Fetch 20 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\h2-wrecker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\h2-wrecker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
