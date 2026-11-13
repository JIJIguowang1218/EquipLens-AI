# 实验与文件索引（2026-11）

> 目的：每个实验都能从“结论 → 数据 → 脚本 → 代码 → commit”追溯，避免散落 JSON/图片。
> 规则：新实验用 `data-test/evals/<topic>-<date>/` 或 `data-test/runs/<run-id>/`；必须带 README/结果文件；
> 运行图片默认不入库，人工核对页的缩略图除外。

## 索引

| 实验 | 结论/状态 | 数据与审核页 | 代码/脚本 | commit |
|---|---|---|---|---|
| E17b/T46 task-brief v2 vs v1 | v2 自动 10/10；v1 3/10；人工 v2 10 PASS、v1 6 PASS/3 FAIL/1 NA；v1 部件 124 vs v2 46 | `data-test/evals/task-brief-eval-v1b-20261111/`：`RESULTS.md`、`review.html`、`review-filled.json`、`REVIEW-SUITE-SUMMARY.md` | `scripts/eval_task_brief.py`、`scripts/render_brief_review.py`、`src/equiplens/briefing.py` | `afb2632`、`a0e9802` |
| E19/T47 意向排序 + 12+2 | 12/12；HF8066 rank6 占槽；2 primary 无图→backup 补位 | `data-test/runs/plan-ab4-20261111/A2/plan-ranked.json`；`data-test/runs/loop-intent-test{,-test2,-test3}-20261111/` | `scripts/rank_plan.py`；`retrieval_engine/{web,engine,cli,contracts}.py` | `5be302c` |
| E20/T48 失败原因 + 先验接线 | 403/DNS + 拼图/多车/客车；12 条失败 URL 重放 0/12；analysis 接 kind/location/family/why；部件兜底 query | `data-test/evals/failure-stats-20261111.{md,json}`、`failure-replay-sample-20261111.json` | `scripts/analyze_failure_stats.py`；`analysis.py`、`retrieval_engine/web.py` | `f8740ea` |
| E21/T49 扩源/换源 | 长 query 0；短 query/harvest 34 张过门卫，仅 1 probable；用户标注：8 目标/5 不是/8 不确定/13 空白；至少 5 张目标图被 unknown 漏掉 | `data-test/evals/source-expansion-{test,quality,harvest,verify}-20261111.json`；`source-expansion-review-20261111/`（`annotations.json`、`ANNOTATION-ANALYSIS.md`） | `scripts/build_source_expansion_review.py`；`imagesearch.py`（harvest） | `5d029b7`、`9b31be2`、`b17346a` |
| E22/T51 harvest 元数据（否定） | 首次 A/B 混淆 base/harvest；只取 harvest 图 21 张 A/B/C 均 0 通过；收益来自 base 搜索标题，不采纳，代码回退 | `data-test/evals/harvest-metadata-ab-20261111.md`、`harvest-only-abc-20261111.json` | `scripts/test_harvest_metadata.py` | 待提交 |
| E23 扩源新 brief | A 矿用宽体自卸车/B 12 方搅拌车（开发）、C 高空作业车（holdout）；均 4 部件，无具体品牌/车型；待人工审后跑 A/B | `data-test/evals/source-expansion-briefs-20261111/`（`briefs-review.html`、README、三份 brief） | `scripts/build_brief.py`、`scripts/render_new_briefs.py` | 待提交 |
| E24/T52 扩源 pilot（标注） | 100 行/81 唯一；53 target/24 not/22 uncertain；19 重复 URL；accepted 9/9 human target；门卫放行 part 场景，交付策略需加整车资格 | `data-test/evals/source-expansion-pilot-review-20261111/`（`annotations.json`、`ANNOTATION-ANALYSIS.md`） | 同上 | 待提交 |
| E24/T52 扩源 pilot | 5 brief ×6 候选=30；base 失败 24；通用 alias+harvest verifier 通过 9/24；C holdout 0/6；待人工盲评 100 图 | `data-test/evals/source-expansion-pilot-review-20261111/`（`review.html`、`PROBE-ANALYSIS.md`）；`data-test/runs/source-expansion-probe-20261111/` | `scripts/probe_source_expansion.py`、`scripts/render_probe_review.py`；新 brief/plan | 待提交 |
| E25/T53 失败 target 漏斗 | 23 唯一车型；base 0 accepted；exp 93 gate pass/23 图 accepted；pending 补评后 accepted precision **69.6%**（16/23），目标图 recall **32.7%**（16/49）；7 张 accepted 错图（车身类型/吨位） | `data-test/runs/source-expansion-funnel-20261111/`（`funnel.json`、`FUNNEL-ANALYSIS.md`）；`source-expansion-funnel-pending-review-20261111/`（`PENDING-ANALYSIS.md`） | `scripts/probe_source_expansion_funnel.py`、`scripts/render_funnel_pending_review.py` | `319d228`、`3dd2bfa`、待提交 |
| E26/T54 车身/吨位 guard | 激进 hard guard precision 75% 但误杀 8 目标；保守 68.2%；overview-only 62.5%；不采纳硬 guard | `data-test/evals/source-expansion-funnel-pending-review-20261111/BODY-GUARD-ANALYSIS.md`、`BODY-GUARD.json` | `scripts/apply_body_guard.py` | 待提交 |
| E27/T55 类目词 query（盲评更正） | 33 张：26 target/7 not；accepted 18：14 target/4 not，precision 77.8%；vs alias 69.6%，Fisher p≈0.726 不显著；不新增策略 | `data-test/evals/source-expansion-class-review-20261111/{review.html,annotations.json,CLASS-REVIEW-ANALYSIS.md}` | 同上 | 待提交 |
| E27/T55 类目词 query | 同 23 target；class query 7 accepted/2 overview，alias 8/1；95 gate pass/75 unknown；33 张盲评待标 | `data-test/runs/source-expansion-class-query-20261111/`、`data-test/evals/source-expansion-class-review-20261111/` | `scripts/probe_class_query.py`、`scripts/render_class_review.py` | 待提交 |
| E28/T56 Platform 层 | 同 23 target/class query；360 5 target accepted、Baidu 8、Bing 0、union 9；盲评后 360 precision 80%、Baidu 94.1%、union 89.8%；union 正确 target 8/23 | `data-test/runs/platform-probe-20261111/`、`data-test/evals/platform-review-20261111/` | `scripts/probe_platforms.py`、`scripts/render_platform_review.py` | 待提交 |
| E29/T57 Platform 完整 loop | 360 vs 360+Baidu 均 12/12；verification accepted 92.2%→25.5%，unknown 20→284；Baidu 丢 HF8066；平台不接入 | `data-test/runs/loop-platform-{360,baidu}-20261112/`、`PLATFORM-LOOP-ANALYSIS.md`、`PLATFORM-LOOP-DEEP-ANALYSIS.md` | `retrieval_engine/{web,cli}.py` opt-in `--platform-extra baidu` | `1399a89` |
| E30/T58 Platform 预筛修复 | 平台路径复用 `_relevant` 后 fetch 608→288、unknown 284→0、accepted 216/220；但丢 HF8066，平台仍不接入 | `data-test/runs/loop-platform-baidu-filtered-20261112/`、`FILTERED-PLATFORM-ANALYSIS.md` | `imagesearch.search_platforms`、`web.py`、`tests/test_imagesearch.py` | 待提交 |
| E31/T59 code prefilter | 360+code prefilter 完整 loop：12/12 构成不变，accepted 236→224；无 target 丢失 | `data-test/runs/loop-code-prefilter-20261112/` | `--code-prefilter`、`web._code_ok` | 待提交 |
| E32/T60 补位与专门来源 | 360+Baidu 定向补位试跑：missing rank2/4 的 Baidu query 0 accepted；360che 反爬、lmjx 超时，专门来源初测失败 | `data-test/runs/loop-platform-360-20261112/BACKFILL-ANALYSIS.md`、`data-test/evals/special-source-test-20261112.md` | `scripts/backfill_baidu.py` | 待提交 |
| E33/T61 P0 交付不变量 | 全局 asset 去重/attempts/part_only 软标记；hard overview 10/12 或 composition 变差，弃用；P0c 12/12 baseline | `data-test/runs/loop-p0c-20261112/P0-REVIEW.md`；`loop-p0/p0b` 为失败试验 | `retrieval_engine/{engine,contracts,web,cli}.py` | 待提交 |
| E39 交付缺口 + 耗时审计 | 4 个正选缺口 run 全部"有图 ≥ N"：c2 with 10 图→8+2、c1 without 11→9+2、c2 without 14→9+4（够 10+4）、c1 baseline 11→9+2。根因是 unit 配额 + 发现时冻结的 `unit_ids`，`_degraded_fill` 被同一把锁挡住；离线模拟"跨 unit 借位"后分别 10+0 / 10+1 / 10+4 / 10+1。耗时中位：plan 101s、rank 43s、loop 345s，loop 中 FETCH 270s（下载约 1s/张）、DISCOVER 71s | `data-test/runs/ab-negative-20261113/AUDIT-DELIVERY-TIMING.md`、`DELIVERY-AUDIT.json`；`docs/delivery-audit-20261113.md` | 分析脚本内联；修复见后续 commit | 待提交 |
| E38 negative A/B（with vs without `-"…"`） | 5 brief 冻结、唯一变量为查询后缀：两臂均 **48/50 + 18/20**，零差异；30 条查询回放 20 条结果完全相同、平均 1.6/20 URL 变化；同配置重跑自带 ±2 台/±12% 成本噪声 → **收益未证实，按预注册规则保留**；审计另发现 `normalize_query` 对所有类目拼 `6x6`、rank 成本未记账、多处死配置 | `data-test/runs/ab-negative-20261113/`（`AB-SUMMARY.md`、`SEARCH-LEVEL.json`、各 case `QUERY-DIFF.json`）；`docs/negative-ab-20261113.md` | `scripts/ab_negative.py`、`plan_candidates.py --no-negative`、`planning.build_query_plan(use_negative=)` | 待提交 |
| E37 修复后 5 输入复跑（clean） | negative 只收短词 + 恢复查询意图后：9/10+b2/4、10/10+b2/4、10/10+b4/4、6/6+b4/4、14/14+b4/4；候选 17/16/27/24/36；峰值成本合计 ¥2.064。**修正 E34/E35**：此前“沙漠牵引车候选空间只有 10–14”是 negative/查询塌缩造成的，不是车源上限；同代码两次 c1 为 9/10 与 10/10，存在 ±1 波动 | `data-test/runs/delivery-20261112-clean/`（SUITE-SUMMARY.md、各 DELIVERY.md） | 同前 | 待提交 |
| E36 去重人工审核（沙漠牵引车） | 14 张卡：12 张合并正确、2 张不该单独保留（#6 并入 #2、#12 弱泛称）、1 张需拆（HF8066/H6066）；离线回放 22 种写法 → **12 个候选**（原 14）。剩余疑似重复：#4/#9（460 牵引头 vs 牵引车头）、#10/#14（东风前缀） | `../dedupe-verdicts.json`（桌面）、`data-test/runs/delivery-20261112-q12/c1-desert-tractor/dedupe-review.html` | `scripts/build_dedupe_review.py`、`planning.merge_candidates` | 待提交 |
| E35 查询构造 + 补查询（对照） | 短查询（去长描述）：正面吊 7/10→10/10、拖拉机 8/10→10/10、叉车备选 2/4→4/4，沙漠牵引车 9/10→7/10（单轮波动，待复跑）；再加 `--topup 2`：正面吊备选 1/4→4/4、沙漠 7/10→8/10，成本 +18% | `data-test/runs/delivery-20261112-q1`、`-q12`（各含 SUITE-SUMMARY.md） | `planning.short_text/top_up_queries`、`plan_candidates --topup` | 待提交 |
| E34 交付泛化测试（5 输入） | ⚠️ 已修正：当轮 brief 的 negative 被 LLM 写成整句，查询产出偏低；数字作废，见 E37 | 10/10/10/6/14 槽：9/10、7/10、8/10、6/6、14/14；备选 1/0/1/2/4。根因是 planner 产出不足（候选 12/8/11/12/30 vs 需 23/23/23/16/29），不是检索执行 | `data-test/runs/delivery-20261112/`（SUITE-SUMMARY.md、各 case 的 DELIVERY.md） | `scripts/run_delivery_suite.py`、`summarize_delivery_suite.py`、`build_delivery_manifest.py` | 待提交 |
| 收口：Recovery/扩源 | 停止叠策略，不接生产；当前是 Query+Source，Platform 未测；class vs alias p≈0.726 不显著；C holdout 0/6 | `docs/recovery-strategy-closeout.md`；E17b/E19–E27 数据 | 相关 probe 脚本仅实验用 | `b15dc8d` 后收口 |
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
