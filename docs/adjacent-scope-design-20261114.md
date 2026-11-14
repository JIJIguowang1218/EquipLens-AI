# 邻近构型检索（Adjacent-Scope Retrieval）设计分析（2026-11-14）

> 状态：**设计分析草案，未实现**。回答产品负责人 2026-11-14 的设想：
> 用户经常不需要全部槽位都是同一车型，跨类/同基础构型的参考很常见；
> 是否在输入阶段让用户决定邻近占比？是否要第一段回环？邻近关系怎么在不查表的前提下系统化？
> 相关：L1.5 关联清单（`HANDOFF.md` §3.2、`docs/association-*`）、
> 四层阶梯（`docs/ui-interaction-spec-v3.md` §9）、brief v3、`p8-idmatch` 三轮筛查。

## 0. 先回答四个问题

1. **第二段是否该收敛？** 机制上**该收敛**：交付 90/90、门卫稳定、身份分级规则稳定，
   剩余问题是"来源标题不带码"，属于来源选择与第一段候选，不是核验结构。
   第二段继续打磨的边际收益已经很低，预算应转到第一段（候选、来源、范围）。
2. **邻近关系是不是以前讨论过的？** **是**。四层阶梯 `exact → environment → platform →
   cross_vehicle` 已在 UI v3 §9 定稿；关联清单（L1.5）已经论证"提议 + 证据 + 确认"，
   并且 T18-assoc 的结论是**证据基础设施 > skill 判断**。本次不是新概念，是把阶梯变成
   **可执行的配额与回环**。
3. **要不要在输入阶段让用户定比例？** **要，但不能让用户裸填一个数字**。做法是
   "默认组合 + 可调 + 说明"，分阶段落地（先 brief/CLI，后 UI 提案卡）。
4. **要不要第一段回环？** **要，但必须是有界恢复**（bounded recovery），不是开放式重规划：
   触发条件、增量预算、放置策略、审计字段全部写死。

## 1. 现状（为什么说第二段收敛、第一段还有空间）

- 三轮全类目（`p8-idmatch-20261114` 及 r2/r3）交付率 1.000；门卫通过率 ~83%、下载失败 ~13%、
  核验拒绝 ~49%（全部是 `identity_unverified`）——**瓶颈是"标题没有可核验标识"，不是判定逻辑**。
- 标识归一化后，同一资产上旧匹配 104 → 新匹配 143 个 confirmed，严格化只拒 2 个旧命中、
  0 台交付受影响：**第二段的规则已经接近它在该输入下的上限**。
- 第一段仍有明确空间：候选池 short（h4 12–15、s6 16–24）、带码候选抓到的标题常常不带码
  （s6 的 AXOR3236 / SY5255GJB2E 全落 probable/unknown）、备选靠补抓。
- 结论：**第二段冻结机制，第一段做范围（scope）与来源（source）**。

## 2. 把你的想法拆成 7 个机制

| # | 机制 | 落点 | 主要风险 | 验收 |
|---|---|---|---|---|
| M1 | **范围组合**：主交付 = N 台 exact + M 台邻近；备选同样拆分 | brief `request.scope` + plan 配额 | 用户不知比例；exact 被挤占 | exact 槽 100%；邻近槽 ≥90% |
| M2 | **邻接推理**（无表）：从 brief 抽轴，LLM 提邻近类目 + 轴级理由 | 规划入口（新函数） | 幻觉邻接；类目错配 | 每条邻近有轴证据 + 池探测 |
| M3 | **用户确认**：默认组合 + 可调 + "为什么这样分" | 交互层（先 CLI 后 UI） | 多一轮交互被嫌烦 | 默认一键通过率 |
| M4 | **第一段回环**：证据不足 → 补邻近候选（不重跑全 plan） | engine GAP_CHECK → replan(scope) | 无限循环；破坏可比性 | ≤1 次/run，增量 ≤25% |
| M5 | **放置策略**：exact 优先、邻近只进预留槽、不进 exact 槽 | engine fill | 邻近挤掉 exact | exact integrity |
| M6 | **证据分级扩展**：邻近有自己的 A 级，不污染 confirmed | identity/契约 | 把邻近算成 confirmed | 命名空间隔离 |
| M7 | **增量交付**：只加不减，用户自选 | delivery manifest + UI | 版本混乱 | 每次增量可追溯 |

## 3. M2：邻近关系怎么"不查表"地系统化

### 3.1 用 brief 自己的四个轴，而不是类目词表

从任务单里抽取（已存在或可派生）：

| 轴 | 来源 | 例子（沙漠牵引车） | 例子（随车吊） | 例子（重型吊车） |
|---|---|---|---|---|
| `base_platform` | `request.base_platform` / `configuration` | 重卡 6×6 底盘 | 重卡底盘 + 上装吊机 | **专用吊车底盘**（非卡车） |
| `body` | `class` + `part_requirements` | 牵引车/鞍座 | 随车吊臂/支腿 | 桁架臂/回转平台 |
| `environment` | `request.environment` | 沙漠/油田 | 城市清障/吊装 | 风电/桥梁 |
| `use_case` | `request.raw` + `design_questions` | 长途运输 | 一车两用 | 大件吊装 |

