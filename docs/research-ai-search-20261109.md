# 开源 AI 搜索产品调研与借鉴（2026-11-09）

| 属性 | 内容 |
|---|---|
| 日期 | 2026-11-09 |
| 范围 | GitHub 为主，补 HuggingFace、论文、官方文档；只看“用 AI 获取网络内容”的搜索式产品/工具 |
| 关注 | 搜索策略设计、技术栈、图像/部件检索、编排与状态机 |
| 结论 | 可借鉴 9 条；LangGraph 只用于“检索 loop”，不做全流程；检索中应独立成模块并单独设计 loop |
| 状态 | 调研稿，供设计讨论；不含实现 |

---

## 0. 一句话结论

开源社区真正成熟的不是“更聪明的 Agent”，而是**把搜索拆成可控制的阶段**：分类/改写 → 分解/并行 → 混合召回 → 重排 → 压缩/引用。我们的项目应当借这些**阶段策略**，而不是借一个“全流程 Agent 框架”。LangGraph 适合做检索 loop 的执行引擎；任务单、策略库、证据库、检索后核验仍是普通 Python 模块。

---

## 1. 调研范围与方法

| 轮次 | 看什么 | 代表项目 |
|---|---|---|
| 1 | 答案引擎 / 搜索式 AI 整机 | Perplexica（现 Vane）、Khoj |
| 2 | 深度研究 Agent | Open Deep Research、GPT Researcher、STORM、MindSearch |
| 3 | 获取层 / 元搜索 | SearXNG、Firecrawl、Tavily、Searqon |
| 4 | 图像 / 部件检索 | Marqo、clip-retrieval、VISE、Pailitao-VL、CVPR 2026 工业件检索、Partclip |
| 5 | 编排与状态机 | LangGraph、Apache Burr、Temporal |

---

## 2. 五类项目

### 2.1 答案引擎：分类 → 检索 → 重排 → 引用

**Vane（原 Perplexica）**：

- 组件：UI + agents/chains + **SearXNG** + LLM + **embedding 重排**；
- 流程：先做一次**分类/改写**（要不要研究、要不要 widget、把问题改写成独立查询）→ 研究 → 生成答案并带引用；
- `optimizationMode` 在 `speed / balanced / quality` 之间权衡；
- 图像/视频是独立端点：先用模型生成聚焦查询，再去搜索后端取结果。

**Khoj**：

- 本地文档 + 网页搜索；
- **bi-encoder 召回 + cross-encoder 重排**；
- 不是多 Agent，而是“检索 + 重排”的工程化产品。

**对我们的意义**：产品级最小形态就是“分类/改写 → 检索 → 重排 → 带证据输出”，不需要一上来就多 Agent。

### 2.2 深度研究 Agent：拆问题、并行研究、压缩、成文

**Open Deep Research（LangGraph 官方参考）**：

```
clarify_with_user → write_research_brief
  → supervisor ⇄ supervisor_tools
       └→ researcher ⇄ researcher_tools → compress_research
  → final_report_generation
```

- Supervisor 把 brief 拆成研究单元，用 `ConductResearch` 并行派给 researcher；
- 有 `max_concurrent_research_units`、`max_researcher_iterations`、`max_react_tool_calls` 等预算；
- Researcher 用搜索工具（默认 Tavily，也支持 MCP）反复搜，最后压缩成 notes；
- `think_tool` 做显式反思，`ResearchComplete` 做停止信号；
- 不同阶段用不同模型（summarization / research / compression / final report），控制成本。

**GPT Researcher**：

- Planner 生成一组研究问题；
- 每个问题交给 crawler agent 抓网页、总结、保留来源；
- 最后过滤聚合，生成 2k+ 字报告；单任务约 20+ 来源、3 分钟、~$0.1。

**STORM**：

- 先发现主题的不同视角（不同作者/角色）；
- 模拟“不同视角的写作者向专家提问”，问题必须落在可信来源上；
- 用收集到的信息生成 outline。

