# EquipLens-AI：协作约定（给 AI / 维护者）

## 1. 触发词

- 用户说 **“检查主体代码索引” / “新机器检查” / “换电脑检查”**：
  立即执行 `PYTHONPATH=src python scripts/check_machine.py`，把输出的
  “正式阶段 / PASS-FAIL 表 / 结果”原样报告；有 FAIL 先按 [`docs/COMMANDS.md`](docs/COMMANDS.md) 排查。
- 用户说 **“看正式链路”**：执行 `PYTHONPATH=src python scripts/check_stages.py`。

## 2. 正式链路以状态机为准

- [`docs/STAGES.md`](docs/STAGES.md) + [`docs/stages.json`](docs/stages.json) 是“现在真实跑哪版代码”的
  唯一权威；`CODE-INDEX.md` 只回答“代码在哪”。
- 新增/替换机制：先改 `stages.json`（旧条目移 `legacy` 并标 `silent`），再改代码；跑
  `check_stages.py` 通过后再提交。
- 不要出现“代码已切、状态机没改”或“状态机改了、入口没接”。

## 3. 数据与测试

- 临时测试输入/参数只放 `tmp/`（gitignored），必须在 README 标“临时、复用需申请”；
  不得写入 `src/` 默认值、配置或词表。上一轮 50 条输入已按单次授权使用，不再复用。
- 词表政策：`src/` 不得含领域实体枚举（品牌/车型/类目/部件表）；类目别名只能显式
  `alias_map` 传入。提交前跑 `tests/test_no_legacy_tables.py`。
- 提交前必跑：`scripts/scan_secrets.py`，以及受影响的 `tests/test_*.py`。

## 4. 文档同步

- 代码变更 → `CODE-INDEX.md`、`DATA-CHANGELOG.md`；
- 机制决策 → `docs/external/doubao-consult-decisions.md` 或 `BACKLOG.md`；
- 测试异常 → `docs/badcases/` 按 `BC-<模块>-<序号>` 登记，状态机式推进。

## 5. 术语口径（2026-11-16 统一）

> 目的：避免“正式 / 生效 / 能用”各说各话。以后所有汇报只用下表口径（六个状态词 + “计划”）。

| 词 | 定义 | 判定方法 |
|---|---|---|
| **生产代码 / 生产链路** | 真实用户任务从 `build_brief` → `plan_candidates` → `retrieval_engine` → `build_delivery_manifest` 默认执行的代码 | 一条用户输入不传实验参数就能跑到 |
| **生产生效** | 在生产链路里且**默认**执行（无需开关） | 读 CLI 默认值 |
| **生产可用（opt-in / 无调用方）** | 代码在 `src/`、质量达标，但需显式开关或尚无生产入口 | grep 调用方/开关 |
| **实验** | 只在 `scripts/` 实验脚本或测试里用 | 不在生产入口 |
| **原型** | 有实现有测试，但无生产入口、接入方案未定 | 无 import 链到 CLI |
| **静默下线（silent / legacy）** | 保留兼容、默认不可达 | `stages.json` 的 `legacy` |
| **计划（planned）** | 已设计未实现 | `stages.json` 的 `status` |

规则：

- 禁用孤立说法：“默认生效”（必须写“生产生效”或“开关默认值”）、“能用/可用”（必须限定为生产生效 / 生产可用 / 仅实验）。
- 阶段状态只用 `active` / `silent` / `planned` / `n-a`；**`active` = 生产生效**，不只是“代码存在”。
- 任何 A/B 必须同时记录 `stages` 版本 + `summary.config`（含 `s0_mechanism`、`session_patches`），否则结果作废。

## 6. 测试汇报格式（2026-11-16 约定）

任何测试/模块开发汇报统一用六段：**阶段 - 目标 - 方法 - 结果（含数据） - 结论 - 效果评价和建议**。

- **阶段**：引用 `M1–M6`、`S0–S5`、`BL-xxx`、`V*`/`E*`、`BC-*`，**不自造新编号体系**；
- **目标**：一句话、可验证；
- **方法**：输入数据、命令、隔离条件（是否复用历史数据）；
- **结果**：必须含数字与文件路径，明确 PASS/FAIL；失败同样要报；
- **结论**：是否达到预期，覆盖范围与未覆盖项；
- **效果评价和建议**：可信度、风险、下一步。

验收要求：新数据、独立 run/session、不污染历史；报告与台账/实验索引同步。

## 7. 当前待办

见 [`docs/BACKLOG.md`](docs/BACKLOG.md)；S0-05 规划见
[`docs/s0-05-session-loop-plan-20261115.md`](docs/s0-05-session-loop-plan-20261115.md)。
