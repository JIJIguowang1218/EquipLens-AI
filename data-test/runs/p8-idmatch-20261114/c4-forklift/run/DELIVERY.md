# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 3 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 恒叉 EF320 四轮单驱平衡重电动叉车 | primary | 1 | 20 | — |
| 2 | 尤恩 FE系列四支点电动叉车 | primary | 2 | 5 | degraded/citation_only |
| 3 | 扬子 CPD40-50B 四轮座驾式电动叉车 | primary | 3 | 25 | degraded/citation_only |
| 4 | Nissan Forklift MXS series 四轮电动平衡重叉车 | primary | 4 | 10 | degraded |
| 5 | CPD30/35 | primary | 6 | 20 | — |
| 6 | CPD40-40B | backup | 7 | 20 | — |

**备选（随包）**：

- 1. J4.0-5.5XN（role=backup，rank=8，10 图）
- 2. CPD50-B（role=backup，rank=9，5 图）
- 3. E-T50（role=backup，rank=10，10 图）
- 4. J1.6-2.0XN（role=pool，rank=12，25 图）

## 二、内部监控（不对用户）

- 下载：hits 295 / downloaded 225 / failed 70 / blocked 0 / gate_pass 170
- 缺图归因：gate_or_verify_rejected 2 / not_delivered 4
- 总耗时：137767 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 24316 |
| FETCH | 30857 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 3991 |
| FETCH | 12162 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1004 |
| FETCH | 17124 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7466 |
| FETCH | 40837 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2094 | ¥0.15 | **¥0.3594** |
| 全空闲 | ¥0.1047 | ¥0.15 | **¥0.2547** |

用量：输入 30750 tokens（按未命中计，偏保守）/ 输出 18493 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c4-forklift\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
