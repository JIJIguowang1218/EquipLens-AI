# 待办清单（BACKLOG）

> 规则：每个待办有 ID、状态（pending/in_progress/done）、触发条件；完成后写 commit/验证。
> 外部意见的采纳状态在 `docs/external/doubao-consult-decisions.md`，本文件只记工程待办。

| ID | 待办 | 状态 | 触发条件 / 说明 |
|---|---|---|---|
| **BL-001** | 把 `briefing.generate_brief` 的**库默认**切到 `use_taskspec=True`，并同步改 `scripts/eval_task_brief.py` 等旧调用方；补一条“默认即新路径”的单测 | pending | 等 S0-05 session 接口稳定后再切，避免评估脚本同时受两层改动影响 |
| **BL-002** | 更新 S1/S2 的 **legacy 标注**（`docs/stages.json`）：把仍有历史引用、但已不在正式路径的旧模块/参数显式标 `silent`，并在 `STAGES.md` 记录 | pending | 等 S1/S2 阶段评审时逐项确认，避免误标 |
| **BL-003** | S0-05 Session/Loop 开发与测试（M1–M6） | in_progress | M2 完成（`session.py` 14/14）；M3.1–M3.5 完成（`session_router.py` 15/15；dev30 30/30；holdout 23/24）；下一步 M4 FakeWorld |
| **BL-004** | S4 在 `stages.json` 落正式入口 | pending | 依赖 BL-003 完成 |
| **BL-005** | 把 `scripts/check_machine.py` 纳入发布前检查清单 | done | 2026-11-15 已加 `COMMANDS.md` / `AGENTS.md` |

## 记录

- 2026-11-15：BL-001/BL-002 由产品负责人明确要求“记住，后续再考虑”；不丢，不提前做。
