# 续接文档：进度与待补信息

| 属性 | 内容 |
|---|---|
| 更新日期 | 2026-10-30 |
| 当前阶段 | **文本检索线（R2 后半）策略验证轮完成，L3 评测基准已建**。图像检索三轮类目测试已验收（T13–T15），判向已收口（v0.2.5）。文本线进展：T16 语料采集（原始）→ T17 重爬+设计分析筛选（10 篇/42,743 字，**可用设计分析仅 6.3%**，核心正例=09 的"京剧脸谱式设计→J6→J7 家族化延续"）→ T18-pre（LLM 查询规划：文章命中率 40%→100%）→ T18-broad（多车型放宽暴露来源污染/歧义/误拦）→ T18-blind（编排器首跑 + 留出类目盲测，runlog/strategy/passage/textrun 全落地）→ T18-budget（修复三个隐藏预算帽）→ T18-budget-curve（离线 q3≈6 篇 A 2,068 字，边际由高产出源决定）→ **T18-eval（L3 评测集 v1：7 篇标注，关键词假阳性率 43%）**。**部件类型学属下游分析整合模块，不在当前检索阶段**。运行台账 `data-test/runs/INDEX.md`。**🔴 待产品负责人审核：①L3 评测集 v1（`data-test/evals/l3-relevance-v1.json`）— 7 篇逐篇标注 + 判定理由，可抽查可复核 ②确定性闸门实现方案（四级判定 A_cat/A_comp/A_gen/C + 类目闸 + 主题类型排除 + 具体性要求）③文本 LLM provider/key/预算**；**10-30 新增：T18-roster 全名录 39 车型筛选测试完成（V 3.2%/P 12.9%/G 9.2%/C 74.8%）——指向具体车型的好文本极稀缺，产品负责人定调 VLM 看图为主、文本换岗为语汇/定调/事实辅助（意见 #21）** |
| 用途 | 新会话/新成员从此接续，不必重读全部讨论历史 |

## 0.0 当前状态快照（2026-10-30，新会话先读这里）

**阶段**：检索模块（文本线）技术侧已完成，进入"整体测试"前夜；**VLM 分析线后置**（等整体测试后再议）。

**已完成工具链（全部有测试与台账）**：

| 层 | 组件 | 状态 |
|---|---|---|
| L1 计划 | `textrun.build_plan`：query_meta 分层（vehicle/component/macro）、预算按类型轮转截断、明确车型不再歧义阻塞 | ✅ 10-30 |
| L2 执行 | `corpus.collect_corpus`：按查询给 relevant_terms；`site:` 定向为实验开关、默认关闭 | ✅ |
| L3 质检 | `passage`（配置行/主题/ABC）+ **`l3gate`**（对象锚定+主题排除+具体性）；假阳性 40.4%→**6.9%**、召回 85.7% | ✅ 10-30 |
| L4 控制 | **`runner`**：有限重试/退避、降级链 auto→延迟百度→Bing、契约验收、断点续跑；`strategy` | ✅ 10-30 |
| L6 评估 | **`audit`**（误杀分层抽样+Wilson 上界）、**`domainbench`**（域名基准/发现）、`evals/`、`runs/INDEX.md` | ✅ 10-30 |

**关键实测**：T18-roster 39 车型（V 3.2%/P 12.9%/G 9.2%/C 74.8%）；domain-bench 发现 www.yoojia.com 入库 high（复测 71.8/千字）；run-chain2/2b 实盘链路通（含自动抽检包）。

**下一步**：①把 `l3gate` 接入 `text-run` 的 grade 阶段；②整体测试（闸门→runner→audit→报告全链路）；③按结果再议 VLM 启动。

**待产品负责人决策（3 项，见 §3.1）**：文本爬取启动时机、关联分析层级策略、关联 skill 形态。

## 0. 部署形态（2026-10-17 讨论）

