# 交付清单：run

> 任务单：`auto-20261112-170547` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 3 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | XS143 | primary | 1 | 42 | — |
| 2 | CV83PDU/CV123PDU | primary | 2 | 14 | degraded/citation_only |
| 3 | CA610D-8 | primary | 3 | 28 | — |
| 4 | LG520D | primary | 4 | 21 | — |
| 5 | RS7220 | primary | 5 | 14 | — |
| 6 | RS8140 | primary | 6 | 28 | — |
| 7 | LG526A9 | primary | 7 | 14 | — |
| 8 | LG520A9/LG520B9 | primary | 8 | 35 | degraded/citation_only |
| 9 | SEM518 | primary | 9 | 35 | — |
| 10 | XS203J/XS223J | primary | 10 | 21 | — |
| 11 | CA510PD | primary | 11 | 14 | — |
| 12 | CA260D-II | primary | 12 | 14 | degraded |
| 13 | BW226D-5CL | primary | 14 | 28 | — |
| 14 | CA610D | backup | 15 | 21 | — |

**备选（随包）**：

- 1. CA250PD（role=backup，rank=17，35 图）
- 2. XS225JIV（role=pool，rank=19，7 图）
- 3. CA600PD（role=backup，rank=16，21 图）
- 4. CA500PD（role=backup，rank=18，21 图）

## 二、内部监控（不对用户）

- 下载：hits 714 / downloaded 588 / failed 119 / blocked 7 / gate_pass 420
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 4
- 总耗时：472257 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 59276 |
| FETCH | 196009 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 53569 |
| FETCH | 109225 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6236 |
| FETCH | 47924 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 14 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2776 | ¥0.23 | **¥0.5076** |
| 全空闲 | ¥0.1388 | ¥0.23 | **¥0.3688** |

用量：输入 29883 tokens（按未命中计，偏保守）/ 输出 27225 / Search 6 次 / Fetch 40 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112\c5-roller\plan-ranked.json`
- 审核页：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112\c5-roller\run\audit.html`
- 证据库：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112\c5-roller\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
