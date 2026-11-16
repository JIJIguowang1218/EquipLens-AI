# 代码位置索引（封装前）

更新：2026-11-15  
原则：先读 `CURRENT-ARCHITECTURE.md`，再按本索引找代码；实验脚本不能当生产入口。
已毙/归档策略见 `docs/killed-strategies.md`（三证②③、part_views、stategy 文件等）。
**正式链路以 [`docs/STAGES.md`](STAGES.md) 为准**（`stages.json` + `scripts/check_stages.py`），本索引是代码位置。

## 1. 项目怎么管代码

- Python 源码：`src/equiplens/`（`PYTHONPATH=src` 导入）
- 命令行入口：`scripts/` 与 `src/equiplens/retrieval_engine/__main__.py`
- 数据/契约：`data/`、`schemas/`
- 技能：`skills/task-brief/`、`skills/association/`
- 测试：`tests/`（`check()` 脚本，不是 pytest）
- 运行产物：`data-test/runs/`、`data-test/evals/`
- 文档：`docs/`，实时框架以 `CURRENT-ARCHITECTURE.md` 为准

现在**还没有封装/打包**；代码就是仓库源码 + 脚本。封装时必须按本索引区分生产/实验/历史。

## 2. 生产主链（必须索引）

| 职责 | 代码 |
|---|---|
| **S0 任务单（正式）** | `src/equiplens/taskspec_llm.py`（parse）→ `src/equiplens/taskspec.py`（normalize/validate）→ `src/equiplens/briefing.py::apply_taskspec`；CLI `scripts/build_brief.py` 默认走此路径 |
| brief 组装（LLM） | `src/equiplens/briefing.py`、`skills/task-brief/SKILL.md` |
| brief 旧路径（silent） | `briefing.generate_brief(use_taskspec=False)`（库默认）、`build_brief.py --legacy-brief`；仅对照/回滚 |
| 状态机检查 | `docs/stages.json`、`scripts/check_stages.py`、`scripts/check_machine.py`（换机器全检） |
| 协作/指令 | `AGENTS.md`、`docs/COMMANDS.md`、`docs/BACKLOG.md` |
| S0-05 设计 | `docs/s0-05-session-loop-plan-20261115.md`、`docs/s0-05-router-strategy-20261115.md` |
| S0-05 Session 入口（原型 L1） | `src/equiplens/session_runner.py`、`scripts/run_session.py`；会话 `data/sessions/<id>.json`（gitignored）；测试 `tests/test_session_runner.py`（4） |
| S0-05 Session（原型）/ M4.3 | `src/equiplens/session.py`、`session_router.py`、`retrieval_engine/engine.py::apply_patches`；A/B：`scripts/run_session_case.py`、`scripts/compare_m43_ab.py`；数据 `data-test/runs/m43-*`、`data-test/evals/m43-*.json` |
| 查询规划/候选 | `src/equiplens/planning.py`、`scripts/plan_candidates.py`（`--concurrency` 默认 4；`--topup` 默认 2、可显式 4；抽取输出 slots/search_key） |
| 意图排序 N+4（N=brief 槽数） | `scripts/rank_plan.py`（`--deterministic` 仅实验开关） |
| 检索 loop | `src/equiplens/retrieval_engine/engine.py`（FILL 正选优先，可跨 unit 借位） |
| 平台/抓取/核验 | `src/equiplens/retrieval_engine/web.py`、`src/equiplens/imagesearch.py` |
| 契约/状态 | `src/equiplens/retrieval_engine/contracts.py`、`state.py` |
| CLI | `src/equiplens/retrieval_engine/cli.py`、`__main__.py` |
| 门卫 | `src/equiplens/gate.py` |
| 审核页 | `scripts/render_fetch_audit.py` |
| 分析（视觉） | `src/equiplens/analysis.py`、`scripts/analyze_batch.py`、`docs/superpowers/specs/2026-10-31-analysis-schema-design.md` |
| 报告/PPT | `scripts/build_report_page.py`、`scripts/export_pptx.py` |
| 评测 | `scripts/eval_task_brief.py`、`data-test/evals/`；视觉探针 `scripts/probe_visual_identity.py`（文本标签，No-Go）、`scripts/probe_visual_reference.py`（image-to-image，条件性） |
| 台账 | `scripts/run_ledger.py`、`data-test/runs/INDEX.md` |
| 交付清单/监控 | `scripts/build_delivery_manifest.py`（DELIVERY.md/json）、`src/equiplens/pricing.py`、`summary.timings` |
| 去重人工审核 | `scripts/build_dedupe_review.py`（生成可离线打开的 review.html） |
| 死图床监测 | `scripts/monitor_bad_domains.py`（只统计，不参与生产） |
| 密钥卫生 | `scripts/scan_secrets.py`、`tests/test_no_secrets.py`（提交前跑） |
| 交付测试套件 | `scripts/run_delivery_suite.py`、`scripts/summarize_delivery_suite.py` |
| 完整测试驱动/评估 | `scripts/run_fulltest.py`、`scripts/eval_fulltest.py`、`scripts/eval_fulltest_repeats.py`、`scripts/eval_plan_snapshot.py`、`scripts/evaluate_identity_match.py`（标识回放） |

## 3. 支撑模块

