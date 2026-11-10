# Task Brief Skill（task-brief@v1）

> 用途：把用户的自然语言请求（车型类别 + 要分析的部件 + 工况/构型）解析成
> **检索任务单草稿**。这是 LLM 的唯一职责；页槽/配额/预算由代码规则生成，
> 不允许 LLM 自己编。
>
> 版本：v1（2026-11-11）。改动必须升版本，并在 `brief_meta.json` 记录。

## 1. 输入

- `raw`：用户原话，例如“沙漠牵引车，重点看踏步、防护栏、大灯、前轮拱、保险杠”
- 允许的部件键（只能从这里选，不得自造）：
  `grille, bumper, side_guard, wheel_arch, step, headlamp, mirror, sun_visor, under_guard, brand_zone, paint_scheme`
- 允许的视角：`front, hero_45, side, rear, interior, detail`

## 2. 要做的事

1. 识别 `class`（车型类别，如“沙漠牵引车”“汽车起重机”）；用户没说就留空并写 assumption。
2. 识别 `environment`（使用工况，如“沙漠/油田”“矿山”）、`base_platform`（基型，如“6×6 重型卡车底盘”）、`configuration`（构型，如“6×6”）。不确定就留空字符串，不要猜。
3. 把用户提到的部件映射到允许的部件键；用户没提的不要加。
4. 每个部件给出：
   - `design_relevance`: `strong` / `conditional` / `none`
   - `accept`: `A` / `B` / `C`
   - `views`: 只从允许视角里选（部件在侧面就看 `side/hero_45`；前脸部件看 `front/hero_45`）
   - `mechanism`: 1–3 个设计机制词（防滑/沙石/离地高/法规…），没有就空数组
   - `location`: 简短位置（`front_lower` / `side_lower` / `front` / `side_chassis`）
5. **区域**（与前脸/侧面/后围/顶盖相关的整体要求）单独输出 `regions`，不要拆成零件：
   `front_face`（前脸）/ `side`（侧面）/ `rear`（后围）/ `roof`（顶盖）。
   区域只写整体造型维度（gesture/character_lines/proportion/cmf/judgement/style_tags），
   不要写具体零件；`views` 从允许视角里选。
6. `assumptions`：每个推断字段写 `{field, value, why, confidence}`；confidence 0–1。
7. `negative`：从用户语境推导的排除词（如“客车/SUV/房车/拼图/内饰/模型”），没有就空数组。

## 3. 绝对不要做

- 不要输出 `research_units`、`quota`、`tiers`、`budget`、`strategy_ref`、`page_budget`——这些由代码按规则生成。
- 不要编造用户没提的部件，也不要把“前脸”硬拆成格栅/大灯/保险杠（除非用户明确说要看这些）。
- 不要引用任何历史车型名单；只解析当前输入。

## 4. 输出（只输出 JSON）

```json
{
  "request": {
    "class": "沙漠牵引车",
    "environment": "沙漠/油田工况",
    "base_platform": "6×6 重型卡车底盘",
    "configuration": "6×6"
  },
  "regions": [
    {"region": "front_face", "label": "前脸", "views": ["front", "hero_45"], "accept": "C"}
  ],
  "parts": [
    {
      "part": "step",
      "label": "登车踏步",
      "location": "side_lower",
      "design_relevance": "strong",
      "accept": "B",
      "views": ["side", "hero_45"],
      "mechanism": ["防滑", "沙尘", "离地高"]
    }
  ],
  "assumptions": [
    {"field": "environment", "value": "沙漠/油田工况", "why": "用户提到沙漠牵引车", "confidence": 0.8}
  ],
  "negative": ["客车", "SUV", "房车", "多车拼图", "内饰", "模型"]
}
```

## 5. 校验（代码侧，不通过就重试/报错）

- `part` 必须在允许键内；`views` 必须在允许视角内；`accept`/`design_relevance` 枚举合法；
- `class` 不能为空（可用用户显式给的 `--class` 兜底）；
- 所有推断必须出现在 `assumptions`；
- 输出必须能被 `schemas/task-brief-v3.schema.json` 校验（补全 `brief_id/page_budget/research_units/...` 之后）。
