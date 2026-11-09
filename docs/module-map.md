# 模块清单（L0–L6，2026-10-30 建；2026-11-08 核对 L1.5/L5 状态）

记录当前系统分层与策略归属，供后续开发与交接对照。

## 分层与代码位置

| 层 | 职责 | 现在谁在做 | 代码/文件 |
|---|---|---|---|
| L0 任务书 | 找什么、不找什么、判据 | 文档 + 产品负责人拍板 | `docs/PRD.md`、`data-test/evals/*`、`docs/test-log.md` 意见纪要 |
| L1 意图与规划 | 意图解析、类目档案、查询计划、查询分层（vehicle/component/macro）、信源定向 | 规则 + 模型 | `schemas/intent.schema.json`、`textrun.resolve_profile`、`textrun.build_plan`、`data/category_profiles.json`、`data/source_registry.json` |
| L1.5 关联分析/清单推荐 | 用户"类目+部件"→ 页数预算内的检索清单（推荐/方向级/备选、四轴阶梯、惰性放闸） | **模型判断 + skill**；**清单模块 M0–M4 尚未开工（2026-11-08 核对）** | `skills/association/`（SKILL.md + schema + 3 脚本 + references + evals）；设计稿 `docs/roster-expansion-design.md` v0.2；校验 `check_list.py`、分配 `slots.py`、盘点 `inventory.py`；回归 `tests/test_association.py`。**缺** `data/part_axes.json`、`data/part_views.json` 与 `coverage()`/放闸实现 |
| L2 检索执行 | 搜索、抓取、robots、配额、去重、锚点过滤；检索 loop/检查点；网页适配器；源路由 | 确定性代码 | `corpus.py`、`webchannel.py`、`roster.py`、`imagesearch.py`、`gate.py`、`channels.py`；**检索中引擎 `retrieval_engine/`（P0–P1 契约/状态机；P2-W1 `web.py`/`evidence.py`；P2-W2 `sources.py` 源健康/熔断/缓存）** |
| L3 结果质检 | 段落切分、设计相关性、指向性判定（V/P/G/C） | 规则粗筛 + 模型 judge | `passage.py`（配置行/主题排除/A-B-C 打分 + `gate_passages` 双轨）+ `l3gate.py`（对象锚定/主题类型/具体性；已接入 text-run grade，假阳性 6.9%）+ 模型判定（评测集/审核包） |
| L4 迭代控制 | 重规划、降级、停止/问人、断点续跑 | 规则 | `strategy.assess`、`textrun` replan 循环、`runlog.py`；**降级链+重试=runner.py（本轮建设）** |
| L5 结构化沉淀 | 分析（图片 → schema）、Facts/Descriptions 抽取、报告 | **部分实现**：分析代码在，未验收 | `analysis.py`（prompt + schema 校验 + 多视角合并 + `analyze_batch.py`）；契约 `docs/superpowers/specs/2026-10-31-analysis-schema-design.md`；报告 `scripts/build_report_page.py`、`export_pptx.py`。**缺**金标评测、成本/延迟数字、与前端/证据表的接口 |
| L6 评估 | 评测集、回归、运行台账、误杀抽检、域名基准 | 规则 + 人工 | `data-test/evals/`、`data-test/runs/INDEX.md`、`src/equiplens/audit.py`、`src/equiplens/domainbench.py`、`T18-*` 报告 |

横切：`cli.py`、`schemas/`、`doctor.py`、审核包生成（`scripts/build_*_review.py`）。

## 策略归属（一句话版）

- **检索策略**（查什么、去哪类源、怎么分层）→ L1 计划层（`build_plan` + `query_meta` + `source_registry`）；L2 只照单执行。
- **筛选策略**（锚点过滤、主题排除、配置行、A/B/C）→ L2 粗筛 + L3 判定；最终语义判定留给模型。**双轨口径**：`a_chars`（关键词）与 `gated_a_chars`（过闸）同批并列，控制层（`strategy`）按后者判低信度。
- **控制策略**（重规划/降级/重试/断点）→ L4；当前只有 replan/stop/ask_user，缺通道级降级链（本轮补）。
- **验收与回归** → L6（评测集 + 台账 + INDEX）。

## 当前形态判断

现在是 **workflow agent**（固定流程图 + 关节处模型判断），不是自主 agent：
模型决定"查什么/怎么判"，但"要不要继续、换不换路"由阈值与规则控制。
演进方向：固定骨架 + 模型在 scope 内选动作（换查询/换源/换通道）+ 确定性护栏（robots/配额/账本/schema）。
