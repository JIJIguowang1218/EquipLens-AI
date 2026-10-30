# scripts/：可复现的评测与测试脚本

从 `tmp/`（gitignore 临时区）迁入，随仓库同步，供新会话复跑与审计。

| 脚本 | 用途 |
|---|---|
| `run_roster_crawl.py` | T18-roster 首跑：4 类目 39 车型语料采集 |
| `recrawl_craneL.py` / `recrawl_generic.py` | 轻型吊车补爬 / 宏观设计查询补爬 |
| `roster_judge_sheet.py` | 生成三分类判定工作表 |
| `roster_verdicts.py` / `roster_verdicts_round2.py` | 模型层判定结果（第一轮/新增） |
| `remap_verdicts.py` | 旧判定 → 稳定 ID 映射 |
| `roster_aggregate.py` | 三类占比聚合与报告 |
| `build_roster_review.py` / `build_l3_review.py` | 审核包 HTML 生成 |
| `eval_l3gate.py` | 确定性闸门在 265 段金标上的评估 |
| `domain-bench-queries*.json` | 域名基准查询集（两轮） |
| `compare_domain_bench.py` | 两轮域名基准对比 |
| `check_yoojia.py` | yoojia 定向复测 |
| `apply_domain_proposals.py` | 域名建议回写注册表 |
| `rerun_roster_textrun.py` | 全名录复测（textrun 新计划） |
| `intent-chain2.json` | 实盘链路验证意图 |

约定：这些脚本只做分析与复现，不承载生产逻辑；生产逻辑在 `src/equiplens/` 与 `tests/`。
临时一次性脚本仍放 `tmp/`（不入库）。
