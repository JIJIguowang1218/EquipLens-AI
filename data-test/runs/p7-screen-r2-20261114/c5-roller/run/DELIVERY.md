# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 3 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA510PD | primary | 2 | 12 | — |
| 2 | CA610D-8 | primary | 3 | 24 | — |
| 3 | XS143J | primary | 4 | 36 | — |
| 4 | XS223JE | primary | 5 | 24 | — |
| 5 | XS265HS | primary | 6 | 30 | — |
| 6 | BW213D-40 | primary | 7 | 30 | — |
| 7 | HC 228D | primary | 8 | 12 | degraded/citation_only |
| 8 | XS395IV | backup | 15 | 12 | degraded/citation_only |
| 9 | LG514D | backup | 16 | 30 | — |
| 10 | XS265JSIV | backup | 17 | 36 | — |
| 11 | 山工 SEM8222 | backup | 18 | 36 | — |
| 12 | 徐工 XS222J | pool | 19 | 30 | — |
| 13 | 山推 SR20MA | pool | 20 | 36 | degraded |
| 14 | LSS2302 | pool | 23 | 36 | — |

**备选（随包）**：

- 1. XS143（role=pool，rank=24，24 图）
- 2. XS202（role=pool，rank=25，36 图）
- 3. XS262J（role=pool，rank=26，24 图）
- 4. XS183J（role=pool，rank=27，24 图）

## 二、内部监控（不对用户）

- 下载：hits 882 / downloaded 780 / failed 102 / blocked 0 / gate_pass 600
- 缺图归因：gate_or_verify_rejected 3 / not_delivered 10
- 总耗时：578479 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 17945 |
| FETCH | 270623 |
| VERIFY | 7 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 11656 |
| FETCH | 158218 |
| VERIFY | 4 |
| FILL | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4177 |
| FETCH | 115842 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2154 | ¥0.29 | **¥0.5054** |
| 全空闲 | ¥0.1077 | ¥0.29 | **¥0.3977** |

用量：输入 30381 tokens（按未命中计，偏保守）/ 输出 19328 / Search 6 次 / Fetch 52 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c5-roller\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