**MindSearch**：

- WebPlanner 把用户问题拆成原子子问题，作为图节点；
- 根据 WebSearcher 的返回**逐步扩展图**；
- WebSearcher 对每个子问题做分层检索；
- 3 分钟可覆盖 300+ 网页。

### 2.3 获取层：把“抓”变成“取”

| 项目 | 定位 | 关键设计 | 对我们的风险 |
|---|---|---|---|
| **SearXNG** | 元搜索 | 70+ 引擎适配器、分类/分页/时间范围、JSON API；不自己爬全网 | 底层仍是 Bing/Google 等，中文工程机械长尾覆盖未知 |
| **Firecrawl** | 网页 → LLM-ready Markdown | JS 渲染、反爬、代理、`/scrape` `/crawl` `/map` `/search` `/extract` | 解决“页面拿不到”，不解决“型号身份” |
| **Tavily** | 为 Agent 设计的搜索/提取 API | 返回排序结果、摘要、URL；Open Deep Research 默认用它 | 中文工程机械覆盖/成本要实测 |
| **Searqon** | 自托管“搜索 + 抓取 + 清洗”层 | Go 单二进制；SearXNG/DuckDuckGo/Wikipedia/arXiv 聚合；4 层反爬（HTTP → TLS 指纹 → 无头浏览器 → 住宅代理）；BM25 + SQLite FTS5 | 源里没有百度/360，中文图/文可能不如国内通道 |

### 2.4 图像 / 部件检索

| 项目/论文 | 做了什么 | 对我们的价值 |
|---|---|---|
| **VISE（Oxford VGG）** | 用**图像区域**作为查询，检索大图库；区域级视觉搜索 | 最接近“在主图上找部件”的检索形态 |
| **clip-retrieval（LAION）** | CLIP embedding + FAISS，支持文本/图像/embedding 查询，可扩到亿级 | 图库检索的工程底座；但 CLIP 粒度粗 |
| **Marqo** | 多模态 embedding + 查询理解 + 重排；支持反向图搜/图像检测 | 查询理解 + 多模态召回 + 重排可参考；电商个性化不适用 |
| **CVPR 2026 工业件检索** | 17k 工业备件；比较 DINOv2 / DINOv3 / SigLIP2；patch token 比 CLS 更适合细粒度；冻结编码器 + 轻量头 | 部件级身份/可见性要用 patch-token 模型 + 训练头，不是零样本 CLIP |
| **Partclip（A*STAR）** | 实测 CLIP 直接用于机械零件检索效果不佳；用知识蒸馏到 EfficientNet B1 | 现有 CLIP 门卫只能判“是不是工程车”，不能判“是不是这个部件/这台车” |
| **Pailitao-VL（阿里）** | 工业多模态检索；embedding 从对比学习转为 ID 识别；listwise 重排 | “绝对 ID 识别 + 列表式重排”是部件级检索的方向 |

### 2.5 编排

| 维度 | LangGraph | Apache Burr | Temporal |
|---|---|---|---|
| 核心抽象 | 状态图 + 节点/边 + checkpointer | 显式状态机 + action + transition | Workflow + Activity（持久化执行） |
| 检查点/恢复 | ✅ checkpointer、thread、time travel | ✅ 持久化、resume、replay | ✅ 最强：崩溃恢复、重试、长任务 |
| 人工介入 | ✅ interrupt | ✅ halt / human-in-loop | ✅ signal/update |
| 可观测 | LangSmith / Studio | 自带 UI、trace | Temporal UI / event history |
| 适合 | 多 Agent、分支、流式 | 确定性状态机、审计/回放 | 云上多租户、长任务、分布式 |
| 代价 | 抽象重、生态绑定 | 生态较小、Apache incubating | 基础设施重（server/worker） |

---

## 3. 可复用的搜索策略模式

