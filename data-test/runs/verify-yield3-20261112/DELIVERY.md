# 交付清单：verify-yield3-20261112

> 任务单：`m1-desert-20261109` · 主 12 台 + 备选 4 台 · 状态 DONE
> 交付 12/12 · degraded 8 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | HOWO TAZ4922 6×6 油田专用全驱牵引车 | primary | 1 | 16 | degraded/citation_only |
| 2 | Zetros 4051 AS 6×6 重型牵引车 | primary | 3 | 24 | degraded |
| 3 | OTTC 越野 6×6 牵引头（460 马力牵引车） | primary | 5 | 4 | degraded |
| 4 | HF8066 6×6 重型沙漠运输车 | primary | 6 | 8 | — |
| 5 | 中东版 6×6 柴油重型卡车（Deutz D13 动力） | primary | 7 | 4 | degraded |
| 6 | 东风 6×6 沙漠卡车（400马力 25吨级） | primary | 8 | 8 | degraded |
| 7 | Arocs 全驱牵引车（6×6/8×8 Zugmaschinen） | backup | 13 | 24 | degraded |
| 8 | 豪沃6×6油田牵引车 | backup | 14 | 16 | degraded |
| 9 | 天龙 EQ2250AX 6×6 沙漠越野卡车 | primary | 9 | 12 | — |
| 10 | 天锦 6×6 沙漠运输车（DFV2223GP6DJ） | primary | 10 | 20 | degraded |
| 11 | DFV5253TSMGP6D 沙漠车（东风六驱） | primary | 11 | 24 | — |
| 12 | ND5250TSMZ04 沙漠车 | primary | 12 | 24 | — |

**备选（随包）**：

- 1. 沙豹 EQ2251AX 6×6 沙漠越野卡车（role=pool，rank=18，24 图）
- 2. EQ2220AX 6×6 沙漠重型货车（role=pool，rank=19，16 图）
- 3. EQ2102G 6×6 沙漠越野卡车（role=pool，rank=20，20 图）
- 4. EQ2162NS 6×6 越野卡车（role=pool，rank=21，20 图）

## 二、内部监控（不对用户）

- 下载：hits 412 / downloaded 344 / failed 56 / blocked 8 / gate_pass 324
- 缺图归因：all_download_failed 2 / no_hits 5 / not_delivered 7
- 总耗时：None ms

| 节点 | 耗时(ms) |
|---|---:|

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2094 | ¥0.03 | **¥0.2394** |
| 全空闲 | ¥0.1047 | ¥0.03 | **¥0.1347** |

用量：输入 29716 tokens（按未命中计，偏保守）/ 输出 18743 / Search 6 次 / Fetch 0 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\evals\task-briefs-20261109\brief-m1-desert.json`（分析模块输入）
- 优先级先验：`data-test\runs\plan-ab4-20261111\A2\plan-ranked.json`
- 审核页：`data-test\runs\verify-yield3-20261112\audit.html`
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
