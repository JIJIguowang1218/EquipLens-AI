# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 1 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | LX2004 | primary | 1 | 25 | — |
| 2 | OPTUM2704 | primary | 2 | 25 | — |
| 3 | PL2304 | primary | 3 | 20 | — |
| 4 | PH2304 | primary | 4 | 20 | — |
| 5 | M1654 | primary | 5 | 20 | — |
| 6 | TT1604（G4） | primary | 6 | 10 | degraded/citation_only |
| 7 | JC2104 | primary | 7 | 10 | — |
| 8 | 6170R | primary | 9 | 30 | — |
| 9 | 2204 | primary | 10 | 10 | — |
| 10 | LX2204系列 | backup | 11 | 15 | — |

**备选（随包）**：

- 1. TN1454（role=backup，rank=13，20 图）
- 2. 2104（role=pool，rank=15，5 图）
- 3. JC1804（G4）（role=pool，rank=18，10 图）
- 4. 1504（role=pool，rank=19，5 图）

## 二、内部监控（不对用户）

- 下载：hits 465 / downloaded 370 / failed 95 / blocked 0 / gate_pass 280
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / not_delivered 7
- 总耗时：501866 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 14766 |
| FETCH | 268417 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1250 |
| FETCH | 30317 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 28136 |
| FETCH | 31333 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 46145 |
| FETCH | 81487 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 14 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1743 | ¥0.23 | **¥0.4043** |
| 全空闲 | ¥0.0871 | ¥0.23 | **¥0.3171** |

用量：输入 29687 tokens（按未命中计，偏保守）/ 输出 14363 / Search 6 次 / Fetch 40 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-clean\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-clean\c3-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-clean\c3-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-clean\c3-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
