# 交付清单：run

> 任务单：`auto-20261112-165410` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 8/10 · degraded 2 · citation_only 1 · 备选 1 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | TT2004 | primary | 1 | 5 | degraded/citation_only |
| 2 | T2004 | primary | 2 | 15 | — |
| 3 | XT3004-N（TK系列260～300马力） | primary | 3 | 5 | degraded |
| 4 | OPTUM3004 | primary | 4 | 25 | — |
| 5 | 悍沃2004 | primary | 5 | 25 | — |
| 6 | RG2004 | primary | 7 | 25 | — |
| 7 | FJ2004 | backup | 11 | 20 | — |
| 8 | YHX2004 | primary | 10 | 25 | — |

**备选（随包）**：

- 1. 2004（role=primary，rank=6，5 图）

## 二、内部监控（不对用户）

- 下载：hits 215 / downloaded 200 / failed 15 / blocked 0 / gate_pass 150
- 缺图归因：gate_or_verify_rejected 2 / not_delivered 1
- 总耗时：209479 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 30877 |
| FETCH | 75096 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 476 |
| FETCH | 13676 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 10626 |
| FETCH | 78717 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 10 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1691 | ¥0.13 | **¥0.2992** |
| 全空闲 | ¥0.0846 | ¥0.13 | **¥0.2146** |

用量：输入 33579 tokens（按未命中计，偏保守）/ 输出 12749 / Search 6 次 / Fetch 20 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112\c3-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112\c3-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112\c3-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
