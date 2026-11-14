# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 3 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 山猫B18S-7四轮电动叉车 | primary | 3 | 30 | degraded |
| 2 | 克拉克SE16/20四轮电动叉车 | primary | 4 | 15 | degraded |
| 3 | 恒叉EF320四轮单驱平衡重电动叉车 | backup | 7 | 20 | — |
| 4 | EL25 | backup | 9 | 10 | — |
| 5 | CPD30/35 | primary | 5 | 20 | — |
| 6 | Nissan MXS series四轮电动平衡叉车 | primary | 6 | 5 | degraded/citation_only |

**备选（随包）**：

- 1. CPD50-B（role=pool，rank=13，5 图）
- 2. J4.0-5.5XN（role=pool，rank=14，20 图）
- 3. 尤恩FE系列四支点电动叉车（role=primary，rank=2，10 图）
- 4. E-T50（role=backup，rank=10，10 图）

## 二、内部监控（不对用户）

- 下载：hits 350 / downloaded 290 / failed 60 / blocked 0 / gate_pass 160
- 缺图归因：gate_or_verify_rejected 2 / not_delivered 6
- 总耗时：217425 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 39499 |
| FETCH | 23966 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 47316 |
| FETCH | 35938 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1856 |
| FETCH | 12004 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 17173 |
| FETCH | 39668 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2692 | ¥0.16 | **¥0.4292** |
| 全空闲 | ¥0.1346 | ¥0.16 | **¥0.2946** |

用量：输入 30954 tokens（按未命中计，偏保守）/ 输出 25917 / Search 6 次 / Fetch 26 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c4-forklift\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
