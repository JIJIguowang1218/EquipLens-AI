# 执行 Loop 机制借鉴备忘（2026-10-30）

目的：检索/采集 loop 出问题（SERP 被拦、锚点误杀、批次欠采样）时能自动降级推进，
而不是停下等人。原则：**只借机制，不搬全家桶**；我们的控制流是固定 workflow，
不需要通用 agent 的多智能体、工具自动发现、自由对话能力。

## 1. 主流框架各解决什么

| 框架 | 与本项目相关的机制 | 参考 |
|---|---|---|
| Temporal | Activity 重试策略（初始间隔/退避系数/最大尝试/不可重试错误）、Heartbeat 断点续跑、幂等要求、事件历史 | https://docs.temporal.io/activities |
| Crawlee | `max_request_retries`、`max_session_rotations`、`failed_request_handler`（重试耗尽后的兜底）、`error_handler` 里设 `no_retry`（区分可重试/不可重试）、SessionPool 按 403/429 退役会话 | https://crawlee.dev/python/docs/guides/error-handling |
| LangGraph | StateGraph 节点+条件边、节点级 `retry_policy`、checkpointer 断点、`interrupt` 人工介入 | 官方文档与社区实践（retry nodes / fallback paths） |
| OpenAI Agents SDK | 有界 loop（max_turns）、handoffs、guardrails（输入/输出护栏） | Agents SDK 文档 |
| Prefect / Dagster | 任务级 retry/backoff、flow 编排、状态持久化 | Prefect 文档 |

结论：我们缺的是 **Temporal 的语义 + Crawlee 的降级细节 + LangGraph 的条件边**，
不需要任何框架运行时。

## 2. 借什么 / 不借什么

| 需要的机制 | 借鉴来源 | 我们的实现 |
|---|---|---|
| 任务单元 + 验收契约 | Temporal Activity 粒度 | `TaskUnit(category, query_group, contract)`：最少落盘数、SERP 拦截率上限、候选段下限 |
| 重试策略 | Temporal RetryPolicy | 数据类：max_attempts / 初始间隔 / 退避系数 / 不可重试错误集合；用 tenacity 或 30 行自研 |
| 错误分类 | Crawlee `no_retry` | robots_denied/too_short 不重试；fetch_error/被拦可重试 |
| 降级阶梯 | Crawlee `failed_request_handler` + LangGraph 条件边 | 通道链 baidu→bing→站内→白名单；锚点链 全名→分词→放宽→类目兜底；每级成功即停 |
| 断点续跑 | Temporal Heartbeat + LangGraph checkpointer | 单元状态机落盘（pending/running/ok/degraded/failed）+ 原子写；重启按状态续跑 |
| 幂等 | Temporal 幂等要求 + Crawlee unique_key | 单元键=类目+查询组+轮次；结果按 URL 去重，已存在跳过 |
| 有界循环 + 有限升级 | OpenAI Agents SDK max_turns + LangGraph interrupt | 每单元最多 2 轮；全部通道失败才停；结构性失败降级并写 blockers，不阻塞其他单元 |
| 可观测 | Temporal event history | 复用 events.jsonl：记录每次 attempt/降级原因/耗时 |

**明确不借**：Temporal 服务端、LangGraph/LangChain 依赖、AutoGen 群聊、
多智能体 handoff、动态工具发现、自由 ReAct 对话——我们的判断点只有
"换哪个查询/哪个源/要不要停"，固定 workflow 足够。

## 3. 落地形态（等 1、2 项完成后实施）

- 新模块 `src/equiplens/runner.py`（约 150 行）：
  - `RetryPolicy`、`StepResult`、`FallbackChain`、`UnitStateStore`、`run_units()`
- `textrun` 的 execute 阶段改为按单元执行，`strategy.assess` 扩展为
  "单元级验收 → 降级重规划"，`replan` 的 scope 从"换查询"扩为
  "换通道/换源/换查询"。
- 依赖：建议只加 `tenacity`（纯 Python、成熟、小）；其余自研。
- 验收：用本轮 T18-roster 的轻型吊车批做回归——模拟"首批被拦"，loop 应
  自动降级补爬并在报告中标 `degraded`，全程不停。

## 4. 与当前先做的 1、2 项的关系

1、2 项（relevant_terms 按查询组配置、配置行修复、查询分层与信源定向）
属于**单元定义与计划层**——runner 的 `TaskUnit` 需要"查询组+信息类型+信源"
这些元数据，所以先做 1、2 正好为 runner 铺路，不冲突。

