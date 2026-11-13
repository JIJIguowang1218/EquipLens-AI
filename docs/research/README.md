# 行业调研索引（2026-11-14）

三轮网络调研的原始报告（均只读检索，未跑框架/未改代码）：

| 文件 | 主题 | 最值得借鉴 |
|---|---|---|
| [rag-candidates-20261114.md](rag-candidates-20261114.md) | 多查询生成 / 候选发现 / 实体规范化 | Gleaning 补抽、结构化槽位、归一化 key、RRF 融合 |
| [entity-matching-20261114.md](entity-matching-20261114.md) | 商品/实体匹配、去重、search_key | Fellegi–Sunter 无标注去重、闭类词自动挖掘、RapidFuzz 子集满分陷阱 |
| [retrieval-eval-20261114.md](retrieval-eval-20261114.md) | 无标注评估、pooling、LLM judge、query drift | 冻结 query 集 + 固定池深度 + bootstrap CI、静默失败分类 |

**落地状态（与实验对应）**：

- Gleaning 一轮：已测（`optimization-round4-20261114.md` §1）→ **0 增益，不采纳**（输入是短摘要，不是全文）；
- 归一化 key：已离线测（§2）→ 0.9% 重复，可做但需身份/型号码护栏；
- 结构化槽位：未测，下一轮；
- RRF / 评估协议：未测，依赖冻结评估集。

**不采纳**：整套 RAG/向量库框架、品牌/类目词表、无条件多路改写（A3 已实测变差）。
