# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 3 · citation_only 0 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA510PD | primary | 2 | 12 | — |
| 2 | SR22-G | primary | 3 | 18 | — |
| 3 | XS143J 单钢轮振动压路机 | primary | 4 | 36 | — |
| 4 | XS222J 机械驱动单钢轮振动压路机 | primary | 5 | 18 | — |
| 5 | XS223JE(第三级) 单钢轮压路机 | primary | 6 | 24 | — |
| 6 | XS265HS 单钢轮压路机 | primary | 7 | 36 | — |
| 7 | XS395IV 单钢轮压路机 | primary | 8 | 36 | degraded |
| 8 | BW213D-40 | primary | 9 | 30 | — |
| 9 | XS143 | backup | 15 | 24 | — |
| 10 | LSS2302 | backup | 16 | 30 | — |
| 11 | SRS200J 机械式单钢轮振动压路机 | pool | 19 | 12 | degraded |
| 12 | LSS327 机械式单钢轮振动压路机 | pool | 20 | 24 | degraded |
| 13 | LSS321 | pool | 21 | 30 | — |
| 14 | 620H | pool | 22 | 12 | — |

**备选（随包）**：

- 1. XS183J（role=pool，rank=23，24 图）
- 2. CA55/65/70（role=pool，rank=24，6 图）
- 3. CA610D-8（role=pool，rank=25，24 图）
- 4. 一汽解放 新J6P重卡 城建工程版 自卸车 CA3310P66K24L1T4E5（role=pool，rank=27，12 图）

## 二、内部监控（不对用户）

- 下载：hits 882 / downloaded 792 / failed 90 / blocked 0 / gate_pass 588
- 缺图归因：gate_or_verify_rejected 3 / not_delivered 10
- 总耗时：382484 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 15244 |
| FETCH | 90297 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 51128 |
| FETCH | 89200 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6494 |
| FETCH | 130103 |
| VERIFY | 8 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.3051 | ¥0.28 | **¥0.5851** |
| 全空闲 | ¥0.1526 | ¥0.28 | **¥0.4326** |

用量：输入 30526 tokens（按未命中计，偏保守）/ 输出 30512 / Search 6 次 / Fetch 50 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-r3-20261114\c5-roller\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
