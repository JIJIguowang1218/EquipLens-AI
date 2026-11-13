# 交付清单：run

> 任务单：`auto-20261114-024759` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 6 · citation_only 5 · 备选 3 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CSJ5255JSQ6 随车起重运输车 | primary | 2 | 7 | degraded/citation_only |
| 2 | 曼恩TGS 6x4工程运输车 | backup | 9 | 35 | degraded |
| 3 | 沃尔沃VNX 300载货车 | backup | 11 | 35 | degraded/citation_only |
| 4 | CA5250JSQP62K1L5T1E6 | backup | 12 | 7 | degraded/citation_only |
| 5 | CA5252JSQP62K1L5T1E6 | pool | 14 | 21 | — |
| 6 | EQ5258JSQF1 随车起重运输车 | primary | 7 | 14 | degraded/citation_only |
| 7 | 宏昌天马牌HCM5240JSQDFV6型随车起重运输车 | primary | 8 | 42 | — |
| 8 | 东风EQ5253JSQZM随车起重运输车 | pool | 15 | 7 | degraded/citation_only |

**备选（随包）**：

- 1. CA5250JSQP62K1L7T3E6（role=primary，rank=4，28 图）
- 2. 豪泺ZZ1317M4661V重型载货车及底盘（role=backup，rank=10，14 图）
- 3. CA5251JSQP62K1L5T1E6（role=pool，rank=13，42 图）

## 二、内部监控（不对用户）

- 下载：hits 574 / downloaded 322 / failed 84 / blocked 60 / gate_pass 259
- 缺图归因：all_download_failed 4 / not_delivered 3
- 总耗时：147173 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 3132 |
| FETCH | 71444 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2062 |
| FETCH | 34741 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 557 |
| FETCH | 13778 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 5590 |
| FETCH | 15860 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3393 | ¥0.14 | **¥0.4793** |
| 全空闲 | ¥0.1696 | ¥0.14 | **¥0.3096** |

用量：输入 43378 tokens（按未命中计，偏保守）/ 输出 31565 / Search 8 次 / Fetch 20 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\h4-crane-truck\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\h4-crane-truck\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