### 3.2 四层阶梯 = 邻近的"距离"

| 层 | 判据 | 沙漠牵引车例 | 吊车例 |
|---|---|---|---|
| `exact` | 同型号/同族码 | 沙漠牵引车 | 随车吊 |
| `environment` | 同底盘+同功能，工况不同 | 普通牵引车跑沙漠 | 随车吊跑风电 |
| `platform` | 同底盘、上装不同 | 牵引车 vs 载货车 | 随车吊 vs 载货车（跨域，距离 2） |
| `cross_vehicle` | 仅功能件/造型语汇可比 | 牵引车 vs 自卸车 | 重型吊车 vs 随车吊（同域、底盘不同，距离 2） |

**关键**：吊车"只能在吊车域内"不是特例表，而是轴约束的自然结果——
`base_platform` 不同 ⇒ `platform` 层不可用；只剩 `cross_vehicle` 的功能件比较，
且必须标"仅参考"。规则本身不枚举任何类目。

### 3.3 提议 → 校验 → 池探测 → 配额（四步，全部可审计）

1. **提议**：LLM 输出 1–3 个邻近候选，每个必须给：
   `{class, tier, shared_axes[], different_axes[], why, confidence}`；
2. **硬校验**（代码，不用表）：
   - 必须与 exact 共享 ≥1 个硬轴（`base_platform` 或 `body`）；
   - 差异轴 ≤2；`tier` 与共享轴必须一致（例如只共享 environment 不能标 platform）；
   - 与 exact 同类目、纯品牌/纯型号差异 → 拒绝；
3. **池探测**：对每个邻近类目发 2–3 条查询（沿用现有 plan 查询模板），
   SERP 有效结果 < N（例如 5）→ 丢弃并记录 `dropped_no_pool`；
4. **配额**：按用户比例 + 置信度分配；默认 `8 exact + 2 adjacent`（主），
   备选 `2 exact + 2 adjacent`；比例可调，但 exact 槽不得少于用户下限（默认 80%）。

**产物**：`brief.request.scope = {mode, ratio, confirmed_by, neighbors[]}`；
`plan` 里每个候选带 `scope_role=exact|adjacent` 与 `tier`；
被拒的邻近也写进 `plan.scope_rejected`（审计用）。

## 4. M4：第一段回环（有界恢复）

**触发**（任一，全部来自第二段证据，不靠猜测）：

- 主槽 `degraded_ratio > 0.6`（当前已知类目常见，需按类目基线调整）；
- 某 target 在 exact 池里没有任何 accepted 图；
- `pool_short`（候选数 < 1.6×(slots+backup)）；
- 备选 filled < required（连续两轮补抓后仍 short）。

**动作**（复用现有通道，不新增状态机）：

1. `GAP_CHECK` 发现触发 → `EXTERNAL_DISCOVER` 前插入一次 `replan(scope="adjacent")`；
2. `replan` 只发邻近类目的补充查询（默认 ≤4 条），结果标记 `scope_role=adjacent`；
3. 放置按 M5：exact 优先，邻近只填"参考槽"；`exact` 槽永不被邻近占用；
4. **上限**：每 run ≤1 次回环、新增查询 ≤ 原查询 25%、新增抓取 ≤ 原 fetch 的 20%；
5. **审计**：`summary.config.scope` 记录 `trigger / neighbors / quota / accepted_adjacent`；
   `decisions` 记录每次回环；`DELIVERY` 标注每台 role+tier。

**为什么不重跑全 plan**：重跑会换掉候选集合，破坏前后可比性，且成本高；
补充查询 + 增量候选可以在同一 run 内闭合，也更容易冻结复现。

## 5. M5/M6：放置与证据（不能污染现有口径）

- **exact 槽**：现有 E1/E2 不变，`confirmed` 语义不变；
- **邻近槽**：新命名空间（不与 E1/E2 混用）：
  - `A1` 同平台（`platform`）：需底盘/构型证据 + 同族上装词；
  - `A2` 同工况（`environment`）：需工况词 + 构型；
  - `A3` 跨车型（`cross_vehicle`）：只允许功能件/造型参考，标"仅参考"，不计入 confirmed；
- 交付清单：`role=exact|adjacent`、`tier`、`evidence` 三列必须可见；
- 统计口径：`confirmed` 只统计 exact 槽；新增 `adjacent_fill`、`adjacent_relevance`（人审）。

## 6. M3：交互设计（先 CLI，后 UI）

**输入阶段**（不改用户习惯）：

```
默认提案卡：
  本次 10 台：8 台沙漠牵引车（精确）+ 2 台邻近参考（普通牵引车，同 6×6 底盘）
  理由：同底盘、同牵引用途；环境特化件不同（防护/进气）
  [保持默认] [调整比例] [只要精确]
```

