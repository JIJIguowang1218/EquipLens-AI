# M1 最小 loop：沙漠牵引车（2026-11-10）

> 目标：用真实输入跑通 **任务单 → 候选 → 检索 → 核验 → 填槽 → 缺口判定**，看它能不能收敛、缺口长什么样。
> 这一轮**不是**产品实现，是 loop 的第一次实跑 + 排障。

## 1. 输入从哪来

- 任务单来自 T19 纸面测试的 **C01 沙漠油田牵引车**（`data-test/evals/task-briefs-20261109/BRIEFS-5.json`）；
- 原输入：`沙漠牵引车（前脸、登车踏步、大灯、前轮拱、防护栏、保险杠）`；
- 转成引擎 brief：`data-test/evals/task-briefs-20261109/brief-m1-desert.json`
  - 3 个车槽（`vehicle_slots=3`）、2 个单元：`u-exact`（quota 2，卡 bumper/side_guard/step）、`u-env`（quota 1，卡 side_guard/step）；
  - 6 条部件要求（保险杠/防护栏/踏步/大灯/前轮拱/格栅）+ 1 条区域要求（前脸整体）；
  - 层级：`exact → environment`，预算 12 查询 / 2 轮。
- 候选车型：**手动给了 3 台**（豪沃6X6 / 德龙X3000 / 北奔NG80）——这是当前架构的已知缺口，见 §5.3。

## 2. 架构：自研状态机，不是 LangGraph

`src/equiplens/retrieval_engine/engine.py` 是一个手写状态机（8 个状态），概念上与 LangGraph 对应：

| LangGraph 概念 | 我们的实现 |
|---|---|
| `StateGraph` + 节点 | `_state_*` 方法 + `state["state"]` |
| 条件边 | `_state_gap_check` 里的 if/else（DONE / EXTERNAL_DISCOVER / DEGRADE） |
| Checkpointer | `state.json` 原子写（每次转移落盘） |
| 事件流 | `events.jsonl`（from → to + decision） |

为什么没用 LangGraph：调研结论是“**LangGraph 只用于检索 loop**”，但 `agent-loop-mechanisms.md` 明确“不借 LangGraph/LangChain 依赖”——loop 只有 8 个状态，自己写更好测、可回放、零依赖。当前实现已经跑通，暂不引入框架。

## 3. 三次运行（同一 brief）

| run | 候选 | 结果 | 车槽 | u-exact | u-env | fetches | 阻断原因 |
|---|---|---|---:|---|---:|---:|---:|---|
| `loop-m1-desert` | 2 | FAILED | 0/3 | 0/2 | 0/1 | 5 | **资产-部件绑定 bug** |
| `loop-m1-desert-v2` | 2 | FAILED | 0/3 | 0/2 | 2/1 | 15 | **跨层抢证据 bug** |
| `loop-m1-desert-v3` | 3 | **DONE** | 3/3 | 3/2 | 3/1 | 22 | — |

### 3.1 v1 的决策轨迹（FAILED）

```
BRIEF_READY → LIBRARY_SEARCH（库内 0）→ FETCH → VERIFY → FILL → GAP_CHECK
  → EXTERNAL_DISCOVER（exact 候选 2）→ FETCH → VERIFY → FILL → GAP_CHECK
  → DEGRADE（exact 耗尽，开 environment）→ EXTERNAL_DISCOVER（候选 2）
  → FETCH → VERIFY → FILL → GAP_CHECK → DEGRADE（全层耗尽）→ FAILED
```

- 只抓到 **5 个资产**，3 个 `low_resolution`，2 个通过；
- 但 `u-exact` 要求 3 个部件各有 1 张通过资产 → 永远不满足。

**根因**：`_state_fetch` 用 `asset_id` **全局**去重，一张整车图只能挂在第一个 part 下；后面两个 part 拿不到资产。真实抓取返回的是整车图，一张图本来可以同时是保险杠/踏步/防护栏的证据。→ 修成 `(asset_id, part)` 去重，`verifications` 也按 `(asset, part)` 存。

### 3.2 v2 的决策轨迹（FAILED，但 u-env 已满）

```
... → EXTERNAL_DISCOVER（exact 候选 2）→ ... → DEGRADE（exact 耗尽）
   → EXTERNAL_DISCOVER（environment 候选 2）→ ... → FAILED
```
- `u-env` 2/1 满，`u-exact` 0/2；
- 状态文件里 3 个车型的 `unit_id` 全被改成了 `u-env`。

**根因**：`_add_targets` 按 `target_id`（车型名）覆盖。environment 层重新发现同一车型时，把 `unit_id` 从 `u-exact` 改成 `u-env`，exact 层的证据被“抢走”。→ 改成 `unit_ids` 列表合并，FILL 按 unit 分别判；全局槽位去重。

### 3.3 v3 的决策轨迹（DONE）

```
BRIEF_READY → LIBRARY_SEARCH（库内 0）
  → FETCH → VERIFY → FILL → GAP_CHECK
  → EXTERNAL_DISCOVER（exact 候选 3）
  → FETCH → VERIFY → FILL → GAP_CHECK
  → DEGRADE（exact 耗尽，开 environment）
  → EXTERNAL_DISCOVER（environment 候选 3）
  → FETCH → VERIFY → FILL → GAP_CHECK（全局 3/3 已满）→ DONE → WRITEBACK
```

- **20 条事件**，2 次发现、1 次降级、3 次填槽判定；
- 3 个车型在两个单元里都通过（同图覆盖多部件已生效）；
- 预算：6 queries / 22 fetches / 22 verifies；耗时约 4 分钟（含 22 次下载）。

## 4. 这一轮改了什么

| # | 问题 | 修法 | 测试 |
|---|---|---|---|
| 1 | 资产-部件绑定（一张图只能挂一个 part） | `(asset_id, part)` 去重；verifications 按 pair 存 | `test_same_asset_covers_multiple_parts` |
| 2 | 跨层抢证据（unit_id 被覆盖） | `target.unit_ids` 合并；FILL 按 unit 分别判 | `test_second_tier_does_not_steal_target` |
| 3 | Windows 上 `os.replace` 偶发 WinError 5 | 状态写盘加重试（6 次退避） | 手动复跑通过 |

`tests/test_retrieval_engine.py`：**15/15**。

## 5. 还没解决的问题（下一步要讨论的）

1. **候选车型不是“发现”的**：`EXTERNAL_DISCOVER` 只是把 `--models` 里的 3 台车分给各单元，没有真的去找新车型。所以“清单 ↔ 检索”还没有闭环。
2. **验收不看部件是否可见**：现在只看标题/构型/分辨率；同一张侧面图能同时满足保险杠、踏步、防护栏，导致“通过”偏宽。这是 P4（部件级视觉）要补的。
3. **单元配额与页槽语义混用**：`u-exact 3/2` 说明 accepted 可以超过 quota（全局上限才停），需要明确“单元满即停”还是“全局满才停”。
4. **证据没落库**：这次没传 `--evidence-db`，`evidence.json` 为空；下一轮要接上。
5. **没有真实“新车型发现”**：现在靠人工给 3 台；接 SearXNG/Tavily 或官网图集后才算闭环。

## 6. 产物

- 三次运行：`data-test/runs/loop-m1-desert{,-v2,-v3}/`（`events.jsonl` / `state.json` / `summary.json`）
- brief：`data-test/evals/task-briefs-20261109/brief-m1-desert.json`
- 代码：`src/equiplens/retrieval_engine/{engine,state}.py`
