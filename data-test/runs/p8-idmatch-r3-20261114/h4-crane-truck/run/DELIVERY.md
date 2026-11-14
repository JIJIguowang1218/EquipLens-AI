# 交付清单：run

> 任务单：`auto-20261114-024759` · 主 8 台 + 备选 4 台 · 状态 FAILED
> 交付 7/8 · degraded 4 · citation_only 4 · 备选 0 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 漢風 XG1-DM270I 随车起重机（整车 XGA5250JSQN6） | primary | 1 | 14 | degraded/citation_only |
| 2 | 尚骏牌 CSJ5255JSQ6 随车起重运输车 | primary | 2 | 35 | — |
| 3 | 宏昌天马牌 HCM5240JSQDFV6 随车起重运输车 | primary | 3 | 28 | — |
| 4 | CA5250JSQP62K1L7T3E6 随车起重运输车 | primary | 4 | 21 | degraded/citation_only |
| 5 | ABC5246JSQCA6 随车起重运输车 | primary | 6 | 28 | degraded/citation_only |
| 6 | 华菱星马随车吊专用底盘（汉马动力+H6 驾驶室） | primary | 7 | 42 | degraded/citation_only |
| 7 | CA1260P2K1T1 | primary | 8 | 7 | — |

## 二、内部监控（不对用户）

- 下载：hits 308 / downloaded 210 / failed 56 / blocked 42 / gate_pass 182
- 缺图归因：gate_or_verify_rejected 1
- 总耗时：106842 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 8471 |
| FETCH | 68504 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 5492 |
| FETCH | 24367 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3291 | ¥0.1 | **¥0.4291** |
| 全空闲 | ¥0.1645 | ¥0.1 | **¥0.2645** |

用量：输入 43345 tokens（按未命中计，偏保守）/ 输出 30296 / Search 8 次 / Fetch 12 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\h4-crane-truck\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\h4-crane-truck\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
