# 交付清单：run

> 任务单：`auto-20261112-184334` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 5 · citation_only 4 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA610D-8 | primary | 2 | 24 | — |
| 2 | CA510PD | primary | 3 | 12 | — |
| 3 | CA610D | primary | 4 | 18 | — |
| 4 | SEM8222 | primary | 5 | 24 | — |
| 5 | SR22-G | primary | 6 | 18 | degraded/citation_only |
| 6 | SR26-G | primary | 7 | 18 | degraded/citation_only |
| 7 | HC 228D | primary | 8 | 12 | degraded |
| 8 | CA600PD | primary | 9 | 18 | degraded/citation_only |
| 9 | XS223JE | backup | 15 | 30 | — |
| 10 | CA602PD | primary | 10 | 6 | degraded/citation_only |
| 11 | XS222 | primary | 11 | 36 | — |
| 12 | BW226D-5CL | primary | 12 | 24 | — |
| 13 | RS7220 | primary | 13 | 12 | — |
| 14 | SSR260C-10H | primary | 14 | 36 | — |

**备选（随包）**：

- 1. XS265HS（role=backup，rank=16，6 图）
- 2. LSS2302（role=backup，rank=18，36 图）
- 3. HC 268i D（role=pool，rank=19，18 图）
- 4. XS225HS（SCR）（role=pool，rank=20，18 图）

## 二、内部监控（不对用户）

- 下载：hits 750 / downloaded 636 / failed 114 / blocked 0 / gate_pass 462
- 缺图归因：not_delivered 9
- 总耗时：503660 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 12635 |
| FETCH | 221947 |
| VERIFY | 8 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 54916 |
| FETCH | 148015 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 16093 |
| FETCH | 50034 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 10 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2387 | ¥0.25 | **¥0.4887** |
| 全空闲 | ¥0.1194 | ¥0.25 | **¥0.3694** |

用量：输入 30611 tokens（按未命中计，偏保守）/ 输出 22191 / Search 6 次 / Fetch 44 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q1\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q1\c5-roller\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q1\c5-roller\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q1\c5-roller\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
