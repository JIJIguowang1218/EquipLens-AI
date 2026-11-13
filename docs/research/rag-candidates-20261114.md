# RAG 检索管线：多查询生成 / 候选发现 / 实体规范化 —— 可借鉴的小机制

调研日期：2026-11-14。只做网络检索，未跑任何框架。目标：为"8 条中文查询 → 抽候选车型 → 图搜核验"两段式管线找可落地的小机制。
标注说明：✅=已读到原文/官方文档；⚠️=方向可信但未验证具体实现或中文效果。

---

## 1. Gleaning：多轮追问"你还漏了什么" ✅

- **来源**：[GraphRAG 数据流](https://microsoft.github.io/graphrag/index/default_dataflow/)、[《Graph RAG from Scratch》第 8 章](https://graphrag.xinbetween.com/chapters/08-entity-relation-extraction.html)
- **他们怎么做的**：第一次抽取后，把模型输出拼回上下文，追加一句"很多实体被漏掉了，请按同样格式补全"；每轮再问一个 Y/N"还有遗漏吗"，答 N 或到轮数上限就停。实测第 1 轮增益最大、第 2 轮多是别名和噪声。
- **我们能怎么用**：**抽取召回**。对每条搜索结果的正文做 `max_gleanings=1` 的补抽，专门捞第一次漏掉的品牌/型号短串；第 2 轮不建议开。
- **落地成本**：低（纯 prompt + 循环，抽取调用数约 ×2）。

## 2. 固定类型白名单 + 类型漂移后归一 ✅

- **来源**：[第 8 章](https://graphrag.xinbetween.com/chapters/08-entity-relation-extraction.html)、[RAGFlow 知识图谱](https://ragflow.com.cn/docs/dev/construct_knowledge_graph)（实体类型为必填项）
- **他们怎么做的**：prompt 里列出 5–8 个允许类型并给一个反例样本；解析后把未知类型（COMPANY/FIRM/厂商）确定性映射回白名单或 OTHER，不靠模型自觉。
- **我们能怎么用**：**规范化**。定义 `BRAND / SERIES / MODEL_CODE / CONFIG / BODY_TYPE`，禁止自由标签；"中国重汽""重汽"统一落 BRAND。这一步直接治"品牌/车系/型号混杂"。
- **落地成本**：低（一个枚举 + 一个映射表 + 一条后处理）。

## 3. 归一化 key：零成本的实体解析第一层 ✅

- **来源**：[第 9 章 实体解析级联](https://graphrag.xinbetween.com/chapters/09-entity-resolution.html)；GraphRAG 系默认按 `(title, type)` 精确合并（[数据流](https://microsoft.github.io/graphrag/index/default_dataflow/)）
- **他们怎么做的**：抽取时要求名称大写/规范大小写，作为"解析前的廉价第一遍"；再做 case fold、去冠词/敬称、去标点、NFKC，生成 `normalized_key`，原文另存为 display/alias。
- **我们能怎么用**：**去重**。中文侧规则：全角→半角、去空格/连字符/点、统一"款/型/版/系"、统一马力与吨位写法、品牌别名表（重汽=中国重汽，陕汽=陕重汽）。现有规则去重可以整体迁到这一层。
- **落地成本**：低（纯函数 + 别名表，可单测）。

## 4. 解析级联 + 类型门控 + 防链式聚类 ✅

- **来源**：[第 9 章](https://graphrag.xinbetween.com/chapters/09-entity-resolution.html)、[RAGFlow 实体解析开关](https://ragflow.com.cn/docs/dev/construct_knowledge_graph)（LLM 合并"2025/2025年""IT/信息技术"）
- **他们怎么做的**：归一化 → 分块（token/缩写/首字）→ 多指标打分（token set、Levenshtein、Jaro-Winkler、名称+描述向量）→ **类型门控**（LOCATION 不与 ORGANIZATION 合并）→ 只有灰区交 LLM 仲裁（输出 same/different/unsure，unsure 视为 different）→ 聚类用 canonical star 或带冲突守卫的 union-find，避免 A~B~C 链式误并。
- **我们能怎么用**：**去重**。把现有"规则去重"升级成这层级联：确定性规则吃掉 80%，灰区才花 token；每条合并记录触发规则，便于事后审计误并。注意同名不同车（"解放 J6"跨代）要靠系列/年份约束，别只看字符串。
- **落地成本**：中（要写分块+打分+聚类，约 200 行；可先只做归一化+类型门控）。

## 5. QueryExpander + 多查询检索器自带跨查询去重 ✅

- **来源**：[Haystack Query Expansion cookbook](https://haystack.deepset.ai/cookbook/query-expansion)
- **他们怎么做的**：`QueryExpander(n_expansions=4)` 生成 4 条同义改写并保留原查询；`MultiQueryInMemoryBM25Retriever` 对每条查询各跑一次，并**自行处理同一文档被多条查询召回**的情况。
- **我们能怎么用**：**多查询生成**。第二段图搜从 1 条查询变成 3–4 条（如"品牌+车系 自卸车 实拍""型号 牵引车 前脸"），按图片 URL/文档 id 去重后再过门卫；第一段的 8 条中文查询也可先扩写再搜。
- **落地成本**：低（一次 LLM 调用 + 一个 dict 去重）。

## 6. 结构化分解：用 Pydantic 槽位代替自由文本 ✅

- **来源**：[Haystack Query Decomposition cookbook](https://haystack.deepset.ai/cookbook/query_decomposition)
- **他们怎么做的**：用 Pydantic 定义 `Questions`/子问题列表，走结构化输出（schema 约束），再逐个子问题检索、汇总推理；而不是让模型自由写一段"抽取出这些车型"。
- **我们能怎么用**：**规范化**。把候选抽取的输出钉成 `{brand, series, model_code, config, body_type, evidence_span, confidence}`，字段可空但不可缺；字符串列表变成结构化记录，"混杂"在源头就少一半，去重也变成按字段比对。
- **落地成本**：低（schema + 解析容错，DeepSeek 支持 JSON 输出即可）。

## 7. RRF 融合多路召回，并按查询类型调权 ✅

- **来源**：[Vespa Hybrid Search](https://learn.vespa.ai/vector-search/hybrid-search/)
- **他们怎么做的**：`RRF = Σ 1/(k + rank_i)`，k 默认 60，只看排名不看分数，因此不需要归一化 BM25 与向量相似度；名称/编号类查询偏文本权重，概念类查询偏向量；RRF 放在 global phase 对 top-N 重排。
- **我们能怎么用**：**候选发现**。把 8 条查询 + 每条扩写查询各自的有序结果用 RRF 合并，而不是并集后靠规则截断；顺带产出"多路命中次数"作为候选置信特征，给第二段门卫/核验用。
- **落地成本**：低（几十行融合函数，无需改检索后端）。

## 8. GLiNER 零样本 NER 作为第二路召回 ⚠️

- **来源**：[txtai Entity pipeline](https://neuml.github.io/txtai/pipeline/text/entity/)
- **他们怎么做的**：token 分类管线，支持 GLiNER 动态标签（`labels=["country","city"]`），返回 `(entity, type, score)`，多 token 实体可按 simple/first/average/max 聚合，可按 score 阈值过滤。
- **我们能怎么用**：**抽取召回**。用自定义标签（品牌/车型/马力/吨位）做一路不花 LLM 的抽取，与 LLM 结果取并集，专门补短型号；中文与工程车领域效果需实测（未验证）。
- **落地成本**：中（要引入模型/推理服务；建议先离线对比一路召回增量）。

---

## 最值得先试的 2 条

**① Gleaning 一轮补抽（第 1 条）。** 它正对"60–126 条只抽 30–40%"这个症状：不是检索没召回，而是抽取阶段主动放弃。改动只在 prompt 与一次循环，抽取调用翻倍但候选清单立刻变长；先固定 `max_gleanings=1` 并用"新增候选数/新增调用数"判断是否值得开第 2 轮。可与第 6 条的结构化槽位同批上线，补抽出来的记录直接进 schema。

**② 类型白名单 + 归一化 key（第 2、3 条，先不碰聚类）。** 这是"混杂 + 规则去重"的最低成本解：一个枚举把品牌/车系/型号分开，一个 `normalize_key` 函数把别名与写法差异吃掉，两者都不改变现有架构，当天可上线，且天然可测——拿 50–100 条标题人工标注 `(brand, series, model)` 做小黄金集，用 pairwise P/R 看归一化前后与补抽前后的变化。等这两步的数字稳住，再上第 4 条的灰区 LLM 仲裁。
