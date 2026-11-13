# 词表审计：项目里还有哪些“枚举表”，它们驱动什么（2026-11-14）

> 触发：H3 brief 的部件被写成 `custom_5a1c7e` 这类 hash，说明“部件词表”仍在决定命名。
> 结论先行：**词表不是准入，但确实在改名字**；已修。其余表逐条列出，分清“危险/可接受”。

## 1. 部件相关

| 表 / 列表 | 位置 | 规模 | 实际作用 | 风险 | 处理 |
|---|---|---|---:|---|---|
| `data/part_taxonomy.json` | `data/` | 11 个部件 + 4 个区域 | `briefing.py` 把用户部件映射到内置键；**内置键之外→`custom_<sha1>`**；analysis 用它标 `term_off_taxonomy`；UI fixture 取构型名 | **高**：命名被表决定，且不可读 | **已修**：词表外部件改为可读 key（`custom_部件名`），表只用于“认识就显示原名/默认族”，不认识不拒绝、不改名 |
| `REGION_VIEWS` | `briefing.py` | 4 组 | 区域→允许视角 | 低：视图枚举、非部件实体 | 保留（schema 常量） |
| `db.FRONT_PARTS` | `db.py` | 3 个 | 正面部件展示 | 低：固定键 | 保留 |
| `VIEW_QUERIES` | `imagesearch.py` | 5 组 | 视角词→查询后缀 | 低：视图不是部件实体 | 保留 |

## 2. 类目 / 品牌

| 表 | 位置 | 规模 | 作用 | 风险 | 建议 |
|---|---|---|---:|---|---|
| `data/category_profiles.json` | `data/` | 6 个类目档案 | 旧 `textrun`/`--profiles` 路径：别名、市场词、代表车型、部件词、来源提示 | **高**（类目词穷举），但**当前检索 loop 不走它** | 标记为 legacy；若确认不再使用则删除 |
| `BRAND_GROUPS` | `imagesearch.py` | 22 组别名 | 品牌别名匹配（现仅作加分/兜底） | 中：仍是白名单 | 保持“加分”定位；不再作为判死门槛；后续可移除 |
| `GENERIC / VEHICLE_WORDS / NON_VEHICLE / _DESC_STEMS` | `imagesearch.py` | 12/25/25/27 | 通用词、车辆词、污染词、描述性词干 | 低：通用语言学小表，不是领域实体穷举 | 保留；新增条目需说明理由 |

## 3. 来源 / 风格

| 表 | 位置 | 规模 | 作用 | 风险 | 建议 |
|---|---|---|---:|---|---|
| `data/source_registry.json` | `data/` | 13 个来源 | 旧链路/domainbench 的来源可信度 | 中：来源白名单 | 与 loop 解耦；只用于统计/审核 |
| `data/style_vocabulary.json` | `data/` | 6 组 | 分析报告的受控风格词 | 低：展示层受控词 | 保留；与检索解耦 |
| `gate` 的 keep/drop/scene/view 标签 | `gate.py` | 固定 | CLIP 文本提示词 | 低：模型提示，不是用户实体表 | 保留 |
| `audit.STRONG_WORDS` / `domainbench.DESIGN_TERMS` | 代码 | 小 | 文档筛选 | 低 | 保留 |

## 4. 哪些文件“提示”去看部件词表

| 文件 | 原话 | 说明 |
|---|---|---|
| `docs/CODE-INDEX.md:88` | “`data/part_taxonomy.json`：部件词表” | **主要入口**；已改为“内置部件键（兼容/显示用，非准入）” |
| `README.md:118` | “词表与来源注册（part_taxonomy / …）” | 已改为“配置与兼容映射” |
| `docs/PRD.md:144` | “按附录 B 部件词表逐类输出” | 产品层描述；补“参考、不是准入” |
| `docs/ui-fixture-spec.md:162/179` | “构型名必须来自词表” | 分析/夹具层受控词，与检索无关 |
| `docs/retrieval-experiments-log.md:343` | “参考词表/规范输出词汇，不是用户输入” | 本身就是正确口径 |
| `docs/agent-loop-mechanisms.md:81` | “领域知识资产：类目档案、部件词表…” | 把词表当资产描述 |
| `skills/task-brief/SKILL.md:116` | “不要用 part_taxonomy 的键做准入” | 技能层已禁止，但代码仍改名 → 现已对齐 |

## 5. 这次改了什么

1. `briefing._part_slug`：词表外部件 key = `custom_` + 可读 slug（中文/字母/数字，≤16 字），
   不再整串 sha1；仍保留 `label` 原文；
2. 单测：`涉水喉` 的 key 必须包含“涉水喉”；
3. H3（扫路车）brief 重新生成，部件变成 `custom_brush_guard` / `custom_hopper_side_panel` /
   `custom_suction_nozzle`，可读；
4. 文档口径修正：CODE-INDEX / README / PRD 的“部件词表”改为“兼容用内置键”。

## 6. 还没做（需你拍板）

- 是否**删除** `data/part_taxonomy.json`（把 11 个内置键降为代码常量）？影响 analysis、UI fixture；
- 是否删除 legacy 的 `data/category_profiles.json`；
- 是否给 `BRAND_GROUPS` 定“只加分、不判死”的正式规则（目前代码已按加分走，但没有文档约束）。
