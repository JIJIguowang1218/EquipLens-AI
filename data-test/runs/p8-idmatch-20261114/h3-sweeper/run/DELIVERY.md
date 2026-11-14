# 交付清单：run

> 任务单：`auto-20261114-025547` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 2 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | QDT5074TSLH5 扫路车 | primary | 2 | 5 | — |
| 2 | HHR5080TXS4JH 扫路车 | primary | 3 | 5 | degraded/citation_only |
| 3 | 东风天锦国四道路清扫车 EQ5160TXS4 | primary | 4 | 15 | — |
| 4 | 中联重科ZBH5073TSUXE6湿式扫路车 | backup | 7 | 30 | degraded/citation_only |
| 5 | ZLJ5063TSLHE3 | backup | 8 | 25 | — |
| 6 | ZLJ5100TSLE3/E4 | backup | 9 | 15 | — |

**备选（随包）**：

- 1. 长安2700扫路车（role=backup，rank=10，15 图）
- 2. ZHF5060TSL（role=pool，rank=11，15 图）
- 3. ZLJ5163TSLE3/E4（role=pool，rank=12，20 图）
- 4. 盈峰环境ZLJ5163TSLE3/E4清扫机（role=pool，rank=13，25 图）

## 二、内部监控（不对用户）

- 下载：hits 335 / downloaded 240 / failed 60 / blocked 35 / gate_pass 210
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 5
- 总耗时：142059 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 12680 |
| FETCH | 59846 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6615 |
| FETCH | 25687 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5516 |
| FETCH | 31703 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2753 | ¥0.13 | **¥0.4053** |
| 全空闲 | ¥0.1377 | ¥0.13 | **¥0.2677** |

用量：输入 32984 tokens（按未命中计，偏保守）/ 输出 26169 / Search 6 次 / Fetch 20 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\h3-sweeper\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\h3-sweeper\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
