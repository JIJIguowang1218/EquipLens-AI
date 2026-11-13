# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 4 · citation_only 0 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 东方红-LX2204系列 | primary | 1 | 30 | — |
| 2 | 东方红-1604/1804 | primary | 2 | 10 | degraded |
| 3 | 雷木1504 | primary | 3 | 30 | degraded |
| 4 | 悍沃1654 | primary | 6 | 25 | degraded |
| 5 | PH2304 | primary | 7 | 20 | — |
| 6 | OPTUM2704 | backup | 11 | 25 | — |
| 7 | 6170R | backup | 12 | 30 | — |
| 8 | 东方红-LX2004 | pool | 15 | 20 | — |
| 9 | M1654-G | pool | 16 | 5 | — |
| 10 | 雷诺曼PH2304 | pool | 17 | 10 | degraded |

**备选（随包）**：

- 1. LX2204（role=pool，rank=18，10 图）
- 2. 1604（role=pool，rank=19，10 图）
- 3. TN1454（role=pool，rank=20，20 图）
- 4. LX1004/1104/1204/1254/1304（role=pool，rank=22，15 图）

## 二、内部监控（不对用户）

- 下载：hits 525 / downloaded 440 / failed 85 / blocked 0 / gate_pass 355
- 缺图归因：gate_or_verify_rejected 3 / no_hits 1 / not_delivered 7
- 总耗时：586275 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 39324 |
| FETCH | 108666 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 33948 |
| FETCH | 234222 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 59324 |
| FETCH | 110776 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 6 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2071 | ¥0.18 | **¥0.3871** |
| 全空闲 | ¥0.1036 | ¥0.18 | **¥0.2836** |

用量：输入 29771 tokens（按未命中计，偏保守）/ 输出 18446 / Search 6 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261113-regress\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261113-regress\c3-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261113-regress\c3-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261113-regress\c3-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
