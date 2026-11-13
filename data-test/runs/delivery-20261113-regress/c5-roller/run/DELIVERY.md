# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 2 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA510PD | primary | 2 | 12 | — |
| 2 | CA610D-8 | primary | 3 | 24 | — |
| 3 | XS143J | primary | 5 | 30 | — |
| 4 | LG514D | primary | 6 | 30 | — |
| 5 | CA262PD | primary | 7 | 24 | — |
| 6 | XS265JSIV | primary | 8 | 36 | — |
| 7 | XS223JE | primary | 9 | 24 | — |
| 8 | XS202J | backup | 15 | 30 | — |
| 9 | YZ(k)18C | backup | 16 | 30 | degraded/citation_only |
| 10 | SR22-G | backup | 17 | 18 | degraded/citation_only |
| 11 | LSS2302 | backup | 18 | 36 | — |
| 12 | SRS200J | pool | 19 | 30 | — |
| 13 | XS265HS | pool | 20 | 6 | — |
| 14 | SSR260C-10H | pool | 21 | 36 | — |

**备选（随包）**：

- 1. XS262J（role=pool，rank=23，24 图）
- 2. 620H（role=pool，rank=24，12 图）
- 3. XS183J（role=pool，rank=25，24 图）
- 4. CA55/65/70（犀牛系列）（role=pool，rank=26，6 图）

## 二、内部监控（不对用户）

- 下载：hits 894 / downloaded 768 / failed 120 / blocked 6 / gate_pass 582
- 缺图归因：gate_or_verify_rejected 2 / not_delivered 11
- 总耗时：753052 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 56770 |
| FETCH | 358008 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22167 |
| FETCH | 122683 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 23476 |
| FETCH | 169925 |
| VERIFY | 6 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 6 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1716 | ¥0.27 | **¥0.4416** |
| 全空闲 | ¥0.0858 | ¥0.27 | **¥0.3558** |

用量：输入 29762 tokens（按未命中计，偏保守）/ 输出 14013 / Search 6 次 / Fetch 48 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261113-regress\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261113-regress\c5-roller\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261113-regress\c5-roller\run\audit.html`
- 证据库：`data-test\runs\delivery-20261113-regress\c5-roller\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