| # | 模式 | 来源 | 怎么用在 EquipLens |
|---|---|---|---|
| 1 | **查询分类 + 改写** | Vane、Marqo | 把“沙漠牵引车+部件”改写成独立检索意图；区分 exact/environment/platform |
| 2 | **多视角提问** | STORM | 对每个部件生成“设计师/维修工/沙漠车队”三种视角的机制问题，变成查询锚点 |
| 3 | **动态子问题图** | MindSearch | 把“12 个槽 × 6 个部件”拆成子问题，按返回逐步扩展/收缩 |
| 4 | **Supervisor + Researcher 并行** | Open Deep Research | 按部件/目标并行研究，受 `max_concurrent` 限制 |
| 5 | **Planner + Executor + 并行问题** | GPT Researcher | 任务单生成研究问题，执行器逐题检索 |
| 6 | **混合召回 + 重排** | Khoj、Marqo、Vane | 文本锚点 + 图像召回 + cross-encoder/多模态重排 |
| 7 | **元搜索/源路由** | SearXNG、Searqon | 按源分层，失败换源；中文源另接 |
| 8 | **预算/停止/引用** | Open Deep Research、Vane | 迭代上限、并发上限、停止信号、每条证据带来源 |

---

## 4. 技术栈观察

| 项目 | 栈 | 备注 |
|---|---|---|
| Vane / Perplexica | Next.js/Node + SearXNG + LLM + embeddings | 轻量整机，不是多 Agent |
| Open Deep Research | Python + LangGraph + LangChain + Tavily/MCP | 生产级 LangGraph 参考 |
| GPT Researcher | Python + planner/executor + crawler | 多 Agent 框架可插拔 |
| STORM / MindSearch | Python + LLM + 检索 | 研究型代码，适合借策略 |
| Khoj | Python + bi-encoder/cross-encoder | 本地搜索 + 重排 |
| SearXNG | Python 元搜索 | 引擎适配器模式 |
| Firecrawl / Tavily / Searqon | 服务/API/单二进制 | 获取层外包 |
| Marqo | 多模态向量检索 | 查询理解 + 重排 |
| clip-retrieval / VISE | CLIP/FAISS、区域搜索 | 图像检索底座 |
| LangGraph / Burr / Temporal | 编排 | 三种不同“持久化”路线 |

---

## 5. LangGraph 评估

### 5.1 专家主张

| 主张 | 评估 |
|---|---|
| 状态图/条件边适合“分类 → 分通道 → 核验 → 补充检索” | **对**；Open Deep Research 就是这种结构 |
| checkpoints 支持有界纠错循环 | **对**，但不是 LangGraph 独有；Burr/Temporal 也有 |
| LangGraph token 效率最高 | **未证实**，且不是选型关键；成本主要在模型调用与抓取 |
| AutoGen 已进维护模式 | 方向可信，但不是决定因素；我们不需要 AutoGen |
| CrewAI 不适合 | **同意**；角色团队隐喻不适合确定性证据管线 |
| 先用 Dify/n8n 验证再迁 LangGraph | **不同意**；CLI + schema + 测试已是原型，再引入可视化 DSL 是第二套运行时 |
| 私有化部署 | **同意**；LangGraph 可自托管，Burr/Temporal 也可 |

### 5.2 结论

- **LangGraph 适合做“检索 loop 的执行引擎”，不适合做“整个产品的架构”。**
- 产品架构应为：`任务单/证据规格`（数据）+ `策略库`（规则）+ `执行引擎`（状态机/检查点/事件账本）；引擎可替换。
- 如果现在就要选一个框架：**LangGraph** 做检索 loop；若更看重“显式状态机 + 审计/回放 + 低抽象”，**Burr** 更贴合；若最终是云上多租户/长任务，**Temporal** 更稳。
- 不要用 LangGraph 定义产品；用 LangGraph 实现检索 loop。

---

## 6. 我们要借鉴的点（含第二推荐）

> 每条都标注：**阶段**（检索前 / 检索中 / 检索后）、**机制**、**必要性（对比现有）**、**首推**、**第二推荐**。

### B1. 任务单 → 研究单元（brief → research units）

