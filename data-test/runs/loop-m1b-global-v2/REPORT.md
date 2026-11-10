# 独立测试：含外国品牌的 12 槽检索（2026-11-10）

测试目标：在**完全隔离**的条件下，让实时检索自主决定候选（含外国品牌），跑满 12 个车槽，检验 T37 的外国品牌召回修复在完整 loop 里是否成立。

## 1. 隔离性（这次测试的硬约束）

| 检查 | 结果 |
|---|---|
| 运行目录 | 开跑前 `data-test/runs/loop-m1b-global-20261110`、`-v2` **都不存在**（`test ! -e` 断言） |
| 候选来源 | 新 brief `brief-m1b-global.json` → `plan_candidates.py` 现场跑 7 次 DeepSeek Search + 1 次 Chat，输出到新目录 `plan-m1b-global/` |
| 库内检索 | `--web-only` → `NullLibraryAdapter`；事件里 `library_scanned: 库内候选 0 个` |
| 人工种子 | 未传 `--models`；候选 100% 来自本次 Search 结果（23 条，全部带引用 URL，1 条无有效引用被丢弃） |
| 历史数据 | 未读取任何历史 run、名录、evidence 索引；新 `evidence.db` 写在本次 run 目录 |
| 重规划 | 本轮 0 次（候选池够用），不存在旧 plan 续用 |

> 注：v1 暴露了一个交付 bug（见 §5），修复后按同样隔离方式重跑 v2。两次运行目录独立，互不读取。

## 2. 规划结果（现场生成）

- 7 个查询（含 `国际品牌 6×6 全驱牵引车 车型`，由 research_unit scope 自动拼出）
- 89 条去重搜索结果 → 23 个候选车型，其中 **11 个外国品牌**：Zetros、Arocs、Actros、MOL HF/H6066、KAMAZ 65225、Scania V8、IVECO T-Way、Renault Kerax、TATRA Phoenix、Steyr 1491、TITAN Z80。

## 3. 交付结果（v2）

| 指标 | 值 |
|---|---:|
| 状态 | **DONE** |
| 交付 / 要求 | **12 / 12**，`missing=0`，`citation_only=1`，`degraded=8` |
| 单元 | u-exact **8/8**、u-intl **4/4**、u-env 0/4（全局已满，未启用） |
| 外国品牌占槽 | **5 台**：Zetros（奔驰）、Actros（奔驰）、H6066（MOL）、T-Way（IVECO）、Kerax（Renault） |
| 抓取行 / 成功 | 372 / 316 |
| 唯一图 / 过门卫 | 79 / 77 |
| ≥800 / ≥1200（行） | 80 / 40 |
| API | 28 次 Fetch 引用核验，**$0.01875**；规划 7 Search + 1 Chat **$0.00525**；合计 **$0.024** |

12 台交付车型：

`TAZ4922`、`HOWO 371hp`、`X3000`、`DFV5253`、`EQ2250AX`、`天锦 DFV2223`、`ND5250`、`Zetros 4051 AS`、`Actros 4060`、`H6066`、`T-Way 540`、`Kerax 400 T XHD`。

## 4. 身份质量（必须和“12/12”一起看）

| 身份 | 车型数 |
|---|---:|
| 有 confirmed 图 | 4（X3000、DFV5253、ND5250、H6066） |
| 只有 probable 图 | 7 |
| 没有任何核验通过的图（仅引用页兜底） | 1（TAZ4922） |

即：**交付 12/12 成立，但 8 台是 degraded**。外国品牌 5 台里只有 H6066 有 confirmed 图，其余 4 台是 probable（标题有车系/品牌 + 构型，但没写完整型号码）。

## 5. v1 暴露的 bug（已修）

第一轮（`loop-m1b-global-20261110`）跑出 **20/12**：单元配额没有硬约束，u-exact 10/8、u-intl 10/4。

- 修复：`_state_fill` 加“单元 quota 与全局槽位双上限”；新增 `test_unit_quota_caps_accepted_targets`。
- 同时修 `delivery.degraded` 统计口径：原来把“抓过图但没占槽”的车型也算进去（v2 一度出现 degraded 17 > delivered 12），现在只统计占槽车型；新增 `citation_only` 字段。
- v1 目录保留作为 bug 证据，不删除。

## 6. 结论与剩余问题

1. **外国品牌能进漏斗、也能占槽**：本轮到 5 台，证明 T37 的召回修复在完整 loop 里有效；此前“0 台”是护栏 bug + 查询写法共同造成。
2. **交付口径**：12/12 是车型槽；其中 8 台 degraded、1 台 citation_only。报告不能只写 12/12。
3. **待收紧**：`citation_only`（TAZ4922 只有 1 张未核验图 + 引用页）应要求“至少 1 张 unknown 以上的图”或降级为“待补图”，否则交付里有 0 证据车型。
4. **外国品牌身份仍偏 probable**：标题多为“奔驰Zetros实拍”，没有 4051/3343 型号码；要 confirmed 需要官网/公告页图集或更细的车型页回访。
5. **下载失败仍高**：56 行失败（403/404/防盗链），集中在经销商/B2B 图床。

## 7. 文件

`state.json`、`summary.json`、`events.jsonl`、`fetch_log.jsonl`、`api_log.jsonl`、`evidence.db`、`audit.html`（79 图，含未过门卫）、`images/`；规划侧 `data-test/runs/plan-m1b-global/{plan.json,api_log.jsonl}`。
