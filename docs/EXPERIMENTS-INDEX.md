# 实验与文件索引（2026-11）

> 目的：每个实验都能从“结论 → 数据 → 脚本 → 代码 → commit”追溯，避免散落 JSON/图片。
> 规则：新实验用 `data-test/evals/<topic>-<date>/` 或 `data-test/runs/<run-id>/`；必须带 README/结果文件；
> 运行图片默认不入库，人工核对页的缩略图除外。

## 索引

| 实验 | 结论/状态 | 数据与审核页 | 代码/脚本 | commit |
|---|---|---|---|---|
| E17b/T46 task-brief v2 vs v1 | v2 自动 10/10；v1 3/10；人工 v2 10 PASS、v1 6 PASS/3 FAIL/1 NA；v1 部件 124 vs v2 46 | `data-test/evals/task-brief-eval-v1b-20261111/`：`RESULTS.md`、`review.html`、`review-filled.json`、`REVIEW-SUMMARY.md` | `scripts/eval_task_brief.py`、`scripts/render_brief_review.py`、`src/equiplens/briefing.py` | `afb2632`、`a0e9802` |
| E19/T47 意向排序 + 12+2 | 12/12；HF8066 rank6 占槽；2 primary 无图→backup 补位 | `data-test/runs/plan-ab4-20261111/A2/plan-ranked.json`；`data-test/runs/loop-intent-test{,-test2,-test3}-20261111/` | `scripts/rank_plan.py`；`retrieval_engine/{web,engine,cli,contracts}.py` | `5be302c` |
| E20/T48 失败原因 + 先验接线 | 403/DNS + 拼图/多车/客车；12 条失败 URL 重放 0/12；analysis 接 kind/location/family/why；部件兜底 query | `data-test/evals/failure-stats-20261111.{md,json}`、`failure-replay-sample-20261111.json` | `scripts/analyze_failure_stats.py`；`analysis.py`、`retrieval_engine/web.py` | `f8740ea` |
| E21/T49 扩源/换源 | 长 query 0；短 query/harvest 34 张过门卫，仅 1 probable；用户标注：8 目标/5 不是/8 不确定/13 空白；至少 5 张目标图被 unknown 漏掉 | `data-test/evals/source-expansion-{test,quality,harvest,verify}-20261111.json`；`source-expansion-review-20261111/`（`annotations.json`、`ANNOTATION-ANALYSIS.md`） | `scripts/build_source_expansion_review.py`；`imagesearch.py`（harvest） | `5d029b7`、`9b31be2`、`b17346a` |
| E22/T51 harvest 元数据（否定） | 首次 A/B 混淆 base/harvest；只取 harvest 图 21 张 A/B/C 均 0 通过；收益来自 base 搜索标题，不采纳，代码回退 | `data-test/evals/harvest-metadata-ab-20261111.md`、`harvest-only-abc-20261111.json` | `scripts/test_harvest_metadata.py` | 待提交 |
| E23 扩源新 brief | A 矿用宽体自卸车/B 12 方搅拌车（开发）、C 高空作业车（holdout）；均 4 部件，无具体品牌/车型；待人工审后跑 A/B | `data-test/evals/source-expansion-briefs-20261111/`（`briefs-review.html`、README、三份 brief） | `scripts/build_brief.py`、`scripts/render_new_briefs.py` | 待提交 |
| E24/T52 扩源 pilot（标注） | 100 行/81 唯一；53 target/24 not/22 uncertain；19 重复 URL；accepted 9/9 human target；门卫放行 part 场景，交付策略需加整车资格 | `data-test/evals/source-expansion-pilot-review-20261111/`（`annotations.json`、`ANNOTATION-ANALYSIS.md`） | 同上 | 待提交 |
| E24/T52 扩源 pilot | 5 brief ×6 候选=30；base 失败 24；通用 alias+harvest verifier 通过 9/24；C holdout 0/6；待人工盲评 100 图 | `data-test/evals/source-expansion-pilot-review-20261111/`（`review.html`、`PROBE-ANALYSIS.md`）；`data-test/runs/source-expansion-probe-20261111/` | `scripts/probe_source_expansion.py`、`scripts/render_probe_review.py`；新 brief/plan | 待提交 |
| E25/T53 失败 target 漏斗 | 23 唯一车型；base 0 accepted；exp 93 gate pass/70 unknown/23 图 accepted；target 8 但 overview 1、part-only 7；recall 主漏损核验 unknown | `data-test/runs/source-expansion-funnel-20261111/`（`funnel.json`、`FUNNEL-ANALYSIS.md`）；pending 盲评 `source-expansion-funnel-pending-review-20261111/` | `scripts/probe_source_expansion_funnel.py`、`scripts/render_funnel_pending_review.py` | 待提交 |
| LangGraph 迁移评估 | 暂不全量迁移；先扩源/恢复；分支/feature flag/并行回归 | `docs/langgraph-migration-plan.md` | 待启动 | `1787605` |
| generic 只标不删 | 12/12，3 generic 交付，82 图；无删除 | `data-test/runs/loop-generic-test-20261111/`、`audit.html` | `scripts/render_fetch_audit.py` | `70970ad` |

## 目录约定

- `data-test/evals/<name>/`：评测/人工审核；保留 `RESULTS.md`、`review.html`、导出 JSON、README。
- `data-test/runs/<run-id>/`：完整 loop；保留 `state.json`、`summary.json`、`fetch_log.jsonl`、`audit.html`、`RUN.json`；`images/` 不入库。
- `scripts/`：可重复运行的入口；每个实验必须能从脚本重建数据。
- `docs/retrieval-experiments-log.md`：实验结论；`docs/test-log.md`：T 编号索引；`docs/HANDOFF.md`：交接状态。

## 未完成/注意

- 扩源 34 张图的用户标注**未成功持久化**（file:// localStorage 被 Edge 禁用）；核对页已修复导出兜底，需重标或从仍打开的旧页用 `RESCUE.md` 的 console 片段导出。
- 扩源尚未接入生产 loop；先做 preferred target 的 `RECOVER`，不要全局 harvest。
