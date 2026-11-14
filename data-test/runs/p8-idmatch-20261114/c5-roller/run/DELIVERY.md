# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 2 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA610D-8 | primary | 1 | 24 | — |
| 2 | XS222J | primary | 2 | 30 | — |
| 3 | CA510PD | primary | 3 | 12 | — |
| 4 | XS143J | primary | 5 | 24 | — |
| 5 | LG514D | primary | 6 | 30 | — |
| 6 | CA262PD | primary | 7 | 24 | — |
| 7 | XS265HS | primary | 8 | 12 | — |
| 8 | XS395IV | primary | 9 | 12 | degraded/citation_only |
| 9 | SR20MA 单钢轮压路机 | backup | 15 | 36 | degraded |
| 10 | SEM8222 单钢轮压路机 | backup | 16 | 36 | — |
| 11 | BW213D-40 | backup | 18 | 30 | — |
| 12 | 620H | pool | 19 | 12 | — |
| 13 | XS143 | pool | 20 | 36 | — |
| 14 | XS262J | pool | 21 | 24 | — |

**备选（随包）**：

- 1. XS183J（role=pool，rank=22，24 图）
- 2. XS202（role=pool，rank=23，36 图）
- 3. SR40-G（role=pool，rank=24，6 图）
- 4. 618A（role=pool，rank=25，18 图）

## 二、内部监控（不对用户）

- 下载：hits 888 / downloaded 738 / failed 138 / blocked 12 / gate_pass 558
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / not_delivered 10
- 总耗时：363333 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 10411 |
| FETCH | 207882 |
| VERIFY | 8 |
| FILL | 2 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22720 |
| FETCH | 52730 |
| VERIFY | 17 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4402 |
| FETCH | 65151 |
| VERIFY | 8 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2438 | ¥0.27 | **¥0.5138** |
| 全空闲 | ¥0.1219 | ¥0.27 | **¥0.3919** |

用量：输入 30389 tokens（按未命中计，偏保守）/ 输出 22878 / Search 6 次 / Fetch 48 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c5-roller\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
