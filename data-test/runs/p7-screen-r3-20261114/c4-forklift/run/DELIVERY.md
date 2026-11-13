# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 6 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CPD40-40B 四轮座驾式电动叉车 | primary | 1 | 25 | degraded |
| 2 | J4.0-5.5XN 四轮电动平衡重叉车 | primary | 3 | 15 | degraded/citation_only |
| 3 | FE4P25N 四轮座驾式电动叉车 | primary | 4 | 10 | degraded |
| 4 | CPD30/35 四轮座驾式电动叉车 | backup | 7 | 25 | degraded |
| 5 | CPD50-B 四轮电动叉车 | backup | 8 | 10 | degraded |
| 6 | E-T50 电动叉车 | backup | 9 | 10 | degraded/citation_only |

**备选（随包）**：

- 1. 海斯特 E80-120XN 四轮电动平衡重式叉车（role=pool，rank=13，15 图）
- 2. 恒叉 EF320 四轮单驱平衡重电动叉车（role=pool，rank=15，20 图）
- 3. 山猫 B18S-7 四轮电动叉车（role=pool，rank=17，20 图）
- 4. 尤恩 FE系列四支点电动叉车（role=backup，rank=10，10 图）

## 二、内部监控（不对用户）

- 下载：hits 365 / downloaded 295 / failed 65 / blocked 5 / gate_pass 250
- 缺图归因：gate_or_verify_rejected 3 / not_delivered 7
- 总耗时：256780 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2166 |
| FETCH | 75760 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2401 |
| FETCH | 32166 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6563 |
| FETCH | 29606 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 27413 |
| FETCH | 80695 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2118 | ¥0.19 | **¥0.4018** |
| 全空闲 | ¥0.1059 | ¥0.19 | **¥0.2959** |

用量：输入 30951 tokens（按未命中计，偏保守）/ 输出 18733 / Search 6 次 / Fetch 32 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c4-forklift\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
