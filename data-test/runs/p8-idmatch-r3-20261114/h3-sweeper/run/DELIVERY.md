# 交付清单：run

> 任务单：`auto-20261114-025547` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 5 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 中联重科 ZLJ5064TSLE3 扫路车 | primary | 1 | 15 | degraded |
| 2 | 恒润高科 HHR5080TXS4JH 扫路车 | primary | 2 | 15 | degraded |
| 3 | 东风小多利卡扫路车 | primary | 4 | 20 | — |
| 4 | XGH5040TSLSBEV纯电动扫路车 | backup | 7 | 25 | degraded |
| 5 | 东风大多利卡8吨扫路车 | backup | 8 | 20 | degraded |
| 6 | XTV5030TSL6CA 扫路车 | backup | 9 | 5 | degraded/citation_only |

**备选（随包）**：

- 1. 长安2700 扫路车（国VI蓝牌）（role=pool，rank=11，15 图）
- 2. 江淮康铃扫路车（CLW 5立方）（role=pool，rank=12，15 图）
- 3. 五十铃扫路车（5吨）（role=pool，rank=13，20 图）
- 4. 东风途逸扫路车国VI蓝牌柴油机（role=pool，rank=14，25 图）

## 二、内部监控（不对用户）

- 下载：hits 350 / downloaded 205 / failed 103 / blocked 20 / gate_pass 195
- 缺图归因：all_download_failed 1 / not_delivered 5
- 总耗时：148181 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 14004 |
| FETCH | 59216 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 17859 |
| FETCH | 25296 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7728 |
| FETCH | 24074 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.269 | ¥0.15 | **¥0.419** |
| 全空闲 | ¥0.1345 | ¥0.15 | **¥0.2845** |

用量：输入 33167 tokens（按未命中计，偏保守）/ 输出 25328 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\h3-sweeper\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\h3-sweeper\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
