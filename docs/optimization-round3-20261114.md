# 优化轮次 3：search_key 落地验证 + 行业调研汇总（2026-11-14）

## C. 抽取阶段输出 search_key

**目的**：解决“纯中文描述名缺可检索标识”的问题，**不引入**车型识别模型、不做单独联网核对。

**方法**：
1. `extract` prompt 增加 `search_key`（品牌/车系/型号码 + 构型，必须来自结果文本）；
2. `validate_extraction` 接收并截断，`merge_candidates` 合并时优先保留带型号码的 key；
3. 用 5 份冻结 brief 重跑 plan（`data-test/runs/p3-searchkey-20261114/`），
   再抽 25 个候选做第二段对照：`normalize_query` vs `search_key`，各搜一次（只搜不下载）。

**结果**：

| 指标 | 数值 |
|---|---:|
| 候选覆盖 search_key | **142/142（100%）** |
| 与派生键不同 | 137（96%） |
| 车型有码时 key 也含码 | **62/67（93%）** |
| 平均长度 | 18.1 字 |
| 探针 25 个：key 命中更多 / 更少 | 5 / **8** |
| 探针 25 个：key 相关命中更多 / 更少 | 5 / **9** |

**结论**：
- **无条件使用 search_key 会更差**（更长、加了品牌/描述词，360 召回下降）；
- **条件使用有效**：`normalize_query` 命中 0 的 3 个样本，key **3/3 救回**
  （`XS265HS` 0→4 且相关 4，`XS395IV` 0→3 且相关 1，`J4.0-5.5XN` 0→2 但相关 0）；
- 因此落地方式改为：**search_key 只作查询阶梯的最后一档兜底**（前三档全 0 才用），
  已写入 `live_fetch`；`Target.query` 仍用派生键，search_key 存在 `WebWorld._search_keys`。

**冲突**：
- 与 A3 英文档同为“兜底档”，**顺序**：search_key（有来源证据）优先于英文档（需拉丁 token）；
- 与 B1 tier 无冲突：search_key 属于正常档，不是回退档；
- 与“不要表”无冲突：search_key 来自抽取模型**已读到的来源文本**，不是品牌词表。

**验证**：`retrieval_engine 47/47`、`planning 15/15`、`imagesearch 16/16`（离线）；
数据 `data-test/evals/search-key-eval-20261114.json`。

## 行业调研汇总（3 份，均在 `docs/research/`）

| 报告 | 覆盖 | 最值得借鉴 |
|---|---|---|
| `rag-candidates-20261114.md` | 多查询/候选发现/实体规范化（GraphRAG、Haystack、RAGFlow、Vespa） | **Gleaning 补抽一轮**、**结构化槽位输出**、**归一化 key 作为去重第一层**、RRF 融合 |
| `entity-matching-20261114.md` | 商品/实体匹配、去重、search_key（Splink、Dedupe、RapidFuzz、SC-Block） | **Fellegi-Sunter 加权去重**（无标注）、**闭类词自动挖掘**（只对功能词建表）、RapidFuzz 的“子集满分”陷阱 |
| `retrieval-eval-20261114.md` | 无标注评估、pooling、LLM judge、query drift | **冻结 query 快照集 + 固定池深度**、pairwise bootstrap CI、静默失败分类（错图率） |

### 与我们机制的关系（不是照搬框架）

| 借鉴点 | 对应我们哪一环 | 判断 |
|---|---|---|
| Gleaning 一轮补抽 | 第一段抽取召回（30–40% 痛点） | **值得先试**：prompt + 一次循环，成本 ×2 抽取调用 |
| 结构化槽位（brand/series/code/config/evidence_span） | 抽取规范化、search_key 生成 | **值得试**：不改架构，直接治“品牌/车系混杂” |
| 归一化 key（大小写/全角/标点/别名） | 去重 | 值得试，纯函数可测 |
| Fellegi–Sunter / Splink | 候选合并（无标注） | 后置：需要先有槽位化字段 |
| RRF 融合多路召回 | 第一段多查询合并 | 可试：几十行，替代“并集+规则截断” |
| 冻结评估集 + pooling + CI | 所有改动的判定 | **优先级最高**：没有它，任何“改进”都不可归因 |
| 静默失败分类（错图率） | 抓图质量 | 值得加入人工抽样表 |

**明确不采纳**：整套 RAG 框架、向量库替换、品牌词表（含 cleanco 式品牌表）、
以及“多路改写越多越好”的做法（我们 A3 已实测：英文档无条件使用会变差）。

### 建议的后续轮次（可并行）

1. **R1 抽取**：Gleaning 1 轮 + 结构化槽位（同时产出 search_key），5 brief 对照；
2. **R2 评估**：冻结 200 条 query 快照 + 池深度固定 + 四指标 + bootstrap CI（先把“好坏”变可判定）；
3. **R3 去重**：归一化 key → 手写 FS 三档加权（数字槽冲突判负）→ 再考虑 Splink；
4. **R4 融合**：RRF 替代并集截断，用 R2 的评估集验证。