产品负责人确认方向：产品期采用**云端部署**（用户主机晚上断电, 不能当线上服务器）。共识框架：①"本地模型"=自托管模型（权重文件装进服务器环境即上云）, 用户永远只请求网页服务、零下载; ②分层原则——高频廉价判断（CLIP 门卫/探针）本地或服务器自托管, 低频高价值判断（VLM）走云 API; ③开发期单机, 演示期轻量云主机或内网穿透。正式结论待架构方案定稿（PRD 开放问题 #5 有了初步答案）。

## 0.1 AI 产品分层与当前研究层（2026-10-23 起协作约定）

产品负责人要求：以后按"AI 产品分层"方式共同优化，每轮明确研究哪一层。分层与当前状态：

| 层 | 职责 | 是否用 LLM | 当前状态 |
|---|---|---|---|
| L0 目标/任务书 | 定义找什么、不要什么（system prompt/任务说明） | 是 | 人类文档已有，未变成模型任务书 |
| L1 查询规划 | 意图识别（类别/车型/目标/约束/歧义）+ 查询改写/拆解/扩展 | **是（已验证）** | T18-pre 文章命中率 40%→100%；T18-broad 证明歧义与选源必须先做 |
| L2 检索执行 | 搜索、抓取、robots、配额 | 否 | 已实现，稳定 |
| L3 结果质检 | 段落抽取、类目相关性、来源质量 | **是（当前重点）** | 闸门 v1 已实现：对象锚定+主题排除+具体性，假阳性 6.9%/召回 85.7% |
| L4 迭代控制 | 缺口检测、换词/加源/停止 | 是 | runner 已实现（重试/降级/断点），待整体测试 |
| L5 结构化沉淀 | Facts/Descriptions 抽取 | 是 | 未实现，随 M4/下游 |
| L6 评估 | 策略 A/B、指标与回归 | 部分 | 运行台账 + 评测集 v1 + audit + domain-bench 已建 |

**当前研究层：L3**（段落级类目相关性/主题类型判定）。`intent.json` 与 `plan.json` 分开建 schema；L1 决定"问什么、去哪类源、问多少、排除什么"，L2 按计划确定性执行，L4 决定"是否再查/停止"。L2 已稳，暂不重做；每轮测试须写明：研究层、对照变量、验收指标。

**自由度原则（2026-10-23）**：写死不变量（robots/配额/账本/检查点/schema），内容知识放数据（来源注册表/类目档案/词表），判断放模型（意图/查询/选源/段落/停止）。长尾类目不枚举：通用层 + 类目档案叠加，新类目走"侦察 → LLM 提议 → 人工确认 → 缓存"；缺档案时用通用层兜底并标记 `profile_missing`。**禁止再往代码里加类目/站点特判**（现有 `BRANDS`/`VEHICLE_WORDS`/`SYNONYMS`/`BLOCK_URL_RE` 列为技术债，逐步迁到数据）。

## 1. 已完成

