# 常用指令卡（换机器 / 日常检查）

> 当用户输入下列**触发词**时，按对应命令执行，不要临场改命令。

| 触发词（用户原话） | 执行 | 说明 |
|---|---|---|
| **“检查主体代码索引”** / “新机器检查” / “换电脑检查” | `PYTHONPATH=src python scripts/check_machine.py` | 换机器后的标准检查：状态机 + 单测 + 台账 + 密钥 |
| “完整检查” / “检查引擎” | `PYTHONPATH=src python scripts/check_machine.py --full` | 追加引擎/图片/分析测试（需要 fixtures） |
| “看正式链路” | `PYTHONPATH=src python scripts/check_stages.py` | 只查状态机：active 入口 / legacy silent |
| “环境自检” | `python scripts/check_env.py` | Python/依赖/key/门卫模型是否就绪 |

## 检查内容（check_machine 默认）

1. `docs/stages.json` 的 active 入口存在、legacy 标 `silent`；
2. `test_taskspec`、`test_briefing`、`test_identity`、`test_planning`、`test_run_ledger`、`test_no_legacy_tables`；
3. `run_ledger --check`（台账完整性）；
4. `scan_secrets`（密钥扫描）；
5. 打印当前正式阶段版本（S0/S1/S2/S3）。

预期输出（2026-11-15）：

```
正式阶段：S0=taskspec-v0.4 / S1=p8-idmatch / S2=p8-idmatch / S3=manifest-v1
...
结果：全部通过
```

## 失败时

1. 先看 `[FAIL]` 那一行的尾行；
2. 状态机失败 → 对照 [`STAGES.md`](STAGES.md) 修入口/符号，不要绕过；
3. 单测失败 → 跑对应 `tests/test_*.py` 看完整输出；
4. 台账失败 → `scripts/run_ledger.py --check`，按提示补 RUN.json；
5. 密钥扫描失败 → 立即停止提交，按提示处理。

## 相关文件

- 状态机：[`STAGES.md`](STAGES.md) / [`stages.json`](stages.json)
- 待办：[`BACKLOG.md`](BACKLOG.md)
- S0-05 规划：[`s0-05-session-loop-plan-20261115.md`](s0-05-session-loop-plan-20261115.md)
