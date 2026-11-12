# 交付清单：run

> 任务单：`auto-20261112-183632` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CPD-D | primary | 2 | 5 | degraded |
| 2 | Electric 3/4 Wheel Truck（1.6–2t，四轮型） | primary | 4 | 10 | degraded |
| 3 | FE4P25N | backup | 7 | 30 | — |
| 4 | 7系列 四轮电动叉车（1.5–3.5t，含Plus） | backup | 8 | 5 | degraded |
| 5 | EL25 | primary | 6 | 5 | — |
| 6 | J1.6-2.0XN | pool | 11 | 25 | degraded/citation_only |

**备选（随包）**：

- 1. FB16CN2–FB20N2 四轮电动平衡重叉车（约1.2–1.8t）（role=backup，rank=9，5 图）
- 2. CPD-25（role=pool，rank=12，25 图）
- 3. MXS series（role=pool，rank=13，5 图）
- 4. ERP15-35UX（role=pool，rank=15，5 图）

## 二、内部监控（不对用户）

- 下载：hits 335 / downloaded 270 / failed 55 / blocked 10 / gate_pass 150
- 缺图归因：gate_or_verify_rejected 3 / no_hits 2 / not_delivered 5
- 总耗时：261969 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 23016 |
| FETCH | 34792 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 11820 |
| FETCH | 38282 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 5800 |
| FETCH | 28131 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 26595 |
| FETCH | 26591 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 744 |
| FETCH | 66184 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 14 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1513 | ¥0.15 | **¥0.3013** |
| 全空闲 | ¥0.0757 | ¥0.15 | **¥0.2257** |

用量：输入 30482 tokens（按未命中计，偏保守）/ 输出 11298 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q1\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q1\c4-forklift\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q1\c4-forklift\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q1\c4-forklift\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