| 产出 | 位置 | 状态 |
|---|---|---|
| 项目总览 | `README.md` | 与 PRD 同步 |
| PRD v1.0 | `docs/PRD.md` | 定稿，含 8 个开放问题 |
| 报告增强研讨稿 | `docs/report-enhancement-proposal.md` | v0.1 待讨论 |
| 架构方案研讨稿（一） | `docs/architecture-discussion.md` | v0.2（交互范式已确认 / workflow-agent 分层 / skill 清单） |
| 数据模型规范（单车素材管理） | `docs/data-model-spec.md` | v0.1 定稿，待产品负责人逐字段复核 |
| 数据层骨架 | `schemas/equip-data.schema.json`、`db/schema.sql`、`src/equiplens/` | 可用：建库 / 导入导出 / 确认撤销 / 派生查询 |
| 数据层第一档测试 | `tests/test_data_layer.py`、`docs/test-report-data-layer.md` | 2026-10-10 执行，27/27 通过 |
| P1·M1 导入与判重 | `src/equiplens/ingest.py`、`src/equiplens/cli.py`、`tests/test_ingest.py` | 2026-10-12 完成：9/9 通过 + 27/27 回归 |
| P1·M2 确认工作流 | `src/equiplens/workflow.py`、CLI 子命令、`tests/test_workflow.py` | 2026-10-12 完成：11/11 三轮稳定 |
| P1·M3 库内检索 | `src/equiplens/query.py`、`tests/test_query.py`、规范 v0.2 | 2026-10-12 完成：组合过滤/聚类/相似检索/文字搜索/词表提名池 |
| 检索模块工具对标调研 | `docs/retrieval-tooling-research.md` | 2026-10-14 完成 |
| 检索模块设计研讨稿 | `docs/retrieval-module-design.md` | 2026-10-14 完成：D12/D13/D14 + R0–R7 + S1–S5 |
| M3.1 补丁 | `src/equiplens/doctor.py` 等 | 2026-10-14 完成：9/9 + 回归 58 项全绿 |
| 检索 R0 脚手架 | `src/equiplens/retrieval.py`、`review.py` 等 | 2026-10-14 完成 |
| 检索 R1 图文检索核心 | `src/equiplens/channels.py` 等 | 2026-10-14 完成 |
| 真实渠道（R7 首半段） | `src/equiplens/webchannel.py` 等 | 2026-10-14 完成 |
| 实时审核服务（意见 #10） | `src/equiplens/reviewserver.py` 等 | 2026-10-15 完成 |
| 数据分库与测试台账 | `docs/test-log.md`、`data-test/` | 2026-10-15/16 完成 |
| CLIP 门卫与判向体系 | `src/equiplens/gate.py` 等 | 2026-10-15/16 完成 |
| T7/T8 批次 | batch-roster2/gener-20261015 | 2026-10-15 完成 |
| 名录驱动搜图 | `src/equiplens/imagesearch.py` 等 | 2026-10-15 完成 |
| 判向探针 v2 | `src/equiplens/probe.py` 等 | 2026-10-17 完成 |
| 判向收口 | 规范 v0.2.5 | 2026-10-17 完成 |
| R2 首半：名录生成器 | `src/equiplens/roster.py` 等 | 2026-10-17 完成 |
| 搜图并行化 + T13 | `imagesearch.py` 等 | 2026-10-17 完成 |
| T14/T15 扩大检索 | roster.py 同义词、批次 craneH/L + r3loader | 2026-10-18 完成 |
| 调研语料采集批（T16） | `src/equiplens/corpus.py`、`tests/test_corpus.py` | 2026-10-22 完成 |
| **T17 语料重爬与设计文本筛选** | `data-test/corpus/batch-corpus-20261023{a,b}/`、`design-passages-20261023.md`、`review-corpus-20261023.html`、`docs/text-retrieval-design.md` | 2026-10-23 完成：10 篇 / 42,743 字；**A 类设计分析 2,698 字 = 6.3%**（叙述性正文 12.5%）；策略 v0.1 |
| **T18-pre LLM 查询规划预实验** | `tmp/corpus-plan-3-llmplan.json`、批次 batch-corpus-20261023c-llmplan | 2026-10-23 完成：设计语汇查询使有 A 段文章 **4/10→8/8**；`grade_batch.py` |
| **T18-broad 多车型放宽预实验** | 批次 batch-corpus-20261023d-broad | 2026-10-23 完成：起重机被爱采购商品页淹没；装载机命中学术文但豆丁只有预览；"翻斗车" vs "装载机"歧义实证；好文被 URL 规则误拦 |
| **T18-blind 编排器首跑 + 留出类目盲测** | `src/equiplens/{runlog,strategy,passage,textrun}.py`；`data/{source_registry,category_profiles}.json`；`schemas/{intent,text-plan}.schema.json`；`data-test/runs/` | 2026-10-23 完成：intent→档案→计划→执行→段落评估→低信度重规划→报告闭环；每次运行 events.jsonl + summary.json + report.md；CLI `text-run`；随车吊盲测 3 篇 / A 198 字 / 1.8% → replan→stop；高空作业车 v3 第 2 轮 6.6% → ok |
| **T18-budget 隐藏预算帽修复** | `textrun.py` 配额模型、`corpus.py` SERP 诊断、schema 上限 | 2026-10-23 完成：修复 `per=min(3,…)`、`quota≤查询数`、`schema quota≤10` 三个暗帽；`max_fetch` 真正生效（6→60 线性缩放）；`serp_looks_blocked` 诊断 |
| **T18-budget-curve 预算-产出曲线** | `data-test/runs/BUDGET-CURVE-20261023.md`、`data-test/runs/INDEX.md`（14 条） | 2026-10-23 完成：在线 4 档被百度验证页全拦；离线近似 **q3≈6 篇 A 2,068 字（5.2%）**，边际由"高产出源"决定；Bing RSS/HTML 不可用已记录 |
| **T18-eval L3 评测集 v1** | `data-test/evals/l3-relevance-v1.json` | 2026-10-23 完成：盲测 7 篇 A 级文章逐篇标注四级（A_cat/A_comp/A_gen/C），**关键词假阳性率 43%**（3/7 是空洞营销/竞赛攻略/毕设代做）；A_cat 真实产出仅 2,410 字（51%） |
| **T18-roster 全名录大规模文本筛选测试** | `data-test/runs/T18-ROSTER-20261030.md`、`data-test/evals/review-roster-20261030.html`、批次 `batch-corpus-roster-*-20261030` | 2026-10-30 完成：4 类目 39 车型（T13–T15 锁定名录），61 篇/3.65M 字正文，265 段模型判定；**V 3.2% / P 12.9% / G 9.2% / C 74.8%**（候选段口径）；39 车型仅 8 个有 V/P 素材（HOWO MAX/JH6/J6G/豪沃6X6/QY25K5C/QY35K5/SAC16000S/金刚S1 EV）；**A 档假阳性 40.4% 复现 L3 v1**；C 档 47% 是汽车之家首页/报价页 |
| **检索计划查询分层 + 信源定向 + 配置行过滤（待办1/2）** | `textrun.build_plan`（query_meta）、`corpus.collect_corpus`（按查询给词）、`passage.CONFIG_LINE_RE`、`source_registry.preferred_domains` | 2026-10-30 完成：查询按 vehicle/component/macro 三类配 relevant_terms；`site:` 定向 360che/21-sun；报价配置行判 C；回归候选段 **265→162（-39%）**，测试全绿 |
| **L4 执行 loop（runner）：重试+降级链+断点** | `src/equiplens/runner.py`、`tests/test_runner.py`，`textrun.execute` 已接入 | 2026-10-30 完成：Temporal 式重试语义（有限尝试/退避）、通道降级链（auto→延迟重试百度→Bing）、单元契约验收、状态 JSON 原子写续跑；runner 6/6 测试通过，真实小批 run-smoke-runner 验证 ok（2 篇/9 候选/auto 通道） |
| **误杀抽样检测（audit）** | `src/equiplens/audit.py`、`tests/test_audit.py`、`data-test/evals/audit/` | 2026-10-30 完成：C 档按"域×长度"分层抽样 + 强语汇/型号护栏队列 + 加权漏杀率估计（含 Wilson 95% 上界）；T18-roster 四批实测 C 档 6,076 段，抽样 23 条全判 C（估计漏杀 0%，95% 上界 14.3%），护栏 166 条抽查 12 条 0 命中；text-run 收尾自动生成 audit-sheet.json/md（run-chain2b 验证） |
| **确定性闸门 v1（L3）** | `src/equiplens/l3gate.py`、`tests/test_l3gate.py`、`data-test/evals/l3-gate-v1.{md,json}`、CLI `gate-batch` | 2026-10-30 完成：对象锚定 + 主题类型排除 + 具体性要求（部件/形态证据）；T18-roster 265 段金标评估：**精确率 93.1% / 召回 85.7% / 假阳性 6.9%**（关键词基线 40.4%）；实盘批次通过 5/750 |
| **域名基准与发现通道（domain-bench）** | `src/equiplens/domainbench.py`、`tests/test_domainbench.py`、`data-test/evals/domain-bench-20261030*/` | 2026-10-30 完成：同查询跨站点对照（A/千字、抓取成功率、robots），产出排行榜+升降级建议；首跑 18 域名/24 页发现 **www.yoojia.com（89.5 A/千字）并入库 high**；复测 26 域名/42 页（yoojia 定向 71.8/千字）确认；提案门槛改为新增需 ≥2 页/≥5K 正文、降级需 ≥3 页/≥15K |

