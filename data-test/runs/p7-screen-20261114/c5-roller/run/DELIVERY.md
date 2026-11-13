# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 5 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 徐工 CV83PDU/CV123PDU | primary | 1 | 30 | — |
| 2 | CA510PD | primary | 2 | 12 | — |
| 3 | BW213D-40 | primary | 3 | 30 | — |
| 4 | XS265HS 单钢轮压路机 | primary | 4 | 36 | degraded |
| 5 | XS395IV 单钢轮压路机 | primary | 5 | 36 | degraded |
| 6 | XS265JSIV 单钢轮压路机 | primary | 6 | 12 | — |
| 7 | HC 228D 单钢轮压路机 | primary | 7 | 18 | degraded |
| 8 | LSS2302 | primary | 8 | 36 | — |
| 9 | XS202J | backup | 15 | 30 | — |
| 10 | CA610D-8 单钢轮振动压路机 | backup | 16 | 18 | — |
| 11 | 柳工 620H | backup | 17 | 30 | degraded/citation_only |
| 12 | KS126PD 全液压单钢轮振动压路机 | backup | 18 | 24 | degraded |
| 13 | 徐工 XS262J | pool | 19 | 24 | — |
| 14 | 徐工 XS183J | pool | 20 | 24 | — |

**备选（随包）**：

- 1. XS143J 单钢轮振动压路机（role=pool，rank=21，24 图）
- 2. XS143（role=pool，rank=22，36 图）
- 3. XS223JE 单钢轮压路机（role=pool，rank=23，18 图）
- 4. LG514D 单钢轮压路机（role=pool，rank=25，24 图）

## 二、内部监控（不对用户）

- 下载：hits 930 / downloaded 798 / failed 90 / blocked 42 / gate_pass 678
- 缺图归因：gate_or_verify_rejected 1 / not_delivered 12
- 总耗时：391591 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 40280 |
| FETCH | 111940 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 61268 |
| FETCH | 102217 |
| VERIFY | 7 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22337 |
| FETCH | 53528 |
| VERIFY | 7 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 2 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2194 | ¥0.29 | **¥0.5094** |
| 全空闲 | ¥0.1097 | ¥0.29 | **¥0.3997** |

用量：输入 30381 tokens（按未命中计，偏保守）/ 输出 19826 / Search 6 次 / Fetch 52 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\c5-roller\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
