# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 4 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA510PD | primary | 1 | 18 | — |
| 2 | CV83PDU | primary | 2 | 12 | — |
| 3 | SR26-G | primary | 3 | 18 | degraded/citation_only |
| 4 | CA610D-8 | primary | 4 | 24 | — |
| 5 | XS85JIV | primary | 5 | 6 | — |
| 6 | XS395IV | primary | 6 | 12 | degraded/citation_only |
| 7 | HC 228D | primary | 7 | 12 | degraded |
| 8 | BW212PD-40 | primary | 8 | 18 | — |
| 9 | YZ(k)18C | primary | 9 | 30 | degraded/citation_only |
| 10 | SRS200J | primary | 11 | 30 | — |
| 11 | 618A | primary | 12 | 18 | — |
| 12 | XS265HS | primary | 13 | 6 | — |
| 13 | XS143J | primary | 14 | 30 | — |
| 14 | SSR260C-10H | backup | 15 | 36 | — |

**备选（随包）**：

- 1. XS223JE（role=backup，rank=16，24 图）
- 2. XS202J（role=backup，rank=17，30 图）
- 3. LG514D（role=backup，rank=18，30 图）
- 4. SR20MA（role=pool，rank=19，18 图）

## 二、内部监控（不对用户）

- 下载：hits 588 / downloaded 492 / failed 96 / blocked 0 / gate_pass 378
- 缺图归因：not_delivered 5
- 总耗时：634279 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 51895 |
| FETCH | 191377 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 31942 |
| FETCH | 91690 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 26314 |
| FETCH | 241045 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 13 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1779 | ¥0.2 | **¥0.3779** |
| 全空闲 | ¥0.089 | ¥0.2 | **¥0.289** |

用量：输入 29682 tokens（按未命中计，偏保守）/ 输出 14820 / Search 6 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c5-roller\with\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c5-roller\with\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c5-roller\with\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
