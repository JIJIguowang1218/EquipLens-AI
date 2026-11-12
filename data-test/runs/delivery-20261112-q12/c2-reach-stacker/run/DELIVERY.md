# 交付清单：run

> 任务单：`auto-20261112-190335` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 4 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | SRSC4535C1 | primary | 1 | 20 | — |
| 2 | XCS4531K2 | primary | 2 | 30 | — |
| 3 | SMV 4542 TBX5 | primary | 3 | 5 | degraded/citation_only |
| 4 | RSH系列（RSH4528-VO2/RSH4532-VO2/RSH4536-VO2） | primary | 4 | 10 | degraded |
| 5 | XCS4531K4 | primary | 5 | 15 | — |
| 6 | LRS 645 曲臂正面吊 | primary | 6 | 20 | degraded |
| 7 | 重型正面吊 | primary | 7 | 10 | — |
| 8 | 集装箱正面吊（结果未给出具体型号） | primary | 10 | 25 | degraded |
| 9 | 正面吊 | backup | 11 | 25 | — |
| 10 | XCS4531K | backup | 12 | 30 | — |

**备选（随包）**：

- 1. 柳工正面吊（港口机械集装箱搬运设备）（role=backup，rank=13，10 图）
- 2. FDM798T-40G（role=backup，rank=14，20 图）
- 3. 正面吊（港口机械）（role=pool，rank=15，30 图）
- 4. SMV 系列（SMV 108 TC6 / SMV 2115 TC3 / SMV 2518 TC3）（role=pool，rank=16，20 图）

## 二、内部监控（不对用户）

- 下载：hits 460 / downloaded 435 / failed 25 / blocked 0 / gate_pass 360
- 缺图归因：no_hits 1 / not_delivered 9
- 总耗时：291754 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 18290 |
| FETCH | 76171 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 7035 |
| FETCH | 45727 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6983 |
| FETCH | 23340 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 47882 |
| FETCH | 66312 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 11 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.248 | ¥0.22 | **¥0.468** |
| 全空闲 | ¥0.124 | ¥0.22 | **¥0.344** |

用量：输入 40100 tokens（按未命中计，偏保守）/ 输出 20981 / Search 8 次 / Fetch 36 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q12\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q12\c2-reach-stacker\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q12\c2-reach-stacker\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q12\c2-reach-stacker\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
