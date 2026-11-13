# 交付清单：run

> 任务单：`auto-20261112-210206` · 主 10 台 + 备选 4 台 · 状态 DONE
> 交付 10/10 · degraded 7 · citation_only 5 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 合力 RSH4532-Vo 正面吊运机 | primary | 2 | 30 | — |
| 2 | XCMG 45吨级集装箱正面吊 | primary | 3 | 15 | degraded/citation_only |
| 3 | DRU450-570 | primary | 4 | 5 | — |
| 4 | SMV 4542 TB4 BH | primary | 5 | 30 | degraded/citation_only |
| 5 | Kalmar DRD420-65S6 正面吊运机 | primary | 6 | 15 | degraded/citation_only |
| 6 | LG420FC4 | primary | 7 | 20 | degraded/citation_only |
| 7 | 临晟 CRS450 集装箱正面吊 | backup | 11 | 10 | degraded/citation_only |
| 8 | RSH4528-VO2 | backup | 12 | 5 | — |
| 9 | 徐工港机正面吊（K系列） | backup | 13 | 20 | degraded |
| 10 | Hyster RS45 正面吊 | pool | 15 | 25 | degraded |

**备选（随包）**：

- 1. 卡尔玛集装箱正面吊（RS）（role=pool，rank=19，20 图）
- 2. 利勃海尔（Liebherr）正面吊（role=pool，rank=21，25 图）
- 3. 科尼（Konecranes）正面吊（role=pool，rank=22，15 图）
- 4. 诺尔正面吊（RS）（role=pool，rank=20，15 图）

## 二、内部监控（不对用户）

- 下载：hits 510 / downloaded 440 / failed 65 / blocked 5 / gate_pass 290
- 缺图归因：gate_or_verify_rejected 4 / no_hits 1 / not_delivered 6
- 总耗时：392293 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4319 |
| FETCH | 90002 |
| VERIFY | 4 |
| FILL | 1 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 19933 |
| FETCH | 131927 |
| VERIFY | 2 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 53815 |
| FETCH | 92285 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2656 | ¥0.22 | **¥0.4857** |
| 全空闲 | ¥0.1328 | ¥0.22 | **¥0.3528** |

用量：输入 39793 tokens（按未命中计，偏保守）/ 输出 23258 / Search 8 次 / Fetch 36 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\c2-reach-stacker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-20261114\c2-reach-stacker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