- **来源**：Open Deep Research（brief → supervisor → research units）。
- **阶段**：检索前（定义单元）+ 检索中（执行单元）。
- **机制**：brief 不只写“要什么证据”，还拆成若干 `research_units`；每个单元有目标、覆盖部件、预算、停止条件；检索按单元并行执行，结果回写。
- **必要性（对比现有）**：现在的任务单只有 `targets` 和层级，没有“执行单元”；检索中要么按车型逐个跑，要么临时拆，导致①重复抓取 ②预算无法按单元控制 ③失败无法定位到单元。
- **首推**：任务单增加 `research_units[]`：`unit_id / parts / scope / quota / budget / stop / priority`；检索按 unit 并行，unit 内再按 target 执行。
- **第二推荐**：先不做 unit，按 target 顺序执行（简单，但并行度和可观测性差）。

### B2. 多视角机制提问（multi-perspective questioning）

- **来源**：STORM（perspective discovery + simulated conversations）。
- **阶段**：检索前（生成查询锚点）+ 检索中（查询展开）。
- **机制**：对每个部件，从不同角色/视角生成问题（设计师看线条、维修工看可拆装、车队看沙尘/防滑），再把问题变成检索锚点；不是让模型自由写一段分析。
- **必要性（对比现有）**：现在 `build_plan` 的查询来自类目词表 + 设计语汇，缺“环境机制”的锚点；例如“沙石冲击、防滑、离地高”这些机制没有稳定进入查询，导致图片检索被标题词带偏。
- **首推**：任务单的 `mechanism` 直接生成 2–3 个机制问题，作为 `query_anchors`；检索只做改写，不做自由发挥。
- **第二推荐**：只用 `mechanism` 词表拼查询（更便宜，但视角单一）。

### B3. 并行有界研究单元（bounded parallel research）

- **来源**：Open Deep Research（supervisor 并行 + max concurrent/iterations）、GPT Researcher（并行 crawler）。
- **阶段**：检索中。
- **机制**：supervisor 一次派 N 个研究单元，限制并发；每个单元有最大迭代/工具调用；达到上限就压缩/停止。
- **必要性（对比现有）**：`runner.py` 是顺序单意图，有重试但无“按单元并行 + 单元级预算”；12 个槽 × 6 个部件会非常慢，且失败无法隔离。
- **首推**：`asyncio` 任务池 + 每单元状态；`max_concurrent=3–5`；单元级 `max_queries/max_rounds`；失败只影响该单元。
- **第二推荐**：顺序执行 + 优先级队列（实现简单，但慢，适合先验证策略）。

### B4. 混合召回 + 重排（hybrid recall + rerank）

- **来源**：Khoj（bi-encoder + cross-encoder）、Marqo（多模态 + 重排）、Vane（embedding 重排）。
- **阶段**：检索中（候选排序）+ 检索后（核验）。
- **机制**：先用宽松召回拿候选（文本/图像/元数据），再用 cross-encoder 或多模态模型重排；规则只做护栏。
- **必要性（对比现有）**：`_relevant()` 是标题关键词规则，标题加“工程车”后缀相关率从 10/12 掉到 2/12；`gate.py` 的 CLIP 只判“是不是工程车”，不判“是不是这台车/这个部件”。没有重排，候选质量完全取决于标题。
- **首推**：文本侧加 cross-encoder 重排；图像侧加多模态/部件级重排；规则保留为硬护栏（构型、品牌、非车词）。
- **第二推荐**：只做规则 + 人工复核（当前），或只做 VLM 逐对判断（贵、慢）。

### B5. 源路由 + 健康度/熔断（source routing + health）

