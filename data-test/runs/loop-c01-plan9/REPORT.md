# C01 · 核验重构后 12 槽交付（2026-11-10）

## 改了什么（对应 6 个核验问题）

| # | 原问题 | 改法 |
|---|---|---|
| 1 | 品牌兜底不生效（`wrong_identity` 无条件追加） | 删除无条件缺陷；身份改为三档 |
| 2 | 身份二元判断 | `confirmed`（型号码/整名命中）/ `probable`（品牌+构型 或 两个非通用词）/ `unknown` |
| 3 | 只信图片标题 | 引用页已证实车型（`citation_ok`）→ 该车有图即可占槽 |
| 4 | 构型只看第一个 | 模型里任一构型命中即可；标题明确写了别的构型才判 `wrong_config` |
| 5 | 部件视角参与否决 | 保持 warning，不参与 accepted |
| 6 | 底盘图当整车 | `not_whole_vehicle` warning（可占降级位） |

另外：重规划上限从 2 次提到 4 次（成本仍很低）。

## 结果

| 指标 | 值 |
|---|---:|
| 候选目标 | 31（含 4 次重规划） |
| **车槽** | **12 / 12，DONE**（exact 9、environment 3） |
| 唯一图 | 38 |
| 过门卫（v4） | 34 |
| 标准 ≥800 | 10 |
| 高清 ≥1200 | 5 |
| 下载失败 | 24 |
| API 调用 | 40 次，**$0.02625** |

### 离线回放对比（同一批已抓资产，只换核验逻辑）

| 口径 | 可占槽车型 |
|---|---:|
| 旧核验 | 9 |
| 新核验 | **13** |

恢复的 6 台：DFV2223（天锦底盘）、DFV5253、EQ2251AX、东风 EQ2102N、EQ2250AXJ（底盘）、北奔 ND2250FD6J7Z01。

## 仍然存在的问题

1. ~~审核页徽章仍只标“过门卫”，未标“已占槽”~~ → 已改（T37）：审核页现在分「过门卫 / 入选交付 / 占槽车型」，未交付车型标“（未占槽）”，并可筛“仅过门卫”。
2. `unknown` 身份仍不进正式槽；若交付不足，需要“降级槽”策略才能兜底。
3. 图仍偏小（34 张过门卫里 10 张 ≥800）。
4. 底盘/部件图可占降级位，但未在报告里按档位统计。

## 交付口径（T37 补）

`summary.delivery` = `{required: 12, delivered: 12, missing: 0, degraded: 7, status: complete}`。

“delivered 12” 是**车型槽**，不等于 12 台都有 confirmed 图：7 台（TAZ4922、DFV5253、DFV2223、大力神 dCi385、EQ2250AXJ、天锦 ISLe375、大力神油田底盘）只有 probable 图，靠引用页兜底占槽。要看 confirmed 比例，以 `verifications` 的 identity 为准。

## 日志

`api_log.jsonl`（40 次/$0.026）、`citation_log.jsonl`、`replan_log.jsonl`、`events.jsonl`、`fetch_log.jsonl`、`state.json`、`evidence.db`、`images/`、`audit.html`。
