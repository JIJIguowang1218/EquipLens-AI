# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 4 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CPD40-40B | primary | 1 | 20 | — |
| 2 | 扬子 CPD40-50B | primary | 3 | 5 | degraded/citation_only |
| 3 | CPD30/35 | primary | 4 | 20 | — |
| 4 | 爵力 CPD40-B | backup | 8 | 20 | degraded/citation_only |
| 5 | 尤恩 FE系列四支点电动叉车 | backup | 9 | 10 | degraded/citation_only |
| 6 | E-T50 | backup | 10 | 10 | degraded/citation_only |

**备选（随包）**：

- 1. FE4P25N（role=pool，rank=15，30 图）
- 2. EL25（role=pool，rank=16，10 图）
- 3. J4.0-5.5XN（role=pool，rank=17，10 图）
- 4. Nissan MXS series（role=pool，rank=11，10 图）

## 二、内部监控（不对用户）

- 下载：hits 450 / downloaded 330 / failed 85 / blocked 13 / gate_pass 235
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / not_delivered 7
- 总耗时：214795 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 28659 |
| FETCH | 23154 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 36701 |
| FETCH | 40976 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5884 |
| FETCH | 28397 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 16257 |
| FETCH | 34763 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2003 | ¥0.19 | **¥0.3903** |
| 全空闲 | ¥0.1001 | ¥0.19 | **¥0.2901** |

用量：输入 30969 tokens（按未命中计，偏保守）/ 输出 17291 / Search 6 次 / Fetch 32 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r2-20261114\c4-forklift\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
