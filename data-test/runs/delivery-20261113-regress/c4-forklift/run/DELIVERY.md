# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 3 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CPD40-40B | primary | 1 | 20 | degraded/citation_only |
| 2 | FE4P25N | primary | 2 | 30 | — |
| 3 | FE系列四支点电动叉车 | backup | 9 | 5 | degraded |
| 4 | CPD30/35 | pool | 11 | 20 | — |
| 5 | CPD40-B | pool | 12 | 5 | degraded/citation_only |
| 6 | EF320 | pool | 14 | 5 | — |

**备选（随包）**：

- 1. B15S-7（7系列）（role=pool，rank=15，15 图）
- 2. 7系列 Plus 四轮电动叉车（role=pool，rank=16，10 图）
- 3. MXS系列（role=pool，rank=18，5 图）
- 4. E-T50（role=backup，rank=8，10 图）

## 二、内部监控（不对用户）

- 下载：hits 295 / downloaded 230 / failed 65 / blocked 0 / gate_pass 145
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / no_hits 3 / not_delivered 4
- 总耗时：378692 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 29969 |
| FETCH | 61141 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 64485 |
| FETCH | 40984 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 64775 |
| FETCH | 55926 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 8786 |
| FETCH | 52617 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 6 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2084 | ¥0.18 | **¥0.3884** |
| 全空闲 | ¥0.1042 | ¥0.18 | **¥0.2842** |

用量：输入 30061 tokens（按未命中计，偏保守）/ 输出 18537 / Search 6 次 / Fetch 30 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261113-regress\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261113-regress\c4-forklift\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261113-regress\c4-forklift\run\audit.html`
- 证据库：`data-test\runs\delivery-20261113-regress\c4-forklift\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
