# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 0 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | EA系列 电动四轮平衡重式叉车 | primary | 1 | 5 | degraded |
| 2 | FE系列四支点电动叉车 | primary | 2 | 5 | degraded |
| 3 | H4（3吨）四轮平衡重式电动叉车 | primary | 3 | 5 | degraded |
| 4 | CPD30/35 | primary | 4 | 20 | — |
| 5 | 7系列 Plus 1.6-2吨四轮电动叉车 | backup | 8 | 10 | degraded |
| 6 | SE16/20 | backup | 9 | 10 | — |

**备选（随包）**：

- 1. FE4P25N（role=backup，rank=10，30 图）
- 2. 山猫 7 系列四轮电动叉车（1.5-1.8 吨、1.6-2 吨、2-3.2 吨等）（role=pool，rank=11，30 图）
- 3. EL25（role=pool，rank=13，5 图）
- 4. EF320（role=pool，rank=14，5 图）

## 二、内部监控（不对用户）

- 下载：hits 250 / downloaded 215 / failed 35 / blocked 0 / gate_pass 125
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / no_hits 1 / not_delivered 4
- 总耗时：219743 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 31633 |
| FETCH | 49972 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 9996 |
| FETCH | 20594 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 10129 |
| FETCH | 29590 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 13888 |
| FETCH | 17259 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1494 |
| FETCH | 35174 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 13 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2008 | ¥0.15 | **¥0.3508** |
| 全空闲 | ¥0.1004 | ¥0.15 | **¥0.2504** |

用量：输入 29629 tokens（按未命中计，偏保守）/ 输出 17697 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c4-forklift\without\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c4-forklift\without\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c4-forklift\without\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
