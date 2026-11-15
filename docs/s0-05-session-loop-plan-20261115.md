# S0-05 规划：Session / Loop（多轮打断与增量重跑）

> 状态：规划稿（2026-11-15），未实现。对应 badcase/决策：S0-05（意图识别）、S4（Loop）。
> 原则：**引擎保持确定性状态机；Session 是外层编排**；先自己实现，LangGraph 作为备选。
> 相关：`docs/STAGES.md`（S4 目前 planned）、`docs/external/doubao-consult-decisions.md` §5。

## 0. 目标与非目标

**目标**
1. 用户可在任何时刻输入新要求（发送即打断），系统识别“改什么”，只重跑受影响节点；
2. 已交付内容不被重复、不被静默删除；新增/替换以 delta 形式出现；
3. 状态、数据、版本可回放；崩溃后可从 checkpoint 恢复；
4. 与现有引擎状态机配合，不引入第二套互相打架的状态。

**非目标（本轮不做）**
- 不改检索策略/排序/门卫；
- 不做前端，只做 API/CLI 与测试；
- 不引入多 agent；LangGraph 只在 M6 之后评估。

## 1. 两层状态机

```
Session（外层，跨 run）                      Job（内层，现有引擎）
IDLE                                        BRIEF_READY
 → ANALYZING（解析/补丁）                     → LIBRARY_SEARCH
 → CLARIFYING（最多 1 个问题）                → FETCH
 → PLANNING                                  → VERIFY
 → RUNNING  ────────── checkpoint ─────────→  → FILL
 → PAUSED（取消/等待）                        → GAP_CHECK
 → DELIVERED                                 → DEGRADE / DONE
 → FAILED
```

- **Session 不复制引擎状态**：只保存 `active_run_id`、`last_checkpoint`、`brief_version`、
  `delivered`、`patches`、`events`；
- 引擎在每个状态边界写 `state.json` + `events.jsonl`（已有），Session 读它做决策；
- 任何 patch 只能在**状态边界**生效（soft）或在**显式 cancel** 后生效（hard）。

### Session 事件与转移

| 事件 | 从 | 到 | 动作 |
|---|---|---|---|
| `USER_MSG`（新任务） | IDLE/DELIVERED | ANALYZING | 解析 TaskSpec，生成 brief v1 |
| `PATCH_READY`（可执行） | ANALYZING/RUNNING/PAUSED | PLANNING | 生成新 brief 版本，计算受影响节点 |
| `NEED_CONFIRM`（破坏性/低置信） | ANALYZING | CLARIFYING | 发 1 个问题（2–4 选项 + 默认） |
| `ANSWER` | CLARIFYING | PLANNING | 合并答案，继续 |
| `RUN_START` | PLANNING | RUNNING | 启动/恢复 Job |
| `CHECKPOINT` | RUNNING | RUNNING | 保存；若有排队 patch → 应用 |
| `INTERRUPT`（hard） | RUNNING | PAUSED | 取消在途请求，保存 checkpoint |
| `RESUME` | PAUSED | RUNNING | 从 last_checkpoint 继续 |
| `DELIVERED` | RUNNING | DELIVERED | 固化交付；delta 追加 |
| `ERROR` | 任意 | FAILED | 记录，保留可恢复点 |

## 2. 反馈分类与节点映射（F1–F9）

| 类型 | 例子 | Patch 目标 | 起始节点 | 默认打断 |
|---|---|---|---|---|
| F1 视图/角度 | “要正脸” | `fetch.filters.views` | FETCH 或 FILL 重排 | soft |
| F2 款型纠错 | “第 3 张不是沙漠版” | `verify.blacklist` + `fill.replace` | VERIFY → FILL | soft（目标明确不确认） |
| F3 质量 | “高清、不要水印” | `fetch.filters.quality` | FETCH/FILL | soft |
| F4 同型号扩充 | “这个型号还有图吗” | `fill.quota` / `fetch.more` | FETCH | soft |
| F5 品牌/车型扩充 | “再找陕汽的” | `plan.add_targets` | EXTERNAL_DISCOVER/plan | soft |
| F6 排除 | “不要挂车/去掉北奔” | `plan.negative` / `fill.filter` | plan + FILL | soft |
| F7 部件细节 | “看前脸格栅” | `fetch.parts` | FETCH | soft |
| F8 范围/配额 | “多来点邻近/只要精确” | `scope.ratio` | plan | hard（改变任务定义） |
| F9 交付/呈现 | “再补 2 台/按品牌分组” | `presentation` / `fill.quota` | FILL/交付 | soft |
| FX 破坏性 | “删掉第 2 张/换掉已交付的” | `delivered.remove` | 目标明确：不确认；不明确：确认 | soft（降级不删） |
| FX2 重置 | “全部重来” | `session.reset` | 先问 1 个问题 | hard + confirm |