- **来源**：SearXNG（引擎适配器）、Searqon（4 层反爬 + 多源聚合）。
- **阶段**：检索中。
- **机制**：把“源”当成可插拔适配器；每个源有健康度、失败计数、熔断、缓存；按任务/类目路由，失败换源，不把“被拦”当成“没结果”。
- **必要性（对比现有）**：现在 360/百度/Bing 是并列尝试，百度 `antiFlag`、Bing 相关 0/12，但系统仍当“尝试过了”；没有健康度、熔断、查询缓存；单点故障直接拖垮整批。
- **首推**：`source_registry` + 健康度/熔断 + 24h 查询缓存 + 失败分账（blocked/empty/ok）。
- **第二推荐**：付费 API（Tavily/Exa/Serper）作主通道，自建通道作备选；成本换稳定性。

### B6. 状态机 + 检查点 + 事件账本（state machine + checkpoints + event log）

- **来源**：LangGraph（checkpointer）、Burr（显式状态机 + UI + replay）、Temporal（durable execution）。
- **阶段**：检索中（执行）+ 跨阶段（审计/回放）。
- **机制**：把检索写成显式状态机；每次状态转移落盘；事件日志记录输入/输出/决策；崩溃可续；已完成的步骤幂等跳过。
- **必要性（对比现有）**：`runner.py` 只有文本检索的状态 JSON；图片/核验/填槽没有统一的 loop 状态；一旦中断，无法知道“这个 target 走到哪、花了多少预算、为什么降级”。
- **首推**：薄状态机 + `state.json` + `events.jsonl` + 幂等步骤 + 预算；不引入框架。
- **第二推荐**：LangGraph（要多 Agent/并行/流式时）或 Burr（要显式状态机 + 自带 UI/replay 时）；云上多租户再考虑 Temporal。

### B7. 区域/部件级视觉检索（region/part-level visual retrieval）

- **来源**：VISE（区域查询）、CVPR 2026 工业件检索（DINOv2/v3、SigLIP2、patch token）、Partclip（CLIP 直接用于机械件效果差）、Pailitao-VL（ID 识别 + listwise 重排）。
- **阶段**：检索中（图像召回）+ 检索后（身份/可见性核验）。
- **机制**：不是“整图相似”，而是“区域/部件相似”：裁图或区域查询 → patch-token 编码 → 轻量训练头/重排 → 判“是不是这个部件、这台车”。
- **必要性（对比现有）**：现在的 `gate` 是零样本 CLIP，只能判“是不是一台工程车”；型号身份靠标题 + 人工；`region_match` 未实装。部件级检索是当前最大技术缺口。
- **首推**：先用 VISE 式区域查询 + SigLIP2/DINOv3 patch token 做小实验（50–100 张标注），再决定是否训练轻量头。
- **第二推荐**：VLM 逐对/列表判断（更贵、更慢，但不需要训练）；或继续人工复核（当前）。

### B8. 证据库 + 回写（evidence library + write-back）

- **来源**：Open Deep Research（notes/compression）、我们自己的 A/B 结论（证据基础设施 > skill）。
- **阶段**：检索后（沉淀）+ 下一次检索前（优先召回）。
- **机制**：把核验通过的“图 + 部件 + 型号 + 身份等级 + 分数”写成记录；下次先查库，不足才外检；检索结果回写。
- **必要性（对比现有）**：文本证据索引只有 24 车型/654 篇/85 条；图片证据库为零；每次重检，质量不累积。A/B 已证明证据基础设施比 skill 更能提升结果。
- **首推**：`image_evidence` 表 + 查库优先 + 人工录 50 条起步。
- **第二推荐**：先做“已验证 URL/资产缓存”（更轻，但不可复用部件级信息）。

### B9. 预算/停止/引用（budget / stop / citation）

- **来源**：Open Deep Research（max concurrent/iterations、ResearchComplete）、Vane（引用）。
- **阶段**：检索前（定义预算）+ 检索中（停止）+ 检索后（引用）。
- **机制**：预算不是“每层找 N 台”，而是并发/迭代/查询上限；停止由“槽满 / 层耗尽 / 收益率低 / 预算到顶”决定；每条证据带来源。
- **必要性（对比现有）**：现在 `runner` 有重试但缺“收益率停止”；任务单上一轮还在用“每层配额”，已删除；证据引用不完整。
- **首推**：收益率停止规则（连续 K 次无新增/查询阶梯用完/预算到顶）+ 证据来源字段。
- **第二推荐**：固定最大轮次（简单，但可能过早停/过晚停）。

