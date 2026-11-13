# 交付清单：run

> 任务单：`auto-20261114-024643` · 主 6 台 + 备选 4 台 · 状态 DONE
> 交付 6/6 · degraded 6 · citation_only 1 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 豪沃MAX 后双桥托吊连体清障车 CSC5250TQZZT6 | primary | 1 | 14 | degraded |
| 2 | 程力重工 CLH5320TQZS6 清障车（重汽6×4底盘） | primary | 2 | 7 | degraded |
| 3 | 解放6*4清障带吊机（程力威牌CLW5250TQZCQA型清障车） | primary | 3 | 21 | degraded |
| 4 | 重汽豪沃 60吨道路清障车（ST5310TQZCZ） | backup | 7 | 21 | degraded |
| 5 | 一汽 6×4 吊车清障车（CA5250JSQP62K1L7T3E6） | backup | 8 | 35 | degraded/citation_only |
| 6 | 一汽解放 J6M 320马力 6X4 清障车(程力威牌)(CLW5250TQZC5) | backup | 9 | 35 | degraded |

**备选（随包）**：

- 1. 重汽豪沃 清障车（CLW5250TQZZ／底盘 ZZ1257N5847C）（role=backup，rank=10，42 图）
- 2. 重汽豪沃NX 黄牌清障车（RLQ5230TQZ6）（role=pool，rank=11，28 图）
- 3. 天龙 260马力 6X4 清障车（江特牌）（role=pool，rank=13，42 图）
- 4. HOWO-7 6X4 清障车（程力威牌）（role=pool，rank=14，21 图）

## 二、内部监控（不对用户）

- 下载：hits 434 / downloaded 301 / failed 85 / blocked 14 / gate_pass 266
- 缺图归因：all_download_failed 1 / no_hits 1 / not_delivered 4
- 总耗时：159165 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 6053 |
| FETCH | 32344 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 24808 |
| FETCH | 39586 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 4719 |
| FETCH | 51645 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2351 | ¥0.14 | **¥0.3751** |
| 全空闲 | ¥0.1176 | ¥0.14 | **¥0.2576** |

用量：输入 29920 tokens（按未命中计，偏保守）/ 输出 21911 / Search 6 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\h2-wrecker\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\h2-wrecker\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
