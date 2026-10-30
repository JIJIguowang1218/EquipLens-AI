# 模块清单（L0–L6，2026-10-30）

记录当前系统分层与策略归属，供后续开发与交接对照。

## 分层与代码位置

| 层 | 职责 | 现在谁在做 | 代码/文件 |
|---|---|---|---|
| L0 任务书 | 找什么、不找什么、判据 | 文档 + 产品负责人拍板 | `docs/PRD.md`、`data-test/evals/*`、`docs/test-log.md` 意见纪要 |
| L1 意图与规划 | 意图解析、类目档案、查询计划、查询分层（vehicle/component/macro）、信源定向 | 规则 + 模型 | `schemas/intent.schema.json`、`textrun.resolve_profile`、`textrun.build_plan`、`data/category_profiles.json`、`data/source_registry.json` |
| L2 检索执行 | 搜索、抓取、robots、配额、去重、锚点过滤 | 确定性代码 | `corpus.py`、`webchannel.py`、`roster.py`、`imagesearch.py`、`gate.py`、`channels.py` |
| L3 结果质检 | 段落切分、设计相关性、指向性判定（V/P/G/C） | 规则粗筛 + 模型 judge | `passage.py`（配置行/主题排除/A-B-C 打分）+ `l3gate.py`（对象锚定/主题类型/具体性，假阳性 6.9%）+ 模型判定（评测集/审核包） |
| L4 迭代控制 | 重规划、降级、停止/问人、断点续跑 | 规则 | `strategy.assess`、`textrun` replan 循环、`runlog.py`；**降级链+重试=runner.py（本轮建设）** |
| L5 结构化沉淀 | Facts/Descriptions 抽取、报告 | 未实现（下游） | — |
| L6 评估 | 评测集、回归、运行台账、误杀抽检、域名基准 | 规则 + 人工 | `data-test/evals/`、`data-test/runs/INDEX.md`、`src/equiplens/audit.py`、`src/equiplens/domainbench.py`、`T18-*` 报告 |

横切：`cli.py`、`schemas/`、`doctor.py`、审核包生成（`scripts/build_*_review.py`）。

## 策略归属（一句话版）

- **检索策略**（查什么、去哪类源、怎么分层）→ L1 计划层（`build_plan` + `query_meta` + `source_registry`）；L2 只照单执行。
- **筛选策略**（锚点过滤、主题排除、配置行、A/B/C）→ L2 粗筛 + L3 判定；最终语义判定留给模型。
- **控制策略**（重规划/降级/重试/断点）→ L4；当前只有 replan/stop/ask_user，缺通道级降级链（本轮补）。
- **验收与回归** → L6（评测集 + 台账 + INDEX）。

## 当前形态判断

现在是 **workflow agent**（固定流程图 + 关节处模型判断），不是自主 agent：
模型决定"查什么/怎么判"，但"要不要继续、换不换路"由阈值与规则控制。
演进方向：固定骨架 + 模型在 scope 内选动作（换查询/换源/换通道）+ 确定性护栏（robots/配额/账本/schema）。
