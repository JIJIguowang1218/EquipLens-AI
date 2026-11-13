# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 8/10 · degraded 7 · citation_only 1 · 备选 0 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | Zetros 4051 AS 6×6 重型牵引车 | primary | 3 | 30 | degraded |
| 2 | TX 6×6 牵引车（ZZ4257V455GF1） | primary | 4 | 30 | degraded |
| 3 | HOWO 6×6 全驱牵引车（全驱系列） | primary | 5 | 30 | degraded/citation_only |
| 4 | OTTC 460马力 6×6 越野牵引头 | primary | 7 | 5 | degraded |
| 5 | 371HP 6×6 全驱越野牵引车 | backup | 12 | 25 | degraded |
| 6 | Zetros 6×6 牵引车头 | primary | 8 | 15 | degraded |
| 7 | HF 8066 6×6 重型越野底盘 | primary | 9 | 30 | degraded |
| 8 | H6066 6×6 特种运输车 | primary | 10 | 10 | — |

## 二、内部监控（不对用户）

- 下载：hits 200 / downloaded 195 / failed 5 / blocked 0 / gate_pass 190
- 缺图归因：all_download_failed 1 / no_hits 3
- 总耗时：205445 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 35654 |
| FETCH | 95408 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 692 |
| FETCH | 33602 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 9694 |
| FETCH | 30382 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 5 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2895 | ¥0.16 | **¥0.4495** |
| 全空闲 | ¥0.1447 | ¥0.16 | **¥0.3047** |

用量：输入 39443 tokens（按未命中计，偏保守）/ 输出 26322 / Search 8 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261113-regress\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261113-regress\c1-desert-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261113-regress\c1-desert-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261113-regress\c1-desert-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