### 不借鉴清单

| 内容 | 原因 |
|---|---|
| 检索前追问用户（clarify_with_user） | 用户明确不要；默认推断 + 事后纠正 |
| 生成一篇长报告（Open Deep Research / GPT Researcher） | 我们的终点是页槽 + 证据单，不是文章 |
| 自由多 Agent 对话（AutoGen/CrewAI） | 流程是确定性证据管线，不需要角色自由协商 |
| Dify/n8n 作原型 | CLI + schema + 测试已是原型；再加一套 DSL 是第二套运行时 |
| 全流程绑在 LangGraph | 任务单/策略库/证据库/UI 不应依赖框架 |
| 先上向量库（Milvus/Qdrant） | 当前 629 张图/85 条证据，SQLite + dHash 足够；到 10^4–10^5 再谈 |

---

## 7. 技术栈怎么表述（LangGraph 只用于检索阶段）

### 7.1 可以只用于检索阶段

可以。LangGraph 是库，不是“必须全流程”的平台。你可以：

- 检索前：普通 Python（意图、任务单、策略选择）；
- 检索中：一个 LangGraph 子图（`RetrievalEngine`），负责状态、检查点、并行、重试；
- 检索后：普通 Python（核验、证据库、分析、排版）；
- API/CLI/UI：FastAPI / CLI / React，调用 `RetrievalEngine.run(brief, strategy)`。

### 7.2 怎么描述整体技术栈

推荐说法：

> **Python + FastAPI/CLI + LangGraph（仅检索 loop）+ SQLite/Postgres + 自建策略库/证据库 + React 前端。**

不要说的是：

> “我们是一个 LangGraph 项目 / 全流程都在 LangGraph 上。”

因为：

- “全流程在 LangGraph”的项目（如 Open Deep Research）是 **agent app**：输入问题 → 图里跑完研究 → 输出报告；
- 我们是 **workflow app + agentic retrieval subgraph**：任务单/策略/证据/排版是普通模块，只有检索 loop 在 LangGraph 里。

### 7.3 拼接形式的边界

| 层 | 是否在 LangGraph | 说明 |
|---|---|---|
| 任务单/证据规格 | ❌ | 纯数据 + Python 规则；可单测 |
| 策略库（P/E） | ❌ | 规则/数据；被 engine 调用 |
| 检索 loop | ✅ | 状态机、检查点、并行、重试 |
| 核验/证据库 | ❌ | 普通 Python + SQLite |
| 分析/排版 | ❌ | 分析模块 + 报告脚本 |
| UI/API | ❌ | FastAPI + React |

这样既拿到 LangGraph 的检查点/并行/流式，又不把产品绑死在框架上。

---

## 8. 检索中是不是单独模块？要不要单独设计 loop？

### 8.1 是单独模块

建议独立为 `retrieval/`（或 `retrieval_engine/`），理由：

1. **生命周期不同**：检索是长任务、可中断、可续跑；任务单/核验是短函数。
2. **失败模式不同**：blocked / empty / wrong identity / wrong view / low resolution，需要独立错误分类。
3. **测试方式不同**：检索需要 fixture 通道、离线回放、覆盖率指标；任务单是纯函数单测。
4. **适配器多**：SearXNG、360、百度、Tavily、图片搜索、库内检索，都应可插拔。
5. **与 UI 解耦**：UI 只订阅事件/读结果，不直接调通道。

模块内容：

```
retrieval/
  engine.py        # 状态机 + loop + 检查点
  state.py         # BriefState / UnitState / CandidateState
  events.py        # events.jsonl
  strategies/      # query expansion, source routing, verification
  adapters/        # searxng, 360, baidu, tavily, image_search, library
  policies/        # budget, stop, degrade, cross
  verify/          # identity, visibility, origin
```

