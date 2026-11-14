# 交付清单：run

> 任务单：`auto-20261114-024643` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 5 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 重汽豪沃 6*4 拖吊连体清障车（华通牌 HCQ525） | primary | 1 | 28 | degraded |
| 2 | 解放 6*4 清障带吊机（程力威牌 CLW5250TQZCQA） | primary | 2 | 28 | degraded |
| 3 | 重汽豪沃MAX 后双桥托吊连体清障车 | primary | 4 | 28 | degraded |
| 4 | 东风天龙 6X4 清障车(江特牌) | backup | 7 | 35 | degraded |
| 5 | 德龙新M3000 6X4 清障车(程力威牌) | backup | 8 | 21 | — |
| 6 | 一汽 6×4 吊车清障车（CA5250JSQP62K1L7T3E6） | backup | 9 | 35 | degraded/citation_only |

**备选（随包）**：

- 1. 中国重汽豪沃 ST5310TQZCZ 60t 清障车（role=backup，rank=10，28 图）
- 2. 重汽豪沃 HOWO-7 6X4 清障车(程力威牌)（role=pool，rank=11，28 图）
- 3. 解放J6M 6X4 清障车(程力威牌)（role=pool，rank=12，21 图）
- 4. 德龙新M3000 6X4 清障车 (CLW5320TQZS5)（role=pool，rank=14，35 图）

## 二、内部监控（不对用户）

- 下载：hits 462 / downloaded 336 / failed 76 / blocked 16 / gate_pass 301
- 缺图归因：all_download_failed 1 / not_delivered 5
- 总耗时：138444 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2893 |
| FETCH | 75566 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7844 |
| FETCH | 22695 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2177 |
| FETCH | 27259 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2753 | ¥0.14 | **¥0.4153** |
| 全空闲 | ¥0.1376 | ¥0.14 | **¥0.2776** |

用量：输入 29859 tokens（按未命中计，偏保守）/ 输出 26945 / Search 6 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\h2-wrecker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\h2-wrecker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