**判定规则**（两个轴，不要混）：

1. **约束强度**：是否必须满足（“不要挂车”是硬约束，必须排除；“要正脸”是软偏好）；
2. **打断类型**：是否要取消在途/重排计划（范围/数量/构型/重置=hard；排除/视角/质量/交付编辑=soft）。

- 交付编辑目标明确（“第 3 张”“该型号”）→ **不必确认**，标 `superseded` 并补新图，交付前不删除；
- 目标不明确（“删掉一张”）→ 先问 1 个问题；
- “全部/整批 + 重来/换”→ 先问 1 个问题，不自动 reset；
- 排除项：`enforce=hard`、`hard=False`，在 checkpoint 应用 FILL 过滤 + 下一轮负词。

## 3. Patch 契约

```json
{
  "patch_id": "p-20261115-0003",
  "base_version": 3,
  "target": "fetch.filters.views",
  "op": "set",
  "value": ["front"],
  "confidence": 0.92,
  "destructive": false,
  "source_msg_id": "m-0007",
  "note": "用户说‘要正脸’"
}
```

规则：
- `target` 白名单（见 §2）；`value` 过 schema；
- 一条消息最多 3 个 patch；超过先拆/先问；
- 冲突：新 patch 覆盖旧值，旧值写 `superseded_by`；
- 幂等：`source_msg_id + patch_id` 唯一，重复消息不重复执行；
- 破坏性：`destructive=true` 必须带 `confirm_token` 才执行。

## 4. 打断语义

- **soft（默认）**：当前节点跑完 → 到 checkpoint → 应用 patch → 只重跑受影响节点；
  已完成节点的结果按 `(brief_hash, node, params)` 命中缓存，不重复抓取；
- **hard（范围/类目切换、删除已交付）**：取消在途请求（网络/下载），保存 checkpoint，
  应用 patch 后从**受影响节点的入口**恢复；
- 交付**只增不减**：旧资产标 `superseded`，不物理删除；替换表现为“新增 + 旧标废弃”；
- 去重键：`(url, sha1, model, target)`；跨 run 维护 `delivered_keys`；
- 每轮 delta 预算：查询 ≤25%、抓取 ≤20%；超限提示用户确认。

## 5. Session 数据模型

```json
{
  "session_id": "s-20261115-01",
  "state": "RUNNING",
  "brief_versions": [{"v": 1, "hash": "...", "path": "..."}],
  "active_brief_version": 3,
  "active_run_id": "run-...",
  "last_checkpoint": {"state": "FETCH", "run_id": "...", "at": "..."},
  "delivered": [{"target": "...", "asset_id": "...", "round": 1, "status": "active|superseded"}],
  "blacklist": {"assets": [], "models": []},
  "preferences": {"views": ["front"], "brands": []},
  "patches": [],
  "events": []
}
```

- 持久化：先 JSON（`data/sessions/<id>.json`，运行时不入库）；稳定后再评估 SQLite；
- 版本：brief 每次 patch 生成新版本；节点缓存按版本 hash 复用；
- 回放：`events.jsonl` append-only，可重建状态。

## 6. Router（意图识别）

输入：用户消息 + `session_summary`（当前 brief 版本、已交付摘要、运行状态、偏好）。
输出：

```json
{
  "intent": "modify",
  "patches": [{"target": "fetch.filters.views", "op": "set", "value": ["front"], "confidence": 0.92}],
  "destructive": false,
  "clarify": null
}
```

- LLM 输出 + 规则校验（白名单、schema、冲突、最多 3 条）；
- `confidence<0.6` 或 `destructive` → 只问 1 个问题（2–4 选项 + 默认）；
- 不把整段历史塞给模型，只给摘要 + 最近 3 轮 patch；
- 识别不了 → 当成“新任务”而不是猜 patch（防误删）。

## 7. 编排方式：自己实现 vs LangGraph

