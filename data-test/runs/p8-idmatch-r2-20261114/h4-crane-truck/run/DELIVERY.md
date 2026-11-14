# 交付清单：run

> 任务单：`auto-20261114-024759` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 4 · citation_only 2 · 备选 3 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | XG1-DM270I 随车起重机 | primary | 1 | 28 | — |
| 2 | HCM5240JSQDFV6 | primary | 2 | 7 | — |
| 3 | 尚骏牌 CSJ5255JSQ6 随车起重运输车 | primary | 3 | 35 | — |
| 4 | EQ5253JSQZM | primary | 5 | 7 | — |
| 5 | 随车吊专用底盘（HN1310C27D6M4J，可选汉马H6/华菱重卡驾驶室） | backup | 9 | 42 | degraded |
| 6 | 小三轴随车起重运输车（轴距2100+4850/2100+5250，可选直臂或折臂吊机） | backup | 10 | 14 | degraded |
| 7 | ABC5316JSQSX6型随车起重运输车 | backup | 11 | 7 | degraded/citation_only |
| 8 | CA1313P7K2L11T4A3E型专用8×4平头随车起重运输车底盘（双前轴距2150mm） | backup | 12 | 28 | degraded/citation_only |

**备选（随包）**：

- 1. EQ5258JSQF1（role=primary，rank=6，7 图）
- 2. CA5250JSQP62K1L7T3E6 随车起重运输车（role=primary，rank=7，14 图）
- 3. ABC5246JSQCA6 随车起重运输车（role=primary，rank=8，28 图）

## 二、内部监控（不对用户）

- 下载：hits 504 / downloaded 357 / failed 91 / blocked 56 / gate_pass 231
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 3
- 总耗时：127885 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7246 |
| FETCH | 66980 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 12096 |
| FETCH | 25612 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1837 |
| FETCH | 14108 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3489 | ¥0.14 | **¥0.4889** |
| 全空闲 | ¥0.1745 | ¥0.14 | **¥0.3145** |

用量：输入 43531 tokens（按未命中计，偏保守）/ 输出 32733 / Search 8 次 / Fetch 20 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\h4-crane-truck\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\h4-crane-truck\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
