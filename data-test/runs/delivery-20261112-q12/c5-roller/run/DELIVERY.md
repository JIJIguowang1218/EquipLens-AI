# 交付清单：run

> 任务单：`auto-20261112-192732` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 1 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA610D | primary | 1 | 28 | — |
| 2 | CA510PD | primary | 2 | 14 | — |
| 3 | SR26H-G | primary | 3 | 42 | — |
| 4 | LG526A9 | primary | 4 | 14 | — |
| 5 | RS8220H | primary | 5 | 14 | — |
| 6 | BW 226 D-5 CL | primary | 6 | 21 | — |
| 7 | 322 | primary | 7 | 21 | degraded/citation_only |
| 8 | XS395 | primary | 8 | 42 | — |
| 9 | SR22 | primary | 9 | 42 | — |
| 10 | XS225JIV | primary | 11 | 7 | — |
| 11 | XS202J | primary | 12 | 35 | — |
| 12 | XS222 | primary | 13 | 42 | — |
| 13 | LSS2302 | primary | 14 | 42 | — |
| 14 | CA610D-8 | backup | 15 | 21 | — |

**备选（随包）**：

- 1. XS223JE（role=backup，rank=16，35 图）
- 2. SRS200J（role=pool，rank=21，35 图）
- 3. XS142（role=pool，rank=22，14 图）
- 4. RS7220（role=pool，rank=23，14 图）

## 二、内部监控（不对用户）

- 下载：hits 917 / downloaded 756 / failed 155 / blocked 0 / gate_pass 616
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 2 / no_hits 1 / not_delivered 10
- 总耗时：574126 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 22561 |
| FETCH | 152667 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 14072 |
| FETCH | 37612 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 31944 |
| FETCH | 40820 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 39741 |
| FETCH | 234690 |
| VERIFY | 1 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 12 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2125 | ¥0.31 | **¥0.5225** |
| 全空闲 | ¥0.1062 | ¥0.31 | **¥0.4162** |

用量：输入 41563 tokens（按未命中计，偏保守）/ 输出 16171 / Search 8 次 / Fetch 54 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-q12\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-q12\c5-roller\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-q12\c5-roller\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-q12\c5-roller\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