| 维度 | 自己实现（推荐先做） | LangGraph |
|---|---|---|
| 确定性/审计 | 直接复用现有 state/events | 需要映射两套状态 |
| 打断/恢复 | 自己写 checkpoint（已有基础） | 原生支持 |
| 增量 patch/最小重跑 | 简单直接 | 图表达更重 |
| 多 agent/复杂分支 | 暂不需要 | 强项 |
| 依赖/学习成本 | 0 | 新增依赖 |

**结论**：M2–M5 自己实现（Session 状态机 + Router + JobRunner）；M6 后如果出现
“多路并行/复杂人机回路/多 agent”，再把 Session 层换 LangGraph，Job 仍是节点。
验收标准：`stages.json` S4 从 planned → active，`STAGES.md` 记录版本。

## 8. API / CLI

```python
s = Session.create(text, context=None)
s.interrupt("再加两台徐工的")      # 入队/立即应用由 soft/hard 决定
s.status()                        # state / brief 版本 / 已交付 / 待确认
s.resume()
s.deliver()
```

CLI（测试用）：

```bash
PYTHONPATH=src python scripts/run_session.py --session tmp/session.json --input "..." --fake
```

## 9. 测试计划（先无网络，再 FakeWorld，最后 live）

### 单元（不联网）
| ID | 用例 | 断言 |
|---|---|---|
| T1 | 初始输入 → TaskSpec → brief v1 | 状态 PLANNING，版本 1 |
| T2 | 运行中“要正脸” | patch 入队，checkpoint 生效，只重跑 FETCH/FILL |
| T3 | “删掉第 2 台” | 进 CLARIFYING，1 个问题，未执行 |
| T4 | cancel → resume | 从 last_checkpoint 恢复，不重头 |
| T5 | 重复消息 | 幂等，patches 不重复 |
| T6 | 冲突 patch | 新覆盖旧，`superseded_by` 存在 |
| T7 | 已交付资产 | 再次出现被去重 |
| T8 | 版本缓存 | 未变节点不重跑 |
| T9 | 超过轮次上限 | 拒绝并提示 |
| T10 | 非法 target | 拒绝，状态不变 |

### 集成（FakeWorld）
| ID | 场景 | 断言 |
|---|---|---|
| T11 | 运行到 FETCH 时加品牌 | 只重跑受影响 target；delta 查询 ≤25% |
| T12 | 纠正错误型号 | blacklist 生效，FILL 替换，交付无重复 |
| T13 | 删除已交付 | 先确认；确认后标 superseded，不物理删 |
| T14 | 崩溃恢复 | 从 checkpoint 继续，事件可回放 |
| T15 | 多轮增量 | 交付只增不减，版本递增 |

### E2E（live，3 个 case，预算内）
| ID | 场景 | 指标 |
|---|---|---|
| T16 | 10 台 → 加 2 台同型号 → 修 1 台 | 意图准确、patch 正确、重复 0、exact 完整 100% |

### 指标门槛
- Router 意图/patch 正确率 ≥85% / ≥90%（离线 30 条）；
- 重复交付 **0**；exact 槽完整率 **100%**；
- delta 查询 ≤25%、抓取 ≤20%；单轮成本增幅 ≤20%；
- 破坏性操作 100% 确认。

## 10. 实验与里程碑

| 阶段 | 内容 | 产出 |
|---|---|---|
| M1 | 本规划 + 契约（patch/状态） | 本文档 |
| M2 | `session.py` 状态机 + 单测 T1–T10 | 无网络可跑 |
| M3 | Router + 离线 30 条（V10） | 意图/patch 指标 |
| M4 | FakeWorld 集成 T11–T15（V11） | 无网络 E2E |
| M5 | live 3 case（V12） | 成本/重复/增量指标 |
| M6 | 落 `stages.json` S4 active + 接 `build_brief` session 上下文 | 正式链路 |

## 11. 风险与拍板点

**风险**：Session 与引擎状态重复；Router 误判导致误删；上下文过长/过期；无限重跑；
缓存键不稳导致重复抓取。

**需要拍板**：
1. ~~soft/hard 默认~~ **已拍板**：范围/数量/构型/重置=hard；排除=约束 hard + 打断 soft；
   交付编辑目标明确不确认、不明确才确认；交付前不删除。
2. 单 session 最大轮次（建议 5）与 delta 预算（25%/20%）？
3. 破坏性操作是否一律二次确认（建议是）？
4. 持久化先用 JSON（建议）还是直接 SQLite？
5. 何时评估 LangGraph（建议 M6 后，出现并行/多 agent 再换）？
6. `generate_brief` 是否接收 session context（BL-001 的前置）？