## 2. 关键结论（30 秒版）

1. 现状流程是"人工 + 通用网页 AI"半自动；产品价值 = 流程产品化（闭集匹配、裁图、排版、溯源、合规）；
2. 车型识别重构为两阶段**闭集匹配**（名录 → 照片对号），FR-1.1 验收口径需改；
3. 素材不足是常态 → FR-1.2 优先级上调；竞品集 = 同类 + 近似类目；
4. FR-3 特征线规格已具体化；PRD 两处遗漏：封底、素材充分性评估；
5. 模块版图五块：素材资产库 + 检索 + 分析整合 + 报告规划 + 排版；统一分析 schema（结构/设计/意图三维度）是四模块公共合同；
6. 知识沉淀走进化式（数据飞轮）；检索模块"对话为壳、结构化对象为核"；
7. 部署形态定为**单机本地（SQLite + 文件系统）**；单车数据模型定稿；
8. 检索模块调研：四层栈均无需自研；
9. **文本检索（2026-10-23）**："车型名+评测/外观"查询产不出设计文本（6.3%）；LLM 查询规划提升文章命中率（40%→100%）；**关键词段落打分假阳性 43%**；预算边际由"高产出源"决定而非篇数；部件类型学归下游分析整合模块。

## 3. 下一步（按序执行）

