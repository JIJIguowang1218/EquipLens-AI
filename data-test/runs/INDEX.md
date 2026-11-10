# 运行台账（data-test/runs）

> 由 `scripts/run_ledger.py` 生成，**不要手改**；结论请写在各目录的 `RUN.json.conclusion` 或 `REPORT.md`。
> 生成时间：2026-11-11T03:52:19 · 共 51 条 · 待补结论 1 条

| 阶段 | run_id | 类型 | 日期 | 状态 | 关键指标 | 结论/报告 |
|---|---|---|---|---|---|---|
| loop | `loop-c01-audit` | run | 2026-11-10 | FAILED | images=46 · gate_pass=37 | [FAILED](data-test/runs/loop-c01-audit/audit.html) |
| loop | `loop-c01-isolated` | run | 2026-11-10 | FAILED | — | [C01 隔离检索 loop 报告（2026-11-10）](data-test/runs/loop-c01-isolated/REPORT.md) |
| loop | `loop-c01-plan` | run | 2026-11-10 | FAILED | images=30 · gate_pass=27 | [1. **在线规划可用**：16 个候选全部带真实引用，外国品牌自然出现，不需要任何品牌表； 2. **引用核验可用**：56% 的引用页能直接匹配车型；未匹配](data-test/runs/loop-c01-plan/REPORT.md) |
| loop | `loop-c01-plan2` | run | 2026-11-10 | FAILED | images=23 · gate_pass=19 · $0.012 | [FAILED](data-test/runs/loop-c01-plan2/summary.json) |
| loop | `loop-c01-plan3` | run | 2026-11-10 | DONE | images=54 · gate_pass=49 · $0.0225 | [DONE](data-test/runs/loop-c01-plan3/summary.json) |
| loop | `loop-c01-plan4` | run | 2026-11-10 | DONE | images=45 · gate_pass=40 · $0.02325 | [C01 在线规划 + 补位 + 重规划 · 12 槽交付（2026-11-10）](data-test/runs/loop-c01-plan4/REPORT.md) |
| loop | `loop-c01-plan5` | run | 2026-11-10 | FAILED | images=47 · gate_pass=43 · $0.02475 | [FAILED](data-test/runs/loop-c01-plan5/summary.json) |
| loop | `loop-c01-plan6` | run | 2026-11-10 | FAILED | images=71 · gate_pass=54 · $0.02175 | [FAILED](data-test/runs/loop-c01-plan6/summary.json) |
| loop | `loop-c01-plan7` | run | 2026-11-10 | FAILED | images=78 · gate_pass=63 · $0.02175 | [FAILED](data-test/runs/loop-c01-plan7/audit.html) |
| loop | `loop-c01-plan8` | run | 2026-11-10 | FAILED | images=64 · gate_pass=52 · $0.021 | [FAILED](data-test/runs/loop-c01-plan8/summary.json) |
| loop | `loop-c01-plan9` | run | 2026-11-10 | DONE | delivery=12/12 · images=36 · gate_pass=32 · degraded=7 · $0.02625 | [C01 · 核验重构后 12 槽交付（2026-11-10）](data-test/runs/loop-c01-plan9/REPORT.md) |
| loop | `loop-c01-res` | run | 2026-11-10 | DONE | images=46 · gate_pass=36 | [C01 隔离检索 loop · 口径修正后重跑（2026-11-10）](data-test/runs/loop-c01-res/REPORT.md) |
| loop | `loop-m1-desert` | run | 2026-11-10 | FAILED | — | [FAILED](data-test/runs/loop-m1-desert/summary.json) |
| loop | `loop-m1-desert-v2` | run | 2026-11-10 | FAILED | — | [FAILED](data-test/runs/loop-m1-desert-v2/summary.json) |
| loop | `loop-m1-desert-v3` | run | 2026-11-10 | DONE | — | [DONE](data-test/runs/loop-m1-desert-v3/summary.json) |
| loop | `loop-m1b-global-20261110` | run | 2026-11-10 | DONE | delivery=20/12 · images=77 · gate_pass=75 · degraded=16 · $0.01875 | [v1：配额 bug 的现场（保留作证据）](data-test/runs/loop-m1b-global-20261110/REPORT.md) |
| loop | `loop-m1b-global-v2` | run | 2026-11-10 | DONE | delivery=12/12 · images=77 · gate_pass=75 · degraded=8 · $0.01875 | [独立测试：含外国品牌的 12 槽检索（2026-11-10）](data-test/runs/loop-m1b-global-v2/REPORT.md) |
| loop | `loop-ab4-a2-20261111` | run | 2026-11-11 | DONE | delivery=12/12 · images=82 · gate_pass=76 · degraded=7 · $0.01875 | [E15 下游验证：去重后 plan 跑 12 槽 → 12/12，无同款重复占槽，82 张唯一图，7 degraded。](data-test/runs/loop-ab4-a2-20261111/audit.html) |
| plan | `plan-ab-20261111` | plan-set | 2026-11-11 | — | — | E13 初版 A/B（一次性抽取）：出处不可归因、同组重合 12–17%。 |
| plan | `plan-ab2-20261111` | plan-set | 2026-11-11 | — | — | E14 planner v2 A/B：出处 100%，同组重合 26–31%。 |
| plan | `plan-ab3-20261111` | plan-set | 2026-11-11 | — | — | 中间实验：per-query 6/8 与池子下限（曾出现 11 台 <12 槽）；结论并入 E15。 |
| plan | `plan-ab4-20261111` | plan-set | 2026-11-11 | — | — | E15 最终 A/B n=3（per-query 8、车型去重后）：进口查询无增量。 |
| plan | `plan-c01` | plan | 2026-11-11 | — | candidates=16 | T34 早期规划（无 api_log，出处审计不完整）。 |
| plan | `plan-c01-auto` | plan | 2026-11-11 | — | candidates=19 | 候选 19 / 查询 6 / 去重移除 10 |
| plan | `plan-c01-auto-v2` | plan | 2026-11-11 | — | candidates=22 | 候选 22 / 查询 6 / 去重移除 13 |
| plan | `plan-c01-v2` | plan | 2026-11-11 | — | candidates=15 | T34 规划（4 次 Search + 引用校验；后续被 planner v2 取代）。 |
| plan | `plan-m1b-global` | plan | 2026-11-11 | — | candidates=23 | 候选 23 / 查询 7 / 去重移除 None |
| search | `diag-foreign` | diag | 2026-11-11 | — | images=17 · gate_pass=17 | E10 诊断：修复前 Zetros/Arocs/Volvo 在 360 的相关性护栏通过数为 0；不是 360 没图。 |
| engine | `p1-demo` | run | 2026-11-09 | DONE | — | [DONE](data-test/runs/p1-demo/summary.json) |
| text-retrieval | `run-budget-q1` | run | 2026-10-23 | — | — | [文本检索运行 run-budget-q1](data-test/runs/run-budget-q1/REPORT.md) |
| text-retrieval | `run-budget-q1-bing` | run | 2026-10-23 | — | — | [文本检索运行 run-budget-q1-bing](data-test/runs/run-budget-q1-bing/REPORT.md) |
| text-retrieval | `run-budget-q10` | run | 2026-10-23 | — | — | [文本检索运行 run-budget-q10](data-test/runs/run-budget-q10/REPORT.md) |
| text-retrieval | `run-budget-q3` | run | 2026-10-23 | — | — | [文本检索运行 run-budget-q3](data-test/runs/run-budget-q3/REPORT.md) |
| text-retrieval | `run-budget-q6` | run | 2026-10-23 | — | — | [文本检索运行 run-budget-q6](data-test/runs/run-budget-q6/REPORT.md) |
| text-retrieval | `run-gaokong-blind` | run | 2026-10-23 | — | — | [文本检索运行 run-gaokong-blind](data-test/runs/run-gaokong-blind/REPORT.md) |
| text-retrieval | `run-gaokong-blind-v2` | run | 2026-10-23 | — | — | [文本检索运行 run-gaokong-blind-v2](data-test/runs/run-gaokong-blind-v2/REPORT.md) |
| text-retrieval | `run-gaokong-blind-v3` | run | 2026-10-23 | — | — | [文本检索运行 run-gaokong-blind-v3](data-test/runs/run-gaokong-blind-v3/REPORT.md) |
| text-retrieval | `run-gaokong-budget20` | run | 2026-10-23 | — | — | [文本检索运行 run-gaokong-budget20](data-test/runs/run-gaokong-budget20/REPORT.md) |
| text-retrieval | `run-gaokong-budget20-v2` | run | 2026-10-23 | — | — | [文本检索运行 run-gaokong-budget20-v2](data-test/runs/run-gaokong-budget20-v2/REPORT.md) |
| text-retrieval | `run-suicheche-blind` | run | 2026-10-23 | — | — | [文本检索运行 run-suicheche-blind](data-test/runs/run-suicheche-blind/REPORT.md) |
| text-retrieval | `run-suicheche-blind-v2` | run | 2026-10-23 | — | — | [文本检索运行 run-suicheche-blind-v2](data-test/runs/run-suicheche-blind-v2/REPORT.md) |
| text-retrieval | `run-suicheche-blind-v3` | run | 2026-10-23 | — | — | [文本检索运行 run-suicheche-blind-v3](data-test/runs/run-suicheche-blind-v3/REPORT.md) |
| text-retrieval | `run-suicheche-profile` | run | 2026-10-23 | — | — | [文本检索运行 run-suicheche-profile](data-test/runs/run-suicheche-profile/REPORT.md) |

## 空目录 / 归档

- `filter-98-20261109` → empty（未删除，仅标记）
- `runs` → archived（未删除，仅标记）
- `web-reassess-20261109` → empty（未删除，仅标记）
- `web-smoke-20261109` → empty（未删除，仅标记）
- `web-smoke-harvest1-20261109` → empty（未删除，仅标记）
- `web-smoke-hd-20261109` → empty（未删除，仅标记）
- `web-smoke-v3-20261109` → empty（未删除，仅标记）
- `web-smoke-v5-20261109` → empty（未删除，仅标记）
