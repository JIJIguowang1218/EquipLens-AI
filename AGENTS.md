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

## 5. 当前待办

见 [`docs/BACKLOG.md`](docs/BACKLOG.md)；S0-05 规划见
[`docs/s0-05-session-loop-plan-20261115.md`](docs/s0-05-session-loop-plan-20261115.md)。