- 默认值来自 `scope` 推理与池探测，不是固定表；
- 用户不选 = 保持默认（8+2）；选"只要精确" = 现有链路，**文案不得写"同类型"**；
- 一旦确认，`scope.confirmed_by=user` 写入 brief，后续可审计。

**交付后**（增量，不删除）：

```
已交付 10 台（8 精确 + 2 邻近）。要更多哪一类？
[更多沙漠牵引车 +2] [更多邻近参考 +2] [就这样]
```

- 追加走新的 delta run（`page_budget.slots=2`），不修改原交付；
- 交付版本号递增，界面让用户自选，**任何调整都是增量**。

## 7. 影响面矩阵

| 阶段/文件 | 改动 | 是否破坏现有 |
|---|---|---|
| brief schema | 新增可选 `request.scope`（默认 absent=现状） | 否（向后兼容） |
| `plan_candidates.py` | 支持 scope 配额、邻近候选标记、`scope_rejected` | 否（默认行为不变） |
| `retrieval_engine` | `replan(scope)`；fill 放置策略；config 记录 | 否（仅当 scope 存在） |
| `DELIVERY`/manifest | role/tier/evidence 三列；增量版本 | 否（新增列） |
| identity | 邻近 A1–A3 命名空间，不影响 E1/E2 | 否（新函数） |
| 台账/评估 | 新 KPI、scope 字段入 INDEX | 需加列，不重算历史 |
| UI | 提案卡 + 增量按钮 | 后置 |

## 8. 指标与验收

| 指标 | 定义 | 预注册门槛 |
|---|---|---|
| `exact_slot_integrity` | exact 槽里没有邻近图 | **100%** |
| `adjacent_fill` | 邻近槽实际填满率 | ≥90% |
| `adjacent_relevance` | 人审"这张图对造型分析有用"的比例 | ≥70%（每 case 抽 6 张） |
| `degraded_ratio`（exact 槽） | 不得因邻近上升 | ≤ 现状 +3pp |
| `cost_delta` | 相对现状的单 case 成本 | ≤ +20% |
| `replan_count` | 每 run 回环次数 | ≤1 |

**反例预注册**：若 `exact_slot_integrity < 100%` 或 `adjacent_relevance < 50%`，
则 scope 默认关闭，回退现状。

## 9. 实验计划（严谨性优先）

**P0（0 成本，离线）**：用现有 10 类目的 plan/池做"范围组合"回放——
把 c3 牵引车当 c1 的 `platform` 邻近、c2 正面吊当 h4 的 `cross_vehicle` 邻近，
按 8+2 重新分配槽位（不抓图），检查：exact 槽完整性、邻近候选供给、标记是否正确。

**P1（CLI，真实链路）**：brief 加 `scope`（默认关），c1/c2/h4 三 case A/B
（现状 vs 8+2），各 1 次；指标见 §8，人审邻近图 6 张/case。
成本预估：+4 查询 + ~20 抓取/case，约 +¥0.1。

**P2（产品化）**：提案卡 + 增量交付 + 交付页 role/tier 标注。

## 10. 风险清单

1. **用户不理解"邻近"**：默认 + 一句理由 + "只要精确"一键回退；
2. **邻近错域**（吊车混卡车）：靠硬轴约束与池探测，不靠类目表；
3. **证据污染**：邻近只进 A1–A3，不写 confirmed；
4. **exact 被挤占**：配额与放置策略硬约束；
5. **成本/时延**：回环上限 + 增量 ≤25%；
6. **可比性**：scope 默认关，历史 run 不受影响；
7. **文案误导**：不得把邻近写成"同类型"，必须标"参考"与 tier。

## 11. 与既有讨论的关系（避免重复造轮子）

- 四层阶梯：`ui-interaction-spec-v3.md` §9（已定稿，直接复用）；
- 关联清单：`HANDOFF.md` §3.2（缺口评估 → 关联提案 → 用户确认 → 检索）；
- 证据优先：`association-skill-archive.md`（skill 降级、证据基础设施 > 判断）；
- **不要复活**：`K3/K4`（part_views/part_axes 已毙）、类目词表/穷举表（`vocabulary-policy`）；
- 本设计**不新增 skill、不新增词表**，只把阶梯变成配额、放置与回环。

## 12. 需要产品负责人拍板的 5 件事

1. **默认比例**：8+2（推荐）还是 10+0 默认、8+2 作为选项？
2. **邻近是否进正式交付**：进主交付（标 tier）还是只进"参考栏"？
3. **回环触发**：允许引擎自动触发（有上限），还是必须用户点"补邻近"？
4. **人审门槛**：`adjacent_relevance ≥70%` 是否接受作为上线门槛？
5. **吊车域**：是否接受"由轴约束自然得出、不写死域表"（推荐）？
