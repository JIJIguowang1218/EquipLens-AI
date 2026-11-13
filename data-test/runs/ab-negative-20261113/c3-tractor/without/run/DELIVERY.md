# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 1 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | KAT2204 | primary | 1 | 25 | — |
| 2 | PH2304 | primary | 2 | 20 | — |
| 3 | LX2204 | primary | 3 | 20 | — |
| 4 | JC2104 | primary | 5 | 10 | — |
| 5 | OPTUM2704 | primary | 6 | 25 | — |
| 6 | 2204 | primary | 7 | 15 | — |
| 7 | M1654 | backup | 11 | 20 | — |
| 8 | LX2004 | primary | 8 | 20 | — |
| 9 | 1654 | primary | 10 | 20 | degraded/citation_only |
| 10 | 1504 | pool | 19 | 5 | — |

**备选（随包）**：

- 1. 东方红-1604/1804（role=pool，rank=15，15 图）
- 2. 雷木1604（role=pool，rank=17，30 图）
- 3. TN1454（role=pool，rank=20，20 图）
- 4. TT1600（G4）（role=backup，rank=14，10 图）

## 二、内部监控（不对用户）

- 下载：hits 460 / downloaded 370 / failed 90 / blocked 0 / gate_pass 290
- 缺图归因：gate_or_verify_rejected 4 / no_hits 1 / not_delivered 5
- 总耗时：320422 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 10499 |
| FETCH | 67104 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 33498 |
| FETCH | 82181 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 9571 |
| FETCH | 69417 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 17513 |
| FETCH | 30628 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 10 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1734 | ¥0.215 | **¥0.3884** |
| 全空闲 | ¥0.0867 | ¥0.215 | **¥0.3017** |

用量：输入 29836 tokens（按未命中计，偏保守）/ 输出 14217 / Search 6 次 / Fetch 37 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c3-tractor\without\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c3-tractor\without\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c3-tractor\without\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
