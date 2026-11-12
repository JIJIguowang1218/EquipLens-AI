# scripts/：可复现的评测与测试脚本

从 `tmp/`（gitignore 临时区）迁入，随仓库同步，供新会话复跑与审计。

> **生产入口（不是实验脚本）**：`build_brief.py`（任务单）、`plan_candidates.py`（候选规划）、
> `rank_plan.py`（12+2 意向排序）、`render_fetch_audit.py`（审核页）、`run_ledger.py`（run 台账）。
> 下面表里的是实验/诊断脚本，只能复现，不能当默认入口（见 `docs/CODE-INDEX.md` §2/§4）。

| 脚本 | 用途 |
|---|---|
| `monitor_bad_domains.py` | 死图床长期监测（只统计，不参与生产）：汇总 403/DNS 到 `data-test/evals/bad-domains-monitor.*` |
| `run_roster_crawl.py` | T18-roster 首跑：4 类目 39 车型语料采集 |
| `recrawl_craneL.py` / `recrawl_generic.py` | 轻型吊车补爬 / 宏观设计查询补爬 |
| `roster_judge_sheet.py` | 生成三分类判定工作表 |
| `roster_verdicts.py` / `roster_verdicts_round2.py` | 模型层判定结果（第一轮/新增） |
| `remap_verdicts.py` | 旧判定 → 稳定 ID 映射 |
| `roster_aggregate.py` | 三类占比聚合与报告 |
| `build_roster_review.py` / `build_l3_review.py` | 审核包 HTML 生成 |
| `eval_l3gate.py` | 确定性闸门在 265 段金标上的评估 |
| `replay_gate.py` | 离线回放：同批语料"关键词基线 vs 过闸"对照（`data-test/evals/gate-replay-*.md`） |
| `domain-bench-queries*.json` | 域名基准查询集（两轮） |
| `compare_domain_bench.py` | 两轮域名基准对比 |
| `check_yoojia.py` | yoojia 定向复测 |
| `apply_domain_proposals.py` | 域名建议回写注册表 |
| `rerun_roster_textrun.py` | 全名录复测（textrun 新计划） |
| `intent-chain2.json` | 实盘链路验证意图 |
| `retrieval_web_smoke.py` | W1 网页检索冒烟（10 查询 × 360；门卫/分层可用/视角提示；`data-test/runs/web-smoke-*`） |
| `export_smoke_images.py` | 把冒烟报告里所有“下载成功”的图重新落盘（含门卫未通过），生成 all-downloads 画廊 |
| `reassess_smoke.py` | **离线**重评一批冒烟图：门卫 v3 + 概览/部件分层，新旧口径对照（`data-test/runs/web-reassess-*`） |
| `replay_filter_98.py` | **离线**两段式门卫全流程回放（98 个已下载文件）：标题护栏→预筛→v2/v3 门卫→视角→分层，产出 `report.md` + 对比页 `index.html`（逐张标签变换与 fail 原因） |

约定：这些脚本只做分析与复现，不承载生产逻辑；生产逻辑在 `src/equiplens/` 与 `tests/`。
临时一次性脚本仍放 `tmp/`（不入库）。
