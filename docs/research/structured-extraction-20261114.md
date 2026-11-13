# 结构化抽取与领域数据标准调研（2026-11-14）

> 方法：仅网络检索；下列链接均于 2026-11-14 实测 HTTP 200。文中“成本”为工程量估算（人日），非报价。效果类结论凡未实测均标“未验证”。

## 一、8 条候选做法
### 1. OpenAI / Azure Structured Outputs（strict JSON Schema）
- 链接：https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs
- 做法：请求里给 `json_schema` + `strict:true`，模型按 schema 生成；Pydantic 模型可直接转 schema 并解析。
- 对应 slots：整条候选即一个 schema，`slots` 作为嵌套对象；`additionalProperties:false` 挡住多余字段。
- 成本/风险：低，1–2 人日可接。但 strict 模式要求**所有字段必填**（可空用 `["string","null"]`），且不支持 `pattern/minLength/maxLength/minimum` 等约束，正则与长度只能后置校验；中文品牌边界仍靠模型。
### 2. Instructor（Pydantic + function calling + 校验重问）
- 链接：https://python.useinstructor.com/
- 做法：用 Pydantic 定义响应模型，校验失败把错误信息回喂模型重试（reask），可配 `max_retries`；支持 DeepSeek/OpenAI 等 15+ provider。
- 对应 slots：`SlotBundle` 用 Pydantic 写，品牌枚举、型号正则、`model_validator` 做跨字段一致性；失败样本自动重问。
- 成本/风险：低–中，2–3 人日。重试放大 token 成本与延迟；对“字段缺失”模型可能编造而非留空，必须配合“未知填 null”的显式约束。
### 3. Outlines（约束解码）
- 链接：https://github.com/dottxt-ai/outlines
- 做法：按 JSON Schema / Pydantic / 正则 / CFG 在**生成时**屏蔽非法 token，保证结构合法；支持 transformers、vLLM、Ollama 等本地/自托管模型。
- 对应 slots：`model_code` 可用正则约束，`vehicle_type` 用 `Literal`，品牌用枚举（若可控）。
- 成本/风险：高，5–10 人日；需自托管模型。只保证“格式合法”不保证“语义正确”；中文 tokenizer 下正则易切坏汉字；闭源 API 用不上。
### 4. BAML（DSL + 生成客户端 + 健壮解析）
- 链接：https://docs.boundaryml.com/home
- 做法：用 `.baml` 定义 `class/function`，生成类型安全客户端；内置 JSON 修复、解析失败重试、流式输出，并可在 VSCode Playground 里跑测试。
- 对应 slots：把 `Candidate`/`Slots` 写成 BAML class，`@description` 直接写在字段上；枚举与可选字段语法比 prompt 清楚。
- 成本/风险：中–高，4–8 人日。多一门 DSL、代码生成与构建步骤；对中文长尾品牌仍是模型能力问题。
### 5. GLiNER（零样本 span 抽取）
- 链接：https://github.com/urchade/GLiNER
- 做法：给实体标签列表（如 brand/series/model_code），模型直接输出**原文 span + 标签 + 阈值分**，CPU 可跑，支持微调。
- 对应 slots：先做 span 级召回（品牌、型号片段），再交给 LLM 归一化；span 天然就是 evidence。
- 成本/风险：中，3–6 人日。官方称多语种覆盖 100+ 语言，但**中文工程机械领域效果未验证**；品牌/车系边界模糊时 span 易切错；阈值分不是校准概率。
### 6. ACES / PIES + 参考库（VCdb/Qdb/Brand Table）
- 链接：https://www.autocare.org/aces 、https://www.autocare.org/pies
- 做法：ACES 用 Year/Make/Model/Engine + Qualifier 表达“适配关系”，PIES 表达产品属性；均以 XML/XSD 发布，配套 VCdb、Qdb、PCdb、Brand Table 等编码库。
- 对应 slots：借其“**受控词表 + qualifier 限定**”思路：brand 用 Brand Table，series/model 用 VCdb 层级，config 拆成 qualifier 键值对。
- 成本/风险：高，需年费订阅参考库，接入 5–10 人日。北美售后体系，工程车/重卡覆盖有限；中文品牌名与国内车系不在库内；XML 重、文档需登录。
### 7. TecDoc（TecAlliance 配件目录标准）
- 链接：https://www.tecalliance.net/solutions/tecdoc
- 做法：以标准化“车辆—发动机—配件”关联组织目录，欧洲 IAM 通用；商用车型另有独立链路（页面为 JS 渲染，具体字段以付费文档为准，**未验证**）。
- 对应 slots：借“车辆类型 + 发动机/配置”作为独立维度，而不是塞进一句 `model` 描述。
- 成本/风险：高，商业授权 + 对接。欧洲中心、中文数据弱；闭源付费；只适合做字段命名参考，不宜做主 schema。
### 8. NHTSA vPIC（VIN 解码）
- 链接：https://vpic.nhtsa.dot.gov/api/
- 做法：17 位 VIN → WMI（厂商）、车型年、厂牌、车型、发动机等字段；提供 DecodeVin / DecodeWMI / GetModelsForMake 等免费接口。
- 对应 slots：若摘要中出现 VIN，可作为 `model_code` 的强证据，并反查 brand/series；也可离线建 brand 别名词表。
- 成本/风险：低，0.5–1 人日。美国登记数据，中国工程车 VIN 覆盖差；只能辅助，不能当唯一真值。

