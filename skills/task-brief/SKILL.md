---
name: task-brief
description: 把用户的工程车/重卡需求（品类 + 工况 + 要分析的区域/部件）分析成检索任务单：先判品类/基型/构型/工况，再判设计对象与设计维度，最后输出结构化 brief。用于用户输入模糊、部件不在词表、需要工程产品设计判断时。
---

# 任务单分析：工程产品设计方法（task-brief@v2）

> 这不是“把用户的话填进 JSON”的模板，而是一套**分析用户输入的方法**：
> 先判断这是什么品类的什么问题，再判断每个设计对象为什么值得看、该看哪些设计维度，
> 最后才落到检索任务单。
>
> 版本：v2（2026-11-11）。v1 是格式说明，v2 增加工程分析引导；改动必须升版本并记录。

## 0. 一句话原则

**先分析“设计问题”，再决定“查什么图”；不要用部件词表反查用户。**

部件是穷举不完的（防沙板、涉水喉、爬梯、支腿、导流罩、随车吊吊臂……）。
词表只用于**归一化已有说法**，不是准入门槛；用户说什么，就分析什么。

## 1. 五层拆解（每次按顺序）

1. **品类**：用户说的是哪类工程产品？（沙漠牵引车 / 汽车起重机 / 矿用自卸车…）
   - 口语词先落参数：如“重型吊车”→ 吨位 + 底盘形式（汽车/全地面/履带）+ 上装；不确定就写 assumption / 需要确认。
2. **基型平台**：这类产品的底盘/驾驶室/上装基型是什么？（6×6 重型卡车底盘、起重机底盘、履带底盘…）
   - 这决定“哪些造型是平台继承，哪些是工况特化”。
3. **构型**：驱动/布置/上装形式（6×6、8×8、中置驾驶室、后置吊臂…）。
4. **工况/环境**：高温、沙尘、强辐射、矿山、油田、寒区、法规区域…
   - 判断每个设计对象**是否因环境而改变**；不是所有部件都环境敏感。
5. **设计对象 + 设计问题**：用户点名的“前脸/踏步/防护栏/防沙板…”分别是什么？
   - 它是 **region（区域）**、**part（部件）**，还是 **function（功能件）**？
   - 用户真正想看的**设计问题**是什么：造型语言？比例？结构/分缝？CMF？人机/法规？环境防护？

## 2. 设计对象怎么判（不查表）

对用户每个说法，依次回答：

| 判断 | 问题 | 输出 |
|---|---|---|
| 类别 | 连续曲面/整体风格 → region；有分缝独立件 → part；以功能命名 → function | `kind` |
| 位置 | 前/侧/后/顶/底盘/上装；同名的前后/侧位要拆开 | `location` |
| 功能 | 它解决什么问题（防沙、防撞、登车、散热、法规…） | `function` |
| 形态/构造 | 板金/型材框架/铸锻/功能附件；分缝、节点、加强筋 | `part_family`（可空） |
| 环境驱动 | 形态是否因工况改变？会 → environment 轴优先；不会 → 平台继承/跨车型 | `relation_axis` |
| 可见性 | 哪些视角能看到？需要特写还是整体？ | `views` |
| 设计维度 | 该对象最值得看的 2–4 个维度（见 §3） | `design_axes` |

### 不知道的部件怎么办

1. 保留用户原词作为 `label`（不要强行翻译成词表里的键）；
2. 给出 `part` 的稳定 slug：已知用 taxonomy 键；未知用 `custom_<短哈希>`；
3. 标 `taxonomy_status: "new"`，写 `part_family` 猜测 + `why`；
4. 用“位置 + 功能 + 形态 + 环境”描述它，保证检索能查到；
5. 不要因为它不在词表里就丢弃。

## 3. 设计维度（分析轴）

对每个对象选 2–4 个，不要全选；每个维度写“为什么这个对象要看它”：

