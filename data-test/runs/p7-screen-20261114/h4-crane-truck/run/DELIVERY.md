# 交付清单：run

> 任务单：`auto-20261114-024759` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 5 · citation_only 4 · 备选 2 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | XG1-DM270I 随车起重机 | primary | 1 | 28 | — |
| 2 | HCM5240JSQDFV6 | primary | 2 | 7 | — |
| 3 | 尚骏牌 CSJ5255JSQ6 | primary | 3 | 35 | — |
| 4 | 解放牌 CSJ5257JSQ6A81 | primary | 4 | 28 | degraded/citation_only |
| 5 | EQ5258JSQF1 随车起重运输车 | primary | 5 | 14 | degraded/citation_only |
| 6 | CSJ5241JSQ6A90 随车起重运输车 | backup | 9 | 14 | degraded/citation_only |
| 7 | 曼恩 TGS 6x4 | backup | 10 | 28 | degraded |
| 8 | 豪泺 ZZ1317M4661V 重型载货车及底盘 | backup | 11 | 28 | degraded/citation_only |

**备选（随包）**：

- 1. 沃尔沃 VNX 载货车（role=backup，rank=12，14 图）
- 2. CA5250JSQP62K1L7T3E6 随车起重运输车（role=primary，rank=8，14 图）

## 二、内部监控（不对用户）

- 下载：hits 490 / downloaded 315 / failed 95 / blocked 12 / gate_pass 217
- 缺图归因：all_download_failed 2 / not_delivered 2
- 总耗时：143775 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 10966 |
| FETCH | 77688 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 3168 |
| FETCH | 13883 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7307 |
| FETCH | 20681 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 3663 |
| FETCH | 6410 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3781 | ¥0.14 | **¥0.5181** |
| 全空闲 | ¥0.189 | ¥0.14 | **¥0.329** |

用量：输入 43338 tokens（按未命中计，偏保守）/ 输出 36422 / Search 8 次 / Fetch 20 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\h4-crane-truck\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\h4-crane-truck\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
