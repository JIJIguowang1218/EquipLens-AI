# 交付清单：run

> 任务单：`auto-20261114-025547` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 5 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 东风天锦扫路车 EQ5160TXS4 | primary | 1 | 25 | — |
| 2 | 中联重科 ZBH5073TSUXE6 湿式扫路车 | primary | 2 | 30 | degraded/citation_only |
| 3 | 恒润高科 HHR5080TXS4JH 扫路车 | primary | 3 | 10 | degraded |
| 4 | 福田2600mm扫路车（国V/国VI） | primary | 4 | 25 | degraded |
| 5 | 东风小多利卡扫路车（国VI） | primary | 5 | 10 | degraded |
| 6 | 中联重科 ZLJ5064TSLE3 扫路车 | primary | 6 | 15 | degraded |

**备选（随包）**：

- 1. 青特 QDT5074TSLH5 干湿两用扫路车（role=backup，rank=7，15 图）
- 2. XGH5040TSLSBEV 纯电动扫路车（role=backup，rank=9，25 图）
- 3. 盈峰环境 ZLJ5163TSLE3/E4 清扫机（role=pool，rank=11，30 图）
- 4. 福田2600mm扫路车国V（role=pool，rank=12，25 图）

## 二、内部监控（不对用户）

- 下载：hits 400 / downloaded 290 / failed 95 / blocked 15 / gate_pass 265
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 7
- 总耗时：139253 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1490 |
| FETCH | 23909 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 856 |
| FETCH | 9192 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7830 |
| FETCH | 61805 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1786 |
| FETCH | 32379 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3022 | ¥0.17 | **¥0.4722** |
| 全空闲 | ¥0.1511 | ¥0.17 | **¥0.3211** |

用量：输入 33162 tokens（按未命中计，偏保守）/ 输出 29485 / Search 6 次 / Fetch 28 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\h3-sweeper\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\h3-sweeper\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
