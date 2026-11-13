# 交付清单：run

> 任务单：`auto-20261114-024759` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 6 · citation_only 4 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CSJ5255JSQ6 | primary | 2 | 7 | degraded/citation_only |
| 2 | 宏昌天马牌HCM5240JSQDFV6型随车起重运输车 | primary | 4 | 42 | — |
| 3 | 解放牌 CA5250JSQP28K2L5T1E6A81 随车起重运输车 | primary | 5 | 35 | degraded/citation_only |
| 4 | 解放牌 CA5315JSQP26K15L7T4E6A81 随车起重运输车 | backup | 10 | 35 | — |
| 5 | 东风EQ5250JSQT12随车起重运输车 | backup | 11 | 21 | degraded |
| 6 | TGS 6x4 工程牵引车 | pool | 13 | 42 | degraded |
| 7 | 豪泺 ZZ1317M4661V 重型载货车及底盘 | pool | 14 | 28 | degraded/citation_only |
| 8 | VNX 重型卡车（VNX 300 / VNX 440） | pool | 15 | 42 | degraded/citation_only |

**备选（随包）**：

- 1. 豪沃金标TX 前四后八平板运输车（role=pool，rank=16，42 图）
- 2. XFC 工程牵引车（前桥静液压驱动）（role=pool，rank=18，35 图）
- 3. CA5250JSQP62K1L7T3E6（role=primary，rank=8，28 图）
- 4. CA5240JSQP62K1L5T1E6（role=backup，rank=9，14 图）

## 二、内部监控（不对用户）

- 下载：hits 798 / downloaded 504 / failed 126 / blocked 94 / gate_pass 455
- 缺图归因：all_download_failed 3 / gate_or_verify_rejected 2 / not_delivered 7
- 总耗时：304304 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7485 |
| FETCH | 107751 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6560 |
| FETCH | 74366 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1158 |
| FETCH | 19602 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1488 |
| FETCH | 27254 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 27859 |
| FETCH | 30765 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3797 | ¥0.22 | **¥0.5997** |
| 全空闲 | ¥0.1898 | ¥0.22 | **¥0.4098** |

用量：输入 53738 tokens（按未命中计，偏保守）/ 输出 34027 / Search 10 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\evals\fulltest-20261114\h4-crane-truck\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\p8b-topup4-20261114\h4-crane-truck\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