## 5. 参考项目：claude-seo（GitHub, MIT）

调研对象：AgriciDaniel/claude-seo（26 sub-skills + 19 sub-agents 的 Claude Code SEO 审计插件）。
它做的是"给定站点做 SEO 审计"，不是开放网络检索，所以**检索阶段没有可直接照搬的策略**；
可借的是**工程化包装与输出形态**：

| 可借点 | 它的做法 | 对我们 |
|---|---|---|
| 一个总编排 skill + 按域拆子 skill | 主 `skills/seo/SKILL.md` 路由到 `seo-technical/content/schema…`，每个 SKILL.md <500 行 | "车型深度调研 skill"按阶段拆：意图澄清/查询规划/选源/采集/段落判定/报告 |
| 参考文件按需加载 | `references/` 13 个文件，避免主 skill 膨胀 | 类目档案/词表/判据放 references，不塞进 skill 正文 |
| 条件 spawn 子 agent | 检测到本地商家才跑 local/maps；有 Google API 才跑 google | 我们：有图片任务才跑图检索；有文本目标才跑文本线；缺档案走通用层 |
| 内置质量闸门 | 阈值（30 警告/50 硬停）防止烂建议 | 对应我们的验收契约与有界循环 |
| 行业模板 + 首页信号自动识别 | 按 SaaS/本地/电商套不同检查表 | 对应类目档案 + `profile_missing` 兜底 |
| `doctor` 自检 | 跑批前检查运行时/浏览器 | 我们已有 `doctor.py`，接入 runner 前置检查 |
| 漂移快照（SQLite baseline/compare） | 同一站点多次审计对比 | 评测集回归：规则/模型变更前后跑同一批，diff 结果 |
| 输出"优先级行动清单+依据+如何验证" | 每条建议带 why/依赖/验收方式 | 我们报告应给每条结论附证据来源与可复核路径 |
| 通过扩展接 SERP 数据（DataForSEO 等 MCP） | 不自研搜索，直接买数据 | 可选：未来 SERP 通道可用现成 MCP，替代自抓百度 |

结论：claude-seo 的检索能力不如我们（它审计已知站点，不做跨站发现）；
它的**skill 分层、条件编排、质量闸门、输出可信度设计**值得直接借鉴。

## 6. 护城河评估（2026-10-30）

搜索、爬取、LLM 调用、agent 编排都是**商品化能力**，不构成护城河。本项目真正可积累的资产：

| 层 | 内容 | 强度 | 说明 |
|---|---|---|---|
| 领域知识资产 | 类目档案、部件词表、设计语汇、来源可信注册表、各车型语料库 | 中高 | 每轮测试都在增厚；竞争者需同样时间与领域判断才能复制 |
| 判定标准 | 对象锚定、V/P/G 三分类、具体性要求、验收契约 | 高 | 编码了产品负责人的隐性审美，且有裁决记录可回归 |
| 可审计流程 | robots/配额/账本/检查点/schema/证据链 | 高（B2B 场景） | 企业客户要的是可追溯，不是聊天框 |
| 产品化输出 | 报告结构、竞品分析模板、客户交付物 | 中高 | 与客户工作流绑定后粘性强 |
| 检索/爬取/编排 | 商品化 | 无 | 应尽量借用成熟方案，不自研 |

风险：若价值只剩"提示词+调用模型"，护城河为零；数据资产须持续新鲜（站点会变、车型会换代）。
建设动作：每轮测试沉淀为资产（词表/档案/评测集/裁决记录）；报告每条结论附证据与复核路径；合规可审计做成卖点。

## 7. 检索站点是否固定、AI 如何决定去哪找

现状：**半固定**——`data/source_registry.json` 维护可信域名（360che 高产、21-sun/ykl/163/csdn 等），
图片走百度/Bing 图片 + 厂商站画廊；这不是硬编码，是数据文件，可增删。
但站点清单会漂移（SERP 被拦、站点改版），所以"固定"只是先验，不是边界。

前沿模型的自主规划方式：拆解任务 → 选工具（web/image/site search/fetch）→ 生成查询 → 读结果 → 追问/翻页/换词 → 综合。
它没有领域先验、不可复现、成本不可控；我们有先验与可复现，但适应性弱。

结论：**骨架保留（可审计、可复现、成本可控），把"选哪个工具/查询/源"的决策交给模型在边界内自主选择**——
即已有的"两端规则、中间模型"原则；不是两选一。