| 维度 | 看什么 | 典型对象 |
|---|---|---|
| `form_gesture` | 整体姿态、体量、线条走向、家族化 | 前脸、侧面、驾驶室 |
| `proportion` | 比例、离地、轮拱与驾驶室关系 | 前脸、轮拱、底盘 |
| `structure` | 分缝、板面/型材、节点、加强筋、装配 | 保险杠、防护栏、踏步 |
| `cmf` | 材料、涂装、表面处理、色彩 | 覆盖件、涂装、轮毂 |
| `function_ergonomics` | 登车、防滑、视野、维修、人机 | 踏步、把手、后视镜 |
| `environment_protection` | 防沙/防尘/散热/防腐/离地 | 防护栏、进气、底盘、踏步 |
| `regulation` | 灯光、防护、反光、尺寸法规 | 大灯、侧防护、后防护 |
| `manufacturing` | 冲压/折弯/铸锻/焊接对造型的约束 | 保险杠、支架、轮拱 |

**关系轴**（决定检索范围，不是设计维度）：

- `exact`：同品类同构型；
- `environment`：因工况而改变的形态（防沙板、涉水喉、散热口）；
- `platform`：继承平台造型（驾驶室轮廓、家族前脸）；
- `cross_vehicle`：功能件可跨类目比较（踏步、爬梯、把手）——默认不开，标 `borrowed`。

## 4. 输出字段（不是完整 brief）

**完整 brief 的格式以 `schemas/task-brief-v3.schema.json` 为准**；下面只是你（LLM）要填的分析字段，
`page_budget / research_units / quota / tiers / budget / strategy_ref` 由代码补，禁止输出。

```json
{
  "request": {
    "class": "车型类别（必填）",
    "environment": "工况/环境（可空）",
    "base_platform": "基型平台（可空）",
    "configuration": "构型（可空）",
    "design_questions": ["这次要回答的设计问题，1–3 条"]
  },
  "regions": [
    {"region": "front_face|side|rear|roof", "label": "区域名",
     "views": ["front|hero_45|side|rear|detail"],
     "design_axes": ["form_gesture|proportion|structure|cmf|function_ergonomics|environment_protection|regulation|manufacturing"]}
  ],
  "parts": [
    {"part": "taxonomy 键或 custom_<hash>", "label": "用户原词/标准名",
     "kind": "part|function", "location": "位置",
     "part_family": "sheet_metal|frame_profile|cast_forged|function_attachment|...",
     "taxonomy_status": "known|new", "relation_axis": "exact|environment|platform|cross_vehicle",
     "design_axes": ["..."], "views": ["..."],
     "design_relevance": "strong|conditional|none", "accept": "A|B|C",
     "mechanism": ["..."], "why": "为什么这个对象值得看，能提供什么证据"}
  ],
  "assumptions": [{"field": "", "value": "", "why": "", "confidence": 0.0}],
  "negative": ["..."]
}
```

> 示例见 `references/example-c01.md`，**只是示例，不是模板**；不要照抄车型/部件/理由。

## 5. 绝对不要

- 不要把用户没提的部件补进来；也不要把“前脸”硬拆成格栅/大灯/保险杠（除非用户明确点名）。
- 不要用 `part_taxonomy.json` 的键做准入；它只是参考词表。
- 不要编 `quota / tiers / budget / page_budget`——这些由代码规则生成。
- 不要用“相似/同系列”当理由；理由必须写“能提供什么设计证据”。
- 不确定就写 assumption / `needs_confirmation`，不要猜型号。

## 6. 代码侧校验

- `part` 可以是任意 slug；`custom_*` 保留原 label；
- `views` 必须在允许视角内；`accept/design_relevance` 枚举合法；
- `design_axes` 必须在 §3 的维度表内；
- 全部推断必须进 `assumptions`；
- 最终 brief 过 `validate_brief` + `schemas/task-brief-v3.schema.json`。
