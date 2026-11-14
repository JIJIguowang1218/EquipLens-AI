# 交付清单：run

> 任务单：`auto-20261114-024643` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 0 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CLH5320TQZS6 6×4 清障车 | primary | 1 | 7 | — |
| 2 | 重汽豪沃MAX 后双桥托吊连体清障车 CSC5250TQZZT6 | primary | 2 | 21 | degraded |
| 3 | 一汽解放 J6M 320马力 6X4 清障车(程力威牌)(CLW5250TQZC5) | primary | 3 | 35 | degraded |
| 4 | 解放6*4清障带吊机（程力威牌CLW5250TQZCQA型清障车） | primary | 4 | 21 | degraded |
| 5 | 中国重汽豪沃 HOWO 6x4 30吨重型平板拖车 | primary | 5 | 7 | degraded |
| 6 | 陕汽重卡 德龙新M3000 336马力 6X4 清障车（程力威牌）CLW5320TQZS5 | primary | 6 | 35 | — |

**备选（随包）**：

- 1. 东风商用车 天龙 260马力 6X4 清障车（江特牌）（role=backup，rank=7，14 图）
- 2. 重汽豪沃 HOWO-7 6X4 清障车（程力威牌）（role=backup，rank=8，28 图）
- 3. Sinotruk HOWO 道路清障车 CLW5250TQZZ（role=backup，rank=9，14 图）
- 4. Sinotruk HOWO 60吨道路清障车 ST5310TQZCZ（role=backup，rank=10，42 图）

## 二、内部监控（不对用户）

- 下载：hits 392 / downloaded 287 / failed 98 / blocked 7 / gate_pass 224
- 缺图归因：not_delivered 4
- 总耗时：133747 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 9886 |
| FETCH | 67517 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 5073 |
| FETCH | 10470 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6692 |
| FETCH | 34101 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2886 | ¥0.12 | **¥0.4086** |
| 全空闲 | ¥0.1443 | ¥0.12 | **¥0.2643** |

用量：输入 29779 tokens（按未命中计，偏保守）/ 输出 28630 / Search 6 次 / Fetch 18 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\h2-wrecker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\h2-wrecker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