## 二、值得抄的小机制（低成本、直接降低混槽）
- **全字段必填 + 可空**：未知显式 `null`，禁止省略字段；省略是幻觉温床（OpenAI strict 模式的做法）。
- **evidence 必填**：每个非空结构化字段配 `{field, source_id, quote, start, end}`；`quote` 必须是对应摘要的**原文子串**（校验时去空白/全半角归一）。
- **source_id 而非裸 URL**：输入结果编号 s1…sn，输出只允许引用这些 id；落库前映射回 URL，天然防编造来源。
- **校验失败回喂重问**：只回传错误字段与错误原因，不回传整段 prompt（Instructor 的 reask 思路）。
- **判别式联合类型**：`vehicle | part | brand_only` 用 tagged union，避免“一句描述”里同时装三类对象。
- **置信度用枚举而非概率**：`high/medium/low` + 规则（有 evidence=high，推测=low），比模型自报 0.87 更可校验。

## 三、不要引入的重框架
- **Outlines 式本地约束解码**：闭源 API 用不上，自托管一套 vLLM 的运维成本远超收益。
- **BAML 全量迁移**：DSL + 代码生成 + 构建链，团队当前阶段收益不抵学习成本；可只借“字段 description + 解析重试”两个点。
- **ACES/PIES 或 TecDoc 作为主 schema**：重 XML、付费、中文/工程车覆盖弱；只借命名与 qualifier 思想。
- **GLiNER 自训练流水线**：没有标注集前先别训；先用现成多语模型做召回评测。

## 四、我们的 slots schema v2 建议
```json
{
  "candidate_id": "c1",
  "vehicle_type": "truck|construction|bus|other|null",
  "brand":  {"raw": "原文", "norm": "归一", "id": "brand_x|null"},
  "series": {"raw": "原文", "norm": "归一"} ,
  "model_code": "string|null",
  "config": {"tonnage": null, "power_hp": null, "drive": null, "cab": null, "emission": null},
  "display_name": "品牌+车系+型号，可空",
  "evidence": [{"field": "brand", "source_id": "s1", "quote": "≤40字原文", "start": 12, "end": 20}],
  "sources": ["s1"],
  "confidence": "high|medium|low",
  "unresolved": ["series 与 model_code 边界不清"]
}
```
- 必填：`candidate_id / vehicle_type / confidence / evidence / sources`；其余可空但**键必须存在**。
- `sources`：非空数组，元素必须 ∈ 输入结果 id 集合；空则整条丢弃。
- `evidence`：每个非空字段至少一条；`quote` 必须是 `source_id` 对应摘要的子串，`start/end` 与 quote 对齐。
- `model_code`：2–20 字符，`^[A-Za-z0-9][A-Za-z0-9 ./-]*$`，不含中文；不通过则降级为 `null` 并记入 `unresolved`。
- 跨字段：`brand != series != model_code`；`display_name` 不得引入 evidence 中不存在的 token（防拼接幻觉）。
- `confidence`：high=关键字段均有 evidence；medium=部分推断；low=仅一条弱证据。low 不进入主结果，只进候选池。
- 顶层 `additionalProperties:false`；Pydantic `model_validator` 统一做上述检查，失败回喂重问一次。

## 五、总结
1. 核心问题不是“模型不会抽”，而是**没有可校验的契约**：自由文本 `model` 一句描述把品牌/车系/型号/配置混在一起。
2. 最低成本路径：Pydantic 定义 schema + strict JSON + 全字段必填/可空 + evidence 子串校验，1–2 人日可上线。
3. 第二步再加 Instructor 式 reask，只回传错误字段，控制重试成本。
4. GLiNER 适合作 span 召回与 evidence 来源，但中文工程机械效果未验证，先小样本评测再决定。
5. ACES/PIES、TecDoc 不要照搬，借“受控词表 + qualifier + 车辆/发动机分维”即可；vPIC 只作 VIN 辅助。
6. 明确不引入：Outlines 本地约束解码、BAML 全量迁移、付费目录做主 schema。
7. 验收指标建议：字段级准确率、evidence 子串命中率、来源合法率、low 置信度占比。
8. 先做 schema v2 + 校验器，再谈换模型；schema 稳定后模型迁移才是可比较的。
