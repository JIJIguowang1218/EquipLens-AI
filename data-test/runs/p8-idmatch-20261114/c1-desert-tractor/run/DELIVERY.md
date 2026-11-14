# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 8 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 豪沃 TAZ4922 6×6 油田专用牵引车 | primary | 1 | 10 | degraded |
| 2 | 奔驰 Zetros 4051 AS 6×6 牵引车 | primary | 3 | 25 | degraded |
| 3 | 豪沃TH7 6×6 牵引车 | primary | 5 | 30 | degraded |
| 4 | MOL H6066 6×6 特种运输车 | primary | 6 | 25 | — |
| 5 | 雷诺 TRM700-100 6×6 牵引车 | primary | 7 | 20 | degraded/citation_only |
| 6 | HOWO 6×6 全驱牵引车 | backup | 12 | 20 | degraded |
| 7 | OTTC 460马力 6×6 牵引头 | backup | 13 | 5 | degraded |
| 8 | Mercedes-Benz Zetros 6×6 牵引车头 | primary | 8 | 10 | degraded |
| 9 | 东风 EQ2082E6D 6×6 沙漠运输车 | primary | 9 | 10 | — |
| 10 | 东风 DFV5253TSMGP6D 6×6 沙漠车 | primary | 10 | 25 | degraded |

**备选（随包）**：

- 1. 东风 6×6 沙漠卡车（400马力）（role=backup，rank=14，30 图）
- 2. 豪沃TX 6×6 牵引车（ZZ4257V455GF1）（role=primary，rank=4，25 图）
- 3. 豪沃TX 6×6 牵引车（role=backup，rank=11，20 图）
- 4. HOWO 6×6 全驱牵引车系列（role=pool，rank=15，25 图）

## 二、内部监控（不对用户）

- 下载：hits 420 / downloaded 350 / failed 70 / blocked 0 / gate_pass 300
- 缺图归因：gate_or_verify_rejected 2 / not_delivered 5
- 总耗时：164107 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 19569 |
| FETCH | 49326 |
| VERIFY | 9 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 1548 |
| FETCH | 53283 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 7224 |
| FETCH | 33139 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2354 | ¥0.14 | **¥0.3754** |
| 全空闲 | ¥0.1177 | ¥0.14 | **¥0.2577** |

用量：输入 30354 tokens（按未命中计，偏保守）/ 输出 21834 / Search 6 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\LHM\Desktop\EquipLens-AI\data-test\runs\p8-idmatch-20261114\c1-desert-tractor\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
