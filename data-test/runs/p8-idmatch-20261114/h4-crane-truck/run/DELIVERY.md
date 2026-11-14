# 交付清单：run

> 任务单：`auto-20261114-024759` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 7 · citation_only 7 · 备选 1 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | XG1-DM270I 随车起重机（整车型号 XGA5250JSQN6） | primary | 2 | 28 | degraded/citation_only |
| 2 | 尚骏牌 CSJ5255JSQ6 随车起重运输车 | primary | 3 | 35 | — |
| 3 | ABC5316JSQSX6 随车起重运输车 | primary | 5 | 7 | degraded/citation_only |
| 4 | ABC5246JSQCA6 随车起重运输车 | backup | 9 | 21 | degraded/citation_only |
| 5 | 宏昌天马 HCM5240JSQDFV6 | primary | 1 | 28 | degraded/citation_only |
| 6 | EQ5258JSQF1 随车起重运输车 | primary | 8 | 14 | degraded/citation_only |
| 7 | CA5250JSQP62K1L7T3E6 随车起重运输车 | primary | 4 | 14 | degraded/citation_only |
| 8 | CA5251JSQP62K1L5T1E6 随车起重运输车 | backup | 11 | 28 | degraded/citation_only |

**备选（随包）**：

- 1. 移动式汽车维修保养工程车（带随车吊）（role=pool，rank=13，21 图）

## 二、内部监控（不对用户）

- 下载：hits 546 / downloaded 280 / failed 85 / blocked 113 / gate_pass 231
- 缺图归因：all_download_failed 2 / gate_or_verify_rejected 2 / not_delivered 1
- 总耗时：147804 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 28889 |
| FETCH | 70669 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2027 |
| FETCH | 30145 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 4677 |
| FETCH | 11387 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3419 | ¥0.12 | **¥0.4619** |
| 全空闲 | ¥0.1709 | ¥0.12 | **¥0.2909** |

用量：输入 43452 tokens（按未命中计，偏保守）/ 输出 31872 / Search 8 次 / Fetch 16 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\h4-crane-truck\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\h4-crane-truck\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
