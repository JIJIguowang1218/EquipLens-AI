# 检索中引擎：P0–P1 实现记录（2026-11-09）

| 属性 | 内容 |
|---|---|
| 阶段 | **检索中**（P0 契约 + P1 状态机） |
| 状态 | P0 ✅ / P1 ✅（夹具，不联网） |
| 测试 | `tests/test_retrieval_engine.py` 10/10 通过 |
| 位置 | `src/equiplens/retrieval_engine/` |
| 不包含 | 真实通道、视觉模型、数据库读写、UI、LangGraph |

---

## 1. 做了什么

### P0 契约

- 任务单 v0.3：`part_requirements`（含 `location` / `design_relevance` / `views` / `accept`）、`research_units`、`tiers`、`budget`、`stop_rules`、`negative`、`strategy_ref`、`assumptions`；
- 状态/事件/证据的 JSON Schema：
  - `schemas/task-brief-v3.schema.json`
  - `schemas/retrieval-state.schema.json`
  - `schemas/retrieval-event.schema.json`
- ~~策略骨架：`data/retrieval_strategies.json`~~（**2026-11-12 已删除**：加载后从不消费，属死配置，见 `docs/killed-strategies.md` K14）；
- 证据表契约：`db/retrieval_tables.sql`（`image_evidence`、`asset_part_feasibility`，P2 才接入）；
- 适配器协议 + 夹具实现：`LibraryAdapter` / `SearchAdapter` / `FetchAdapter` / `Verifier`。

### P1 状态机

- 状态：`BRIEF_READY → LIBRARY_SEARCH → FETCH → VERIFY → FILL → GAP_CHECK → EXTERNAL_DISCOVER → DEGRADE → DONE/FAILED → WRITEBACK`；
- 检查点：`state.json` 原子写；事件：`events.jsonl`；证据：`evidence.json`；汇总：`summary.json`；
- 幂等：按 `asset_id` 去重；已完成的 run 直接复用；
- 预算：`max_queries`、`max_models`（P1 只用查询/候选计数，收益率停止在 P3 补）；
- CLI：`python -m equiplens.retrieval_engine`。

---

## 2. 文件

| 文件 | 作用 |
|---|---|
| `src/equiplens/retrieval_engine/contracts.py` | Brief / PartRequirement / ResearchUnit / Target / Asset / Verification；校验与加载 |
| `src/equiplens/retrieval_engine/state.py` | 初始状态、RunStore（state/events/evidence/summary） |
| `src/equiplens/retrieval_engine/adapters.py` | 适配器协议 + `FakeWorld`（夹具） |
| `src/equiplens/retrieval_engine/engine.py` | 检索 loop / 状态转移 / 填槽 / 降级 |
| `src/equiplens/retrieval_engine/cli.py` | 夹具 CLI |
| `data-test/retrieval-fixtures-20261109/` | 演示 brief + 假世界 |
| `tests/test_retrieval_engine.py` | 10 个离线测试 |
| `schemas/task-brief-v3.schema.json` | 任务单契约 |
| `schemas/retrieval-state.schema.json` | 状态契约 |
| `schemas/retrieval-event.schema.json` | 事件契约 |
| ~~`data/retrieval_strategies.json`~~ | 已删除（K14，死配置） |
| `db/retrieval_tables.sql` | 证据表 DDL（P2 用） |

---

## 3. 怎么跑

```bash
# 方式 A：主 CLI 子命令
PYTHONPATH=src python -m equiplens retrieval-run \
  --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
  --fixtures data-test/retrieval-fixtures-20261109/world-desert.json \
  --run-root data-test/runs --run-id p1-demo

# 方式 B：模块 CLI
PYTHONPATH=src python -m equiplens.retrieval_engine \
  --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
  --fixtures data-test/retrieval-fixtures-20261109/world-desert.json \
  --run-root data-test/runs --run-id p1-demo

# 测试
PYTHONPATH=src python tests/test_retrieval_engine.py
```

演示输出：`u-exact 2/2`、`u-env 1/1`、`DONE`；运行产物在 `data-test/runs/p1-demo/`。

---

## 4. 关键设计决定

### 4.1 “全局槽位”与“unit 配额”分开

- `request.page_budget.vehicle_slots` 是**页面要的槽数**（报告约束）；
- `research_units[].quota` 是**每个搜索单元打算找几台**（检索目标）；
- **是否 DONE 看全局槽位**，不是看每个 unit 是否达标；
- unit 未达标但全局槽已满 → 仍然 DONE，但 `gaps` 里会保留“这个 unit 没找满”，给后续补检/报告用。

这条是 P1 测试暴露出来的：如果把 unit 配额当硬门槛，exact 单元失败会拖垮整体，即使 environment 已经补上页面槽位。

### 4.2 库内优先

`LIBRARY_SEARCH` 先跑；库内候选也走 `FETCH → VERIFY → FILL`，与外部候选同一套验收。库内全满足时不触发外检。

### 4.3 状态与事件分离

- `state.json` 是“现在在哪、还剩什么”；
- `events.jsonl` 是“怎么走到这里的”；
- `evidence.json` 是“最终哪些证据被接受”。

三者分开，方便回放、审计、调试。

### 4.4 P1 不做的

- 不做真实 360/百度/Bing 适配器（P3）；
- 不做部件级视觉/身份核验（P4）；
- 不做收益率停止（P3 补）；
- 不做 cross 层（P1 只跑 exact/environment）；
- 不做 LangGraph/Burr/Temporal（先薄状态机）。

---

## 5. 已知限制

1. `max_rounds` 还没真正驱动循环；P1 只按 tier 降级，不做同层多轮。
2. `RETRY` 只在候选子状态图里有；P1 代码没有独立 RETRY 状态，核验不通过就不占槽，直接进下一层。
3. `gaps` 是 unit 级缺口，不等于页面槽位缺口；summary 里 `slots` 才是页面口径。
4. 事件只记状态转移；决策细节在 `state.decisions` 里。
5. 夹具是“假世界”，不代表真实通道行为；P3 才接真实数据。

---

## 6. 下一步（P2）

- `image_evidence` / `asset_part_feasibility` 落 SQLite；
- 人工录 50 条库内证据；
- 库内检索按部件/位置/视角/分辨率返回候选；
- 用真实库快照替换 `FakeWorld.library_targets`，外检仍用夹具。

P2 完成后再做 P4 的 100 张部件级视觉实验。
