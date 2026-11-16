# 待办清单（BACKLOG）

> 规则：每个待办有 ID、状态（pending/in_progress/done）、触发条件；完成后写 commit/验证。
> 外部意见的采纳状态在 `docs/external/doubao-consult-decisions.md`，本文件只记工程待办。

| ID | 待办 | 状态 | 触发条件 / 说明 |
|---|---|---|---|
| **BL-001** | 把 `briefing.generate_brief` 的**库默认**切到 `use_taskspec=True`，并同步改 `scripts/eval_task_brief.py` 等旧调用方；补一条“默认即新路径”的单测 | pending | 等 S0-05 session 接口稳定后再切，避免评估脚本同时受两层改动影响 |
| **BL-002** | 更新 S1/S2 的 **legacy 标注**（`docs/stages.json`）：把仍有历史引用、但已不在正式路径的旧模块/参数显式标 `silent`，并在 `STAGES.md` 记录 | pending | 等 S1/S2 阶段评审时逐项确认，避免误标 |
| **BL-003** | S0-05 Session/Loop 开发与测试（M1–M6） | in_progress | M2 完成（`session.py` 15/15）；M3.1–M3.5 完成（`session_router.py` 15/15；dev30 30/30；holdout 23/24）；M4.2 完成 3 个 live 检索会话（18/18，704.6s）；**M4.3 完成（接线 + 5 case A/B）**；**L1 完成（2026-11-16：SessionRunner + run_session CLI；offline 4/4、live c1 10/10、续跑持久化）**；L2 进行中（2026-11-16 **5-case live 验收：交付 42/42、missing 0、重复 0、意图 25/25**）；剩首轮建单（M6）、交付后编辑落引擎、报告/PPT 生成（L3 前）；S4 仍 planned |
| **BL-004** | S4 在 `stages.json` 落正式入口 | pending | 依赖 BL-003 完成 |
| **BL-006** | 扩大测试：router holdout 扩到 100+ 条、加入真实用户话术；S4 集成后做 3 个 live case | pending | 产品负责人 2026-11-15 明确要求；不得用合成集当线上准确率 |
| **BL-007** | 第三方图文/搜索通道获取与测试（豆包 image API 为主）：申请 key/预算 → 冻结 plan 3 case A/B（覆盖率 / 标题带码率 / 成本）→ 决定接不接 | pending | 产品负责人 2026-11-15 指定：S1-06 与 S1-08 是同一个问题，合并处理；到 S1 通道决策（D1）时提醒其开通/付费；官方 Count≤5、免费额度≈1 轮 |
| **BL-008** | 冷启动种子层 `ColdStartSeeder`（默认关、池 short 开、≤8 查询/类目、证据门槛） | pending | S0-03 已采纳为“改进”；实现后先跑 V7 A/B（池扩大 ≥20% 且 confirmed 不降），不得默认开启 |
| **BL-010** | TaskSpec 剩余字段接线（**P0 已完成 2026-11-16**：`brands_include/exclude` → 品牌查询 + negative、`models_pinned` → engine pins；P1 已完成（2026-11-16：`constraints.exclude` → negative、`constraints.views` → part_requirements、`brand_quota` 软执行+披露、`foreign_ratio` 未核验标记）；P2：`scope` → 邻近设计） | in_progress | P0 已接：`taskspec.to_brief` → `briefing.apply_taskspec` → `planning.build_query_plan`/`negative_terms` → engine `pins`；P1/P2 未做；P1 仍是首次交付硬门槛的一半（配额披露） |
| **BL-011** | rank 默认对照：先比 plan 层 top-N 与每 target 分布，有实质差异再跑 5 brief × 2 臂 loop（LLM vs 确定性） | pending | E41 仅 2 case；门槛：交付/备选/degraded 一致且省 ≥20 s 才切默认；排 M4.3 验收后、第一次用户交付前 |
| **BL-013** | tmp 原始实验资产归档（V8–V12：输入集/holdout/错误分层/探针脚本）→ `data-test/evals/` 或对象存储 | pending | 产品负责人 2026-11-16：数据必须任意机器可取，临时代码可不入库；当前在另一台机器 `tmp/`，清单见 `data-test/evals/tmp-assets-inventory.md` |
| **BL-012** | 离线视觉参考库（S2-06 条件性 go）：≥30 型号、≥10 图/型号、≥300 run-disjoint + 人工核验测试图；目标 top-1 ≥75%、balanced ≥70%、margin p10 > 0 | pending | 达标前只允许 top-3 短名单，不得 accept/reject；数据采集是主要成本；V19 探针：53.0% vs 6.7% |
| **BL-005** | 把 `scripts/check_machine.py` 纳入发布前检查清单 | done | 2026-11-15 已加 `COMMANDS.md` / `AGENTS.md` |

## 记录

- 2026-11-15：BL-001/BL-002 由产品负责人明确要求“记住，后续再考虑”；不丢，不提前做。
- 2026-11-15：BL-007 由产品负责人指定：S1-06（现有通道）与 S1-08（豆包）是同一问题；到 D1 前提醒其提供 key/预算。
- 2026-11-15：S0 收口（6/6）；S0-03 种子层落 BL-008，S0-06 归档移交 S3-05。
- 2026-11-15：核对发现 TaskSpec 仅 class/env/config/slots 确定性落 brief，其余字段未消费；落 BL-010（会影响 S1 的品牌/指定车型接线）。
- 2026-11-15：S1 拍板 4 条（02/03/09/10）；S1-14 排 BL-011（M4.3 之后）；BL-010 拆 P0/P1/P2，P0 定为首次用户交付硬门槛。
- 2026-11-16：BL-010 P0 完成（品牌/指定车型/排除项接通 brief→plan→engine）；定向验证 3 条通过，
  过程中修了 BC-S01-014（用户排除项截断）；P1 配额/披露未做。
- 2026-11-16：定向验证发现“品牌约束下 plan 池 7<需求 20 → 7/8 交付”，归 D2 池供给，不归接线。