1. ~~M3.1 / R0 / R1 / 真实渠道 / 名录搜图 / 泛化测试~~ ✅；
2. ~~判向探针~~ ✅（2026-10-17 收口）；
3. ~~扩大检索测试 T13–T15~~ ✅（2026-10-18，三类目泛化验证通过）；
4. **文本检索线（R2 后半·当前主线）**：
   - ~~第 0 步语料采集（T16）~~ ✅
   - ~~第 0 步复盘（T17：设计分析 6.3%，策略 v0.1）~~ ✅
   - ~~T18-pre LLM 查询规划预实验~~ ✅（文章命中率 40%→100%）
   - ~~T18-broad 多车型放宽~~ ✅（暴露来源污染/歧义/误拦）
   - ~~T18-blind 编排器首跑 + 留出类目盲测~~ ✅（随车吊 1.8%→stop；高空作业车 6.6%→ok）
   - ~~T18-budget 隐藏预算帽修复~~ ✅
   - ~~T18-budget-curve 预算-产出曲线~~ ✅（q3≈6 篇 A 2,068 字；边际由高产出源决定）
   - ~~T18-eval L3 评测集 v1~~ ✅（假阳性 43%）；10-30 产品负责人逐篇裁决（意见 #20）：指向性标准=对象锚定
   - ~~T18-roster 全名录大规模文本筛选~~ ✅（10-30：39 车型/265 段判定，V 3.2%/P 12.9%/G 9.2%；A 档假阳性 40.4% 复现）
   - ~~确定性闸门~~ ✅（10-30：`l3gate.py` 对象锚定+主题排除+具体性；假阳性 6.9%、召回 85.7%；CLI `gate-batch`）
   - **下一步（10-30）**：①`l3gate` 接入 `text-run` 的 grade 阶段 ②整体测试（闸门→runner→audit→报告）③按结果再议 VLM
   - 信源定向：选 B（放弃 query 级 site 定向，保留域名信任加权）
   - 关联分析（10-30 新需求，见 §3.1 P2/P3）：缺口评估 → 关联提案（带依据/置信度/注意事项）→ 用户确认 → 检索
   - → T18 部件专项（12 部件 × 3 车型）→ T19 主题趋势 → T20 跨类目——仍只验证检索策略，不建类型学
   - **类型学与分析写作规范归下游分析整合模块**

