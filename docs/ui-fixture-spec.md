# UI 数据契约（fixture）v1

| 属性 | 内容 |
|---|---|
| 日期 | 2026-11-05 |
| 状态 | **模拟数据**：结构按真实链路，文案由人手写；数值不代表真实检索结果 |
| 用途 | 高保真可交互页面的填充源、联调期的假后端、回归时的固定输入 |
| 生成 | `PYTHONPATH=src python scripts/make_ui_fixtures.py`（幂等，可重跑） |
| 产物 | `data-test/ui-fixtures/{s1-retrieval,s2-analysis,s3-report}.json` |

本文件是**字段与规则的唯一出处**。改字段先改这里，再改生成脚本，再重跑。

---

## 1. 为什么需要

高保真要"填充已经跑好的数据"，但仓库现状是：

- 图片与名录有（70 张实拍、14 条目标），**分析产物与排版产物没有**；
- `data-test/equiplens.db` 是空的（7 张表 0 行），`scripts/analyze_batch.py` 查库取图，现在跑不起来；
- `scripts/build_report_page.py` / `build_report_book.py` / `export_pptx.py` 都在，但依赖并不存在的 `data-test/analysis-<date>/` 与 `data-test/report-book/`。

所以先用 fixture 把**数据形状**固定下来：真实链路恢复后，把同一份契约里的假文案换成真文案即可，页面代码不用改。

---

## 2. 文件与页面的对应

| 页面 | 文件 | 主要读取 |
|---|---|---|
| S1 检索台 | `s1-retrieval.json` | `analysis.prose`（右栏散文）、`cards[]`（卡片与清单） |
| S2 素材与分析 | `s2-analysis.json` | `vehicles[].views[]`（图 + 每个视角的 analysis） |
| S3 排版 | `s3-report.json` | `pages[]`（12 页与每页 blocks） |

---

## 3. `s1-retrieval.json`

```jsonc
{
  "fixture": "s1-retrieval", "version": "1.0", "generated_at": "…",
  "notice": "模拟数据…",                       // 必读，页面应可折叠展示
  "contract": "docs/ui-fixture-spec.md",
  "prose_ref": "docs/ui-interaction-spec-v3.md §9",
  "request": { "raw": "…", "category": "沙漠牵引车", "parts": ["踏步","防护栏"], "want": 6 },
  "analysis": {
    "axes": ["exact", "environment", "platform", "cross_vehicle"],
    "prose": "四层散文，一段，不分点…"
  },
  "budget": { "recommended": 6, "backup": 2, "requested": 12 },
  "cards": [ { … } ]
}
```

`cards[]` 字段：

| 字段 | 类型 | 说明 | 页面用法 |
|---|---|---|---|
| `id` | string | 名录目标 id（`t01`…） | 选中集合的主键 |
| `role` | `recommended` \| `backup` | 推荐 / 备选 | 备选灰化、虚线、不可勾选 |
| `model` | string | 车系名 | 卡片标题（等宽） |
| `configuration` | string | 构型 | 标题下的 `品牌 · 构型` |
| `relation` | `exact` \| `environment` \| `platform` \| `cross_vehicle` | 关联轴 | 关联程度色点与文案 |
| `tier` | number | 1–3 | 排序 |
| `confidence` | number | 0–1 | 只上浮到 tooltip，不上卡片 |
| `selected` | bool | 默认勾选 | 勾选框初值 |
| `reason` | string | 关联原因（来自名录，已定稿） | 清单横条的右段 |
| `evidence[]` | `{title,url,grade}` | 证据链接 | 悬停/展开，不占版面 |
| `images[]` | string[] | 仓库相对路径 | 主图轮播 |
| `image_count` | number | = `images.length` | 右下角 `1 / N` |
| `image_state` | `ok` \| `missing` | 缺图标记 | 缺图时显示占位并标灰 |

**颜色不写进数据**：层级到颜色的映射在样式层（v3 §3「层级配色」），数据只给轴名。

---

## 4. `s2-analysis.json`

```jsonc
{
  "fixture": "s2-analysis", "version": "1.0",
  "schema_ref": "docs/superpowers/specs/2026-10-31-analysis-schema-design.md",
  "slots": ["grille","bumper","side_guard","wheel_arch","step"],
  "slot_labels": { "grille": "进气格栅", … },
  "vehicles": [
    {
      "id": "v1", "name": "德龙 X3000", "brand": "陕汽", "configuration": "6×6 沙漠越野",
      "style_tags": [ {"tag","cluster","evidence"} ×3 ],
      "views": [
        { "id": "v1-m1", "view": "hero_lf", "image": "data-test/ab-images/…/1.jpg",
          "analysis": { "unit": {…}, "parts": [ … ], "unplaced": [] } }
      ]
    }
  ]
}
```

### 4.1 `analysis` 就是真实 schema，不另立字段

`unit` 与 `parts` 完全按分析 schema §2.1 / §2.2：`term / aliases / part_family / family_reason / visible / bbox / form / cmf / intent`，`bbox` 为 0–1000 归一化坐标。**不要**在 fixture 里加"给 UI 用的简化字段"——页面自己派生。

### 4.2 部件行的四态由页面派生（数据里不存）

