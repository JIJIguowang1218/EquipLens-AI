# 交付清单：run

> 任务单：`auto-20261112-205307` · 主 10 台 + 备选 4 台 · 状态 FAILED
> 交付 9/10 · degraded 8 · citation_only 2 · 备选 2 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | H6066 6×6 特种运输/牵引车 | primary | 2 | 10 | — |
| 2 | HF 8066 6×6 重型越野底盘 / 牵引车 | primary | 3 | 30 | degraded |
| 3 | 中东版 6X6 柴油重型牵引车（565 马力） | primary | 4 | 5 | degraded |
| 4 | Zetros 4051 AS 6×6 重型牵引车 | primary | 6 | 30 | degraded |
| 5 | TX 6×6 牵引车（ZZ4257V455GF1） | primary | 7 | 30 | degraded |
| 6 | Zetros 6×6 牵引头（tractor-head） | backup | 11 | 25 | degraded |
| 7 | 油田/井场特种牵引车（井场搬迁、模块运输用） | backup | 13 | 10 | degraded |
| 8 | HOWO 6×6 全驱牵引车（牵引系列） | primary | 8 | 25 | degraded/citation_only |
| 9 | KAMAZ K-65959（6×6 牵引车/prime mover） | primary | 9 | 20 | degraded/citation_only |

**备选（随包）**：

- 1. 东风 6×6 沙漠卡车（400马力、总重25吨级越野货车）（role=pool，rank=15，25 图）
- 2. TH7 6×6牵引车（role=pool，rank=17，30 图）

## 二、内部监控（不对用户）

- 下载：hits 270 / downloaded 245 / failed 25 / blocked 0 / gate_pass 240
- 缺图归因：no_hits 6 / not_delivered 2
- 总耗时：303953 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 23400 |
| FETCH | 87782 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 3321 |
| FETCH | 89566 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 10550 |
| FETCH | 89318 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| FAILED | 0 |
| WRITEBACK | 9 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2844 | ¥0.18 | **¥0.4644** |
| 全空闲 | ¥0.1422 | ¥0.18 | **¥0.3222** |

用量：输入 39291 tokens（按未命中计，偏保守）/ 输出 25725 / Search 8 次 / Fetch 28 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-clean\c1-desert-tractor\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-clean\c1-desert-tractor\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-clean\c1-desert-tractor\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-clean\c1-desert-tractor\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