| 模块 | 代码 |
|---|---|
| 数据库/摄取 | `db.py`、`ingest.py`、`corpus.py` |
| 源适配/健康 | `channels.py`、`webchannel.py`、`retrieval_engine/sources.py` |
| 证据 | `retrieval_engine/evidence.py` |
| 审核服务 | `review.py`、`reviewserver.py`、`scripts/build_*_review.py` |
| L3 段落质检 | `passage.py`、`l3gate.py`、`scripts/eval_l3gate.py` |
| 旧 text/workflow | `textrun.py`、`workflow.py`、`runner.py`、`strategy.py`、`query.py`、`roster.py` |
| 辅助模块 | `doctor.py`（环境自检）、`identity.py`（**车型标识规范，第一段/第二段共用**）、`taskspec.py`（S0-01 任务单规范化/校验，含固定 policy 枚举）、`session.py`（S0-05 Session 原型 + `apply_to_brief`；S4 未激活）、`session_router.py`（LLM 提议 + context + 守卫 + `values` 结构化值）、`domainbench.py`（域名基准）、`probe.py`（判向探针）、`retrieval.py`（R1 检索任务）、`runlog.py`（run 日志，`est` 恒为真，成本仅估算）、`retrieval_engine/discover.py`、`retrieval_engine/adapters.py`（FakeWorld，仅 `--fixtures`） |

## 4. 实验脚本（不得默认进生产）

- `scripts/ab_negative.py`：negative with/without A/B（2026-11-13）
- `scripts/ab_plan_concurrency.py`：plan 串行 vs 并发（A 测试）
- `scripts/ab_rank.py`：LLM rank vs 确定性排序小 A/B
- `scripts/bench_download_concurrency.py`：下载并发基准（不改 loop）
- `scripts/probe_platforms.py`
- `scripts/probe_class_query.py`
- `scripts/probe_query_fallback.py`（E44 判死回退探针）
- `scripts/probe_cold_start.py`（V6：LLM 冷启动型号 → 搜索验证）
- `scripts/probe_english_query.py`（E51/E53 英文条件档）
- `scripts/evaluate_kill_chain_offline.py`（E46 判死链离线回放）
- `scripts/evaluate_source_provenance.py`（E50 A1 来源降权评估）
- `scripts/evaluate_search_key.py`（E54 search_key 评估）
- `scripts/probe_source_expansion.py`
- `scripts/probe_source_expansion_funnel.py`
- `scripts/backfill_baidu.py`
- `scripts/apply_body_guard.py`
- `scripts/test_harvest_metadata.py`
- `scripts/render_*_review.py`（审核辅助）
- `scripts/diag_foreign_search.py`、`scripts/ab_image_crawl.py` 等诊断

这些可以保留作复现，但封装时不能作为用户入口，也不能读取预制 brief 冒充真实输入。

## 5. 测试索引

| 测试 | 覆盖 |
|---|---|
| `tests/test_briefing.py` | brief API/组装/校验（7） |
| `tests/test_retrieval_engine.py` | 状态机/配额/fill/跨 unit 借位/code prefilter/重规划（48） |
| `tests/test_imagesearch.py` | 搜索/平台预筛/下载阶梯 |
| `tests/test_planning.py` | 查询计划/候选归并/negative 护栏/slots/model_code 校验（20） |
| `tests/test_identity.py` | 车型标识归一化（主码/括号规则/尾部后缀/边界，10） |
| `tests/test_session.py` | Session 状态机：软/硬打断、两轴约束、确认、幂等、去重、轮次、持久化、资产定位（15） |
| `tests/test_session_router.py` | Router 守卫：白名单/硬软/删除确认/上下文/回退/工厂（15） |
| `tests/test_session_engine.py` | Session × FakeWorld：step 续跑、checkpoint、交付编辑、纠错定位、原始编号、delta run；M4.3 接线（views/quality/parts/negative/add_targets）（12） |
| `tests/test_taskspec.py` | TaskSpec 规范化/接入：policy 枚举、软硬分流、品牌配额、修改 delta、parts 去重、提问策略、apply_taskspec 覆盖（22） |
| `tests/test_gate.py` | 门卫 |
| `tests/test_run_ledger.py` | 台账 |
| `tests/test_no_legacy_tables.py` | 词表守卫（src 全量禁旧表名、三表必须不存在、品牌组为空、主链不 import 旧链路，4） |
| `tests/test_analysis.py` | 分析（去表化口径，14） |
| `tests/test_manifest.py` | 交付清单透明化：source_url / evidence_grade / 边界与缺口（5） |

## 6. 契约/数据

- `schemas/task-brief-v3.schema.json`：brief 结构
- `schemas/retrieval-state.schema.json`：run state
- `schemas/retrieval-event.schema.json`：events
- `data/legacy/`：**已删除**（2026-11-14，部件/类目/品牌三表）；主体代码不得再引用，规则见 `docs/vocabulary-policy.md`
- `data/source_registry.json`：来源运维配置（不参与交付准入）

## 7. 封装检查

- 生产只走 `CURRENT-ARCHITECTURE.md` §2 主链；
- 不把 `data-test/evals/*` 预制 brief 当用户输入；
- 不把 fixture/mock 图当真实素材；
- 不恢复已收口策略（Platform union、body guard、harvest 元数据等）；
- 打包清单以本索引 + CURRENT-ARCHITECTURE 为准。
