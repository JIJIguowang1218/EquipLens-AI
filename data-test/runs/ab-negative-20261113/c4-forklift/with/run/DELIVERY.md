# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 3 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CPD30/35 | primary | 1 | 20 | — |
| 2 | 3.0T电动叉车（四轮平衡重款） | primary | 2 | 5 | degraded |
| 3 | EA系列（E25A） | primary | 3 | 10 | degraded/citation_only |
| 4 | EL25 | primary | 4 | 5 | — |
| 5 | FE系列四支点电动叉车 | primary | 5 | 5 | degraded |
| 6 | FE4P25N | primary | 6 | 30 | — |

**备选（随包）**：

- 1. EF320（role=backup，rank=8，5 图）
- 2. 4.0T电动叉车（四轮平衡重款）（role=backup，rank=9，15 图）
- 3. B18S-7（7系列）（role=pool，rank=11，5 图）
- 4. J4.0-5.5XN（role=pool，rank=14，10 图）

## 二、内部监控（不对用户）

- 下载：hits 360 / downloaded 275 / failed 85 / blocked 0 / gate_pass 145
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 7
- 总耗时：307780 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 38726 |
| FETCH | 32639 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 34800 |
| FETCH | 18188 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 32373 |
| FETCH | 42541 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 19807 |
| FETCH | 88692 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 14 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1861 | ¥0.17 | **¥0.3561** |
| 全空闲 | ¥0.0931 | ¥0.17 | **¥0.2631** |

用量：输入 29731 tokens（按未命中计，偏保守）/ 输出 15831 / Search 6 次 / Fetch 28 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c4-forklift\with\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c4-forklift\with\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c4-forklift\with\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
