# 交付清单：run

> 任务单：`auto-20261112-170006` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 4 · citation_only 3 · 备选 2 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | EA系列 E25A | primary | 1 | 25 | degraded/citation_only |
| 2 | KLA-I | primary | 3 | 5 | degraded |
| 3 | EL18PRO | backup | 7 | 10 | degraded/citation_only |
| 4 | EL30 | backup | 9 | 10 | — |
| 5 | EL16PRO | primary | 5 | 30 | degraded/citation_only |
| 6 | XCB35 | pool | 11 | 10 | — |

**备选（随包）**：

- 1. EL35（role=backup，rank=10，20 图）
- 2. CPD40-35B（role=pool，rank=12，20 图）

## 二、内部监控（不对用户）

- 下载：hits 315 / downloaded 250 / failed 65 / blocked 0 / gate_pass 130
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 3 / not_delivered 2
- 总耗时：201135 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4933 |
| FETCH | 43473 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22747 |
| FETCH | 51797 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 14015 |
| FETCH | 30905 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7737 |
| FETCH | 25512 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DONE | 0 |
| WRITEBACK | 16 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1241 | ¥0.14 | **¥0.2641** |
| 全空闲 | ¥0.0621 | ¥0.14 | **¥0.2021** |

用量：输入 32136 tokens（按未命中计，偏保守）/ 输出 7482 / Search 6 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112\c4-forklift\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112\c4-forklift\plan-ranked.json`
- 审核页：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112\c4-forklift\run\audit.html`
- 证据库：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112\c4-forklift\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
