# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 2 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 徐工 CV83PDU | primary | 1 | 24 | — |
| 2 | CA510PD | primary | 2 | 12 | — |
| 3 | CA610D-8 | primary | 3 | 24 | — |
| 4 | HC 228D | primary | 4 | 12 | — |
| 5 | HAMM HC 系列 | primary | 5 | 18 | degraded/citation_only |
| 6 | XS223JE | primary | 6 | 24 | — |
| 7 | XS202J | primary | 7 | 30 | — |
| 8 | 徐工 XS262J | primary | 8 | 24 | — |
| 9 | XS143J | primary | 9 | 30 | — |
| 10 | BW213D-40 | primary | 11 | 30 | — |
| 11 | SR20MA单钢轮压路机 | primary | 12 | 24 | degraded |
| 12 | SRS200J | primary | 13 | 30 | — |
| 13 | 618A | primary | 14 | 18 | — |
| 14 | YZ(k)18C | backup | 15 | 30 | — |

**备选（随包）**：

- 1. SAKAI SV512T-F（role=backup，rank=17，6 图）
- 2. XS265HS（role=backup，rank=18，6 图）
- 3. LSS327（role=primary，rank=10，6 图）
- 4. 柳工 620H（role=backup，rank=16，30 图）

## 二、内部监控（不对用户）

- 下载：hits 606 / downloaded 492 / failed 96 / blocked 18 / gate_pass 390
- 缺图归因：not_delivered 5
- 总耗时：416533 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 46124 |
| FETCH | 218433 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 21039 |
| FETCH | 70319 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 15373 |
| FETCH | 45235 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2396 | ¥0.2 | **¥0.4396** |
| 全空闲 | ¥0.1198 | ¥0.2 | **¥0.3198** |

用量：输入 30389 tokens（按未命中计，偏保守）/ 输出 22356 / Search 6 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c5-roller\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
