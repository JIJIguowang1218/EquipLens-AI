# 交付清单：run

> 任务单：`auto-20261114-025547` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 0 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 中联重科 ZLJ5064TSLE3 扫路车 | primary | 1 | 15 | degraded |
| 2 | 恒润高科 HHR5080TXS4JH 扫路车 | primary | 2 | 15 | degraded |
| 3 | 青特 QDT5074TSLH5 干湿两用扫路车 | primary | 3 | 15 | degraded |
| 4 | ZLJ5063TSLHE3 | primary | 4 | 20 | — |
| 5 | HHR5060TSL | primary | 5 | 5 | — |
| 6 | 东风大多利卡 8吨扫路车（2.5水/5尘） | primary | 6 | 20 | degraded |

**备选（随包）**：

- 1. 长安蓝牌扫路车（4×2 底盘）（role=backup，rank=7，20 图）
- 2. ZHF5060TSL（role=backup，rank=8，20 图）
- 3. 五十铃扫路车（5吨）（role=backup，rank=9，20 图）
- 4. 中联重科ZBH5073TSUXE6湿式扫路车（role=backup，rank=10，30 图）

## 二、内部监控（不对用户）

- 下载：hits 275 / downloaded 195 / failed 70 / blocked 10 / gate_pass 185
- 缺图归因：not_delivered 4
- 总耗时：145156 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2482 |
| FETCH | 26545 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 10415 |
| FETCH | 56119 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 15976 |
| FETCH | 33613 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2739 | ¥0.12 | **¥0.3939** |
| 全空闲 | ¥0.137 | ¥0.12 | **¥0.257** |

用量：输入 32982 tokens（按未命中计，偏保守）/ 输出 25995 / Search 6 次 / Fetch 18 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\h3-sweeper\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\h3-sweeper\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
