# 交付清单：run

> 任务单：`auto-20261112-164934` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 7/10 · degraded 4 · citation_only 0 · 备选 0 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 标准型正面吊 | primary | 1 | 10 | — |
| 2 | CRS450Z5 | primary | 2 | 20 | — |
| 3 | G系列 RSH4531-VO5 | primary | 3 | 25 | degraded |
| 4 | 重型正面吊 | primary | 4 | 10 | — |
| 5 | G系列 RSH4532-VO | primary | 5 | 5 | degraded |
| 6 | 标准型正面吊（港机系列） | primary | 6 | 5 | degraded |
| 7 | 集装箱正面吊（无具体型号，销售页） | primary | 8 | 30 | degraded |

## 二、内部监控（不对用户）

- 下载：hits 180 / downloaded 140 / failed 40 / blocked 0 / gate_pass 125
- 缺图归因：gate_or_verify_rejected 1
- 总耗时：184480 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 24512 |
| FETCH | 150156 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 751 |
| FETCH | 9050 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 10 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.0826 | ¥0.08 | **¥0.1626** |
| 全空闲 | ¥0.0413 | ¥0.08 | **¥0.1213** |

用量：输入 20731 tokens（按未命中计，偏保守）/ 输出 5143 / Search 6 次 / Fetch 10 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112\c2-reach-stacker\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112\c2-reach-stacker\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112\c2-reach-stacker\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
