# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 7 · citation_only 1 · 备选 3 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | XCMG集装箱正面吊（45吨级） | primary | 1 | 15 | degraded |
| 2 | DRU450-570（Essential系列正面吊） | primary | 2 | 10 | — |
| 3 | 美科斯 集装箱正面吊（沃尔沃发动机+德纳/采埃孚变速箱+凯斯勒桥） | primary | 4 | 30 | degraded |
| 4 | RSH4532-Vo | primary | 5 | 5 | — |
| 5 | LG420FC4 | primary | 6 | 20 | degraded/citation_only |
| 6 | 柳工正面吊（港口机械） | primary | 7 | 30 | degraded |
| 7 | 港口集装箱正面吊（产品线） | backup | 14 | 5 | degraded |
| 8 | CRS450Z5 | primary | 8 | 20 | — |
| 9 | HCS46 集装箱正面吊运起重机 | primary | 10 | 10 | degraded |
| 10 | RS45正面吊 | pool | 16 | 20 | degraded |

**备选（随包）**：

- 1. RSH4532-Vo正面吊运机（role=pool，rank=17，20 图）
- 2. RSH4528-VO2（role=pool，rank=18，5 图）
- 3. 徐工港机 集装箱正面吊（伸缩臂叉车/正面吊系列）（role=pool，rank=21，20 图）

## 二、内部监控（不对用户）

- 下载：hits 420 / downloaded 335 / failed 63 / blocked 0 / gate_pass 215
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 4 / no_hits 3 / not_delivered 3
- 总耗时：613699 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 47584 |
| FETCH | 127695 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 67452 |
| FETCH | 106129 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 9857 |
| FETCH | 77599 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 10005 |
| FETCH | 167366 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 6 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2166 | ¥0.21 | **¥0.4266** |
| 全空闲 | ¥0.1083 | ¥0.21 | **¥0.3183** |

用量：输入 38684 tokens（按未命中计，偏保守）/ 输出 17406 / Search 8 次 / Fetch 34 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261113-regress\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261113-regress\c2-reach-stacker\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261113-regress\c2-reach-stacker\run\audit.html`
- 证据库：`data-test\runs\delivery-20261113-regress\c2-reach-stacker\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
