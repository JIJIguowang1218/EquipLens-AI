# 代码位置索引（封装前）

更新：2026-11-12  
原则：先读 `CURRENT-ARCHITECTURE.md`，再按本索引找代码；实验脚本不能当生产入口。
已毙/归档策略见 `docs/killed-strategies.md`（三证②③、part_views、stategy 文件等）。

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
| brief 生成 | `src/equiplens/briefing.py`、`scripts/build_brief.py`、`skills/task-brief/SKILL.md` |
| 查询规划/候选 | `src/equiplens/planning.py`、`scripts/plan_candidates.py` |
| 意图排序 N+4（N=brief 槽数） | `scripts/rank_plan.py` |
| 检索 loop | `src/equiplens/retrieval_engine/engine.py` |
| 平台/抓取/核验 | `src/equiplens/retrieval_engine/web.py`、`src/equiplens/imagesearch.py` |
| 契约/状态 | `src/equiplens/retrieval_engine/contracts.py`、`state.py` |
| CLI | `src/equiplens/retrieval_engine/cli.py`、`__main__.py` |
| 门卫 | `src/equiplens/gate.py` |
| 审核页 | `scripts/render_fetch_audit.py` |
| 分析（视觉） | `src/equiplens/analysis.py`、`scripts/analyze_batch.py`、`docs/superpowers/specs/2026-10-31-analysis-schema-design.md` |
| 报告/PPT | `scripts/build_report_page.py`、`scripts/export_pptx.py` |
| 评测 | `scripts/eval_task_brief.py`、`data-test/evals/` |
| 台账 | `scripts/run_ledger.py`、`data-test/runs/INDEX.md` |
| 交付清单/监控 | `scripts/build_delivery_manifest.py`（DELIVERY.md/json）、`src/equiplens/pricing.py` |
| 去重人工审核 | `scripts/build_dedupe_review.py`（生成可离线打开的 review.html） |
| 死图床监测 | `scripts/monitor_bad_domains.py`（只统计，不参与生产） |
| 交付测试套件 | `scripts/run_delivery_suite.py`、`scripts/summarize_delivery_suite.py` |

## 3. 支撑模块

| 模块 | 代码 |
|---|---|
| 数据库/摄取 | `db.py`、`ingest.py`、`corpus.py` |
| 源适配/健康 | `channels.py`、`webchannel.py`、`retrieval_engine/sources.py` |
| 证据 | `retrieval_engine/evidence.py` |
| 审核服务 | `review.py`、`reviewserver.py`、`scripts/build_*_review.py` |
| L3 段落质检 | `passage.py`、`l3gate.py`、`scripts/eval_l3gate.py` |
| 旧 text/workflow | `textrun.py`、`workflow.py`、`runner.py`、`strategy.py`、`query.py`、`roster.py` |

## 4. 实验脚本（不得默认进生产）

- `scripts/probe_platforms.py`
- `scripts/probe_class_query.py`
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
| `tests/test_briefing.py` | brief API/组装 |
| `tests/test_planning.py` | 查询计划/候选归并 |
| `tests/test_retrieval_engine.py` | 状态机/配额/fill/code prefilter |
| `tests/test_imagesearch.py` | 搜索/平台预筛/下载阶梯 |
| `tests/test_gate.py` | 门卫 |
| `tests/test_run_ledger.py` | 台账 |
| `tests/test_analysis.py` | 分析（历史有失败，需单独看） |

## 6. 契约/数据

- `schemas/task-brief-v3.schema.json`：brief 结构
- `schemas/retrieval-state.schema.json`：run state
- `schemas/retrieval-event.schema.json`：events
- `data/part_taxonomy.json`：部件词表
- `data/source_registry.json`：来源注册
- `data/category_profiles.json`：类目档案

## 7. 封装检查

- 生产只走 `CURRENT-ARCHITECTURE.md` §2 主链；
- 不把 `data-test/evals/*` 预制 brief 当用户输入；
- 不把 fixture/mock 图当真实素材；
- 不恢复已收口策略（Platform union、body guard、harvest 元数据等）；
- 打包清单以本索引 + CURRENT-ARCHITECTURE 为准。
