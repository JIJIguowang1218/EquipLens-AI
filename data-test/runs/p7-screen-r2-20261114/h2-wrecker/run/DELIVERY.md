# 交付清单：run

> 任务单：`auto-20261114-024643` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 5 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 重汽豪沃6*4拖吊连体清障车（HCQ525） | primary | 1 | 35 | degraded |
| 2 | 解放6*4清障带吊机（程力威牌CLW5250TQZCQA型清障车） | primary | 2 | 21 | degraded |
| 3 | 一汽解放 J6M 320马力 6X4 清障车(程力威牌)(CLW5250TQZC5) | primary | 4 | 35 | degraded |
| 4 | CA5250JSQP62K1L7T3E6 | backup | 8 | 28 | degraded/citation_only |
| 5 | 德龙新M3000 6X4 清障车（CLW5320TQZS5） | primary | 5 | 42 | — |
| 6 | 东风天龙 6X4 清障车（江特牌） | primary | 6 | 35 | degraded |

**备选（随包）**：

- 1. CLH5320TQZS6 6×4 清障车（role=pool，rank=12，7 图）
- 2. HOWO-7 6X4 清障车（role=pool，rank=13，21 图）
- 3. ST5310TQZCZ（role=backup，rank=9，28 图）
- 4. HOWO NX RLQ5230TQZ6（role=backup，rank=10，14 图）

## 二、内部监控（不对用户）

- 下载：hits 532 / downloaded 385 / failed 60 / blocked 47 / gate_pass 322
- 缺图归因：all_download_failed 2 / gate_or_verify_rejected 1 / not_delivered 5
- 总耗时：215702 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 3808 |
| FETCH | 46143 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 15368 |
| FETCH | 72863 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 3677 |
| FETCH | 21206 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 3366 |
| FETCH | 49260 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3729 | ¥0.14 | **¥0.5129** |
| 全空闲 | ¥0.1865 | ¥0.14 | **¥0.3265** |

用量：输入 29920 tokens（按未命中计，偏保守）/ 输出 39135 / Search 6 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\h2-wrecker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\h2-wrecker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
