# EquipLens-AI

> **新会话 / 换机接续**：先读 [docs/HANDOFF.md](docs/HANDOFF.md) §0.1–§0.5，再看
> [docs/CURRENT-ARCHITECTURE.md](docs/CURRENT-ARCHITECTURE.md)（当前框架）
> 与 [docs/killed-strategies.md](docs/killed-strategies.md)（已毙策略，别重复提）。
> 开工前请先提供 `DEEPSEEK_API_KEY`（写入 `~/.equiplens/deepseek.env`，仓库不含 key），
> 然后跑 `PYTHONPATH=src python scripts/check_env.py` 自检。

> AI 驱动的工程车辆外观部件设计前期分析报告生成工具 —— 让 AI 承担资料检索、图像分析与报告初稿制作，设计师专注于判断与创意。

## 1. 项目定位

EquipLens-AI 是一款面向工程机械（挖掘机、装载机、起重机、矿用车辆等）**外观部件设计前期分析**的 AI 辅助工具。它利用大模型的**多模态图像识别、知识检索（RAG）与工具调用**能力，协助设计团队在项目启动阶段快速产出**可编辑的前期分析报告（PPT / PDF）**，将传统需要数天的资料整理与报告制作压缩到小时级。

### 解决的问题

前期分析报告（竞品造型分析、品牌基因研究、趋势研究、法规约束梳理等）目前高度依赖人工：

- 竞品图片收集、分类、特征标注耗时长；
- 多源资料（设计规范、法规标准、历史项目报告）散落各处，检索困难；
- 报告排版、图表制作等格式化工作占用大量创意时间；
- 分析质量依赖个人经验，难以沉淀为可复用的组织资产。

### 目标用户

- 工程机械企业的工业设计 / 造型团队（主要用户）
- CMF 设计师、产品定义工程师
- 设计管理与前期调研人员

## 2. 核心 AI 能力

| 能力 | 在本工具中的用途 |
|---|---|
| 多模态图像识别（VLM） | 竞品图片特征解析：造型语言、覆盖件分块与分缝、灯具 / 格栅 / Logo 区域布局、CMF、风格要素提取与横向对比 |
| 检索增强生成（RAG） | 检索品牌设计规范、法规标准（ISO / GB / EN 等）、历史项目报告、行业趋势资料，并支持引用溯源 |
| 工具调用（Function Calling / MCP） | 联网搜索、图片检索、图表生成、文档解析、PPT / PDF 渲染等 |
| Agent 编排 | 任务规划 → 检索 → 分析 → 撰写 → 渲染报告的多步工作流，关键环节支持人工确认（Human-in-the-loop） |

## 3. 典型工作流

```mermaid
flowchart LR
    A[输入: 分析主题<br>+ 竞品图片 / 资料] --> B[Agent 规划报告大纲]
    B --> C[图像特征分析<br>+ 知识库 / 联网检索]
    C --> D[分章节生成图文内容]
    D --> E[渲染可编辑 PPT / PDF]
    E --> F[用户审阅与定向修改]
    F -->|反馈| D
```

1. **输入**：用户给出分析主题（如"某竞品挖掘机覆盖件造型分析"），上传图片素材或让工具联网收集；
2. **分析**：VLM 解析图像造型特征，RAG 检索品牌规范、法规与历史资料；
3. **撰写**：Agent 按大纲逐章生成图文内容，素材与结论均可溯源；
4. **产出**：渲染为**可编辑 PPT（优先）**或 PDF，文字、图表、版式保持可修改；
5. **迭代**：用户针对章节或素材给出反馈，AI 定向修改后重新渲染。

## 4. 功能模块规划（初步）

| 模块 | 内容 | 优先级 |
|---|---|---|
| M1 图像分析 | 图片上传 / 批量导入、VLM 特征提取、结构化标注（形态语言、分块分缝、特征线、CMF） | P0 |
| M2 素材检索与整理 | 散图自动归类整理（分类 / 去重 / 质检 / 聚类）、联网竞品检索、素材池管理（独立 Agent） | P0（散图整理）/ P1（联网检索） |
| M3 报告生成 | 大纲规划、章节撰写、图表生成、可编辑 PPT / PDF 渲染 | P0 |
| M4 工作台前端 | 项目管理、素材库、报告预览与迭代编辑、导出 | P1 |
| M5 知识库增强（RAG） | 品牌规范 / 法规 / 历史项目知识库接入、引用溯源 | P2 |

