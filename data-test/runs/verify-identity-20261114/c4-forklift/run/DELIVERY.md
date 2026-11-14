# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 扬子 CPD40-40B 四轮座驾式电动叉车 | primary | 1 | 25 | degraded/citation_only |
| 2 | J4.0-5.5XN | primary | 2 | 10 | — |
| 3 | 诺力 FE4P25N 四轮座驾式电动叉车 | primary | 3 | 30 | degraded/citation_only |
| 4 | 比亚迪 EL25 四支点平衡重电动叉车 | primary | 4 | 25 | degraded |
| 5 | FE系列四支点电动叉车 | primary | 5 | 5 | degraded/citation_only |
| 6 | CPD40-B 电动四轮叉车 | primary | 6 | 10 | — |

**备选（随包）**：

- 1. CPD50-B（role=backup，rank=7，5 图）
- 2. 3.0T 锂电电动叉车（四轮平衡重款）（role=pool，rank=11，5 图）
- 3. CPD40-50B 四轮座驾式电动叉车（role=pool，rank=12，25 图）
- 4. E-T50（role=backup，rank=8，10 图）

## 二、内部监控（不对用户）

- 下载：hits 260 / downloaded 240 / failed 20 / blocked 0 / gate_pass 190
- 缺图归因：gate_or_verify_rejected 2 / no_hits 1 / not_delivered 5
- 总耗时：229503 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 26207 |
| FETCH | 31283 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 33426 |
| FETCH | 11877 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 35339 |
| FETCH | 37190 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 20662 |
| FETCH | 33511 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.0 | ¥0.13 | **¥0.13** |
| 全空闲 | ¥0.0 | ¥0.13 | **¥0.13** |

用量：输入 0 tokens（按未命中计，偏保守）/ 输出 0 / Search 0 次 / Fetch 26 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\verify-identity-20261114\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\verify-identity-20261114\c4-forklift\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
