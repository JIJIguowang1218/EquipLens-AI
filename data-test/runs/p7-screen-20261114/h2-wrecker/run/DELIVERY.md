# 交付清单：run

> 任务单：`auto-20261114-024643` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 5 · citation_only 0 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 重汽豪沃MAX 后双桥托吊连体清障车 CSC5250TQZZT6 | primary | 1 | 21 | degraded |
| 2 | 重汽豪沃 6*4 拖吊连体清障车（华通牌 HCQ525） | primary | 2 | 28 | degraded |
| 3 | 解放 6*4 清障带吊机（程力威牌 CLW5250TQZCQA） | primary | 3 | 28 | degraded |
| 4 | 中国重汽 豪沃 6×4 带吊清障车（CL5251TQZ6ZQ） | backup | 7 | 21 | degraded |
| 5 | 程力牌 CL5251TQZ6BZQ 6×4 清障车（东风天龙底盘） | backup | 8 | 28 | — |
| 6 | 重汽豪沃后双桥拖吊连体清障车 CLW5250TQZZ6 | backup | 9 | 14 | degraded |

**备选（随包）**：

- 1. 陕汽重卡 德龙新M3000 336马力 6X4 清障车(程力威牌)（role=backup，rank=10，35 图）
- 2. 一汽解放 J6M 320马力 6X4 清障车(程力威牌)（role=pool，rank=11，28 图）
- 3. 重汽豪沃 HOWO-7 6X4 清障车(程力威牌)（role=pool，rank=12，28 图）
- 4. 东风商用车 天龙 260马力 6X4 清障车(江特牌)（role=pool，rank=13，14 图）

## 二、内部监控（不对用户）

- 下载：hits 490 / downloaded 329 / failed 95 / blocked 32 / gate_pass 294
- 缺图归因：all_download_failed 1 / not_delivered 5
- 总耗时：186492 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 17332 |
| FETCH | 73573 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 9600 |
| FETCH | 45365 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4767 |
| FETCH | 35845 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3762 | ¥0.14 | **¥0.5162** |
| 全空闲 | ¥0.1881 | ¥0.14 | **¥0.3281** |

用量：输入 39941 tokens（按未命中计，偏保守）/ 输出 37043 / Search 8 次 / Fetch 20 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\h2-wrecker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\h2-wrecker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
