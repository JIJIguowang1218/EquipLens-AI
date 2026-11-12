# 交付清单：run

> 任务单：`auto-20261112-182808` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 3 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | PH2304 | primary | 1 | 20 | — |
| 2 | M2404-7R(G4) | primary | 2 | 25 | — |
| 3 | JT2404 | primary | 3 | 10 | — |
| 4 | RZ2104-A | primary | 4 | 30 | — |
| 5 | SWT2004 | primary | 5 | 5 | degraded/citation_only |
| 6 | 2104-S | primary | 6 | 15 | degraded/citation_only |
| 7 | LP2604 | primary | 7 | 15 | — |
| 8 | HMT2104 | primary | 9 | 25 | — |
| 9 | 2004 | primary | 10 | 5 | degraded/citation_only |
| 10 | LX2204 | backup | 11 | 20 | — |

**备选（随包）**：

- 1. LX2004（role=backup，rank=12，25 图）
- 2. MH2204（G4）（role=backup，rank=13，25 图）
- 3. RG2104（role=backup，rank=14，30 图）
- 4. 雷诺曼PH2304（role=pool，rank=16，10 图）

## 二、内部监控（不对用户）

- 下载：hits 450 / downloaded 375 / failed 75 / blocked 0 / gate_pass 305
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 6
- 总耗时：327785 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 32472 |
| FETCH | 167046 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 7444 |
| FETCH | 37195 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 20250 |
| FETCH | 23617 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4880 |
| FETCH | 34867 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 10 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2093 | ¥0.19 | **¥0.3993** |
| 全空闲 | ¥0.1046 | ¥0.19 | **¥0.2946** |

用量：输入 30316 tokens（按未命中计，偏保守）/ 输出 18579 / Search 6 次 / Fetch 32 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q1\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q1\c3-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q1\c3-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q1\c3-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
