# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 3 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA610D-8 | primary | 1 | 24 | — |
| 2 | CA510PD | primary | 3 | 12 | — |
| 3 | XS85JIV | primary | 4 | 6 | — |
| 4 | 3412P | primary | 5 | 6 | degraded/citation_only |
| 5 | SRS200J | primary | 6 | 30 | — |
| 6 | XS223JE(第三级) | primary | 7 | 24 | — |
| 7 | XS222J | primary | 8 | 30 | — |
| 8 | LSS327 | primary | 9 | 6 | degraded/citation_only |
| 9 | XS202J | backup | 15 | 30 | — |
| 10 | SSR260C-10H | primary | 10 | 36 | — |
| 11 | HC 228D | primary | 11 | 12 | degraded |
| 12 | LSS2302 | primary | 12 | 36 | — |
| 13 | BW212PD-40 | primary | 13 | 18 | — |
| 14 | LG520A6 | primary | 14 | 36 | — |

**备选（随包）**：

- 1. 618A（role=backup，rank=18，18 图）
- 2. XS262J（role=pool，rank=19，24 图）
- 3. XS183J（role=pool，rank=20，24 图）
- 4. HC系列（role=pool，rank=22，6 图）

## 二、内部监控（不对用户）

- 下载：hits 732 / downloaded 648 / failed 84 / blocked 0 / gate_pass 486
- 缺图归因：no_hits 1 / not_delivered 8
- 总耗时：415781 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 55858 |
| FETCH | 211425 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6571 |
| FETCH | 83213 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 8510 |
| FETCH | 50188 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 12 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2477 | ¥0.25 | **¥0.4977** |
| 全空闲 | ¥0.1239 | ¥0.25 | **¥0.3739** |

用量：输入 29524 tokens（按未命中计，偏保守）/ 输出 23582 / Search 6 次 / Fetch 44 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c5-roller\without\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c5-roller\without\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c5-roller\without\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