### 3.1 决策台账（2026-10-30）

**已定**：

| # | 决策 | 记录 |
|---|---|---|
| D1 | 产品期云端部署；开发期单机 | 2026-10-17，§0 |
| D2 | 按 AI 分层协作（L0–L6），每轮写明研究层/对照变量/验收指标 | 2026-10-23，§0.1 |
| D3 | 自由度原则：写死不变量 / 知识放数据 / 判断放模型 | 2026-10-23，§0.1 |
| D4 | 指向性标准=对象锚定；三分类 V/P/G/C；L3 评测集逐篇裁决 | 意见 #20 |
| D5 | 战略：VLM 看图为主，文本换岗为语汇/定调/事实辅助 | 意见 #21 |
| D6 | 确定性闸门现在做（选 A） | 意见 #22；`l3gate` 假阳性 6.9% |
| D7 | VLM 后置：检索模块做完 + 整体测试后再议 | 意见 #22 |
| D8 | 信源定向选 B：放弃 query 级 site 定向，保留域名信任加权 | 意见 #22；site 实测无效 |

**待决（P1–P3）**：

| # | 问题 | 建议默认 |
|---|---|---|
| P1 | 文本爬取启动时机：清单确认后即后台启动 vs 图片确认后 | 清单确认后即启动（省墙钟；删车型则丢弃结果） |
| P2 | 关联分析层级：L1–L3 默认纳入、L4 逐条确认 vs 全部逐条确认 | L1–L3 默认、L4 逐条 |
| P3 | 关联 skill 形态：先文档+人工扮演 vs 等 VLM/API 就绪一起做 | 先文档+人工扮演（零成本验证） |
5. **交互层**（文本线核心能力之后）：选车确认包 + 意见 #15/#16 改进项一体建造；
6. **判向定位**（已收口）：嵌入式元数据；
7. 搁置事项：D10/D11 维持暂按推荐；data-export/import；M5 配额数值。

**主线决策（2026-10-14）**：产品负责人选择**提前启动检索模块**——R0–R6 为主线，M4 VLM 打标延后。

可并行插入的专项菜单：FR-3 特征线 / 图像背景处理 / 铭牌 OCR 与闭集匹配。

**P1 里程碑总账**：

| 里程碑 | 内容 | 测试 | 成本 |
|---|---|---|---|
| M1 导入与判重 ✅ | 批量导入 → 解码尺寸 → sha256/感知哈希 → 原图落盘 → unbound 入库 | 9/9 + 27/27 回归 | 零 |
| M2 确认工作流 ✅ | 车型管理 / 对号 / 打标确认 / 拒绝 / 裁图 / 摘要 | 11/11 三轮稳定 | 零 |
| M3 库内检索 ✅ | 组合过滤 / 聚类 / 相似检索 / 词表服务 | 11/11 + 迁移测试 | 零 |
| M4 VLM 自动打标 | 模型网关薄封装；输出约束过 schema | mock 网关单元测试 | 起产生 API 费用 |
| M5 评测集 v0 + 第二档 | 历史散图 30–50 张黄金集；FR-1.1 验收指标 | 评测报告 v0 + 基线数字 | 需素材到位 |
| M6 收尾 | ingest 批处理 CLI、成本报表、使用文档 | 端到端演练 | 零 |

