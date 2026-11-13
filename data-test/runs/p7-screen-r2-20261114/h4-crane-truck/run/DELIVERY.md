# 交付清单：run

> 任务单：`auto-20261114-024759` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 5 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | XG1-DM270I 随车起重机 | primary | 1 | 28 | — |
| 2 | HCM5240JSQDFV6 | primary | 2 | 7 | — |
| 3 | 尚骏牌 CSJ5255JSQ6 随车起重运输车 | primary | 3 | 35 | — |
| 4 | 东风EQ5253JSQZM随车起重运输车 | primary | 5 | 7 | degraded/citation_only |
| 5 | 解放牌 CA5251JSQP62K1L5T1E6 随车起重运输车 | backup | 9 | 21 | degraded |
| 6 | TGS 6x4 工程运输车（牵引车状态改装） | backup | 12 | 42 | degraded |
| 7 | 解放 CA5250JSQP62K1L7T3A1E5 随车起重运输车 | pool | 13 | 42 | degraded/citation_only |
| 8 | 豪沃TX 前四后八平板运输车（工程机械运输车） | pool | 14 | 28 | degraded |

**备选（随包）**：

- 1. Arocs 4148 8x8 铺路车（FAUN Trackway 上装）（role=pool，rank=15，42 图）
- 2. XFC 工程牵引车（前桥静液压驱动）（role=pool，rank=16，35 图）
- 3. 解放牌 CA5250JSQP62K1L5T1E6 随车起重运输车（role=primary，rank=8，28 图）
- 4. 移动式汽车维修保养工程车（随车吊）（role=backup，rank=11，7 图）

## 二、内部监控（不对用户）

- 下载：hits 644 / downloaded 413 / failed 140 / blocked 85 / gate_pass 322
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 3 / not_delivered 4
- 总耗时：186282 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7327 |
| FETCH | 71481 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2397 |
| FETCH | 36349 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 977 |
| FETCH | 22322 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 21162 |
| FETCH | 24256 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3457 | ¥0.16 | **¥0.5057** |
| 全空闲 | ¥0.1729 | ¥0.16 | **¥0.3329** |

用量：输入 43378 tokens（按未命中计，偏保守）/ 输出 32369 / Search 8 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\h4-crane-truck\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\h4-crane-truck\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
