# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 6 · citation_only 4 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CPD40-40B 四轮座驾式电动叉车 | primary | 1 | 25 | degraded |
| 2 | FE4P25N 四轮座驾式电动叉车 | primary | 2 | 10 | degraded |
| 3 | 扬子 CPD40-50B 四轮座驾式电动叉车 | primary | 3 | 20 | degraded/citation_only |
| 4 | CPD50-B | primary | 4 | 5 | degraded/citation_only |
| 5 | J4.0-5.5XN 四轮电动平衡重叉车 | primary | 5 | 15 | degraded/citation_only |
| 6 | 尤恩 FE系列四支点电动叉车 | backup | 7 | 10 | degraded/citation_only |

**备选（随包）**：

- 1. CPD30/35（role=backup，rank=8，20 图）
- 2. 山猫 B18S-7 四轮电动叉车（7系列）（role=pool，rank=11，25 图）
- 3. Hyster J7.0-9.0XNL 四轮电动平衡重叉车（role=backup，rank=9，10 图）
- 4. UN Forklift FB15-FENLZD 四轮电动叉车（role=pool，rank=12，5 图）

## 二、内部监控（不对用户）

- 下载：hits 250 / downloaded 205 / failed 45 / blocked 0 / gate_pass 165
- 缺图归因：gate_or_verify_rejected 2 / not_delivered 4
- 总耗时：189617 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2678 |
| FETCH | 46743 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1144 |
| FETCH | 59130 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22877 |
| FETCH | 15754 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 5227 |
| FETCH | 36057 |
| VERIFY | 2 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 0 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1857 | ¥0.15 | **¥0.3357** |
| 全空闲 | ¥0.0928 | ¥0.15 | **¥0.2428** |

用量：输入 30863 tokens（按未命中计，偏保守）/ 输出 15492 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\c4-forklift\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
