# 交付清单：run

> 任务单：`auto-20261112-191206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 3 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 东方红-1604/1804 | primary | 1 | 15 | degraded |
| 2 | TT1604（G4） | primary | 3 | 10 | degraded/citation_only |
| 3 | 东方红-LX2004 | primary | 4 | 20 | — |
| 4 | 传奇1604-D（G4） | primary | 5 | 20 | degraded |
| 5 | 雷诺曼PH2304 | primary | 7 | 20 | — |
| 6 | JT2404 | backup | 11 | 10 | — |
| 7 | T234 | backup | 12 | 20 | — |
| 8 | M2404-7R(G4) | primary | 8 | 25 | — |
| 9 | MH2204（G4） | primary | 9 | 25 | — |
| 10 | MAGNUM3104 | primary | 10 | 20 | — |

**备选（随包）**：

- 1. SL2104（role=backup，rank=13，30 图）
- 2. M1004-D（role=backup，rank=14，25 图）
- 3. 2304（role=pool，rank=15，5 图）
- 4. 2004（role=pool，rank=16，5 图）

## 二、内部监控（不对用户）

- 下载：hits 415 / downloaded 335 / failed 80 / blocked 0 / gate_pass 260
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 1 / not_delivered 5
- 总耗时：335614 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 38871 |
| FETCH | 107723 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6802 |
| FETCH | 146976 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 5704 |
| FETCH | 29524 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 11 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2277 | ¥0.2 | **¥0.4277** |
| 全空闲 | ¥0.1139 | ¥0.2 | **¥0.3139** |

用量：输入 30366 tokens（按未命中计，偏保守）/ 输出 20873 / Search 6 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q12\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q12\c3-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q12\c3-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q12\c3-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