### 8.2 是单独的 loop

是。检索中不是“一次函数调用”，而是一个有界 loop：

```
BRIEF_READY
  → LIBRARY_SEARCH
  → GAP_CHECK
  → EXTERNAL_DISCOVER
  → FETCH
  → VERIFY
  → FILL
  → (DEGRADE | RETRY | DONE | FAILED)
  → WRITEBACK
```

每个状态：

- 输入：`state.json`（brief、unit、候选、覆盖、预算、决策）；
- 输出：新状态 + `events.jsonl`；
- **检查点**：每次转移后落盘；
- **幂等**：已完成的不重复；
- **有界**：`max_rounds / max_queries / max_models`；
- **可回放**：同一 brief + 同一批 fixture 能复现。

候选级还有子状态：

```
candidate → querying → fetched → gated → verified → accepted / rejected / retry
```

### 8.3 为什么不能把 loop 藏进策略

- 策略是“怎么做”（查询阶梯、源路由、验收）；loop 是“现在走到哪、下一步走哪条边、预算还剩多少”。
- 把 loop 藏进策略，会导致：状态不可见、无法续跑、无法审计、无法并行。
- 所以：**策略可插拔，loop 独立且显式**。

---

## 9. 来源

- [Vane（原 Perplexica）](https://github.com/ItzCrazyKns/Vane)、[架构](https://github.com/ItzCrazyKns/Vane/blob/master/docs/architecture/README.md)、[工作流程](https://github.com/ItzCrazyKns/Vane/blob/master/docs/architecture/WORKING.md)
- [Open Deep Research](https://github.com/langchain-ai/open_deep_research)、[主图实现](https://github.com/langchain-ai/open_deep_research/blob/main/src/open_deep_research/deep_researcher.py)
- [GPT Researcher](https://github.com/assafelovic/gpt-researcher)、[架构](https://docs.gptr.dev/docs/gpt-researcher/getting-started/introduction)
- [STORM](https://arxiv.org/abs/2402.14207)、[MindSearch](https://arxiv.org/abs/2407.20183)
- [SearXNG](https://github.com/searxng/searxng)、[引擎文档](https://docs.searxng.org/dev/engines/engine_overview.html)
- [Firecrawl](https://github.com/firecrawl/firecrawl)、[Tavily](https://tavily.com/)、[Searqon](https://github.com/Sooriya04/Searqon)
- [Khoj](https://github.com/khoj-ai/khoj)、[搜索实现](https://docs.khoj.dev/features/search/)
- [Marqo](https://github.com/marqo-ai/marqo)、[六层栈](https://docs.marqo.ai/home/why-marqo-wins/)
- [clip-retrieval](https://github.com/rom1504/clip-retrieval)、[VISE](https://github.com/Digital-Scholarship-Oxford/vise)
- [CVPR 2026 工业件检索](https://www.openaccess.thecvf.com/content/CVPR2026W/FGVC13/html/Liu_Efficient_Fine-grained_Image_Retrieval_with_Vision_Foundation_Models_for_Industrial_CVPRW_2026_paper.html)、[Partclip](https://oar.a-star.edu.sg/communities-collections/articles/20851)、[Pailitao-VL](https://arxiv.org/abs/2602.13704)
- [LangGraph](https://github.com/langchain-ai/langgraph)、[checkpointers](https://docs.langchain.com/oss/javascript/langgraph/checkpointers)
- [Apache Burr](https://github.com/apache/burr)、[Burr 文档](https://burr.apache.org/)
- [Temporal](https://temporal.io/)、[OpenAI Agents SDK + Temporal](https://temporal.io/blog/announcing-openai-agents-sdk-integration)
- HuggingFace：[sentence-transformers 图像搜索示例](https://github.com/huggingface/sentence-transformers/tree/main/examples/sentence_transformer/applications/image-search)、[CLIP image search Space](https://huggingface.co/spaces/marcelcastrobr/CLIP-image-search)
