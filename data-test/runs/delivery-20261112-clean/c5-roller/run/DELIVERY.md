# 交付清单：run

> 任务单：`auto-20261112-212742` · 主 14 台 + 备选 4 台 · 状态 DONE
> 交付 14/14 · degraded 2 · citation_only 0 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | CA510PD | primary | 2 | 12 | — |
| 2 | CA610D-8 | primary | 3 | 24 | — |
| 3 | SR20MA 单钢轮压路机 | primary | 4 | 36 | degraded |
| 4 | SRS200J | primary | 5 | 30 | — |
| 5 | XS265HS | primary | 6 | 12 | — |
| 6 | SSR260C-10H | primary | 8 | 36 | — |
| 7 | XS143J | primary | 9 | 30 | — |
| 8 | 618A | backup | 15 | 18 | — |
| 9 | XS143 | backup | 16 | 30 | — |
| 10 | BW213D-40 | primary | 11 | 30 | — |
| 11 | LSS2302 | primary | 12 | 36 | — |
| 12 | HC 228D | primary | 14 | 12 | degraded |
| 13 | HC系列 | pool | 25 | 6 | — |
| 14 | XS85JIV | pool | 26 | 6 | — |

**备选（随包）**：

- 1. XS225HS（SCR）（role=backup，rank=17，18 图）
- 2. XS223JE（role=backup，rank=18，30 图）
- 3. XS202J（role=pool，rank=19，30 图）
- 4. XS262J（role=pool，rank=20，24 图）

## 二、内部监控（不对用户）

- 下载：hits 852 / downloaded 714 / failed 138 / blocked 0 / gate_pass 510
- 缺图归因：all_download_failed 1 / gate_or_verify_rejected 3 / no_hits 1 / not_delivered 9
- 总耗时：441659 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 42252 |
| FETCH | 114855 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 28442 |
| FETCH | 73804 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 31973 |
| FETCH | 78373 |
| VERIFY | 1 |
| FILL | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 7580 |
| FETCH | 64350 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 22 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.1773 | ¥0.28 | **¥0.4573** |
| 全空闲 | ¥0.0887 | ¥0.28 | **¥0.3687** |

用量：输入 29349 tokens（按未命中计，偏保守）/ 输出 14826 / Search 6 次 / Fetch 50 次

## 三、可复用中间产物（给其它环节）

- 任务单：`data-test\runs\delivery-20261112-clean\c5-roller\brief.json`（分析模块输入）
- 优先级先验：`data-test\runs\delivery-20261112-clean\c5-roller\plan-ranked.json`
- 审核页：`data-test\runs\delivery-20261112-clean\c5-roller\run\audit.html`
- 证据库：`data-test\runs\delivery-20261112-clean\c5-roller\run\evidence.db`
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
