# 待办清单（BACKLOG）

> 规则：每个待办有 ID、状态（pending/in_progress/done）、触发条件；完成后写 commit/验证。
> 外部意见的采纳状态在 `docs/external/doubao-consult-decisions.md`，本文件只记工程待办。

| ID | 待办 | 状态 | 触发条件 / 说明 |
|---|---|---|---|
| **BL-001** | 把 `briefing.generate_brief` 的**库默认**切到 `use_taskspec=True`，并同步改 `scripts/eval_task_brief.py` 等旧调用方；补一条“默认即新路径”的单测 | pending | 等 S0-05 session 接口稳定后再切，避免评估脚本同时受两层改动影响 |
| **BL-002** | 更新 S1/S2 的 **legacy 标注**（`docs/stages.json`）：把仍有历史引用、但已不在正式路径的旧模块/参数显式标 `silent`，并在 `STAGES.md` 记录 | pending | 等 S1/S2 阶段评审时逐项确认，避免误标 |
| **BL-003** | S0-05 Session/Loop 开发与测试（M1–M6） | **done** | M2 完成（`session.py` 15/15）；M3.1–M3.5 完成（`session_router.py` 15/15；dev30 30/30；holdout 23/24）；M4.2 完成 3 个 live 检索会话（18/18，704.6s）；**M4.3 完成（接线 + 5 case A/B）**；**M4.3 后入口原型完成**（SessionRunner + run_session CLI；测试 8/8、live c1 10/10、续跑持久化）；**5-case live 验收通过**（交付 42/42、missing 0、重复 0、意图 25/25）；**M6 首轮建单已完成（2026-11-16：create_from_text + --create；live 10/10、applied 1；测试 9/9）**；**S4 已 active（后端入口，2026-11-16）**；剩交付后编辑落引擎、报告/PPT 生成 |
| **BL-004** | S4 在 `stages.json` 落正式入口 | **done** | 2026-11-16：S4 `active`（后端入口：Session/SessionRouter/SessionRunner/run_session）；前端入口未接 |
| **BL-006** | 扩大测试：router holdout 扩到 100+ 条、加入真实用户话术；S4 集成后做 3 个 live case | in_progress | 2026-11-16：100 条**合成盲写**已完成（两次 exact 81–82%）；**用户审核：13 条不合理/罕见、6 条能力外、10 余处口径修正；合成集只算广度，不得当线上准确率，也不得写“真实用户输入”**；真实分阶段高频测试见 BL-016；2026-11-16 按用户口径重标后 **all 99/100、realistic 86/87、capability 6/6**（#17 仍缺 add_targets，BC-S4-010）；**P3 290 条草案已生成，待用户审** |
| **BL-007** | 第三方图文/搜索通道获取与测试（豆包 image API 为主）：申请 key/预算 → 冻结 plan 3 case A/B（覆盖率 / 标题带码率 / 成本）→ 决定接不接 | pending | 产品负责人 2026-11-15 指定：S1-06 与 S1-08 是同一个问题，合并处理；到 S1 通道决策（D1）时提醒其开通/付费；官方 Count≤5、免费额度≈1 轮 |
| **BL-008** | 冷启动种子层 `ColdStartSeeder`（默认关、池 short 开、≤8 查询/类目、证据门槛） | pending | S0-03 已采纳为“改进”；实现后先跑 V7 A/B（池扩大 ≥20% 且 confirmed 不降），不得默认开启 |
| **BL-010** | TaskSpec 剩余字段接线（**P0 已完成 2026-11-16**：`brands_include/exclude` → 品牌查询 + negative、`models_pinned` → engine pins；P1 已完成（2026-11-16：`constraints.exclude` → negative、`constraints.views` → part_requirements、`brand_quota` 软执行+披露、`foreign_ratio` 未核验标记）；P2：`scope` → 邻近设计） | in_progress | P0 已接：`taskspec.to_brief` → `briefing.apply_taskspec` → `planning.build_query_plan`/`negative_terms` → engine `pins`；P1/P2 未做；P1 仍是首次交付硬门槛的一半（配额披露） |
| **BL-011** | rank 默认对照：先比 plan 层 top-N 与每 target 分布，有实质差异再跑 5 brief × 2 臂 loop（LLM vs 确定性） | pending | E41 仅 2 case；门槛：交付/备选/degraded 一致且省 ≥20 s 才切默认；排 M4.3 验收后、第一次用户交付前 |
| **BL-015** | 10-case 交付回归（5 新类目）：80/80、missing 0；h2e 池不足→备选 2/4 | **done** | 2026-11-16：见 DATA-CHANGELOG §65；新类目覆盖洒水/汽车吊/搅拌/高空/矿卡 |
| **BL-014** | 分析模块过程引导：建 `skills/analysis/SKILL.md`（观察→定位→可见性→证据→自检→输出）+ 两段式（观察清单→结构化）+ 字段级证据 + 质量评测（20–30 张人工标注） | pending | 2026-11-16 评估：现有分析模块只有出口契约（prompt 字段+事后校验+一次重试），无分析过程 skill/证据/质量评测；14/14 单测只覆盖输出格式 |
| **BL-018** | UI 操作引导：交付格式/导出等界面功能，用户问“在哪/怎么操作”时返回 `action=guide` + 具体位置步骤，不产生 patch | **done** | 2026-11-17：UI_GUIDE 同时覆盖“直接问”和“指令式操作”；A8 10/10 |
| **BL-019** | 暂停+附带要求（B3）：pause 不吞掉修改，记录待应用修改，恢复时确认 | pending | 典型：“先停一下，等我把品牌加上”；需定义顺序/确认 |
| **BL-020** | 低置信/兜底反馈闭环：记录 proposal+用户二次反馈→人工判定→案例库→相似 few-shot 检索；定期复盘机制漏洞 | pending | 不训练小模型；先做数据闭环与检索增强的离线 A/B |
| **BL-021** | 分层模型路由评估（小模型/规则/LLM 级联） | pending | 当前单 LLM + 守卫；低 QPS/高模糊，暂不必要；触发条件=QPS/成本/延迟或意图分布稳定后 |
| **BL-025** | S4 hard 动作 no-op：先 gate 为 clarify/explain | **done** | 2026-11-17：`Session.interrupt` 已 gate 5 个动作，返回 clarify + 选项，不产 patch；`gated_action` 事件/`gated_actions` 计数已记 |
| **BL-027** | delta 编辑的新图源：fetch-more（换查询/翻页/新来源），否则 live 换图 added=0 | pending | 2026-11-17 live c1e 实测；机制已通，源未通；策略：**replace 无新图保留旧图**、remove 报缺口、预算有界；对应 BC-S4-017 |
| **BL-028** | delta fetch-more 的预算边界：最多 2 轮/6 查询/60s；只换查询/页/来源，不换 target；失败保留旧图并说明 | pending | 2026-11-17 产品要求：先保证最终交付，边界内尝试；实现随 BL-027 |
| **BL-026** | hard 动作真实重排/重跑（quantity/config/scope/reset/pause） | **待后续版本开发** | gate 已完成；真实执行需重建 plan/engine，放 delta 之后；对应 BC-S4-016 的后续 |
| **BL-024** | 角度/部件补充（主交付后剩余预算 delta） | **待后续版本开发** | 2026-11-17 产品决定：当前版本不保留角度/部件要求，识别为澄清并建议“多找几张这辆车”；已在 `stages.json` S4 `planned_extensions` 登记 |
| **BL-023** | 低置信日志 + 案例库 + few-shot 离线 A/B（先记录、后改行为） | pending | P3 后推荐：记录 proposal/confidence/用户二次反馈→人工判定→检索相似案例；先离线 A/B，确认增益后再接 prompt；训练仍走 BL-022 |
| **BL-022** | 负样本/难例增强与小模型训练评估（边界 case 库、hard negatives、小分类器/重排） | **待后续版本开发测试** | 2026-11-17 评估：当前真实数据量与标签稳定性不足；先做 BL-020 反馈闭环 + few-shot，累计 500–1000 条真实确认案例后再评估；不替代大模型 |
| **BL-016** | 分阶段高频真实测试集：输入 / 运行中 / 看到结果后 三阶段，各 100+，按真实频率加权，优先真实日志/客服话术 | in_progress | 2026-11-17：290 条按真实输入执行；角度/部件改澄清后 **288/290（99.3%）**（A120/120、B69/70、C99/100）；仅剩 B041 pause+edit、C074 身份未指张 |
| **BL-017** | Router 能力/阶段/数量语义重构：capability gate + stage gate + 数量四义 + 澄清选项化 | **done** | 2026-11-16：P0（能力/阶段）+ P1（数量四义/per-model/replenish）+ P2（复合意图/选项化澄清/构型区分）完成；holdout raw 82→86、cap 87→91；BC-S4-006/007/008/009 已处理；P3 真实分阶段测试见 BL-016 |
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
- 2026-11-16：定向验证发现“品牌约束下 plan 池 7<需求 20 → 7/8 交付”，归台账 S1-05 池供给（A6/A2），不归接线。
