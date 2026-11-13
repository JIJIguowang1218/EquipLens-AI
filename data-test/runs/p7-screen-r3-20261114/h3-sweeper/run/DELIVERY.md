# 交付清单：run

> 任务单：`auto-20261114-025547` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 3 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 中联重科 ZBH5073TSUXE6 湿式扫路车 | primary | 1 | 30 | degraded/citation_only |
| 2 | HHR5080TXS4JH 扫路车 | primary | 2 | 5 | degraded/citation_only |
| 3 | 长安2700扫路车（国VI蓝牌） | primary | 4 | 15 | degraded |
| 4 | QDT5074TSLH5 扫路车 | backup | 7 | 5 | — |
| 5 | 东风小多利卡扫路车 | backup | 8 | 20 | — |
| 6 | 东风大多利卡扫路车国VI | backup | 9 | 15 | — |

**备选（随包）**：

- 1. HHR5060TSL（role=backup，rank=10，10 图）
- 2. ZLJ5063TSLHE3（role=pool，rank=11，25 图）
- 3. ZHF5060TSL（role=pool，rank=12，20 图）
- 4. 东风途逸扫路车（role=pool，rank=14，25 图）

## 二、内部监控（不对用户）

- 下载：hits 360 / downloaded 220 / failed 80 / blocked 60 / gate_pass 190
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 5
- 总耗时：138822 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2170 |
| FETCH | 63827 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2609 |
| FETCH | 33320 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6391 |
| FETCH | 30499 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3338 | ¥0.15 | **¥0.4839** |
| 全空闲 | ¥0.1669 | ¥0.15 | **¥0.3169** |

用量：输入 32985 tokens（按未命中计，偏保守）/ 输出 33485 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\h3-sweeper\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\h3-sweeper\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
