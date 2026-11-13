# 交付清单：run

> 任务单：`auto-20261112-211042` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 4 · citation_only 2 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 雷诺曼 PH2304 | primary | 1 | 20 | — |
| 2 | TT1600（G4） | primary | 2 | 10 | degraded/citation_only |
| 3 | TG1654 / M1654-G | primary | 3 | 25 | degraded/citation_only |
| 4 | 1804 | primary | 4 | 5 | — |
| 5 | 东方红1604/1804 | primary | 5 | 25 | degraded |
| 6 | 东方红-LX2004 | primary | 6 | 20 | — |
| 7 | KAT2204 | primary | 7 | 25 | — |
| 8 | JC2104 | primary | 8 | 10 | — |
| 9 | 悍沃1654 | primary | 9 | 25 | degraded |
| 10 | OPTUM2704 | primary | 10 | 25 | — |

**备选（随包）**：

- 1. 东方红-LX2204系列（role=backup，rank=11，25 图）
- 2. 雷木1604（role=backup，rank=13，30 图）
- 3. M1654（role=backup，rank=14，10 图）
- 4. 东方红LX2004（role=pool，rank=15，10 图）

## 二、内部监控（不对用户）

- 下载：hits 465 / downloaded 425 / failed 40 / blocked 0 / gate_pass 375
- 缺图归因：gate_or_verify_rejected 2 / not_delivered 5
- 总耗时：237643 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 23809 |
| FETCH | 59395 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 6928 |
| FETCH | 25350 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 40517 |
| FETCH | 81631 |
| VERIFY | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 11 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1502 | ¥0.16 | **¥0.3102** |
| 全空闲 | ¥0.0751 | ¥0.16 | **¥0.2351** |

用量：输入 29895 tokens（按未命中计，偏保守）/ 输出 11305 / Search 6 次 / Fetch 26 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\delivery-20261112-clean\c3-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\ab-negative-20261113\c3-tractor\with\plan-ranked.json`
- 审核页：`data-test\runs\ab-negative-20261113\c3-tractor\with\run\audit.html`
- 证据库：`data-test\runs\ab-negative-20261113\c3-tractor\with\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