等产品负责人的输入：

0. **P1–P3（见 §3.1）**：文本爬取启动时机 / 关联分析层级策略 / 关联 skill 形态；
1. 文本 LLM provider/key/预算（暂缓，等整体测试后再定）；
2. VLM 选型 + API key + 预算量级（后置，整体测试后启动）；
3. M5 前：评测集素材 30–50 张历史散图 + 设计师标注标准答案。

## 4. 待补充信息（12 条，完整表述见研讨稿 §5）

| # | 问题 | 影响 |
|---|---|---|
| 1 | 汇报会上客户最常追问/质疑什么？ | 增强页型取舍 |
| 2 | 单次项目竞品数量与品牌家族数常态？ | 成本与版式 |
| 3 | "最重要品牌"默认清单认可度与增删？ | FR-1.2 / FR-4 / 市场格局页 |
| 4 | 近似类目类比链符合内部惯例吗？ | FR-4 竞品集定义 |
| 5 | 人工描一张特征线图平均耗时？ | FR-3 收益量化 |
| 6 | 情绪版意象图来源与工时？是否提前到 P1？ | 情绪版排期 |
| 7 | 封底内容构成？ | FR-5.3 |
| 8 | "指定部位"由谁确定？与附录 B 词表关系？ | FR-2.3 |
| 9 | 现用网页 AI 是哪个？满意/不满意点？ | 竞争基线与评测对照 |
| 10 | PPT 比例与母版源文件现状？ | FR-8 / 开放问题 #4 |
| 11 | 素材发通用网页 AI 是否被客户默许？ | NFR-7 卖点 |
| 12 | 各环节工时占比拆解？ | 开放问题 #1、MVP 优先级 |

## 5. 待拍板（3 项）

1. **MVP 是否内置第一期增页**（竞品总览 / 方法与来源说明 / 封底）；
2. **设计机会点页**是否加入；
3. **简版情绪版**是否提前到 P1。

## 6. 新会话续接指引

1. **先读**：§0.0 状态快照 → `docs/module-map.md` → `docs/agent-loop-mechanisms.md` → `docs/domain-bench-runbook.md`。
2. **代码地图**：`src/equiplens/{textrun,corpus,passage,l3gate,runner,audit,domainbench,strategy,runlog}.py`；
   测试 `tests/test_{textrun,corpus,l3gate,runner,audit,domainbench}.py`。
3. **跑测试**（跳过 `test_probe`，需模型权重）：
   `for f in tests/test_{textrun,corpus,l3gate,runner,audit,domainbench,query,workflow,ingest,data_layer,m31,r0,r1}.py; do PYTHONPATH=src python $f; done`
4. **复跑检索**（必须用新 run_id，否则 runner 续跑会复用旧批次）：
   `PYTHONPATH=src python -m equiplens text-run scripts/intent-chain2.json --data-dir data-test --run-root data-test/runs --run-id <new-id>`
5. **闸门评估**：`PYTHONPATH=src python scripts/eval_l3gate.py`（结果 `data-test/evals/l3-gate-v1.md`）。
6. **误杀抽检**：`python -m equiplens audit-batch <batch_dir> --data-dir data-test`，再用 `audit-apply` 出报告。
7. **域名基准**：`python -m equiplens domain-bench scripts/domain-bench-queries.json --data-dir data-test`。
8. **已知坑**：百度间歇拦截（降级链 auto→延迟百度→Bing）；`site:` 定向默认关闭；复测必须新 run_id；A 档产出 ≠ 全部价值（163 等门户可能产 G 档）。
9. **台账**：`docs/test-log.md`（意见 #20–#23）、`data-test/runs/INDEX.md`、`data-test/evals/`。