## 5. 当前技术栈（2026-11-13，与代码一致）

| 层 | 实际实现 |
|---|---|
| 语言/运行时 | Python **3.11**（`PYTHONPATH=src`） |
| 数据 | **SQLite + 文件系统**（`data-test/equiplens.db`、`runs/`、`evidence.db`）；无向量库 |
| 图像门卫 | **UForm3**（`unum-cloud/uform3-image-text-english-small`，ONNX/CPU 零样本）+ 确定性预筛 |
| 检索 | **360 图片接口为主**，百度/Bing 兜底；`requests` + 规则护栏；无 Playwright 依赖 |
| 规划/分析 | DeepSeek API（Chat + Search + Fetch）；key 在 `~/.equiplens/deepseek.env` |
| 报告/审核 | 静态 HTML 审核页 + `python-pptx` 导出 |
| 前端 | 目前只有静态高保真（`docs/ui-hifi-dark/`）；**React 工程尚未创建** |
| 编排 | 确定性状态机（`retrieval_engine/`）；LangGraph 仅做 feedback spike 计划 |

> 早期设想的 FastAPI / pgvector / Milvus / 自研 Agent 编排**均未采用**，以本节为准。

## 6. 开发范式与规范（原则）

遵循当前 AI 产品开发的主流范式，具体规范文档将随讨论逐步建立并归档至 `docs/`：

- **Spec 驱动开发**：先写需求、接口与数据规格说明，评审后再实现；
- **评测优先（Eval-first）**：为图像分析与内容生成建立评测集与评分标准（LLM-as-judge + 人工抽检），Prompt 或流程变更必须通过评测；
- **Prompt 即资产**：Prompt 版本化管理，与代码同仓同评审；
- **全链路可观测**：每次生成的检索命中、模型调用、耗时与成本可追溯（Tracing）；
- **人在回路**：大纲、素材引用、成稿等关键环节设置确认点，AI 产出必须可溯源；
- **数据合规**：明确企业资料与竞品图片的存储、使用与展示边界。

## 7. 路线图（2026-11-13 现状）

| 阶段 | 目标 | 状态 |
|---|---|---|
| 检索 v1 收敛 | 360 + gate v4 + 身份核验 + **N 主 + 4 备**（N=用户输入）+ 审核页 | ✅ 收口；填槽修复后待 5 case 复跑 |
| 第一次用户交付 | beta + 人审，收集真实反馈 | 🔄 准备中 |
| 意图识别（feedback router + session） | 反馈 → 意图 → 回溯节点 | 待开工 |
| 分析模块整体测试 | 前置预分析 → 分析模块的信息传递 + 价值 A/B | 待开工 |
| 知识库 | 人审通过的分析/证据沉淀 + 库内优先召回 | 待设计 |
| LangGraph | 只做 feedback/session spike，不重写核心 | 待 spike |
| 后端 + 前端 | 事件流 → API；S0–S3 接真实数据 | 未开始 |

> 扩源（Query/Source/Platform）已收口，不再排期；三证②③ 已归档/毙。见 `docs/killed-strategies.md`。

## 8. 仓库结构（实际）

```
EquipLens-AI/
├── README.md
├── docs/              # 需求/架构/评测/交接；CURRENT-ARCHITECTURE.md 是框架单一事实源
├── src/equiplens/     # 生产代码：检索 loop、门卫、规划、分析、数据层
│   └── retrieval_engine/   # 状态机 + 网页适配 + 证据落库
├── scripts/           # 生产入口（build_brief / plan_candidates / rank_plan / render_fetch_audit / run_ledger）+ 实验脚本
├── skills/            # task-brief（brief 生成方法）
├── schemas/           # brief / state / event 契约
├── data/              # 运维配置；legacy/ 为静默词表（默认不加载）
├── tests/             # check() 脚本（不是 pytest）
└── data-test/         # runs/ 台账、evals/ 评测、fixtures/
```

> 早期规划的 `backend/`、`frontend/`、`prompts/`、`evals/`、`samples/` 目录**不存在**。
