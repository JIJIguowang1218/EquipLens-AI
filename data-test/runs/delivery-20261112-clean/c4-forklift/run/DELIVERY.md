# 交付清单：run

> 任务单：`auto-20261112-212154` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | FE4P25N | primary | 1 | 30 | — |
| 2 | ERP15-35UX | primary | 2 | 10 | degraded/citation_only |
| 3 | EL25 | primary | 3 | 5 | — |
| 4 | J1.6-2.0XN | primary | 4 | 5 | degraded/citation_only |
| 5 | H4 3吨电动叉车 | primary | 6 | 30 | degraded |
| 6 | EA系列 电动四轮平衡重式叉车 | backup | 8 | 5 | degraded |

**备选（随包）**：

- 1. 3.0T电动叉车（锂电四轮平衡重款）（role=pool，rank=11，30 图）
- 2. CPD20/CPD25 四轮电动叉车（role=primary，rank=5，30 图）
- 3. CPD40-50B（role=backup，rank=10，20 图）
- 4. B15S-7（7系列四轮电动叉车）（role=pool，rank=12，5 图）

## 二、内部监控（不对用户）

- 下载：hits 255 / downloaded 230 / failed 25 / blocked 0 / gate_pass 170
- 缺图归因：gate_or_verify_rejected 1 / no_hits 1 / not_delivered 4
- 总耗时：176459 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22210 |
| FETCH | 34965 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 12795 |
| FETCH | 17457 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 3464 |
| FETCH | 17075 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 24837 |
| FETCH | 43646 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 10 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1606 | ¥0.15 | **¥0.3106** |
| 全空闲 | ¥0.0803 | ¥0.15 | **¥0.2303** |

用量：输入 30840 tokens（按未命中计，偏保守）/ 输出 12366 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-clean\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-clean\c4-forklift\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-clean\c4-forklift\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-clean\c4-forklift\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
