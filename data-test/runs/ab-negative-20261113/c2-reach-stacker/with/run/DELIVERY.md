# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 8/10 · degraded 2 · citation_only 1 · 备选 2 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | RSH4528-VO2 | primary | 1 | 5 | — |
| 2 | RSH4532-Vo | primary | 2 | 5 | — |
| 3 | RS45 | primary | 4 | 25 | — |
| 4 | DRU450-570（Essential系列正面吊） | primary | 5 | 15 | — |
| 5 | LG420FC4 | primary | 6 | 20 | degraded/citation_only |
| 6 | CRS450Z5 | primary | 7 | 20 | — |
| 7 | 柳工正面吊 | backup | 14 | 20 | — |
| 8 | HCS46 集装箱正面吊运起重机 | primary | 10 | 10 | degraded |

**备选（随包）**：

- 1. XCMG集装箱正面吊（role=pool，rank=15，10 图）
- 2. G系列（Gloria）正面吊（role=pool，rank=16，15 图）

## 二、内部监控（不对用户）

- 下载：hits 345 / downloaded 250 / failed 73 / blocked 0 / gate_pass 145
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 3 / no_hits 2 / not_delivered 2
- 总耗时：387234 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 35873 |
| FETCH | 184170 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 20049 |
| FETCH | 86876 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 11925 |
| FETCH | 48328 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 12 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2092 | ¥0.15 | **¥0.3592** |
| 全空闲 | ¥0.1046 | ¥0.15 | **¥0.2546** |

用量：输入 39185 tokens（按未命中计，偏保守）/ 输出 16348 / Search 8 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c2-reach-stacker\with\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c2-reach-stacker\with\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c2-reach-stacker\with\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
