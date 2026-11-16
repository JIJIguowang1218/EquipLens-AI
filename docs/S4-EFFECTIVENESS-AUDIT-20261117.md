# S4 后端 Loop 生效性检查（2026-11-17）

> 问题：Loop 做完后，哪些机制真正在正式链路里生效？哪些只是“记录/提示”但没有执行效果？
> 口径按 `AGENTS.md` §5（生产生效 / 生产可用 / 原型 / 计划）。

## 1. 结论先行

**S4 的入口（建单、会话、持久化、路由、守卫）是生效的；但 patch 执行只覆盖一部分。**
以下动作目前**只记录、不改变引擎/交付**，不能按“生产生效”对外承诺：

| 动作 | 引擎/runner 是否执行 | 现状 | 建议级别 |
|---|---|---|---|
| `plan.quantity`（总量） | ❌ 无分支、不重排 | **已 gate：Session 返回 clarify，不产 patch** | **gate（未执行）** |
| `plan.configuration`（构型） | ❌ | **已 gate：clarify** | **gate（未执行）** |
| `scope.ratio`（范围比例） | ❌ | **已 gate：clarify** | **gate（未执行）** |
| `session.reset`（整批重来） | ❌ 只把 delivered 标 superseded | **已 gate：clarify** | **gate（未执行）** |
| `session.pause`（暂停） | ❌ runner 不检查 | **已 gate：clarify** | **gate（未执行）** |
| `delivered.remove/replace` | ⚠️ 只标 superseded + `pending_replenish` | 无 delta 重抓/替换 | **原型（部分）** |
| `verify.blacklist` / `fill.replace` | ⚠️ 只标记 | 无重抓 | **原型（部分）** |
| `delivery.report` | ⚠️ 只记 `preferences.delivery` | 不生成文件 | **计划/原型** |
| `fetch.filters.views/parts` | ❌（产品决定） | 识别为 clarify | **计划（待后续版本开发）** |

## 2. 真正生效的部分

- `SessionRunner` / `Session`：建单（M6）、消息、pending、持久化、续跑、交付摘要；
- `session_router`：LLM 提议 + capability/stage/quantity/复合/UI 引导守卫；
- 引擎 patch 子集：`plan.add_targets`、`fill.quota`、`plan.negative`（仅 FILL 过滤）、
  `fetch.filters.quality`（后续 fetch 的 verifier）、`plan.quantity_per_model`（今天补上 runner 白名单）；
- 这些是**生产生效（仅后端入口）**；但 `quality`/`negative`/`fill.quota`/`per_model` 是
  **部分生效/尽力而为**，不是精确重排。

## 3. 今天检查中发现的接线问题（已修）

- `plan.quantity_per_model` 有引擎分支，但 `SessionRunner.ENGINE_TARGETS` 未包含它 →
  之前只会被当成 session-only，**永远到不了引擎**。已加入白名单，并补 runner 单测（12/12）。

## 4. 文档/口径冲突（已修）

- `HANDOFF.md` 顶部仍写 `S4=planned`、旧计数、旧“下一步 M4.3”；
- `CURRENT-ARCHITECTURE.md` 仍写“S4 planned”；
- `CODE-INDEX.md` 仍把 Session 叫“入口原型 / Session（原型）”；
- `AGENTS.md` 写“六个词”，但表里有 7 行（含“计划”）；
- `STAGES.md` S4 虽写“仅后端入口”，但没有写“patch 只覆盖子集”。

## 5. Gate 已落地（2026-11-17）

`Session.interrupt` 对上述 5 个 hard 动作统一返回 `clarify` + “重开一轮/先不操作”，
并记录 `gated_action` 事件；`SessionRunner.summary` 增加 `gated_actions` 计数。
不产生 patch、不静默记录。真实重排/重跑留待后续（BL-026）。

## 6. 建议下一步（阻塞项）

在 delta 编辑之前，先处理**无效果的 hard 动作**，否则用户说“改成 12 台”后系统会记录但交付不变：

1. **短期（推荐）**：把 `plan.quantity` / `plan.configuration` / `scope.ratio` / `session.reset` /
   `session.pause` 改为 **clarify/explain**（“当前版本需要重建任务，是否重开一轮？”），
   避免静默失败；或
2. **实现**：在 runner 里对 hard 动作触发**重新建 plan/重跑**（工作量大，放 delta 之后）；
3. delta 编辑按原计划实现：`delivered.replace/remove` 真正触发小 delta 重抓 + 合并交付。

记录：**BL-025**（hard 动作 no-op 的 gate/实现）、**BC-S4-016**。
