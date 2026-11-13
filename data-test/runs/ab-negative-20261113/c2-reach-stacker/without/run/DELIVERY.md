# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 9/10 · degraded 6 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | RSH4532-Vo 正面吊运机 | primary | 1 | 25 | — |
| 2 | CRS450Z5 | primary | 2 | 20 | — |
| 3 | XCMG集装箱正面吊（徐工港机正面吊车系） | primary | 3 | 10 | degraded |
| 4 | RS45 | primary | 5 | 25 | — |
| 5 | LG420FC4 | primary | 6 | 20 | degraded/citation_only |
| 6 | Essential系列正面吊 DRU450-570 | primary | 7 | 5 | degraded |
| 7 | HCS46 集装箱正面吊运起重机 | backup | 12 | 10 | degraded |
| 8 | 林德45吨级集装箱正面吊 | primary | 9 | 10 | degraded |
| 9 | XCMG 45吨级集装箱正面吊（燃油/纯电动产品线） | primary | 8 | 15 | degraded/citation_only |

**备选（随包）**：

- 1. RSH4528-VO2（重型正面吊）（role=backup，rank=13，20 图）
- 2. RSH4532-VO2（重型正面吊）（role=backup，rank=14，5 图）
- 3. RSH4536-VO2（重型正面吊）（role=pool，rank=15，5 图）
- 4. 柳工正面吊（港口机械集装箱搬运设备）（role=pool，rank=16，10 图）

## 二、内部监控（不对用户）

- 下载：hits 395 / downloaded 300 / failed 73 / blocked 0 / gate_pass 215
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 1 / no_hits 1 / not_delivered 5
- 总耗时：369808 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 28843 |
| FETCH | 146721 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 11432 |
| FETCH | 138786 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 17326 |
| FETCH | 26687 |
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
| 全高峰 | ¥0.2061 | ¥0.2 | **¥0.4061** |
| 全空闲 | ¥0.103 | ¥0.2 | **¥0.303** |

用量：输入 39049 tokens（按未命中计，偏保守）/ 输出 15998 / Search 8 次 / Fetch 32 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c2-reach-stacker\without\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c2-reach-stacker\without\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c2-reach-stacker\without\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
