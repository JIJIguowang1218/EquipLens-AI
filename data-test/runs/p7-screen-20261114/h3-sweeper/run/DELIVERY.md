# 交付清单：run

> 任务单：`auto-20261114-025547` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 东风天锦扫路车EQ5160TXS4 | primary | 1 | 25 | — |
| 2 | 中联重科 ZLJ5064TSLE3 扫路车 | primary | 2 | 15 | degraded |
| 3 | 恒润高科 HHR5072TSL3QL 扫路车 | primary | 3 | 30 | degraded |
| 4 | 中联重科ZBH5073TSUXE6湿式扫路车 | primary | 4 | 30 | degraded/citation_only |
| 5 | 青特 QDT5074TSLH5 干湿两用扫路车 | primary | 5 | 15 | degraded |
| 6 | 长安2700扫路车 | primary | 6 | 15 | — |

**备选（随包）**：

- 1. 东风D9（多利卡D9）扫路车（role=backup，rank=9，5 图）
- 2. 盈峰环境ZLJ5163TSLE3/E4清扫机（role=backup，rank=10，25 图）
- 3. 恒润高科 HHR5080TXS4JH 扫路车（role=backup，rank=7，5 图）
- 4. 华通牌HCQ5083TSLJX5扫路车（江铃凯锐N800）（role=backup，rank=8，20 图）

## 二、内部监控（不对用户）

- 下载：hits 285 / downloaded 225 / failed 50 / blocked 10 / gate_pass 195
- 缺图归因：not_delivered 4
- 总耗时：98875 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 12996 |
| FETCH | 31255 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 4175 |
| FETCH | 14685 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5426 |
| FETCH | 30331 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2289 | ¥0.12 | **¥0.3489** |
| 全空闲 | ¥0.1145 | ¥0.12 | **¥0.2345** |

用量：输入 32953 tokens（按未命中计，偏保守）/ 输出 20375 / Search 6 次 / Fetch 18 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\h3-sweeper\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\h3-sweeper\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
