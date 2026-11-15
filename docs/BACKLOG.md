# 待办清单（BACKLOG）

> 规则：每个待办有 ID、状态（pending/in_progress/done）、触发条件；完成后写 commit/验证。
> 外部意见的采纳状态在 `docs/external/doubao-consult-decisions.md`，本文件只记工程待办。

| ID | 待办 | 状态 | 触发条件 / 说明 |
|---|---|---|---|
| **BL-001** | 把 `briefing.generate_brief` 的**库默认**切到 `use_taskspec=True`，并同步改 `scripts/eval_task_brief.py` 等旧调用方；补一条“默认即新路径”的单测 | pending | 等 S0-05 session 接口稳定后再切，避免评估脚本同时受两层改动影响 |
| **BL-002** | 更新 S1/S2 的 **legacy 标注**（`docs/stages.json`）：把仍有历史引用、但已不在正式路径的旧模块/参数显式标 `silent`，并在 `STAGES.md` 记录 | pending | 等 S1/S2 阶段评审时逐项确认，避免误标 |
| **BL-003** | S0-05 Session/Loop 开发与测试（M1–M6） | in_progress | M2 完成（`session.py` 14/14）；M3.1–M3.5 完成（`session_router.py` 15/15；dev30 30/30；holdout 23/24）；M4.2 完成 3 个 live 检索会话（18/18，704.6s）；M4.3 待做：中途 patch 真正影响引擎/增量重排 |
| **BL-004** | S4 在 `stages.json` 落正式入口 | pending | 依赖 BL-003 完成 |
| **BL-006** | 扩大测试：router holdout 扩到 100+ 条、加入真实用户话术；S4 集成后做 3 个 live case | pending | 产品负责人 2026-11-15 明确要求；不得用合成集当线上准确率 |
| **BL-007** | 第三方图文/搜索通道获取与测试（豆包 image API 为主）：申请 key/预算 → 冻结 plan 3 case A/B（覆盖率 / 标题带码率 / 成本）→ 决定接不接 | pending | 产品负责人 2026-11-15 指定：S1-06 与 S1-08 是同一个问题，合并处理；到 S1 通道决策（D1）时提醒其开通/付费；官方 Count≤5、免费额度≈1 轮 |
| **BL-005** | 把 `scripts/check_machine.py` 纳入发布前检查清单 | done | 2026-11-15 已加 `COMMANDS.md` / `AGENTS.md` |

## 记录

- 2026-11-15：BL-001/BL-002 由产品负责人明确要求“记住，后续再考虑”；不丢，不提前做。
- 2026-11-15：BL-007 由产品负责人指定：S1-06（现有通道）与 S1-08（豆包）是同一问题；到 D1 前提醒其提供 key/预算。