| 状态 | 推导规则（对当前视角 / 当前车） |
|---|---|
| 已框定 | 当前 view 有该 slot 的 `bbox` |
| 本图可见·待框选 | `visible != not_visible` 且当前 view 无 `bbox` |
| 在图 N 框选 | 当前 view 不可见，但同车其它 view 有 |
| 本图不可见 | 所有 view 都是 `not_visible` |

v3 §4.3 的语义以此为准；四态是**视图状态**，不进 JSON。

### 4.3 `not_visible` 必须真为空

`term / form / cmf / intent` 一律 `null`，`bbox` 为 `null`。schema §2.2 的硬规则：看不见不许命名，不能拿常识补全。fixture 里 `解放 JH6` 的 `side_guard` 就是三视角全不可见的样例。

### 4.4 派生字段（页面算，不存）

- CMF 展示串：`${cmf.material_class} · ${cmf.finish}`；
- 风格三词：直接取 `style_tags[].tag`（已保证三簇不重）；
- 胶片条计数：`views.length`、`views[].image`。

---

## 5. `s3-report.json`

```jsonc
{
  "fixture": "s3-report", "version": "1.0",
  "meta": { "category": "沙漠牵引车", "aspect": "16:9", "total": 12, "title": "…" },
  "pages": [
    { "id": "p01", "type": "cover|method|car|overview|back",
      "title": "沙漠牵引车", "subtitle": "竞品设计分析 · 2026 年 11 月",
      "status": "full|thin", "blocks": [ … ] }
  ]
}
```

页面结构与页序按 v3 §5.2：封面 / 方法 / 8 车型 / 总览 / 封底 = 12 页。

`blocks[]` 的 `kind`：

| kind | 字段 | 渲染 |
|---|---|---|
| `text` | `text` | 文本块（标题、副标题、判断句） |
| `tags` | `items[{term,evidence}]` | 风格三词 |
| `image` | `src` | 主图 |
| `grid` | `items[{term,cmf}]` | 2×2 部件裁图（构型名＋CMF） |
| `note` | `text` | 备注/占位说明 |

`status: "thin"` 表示该页只有标题与占位（本轮 5 台车未做部件分析），用于同时验证"满配页"与"缺项页"的排版，**不要**当成缺陷。

---

## 6. 文案规则（不在此重复定义，只指路）

| 规则 | 出处 | 执行者 |
|---|---|---|
| 六条文风（≤30 字/句、禁框架句、每槽 ≤2 句、intent ≤1 句、数字标（估）、禁空评价） | 分析 schema **§5** | prompt + `analysis.validate_analysis` |
| region / part 字段与 `not_visible` 空值 | 分析 schema **§2.1 / §2.2** | 同上 |
| 部件族判定（主体定族，装配只进 form） | 分析 schema **§3** | 同上 |
| 构型名必须来自词表 | `data/part_taxonomy.json` | `validate_analysis` 的 `term_off_taxonomy` |
| 风格三词：三簇不重、跨车去重、必须给 evidence | `data/style_vocabulary.json` 的 `rules` | `validate_analysis` |
| 关联散文四层顺序与写作约束 | v3 **§9**（含正本） | 本 fixture 的 `analysis.prose` 直接采用正本 |
| 12 栏版式 | v3 **§12** | `docs/ui-mock/v4/` |

---

## 7. 生成与校验

```bash
PYTHONPATH=src python scripts/make_ui_fixtures.py
```

脚本做的事：

1. 从 `data-test/evals/sample-association-list-desert.json` 取名录目标、关联轴、理由、证据；
2. 从 `data-test/ab-images/manifest.json` 按型号名匹配**一台车一个目录**，最多取 4 张；
3. 从 `data/part_taxonomy.json` 取构型名与默认族，从 `data/style_vocabulary.json` 取风格词；
4. 把每台车每个视角拼成 schema 结构，逐个调用 `analysis.validate_analysis(...)`；
5. 任一视角不通过、或构型名不在词表，脚本**以非零码退出**——fixture 不合格。

因此"数据是否合规"不靠人肉检查，重跑脚本即可。

---

## 8. 与真实后端对接时的替换点

| fixture 字段 | 真实来源（待恢复） |
|---|---|
| `s1.analysis.prose` | 关联分析生成器（四层结构） |
| `s1.cards[].reason / evidence` | 名录 + 检索证据链 |
| `s1.cards[].images` | `assets` 表（`view_angle` 分组） |
| `s2.vehicles[].views[].analysis` | `scripts/analyze_batch.py` 产出 |
| `s2...bbox` | 分析时由模型给出，或用户在 S2 里框选后回写 |
| `s3.pages[].blocks` | `scripts/build_report_page.py --dump-blocks` |

字段名保持不变；页面只依赖上面这些键。缺图时用 `image_state: "missing"`，不要删数组。

---

## 9. 已知缺口

1. `s3` 的 12 页里，5 个车型页是 `thin`（无部件分析），补齐需先恢复数据库并跑 `analyze_batch`；
2. 数据库为空这件事本身没修（`db/schema.sql` 在，数据要 ingest），fixture 只是绕开它；
3. 真实链路尚未产出过 `analysis-<date>/*.json`（git 历史中从未提交），所以 fixture 的字段宽度是"按 schema 推导"的，不是"从真实产物抄的"。恢复链路后应重跑一次并对比字段。
