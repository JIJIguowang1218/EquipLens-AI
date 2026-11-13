# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 2 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA510PD | primary | 2 | 12 | — |
| 2 | XS143J | primary | 3 | 36 | — |
| 3 | XS223JE | primary | 4 | 24 | — |
| 4 | XS265HS | primary | 5 | 6 | — |
| 5 | XS395IV | primary | 6 | 12 | degraded/citation_only |
| 6 | BW213D-40 | primary | 7 | 30 | — |
| 7 | CA610D-8 单钢轮振动压路机 | primary | 8 | 18 | — |
| 8 | SR22-G | primary | 9 | 18 | degraded/citation_only |
| 9 | XS265JSIV | backup | 15 | 36 | — |
| 10 | XS303S | backup | 16 | 18 | — |
| 11 | SRS200J | backup | 18 | 30 | — |
| 12 | XS222J | pool | 19 | 30 | — |
| 13 | XS143 | pool | 20 | 24 | — |
| 14 | SR20MA | pool | 21 | 18 | — |

**备选（随包）**：

- 1. XS202J（role=pool，rank=22，30 图）
- 2. CA262PD 单钢轮振动压路机（role=pool，rank=23，18 图）
- 3. 620H（role=pool，rank=24，12 图）
- 4. LSS2302（role=pool，rank=26，36 图）

## 二、内部监控（不对用户）

- 下载：hits 882 / downloaded 750 / failed 126 / blocked 6 / gate_pass 564
- 缺图归因：gate_or_verify_rejected 3 / not_delivered 10
- 总耗时：606833 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5588 |
| FETCH | 341957 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5402 |
| FETCH | 76041 |
| VERIFY | 6 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4584 |
| FETCH | 173244 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2322 | ¥0.29 | **¥0.5222** |
| 全空闲 | ¥0.1161 | ¥0.29 | **¥0.4061** |

用量：输入 30386 tokens（按未命中计，偏保守）/ 输出 21429 / Search 6 次 / Fetch 52 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\c5-roller\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
