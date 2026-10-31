# 分析模块（L5）设计稿 v0.1

- 日期：2026-10-31
- 状态：待产品负责人审阅
- 上游：`docs/architecture-discussion.md` §2（统一分析 schema 三维度）、`docs/data-model-spec.md`（Descriptions 即分析输出）、`docs/PRD.md` 附录 A/B
- 下游：报告规划与排版模块、Web 交互层

## 1. 目标与边界

**目标**：给定一台车的主图（人已确认）+ 指定部位清单，产出可直接进"一车一页"的结构化分析。

**做**：区域级风格判断（前脸/侧面）、部件级四槽分析、风格三词、证据锚定、简洁文风、机器可校验。

**不做**：跨车对比结论、趋势判断、类型学归纳、报告排版（下一模块）、多视角融合（v0.2）。

**成功判据**：单台车的输出满足"三个一眼"——一眼看出是这台车、一眼能让设计师改、一眼能追溯到图上的位置。

## 2. 核心契约：一个对象，两种形态

分析单元只有两种，互斥且字段不混：

| | `region`（区域） | `part`（部件） |
|---|---|---|
| 定义 | 连续曲面，无分缝可拆，边界靠视觉划分 | 有分缝、有装配关系的独立件 |
| 例 | 前脸整体、侧面、后围、顶盖 | 保险杠、防护栏、轮拱、踏步、格栅 |
| 字段 | gesture / character_lines / proportion / cmf / judgement / style_tags | term / aliases / part_family / form / cmf / intent |
| 报告呈现 | 压在主图上的引线标注 | 独立裁图 + 文本框 |

**关系而非第三类**：`region.members[]` 指向其下的部件槽。前脸是 region，成员是格栅/大灯/保险杠/品牌区——不新增 `assembly` 分类，避免每台车都要纠结"算不算总成"。

### 2.1 region 对象

```json
{
  "slot": "front_face",
  "kind": "region",
  "members": ["grille", "headlamp", "bumper", "brand_zone"],
  "gesture": "一句 ≤30 字",
  "character_lines": ["2–3 条，每条 ≤30 字，写清从哪到哪"],
  "proportion": "一句；可给估读比例并标（估）",
  "cmf": "一句",
  "judgement": "一句 ≤30 字",
  "style_tags": [
    {"tag": "厚实", "cluster": "stability", "evidence": "≤20 字，回指图形"}
  ]
}
```

### 2.2 part 对象

```json
{
  "slot": "bumper",
  "term": "整体式保险杠",
  "aliases": ["一体式前包围"],
  "part_family": "sheet_metal",
  "family_reason": "引用图上证据的一句话",
  "visible": "full",
  "bbox": [88, 573, 333, 755],
  "form": "≤2 句",
  "cmf": {"material_class": "", "finish": ""},
  "intent": "≤1 句，因果最多两级"
}
```

`visible ∈ {full, partial, not_visible}`；`not_visible` 时 `term/form/cmf/intent` 必须为 null，**不许用常识补全**。若确实需要先记一个目标构型，只能写进 `expected_term`（不参与对比矩阵）。

`bbox` 为 0–1000 归一化坐标。

> 规则来源：2026-10-31 第三次探针中，`side_guard` 判 `not_visible` 却仍给了具体构型名「型钢侧防护栏」——看不见却命名，等于用常识补全，立即封堵。

## 3. 部件族判定

**一句话规则：主体构成定族，装配关系只进 form。**

| 族 | 判据 | 典型 |
|---|---|---|
| `sheet_metal` | 连续板面，有折边/冲压/分缝 | 保险杠、轮拱、面罩 |
| `frame_profile` | 杆件或型材框架，节点可见 | 防护栏、爬梯、桁架 |
| `cast_forged` | 铸锻/机加实体，有拔模或加强筋 | 桥壳、轮毂、吊钩 |
| `function_attachment` | 独立功能件，挂装可拆 | 踏步、大灯、后视镜 |

v0 曾出现"格栅因独立嵌入被判 function_attachment"的漂移（2026-10-31 实测），本规则用于消除该歧义：格栅主体是板面 → `sheet_metal`。

## 4. 数据资产（两个词表）

| 文件 | 内容 | 谁维护 |
|---|---|---|
| `data/part_taxonomy.json` | 槽位定义、region 成员、每个槽允许的构型名 + 别名 + 适用条件 | 设计师可改 |
| `data/style_vocabulary.json` | 6 簇 42 个风格词 + 每簇适用条件 | 设计师可改 |

**term 必须命中词表**；命中不了则 `term=null` 并进 `unplaced`，附 `suggested_term`。**不许自造构型名**——这是跨车对比矩阵能对齐的前提。

## 5. 文风契约

六条硬规则（写进 prompt + 由校验脚本检查）：

1. 一句一个判断，句长 ≤30 字（region 的 gesture/judgement/character_lines、part 的 form/intent）
2. 禁用框架句：「由……构成」「通过……实现」「呈现出」「值得注意的是」「不仅……而且」
3. 术语直接用，不解释
4. 每槽 ≤2 句；intent ≤1 句，因果最多两级
5. 数字只在能估读时给，并标（估）
6. 禁空评价（整体感强/大气/很有质感/彰显）——换成可指认的图形

**不给「其它」字段**。装不下的信息进 `unplaced[{text, reason_not_fit, suggested_slot}]`，不进正文，只做缺口统计。分类可以兜底（PRD 附录 B 已有"其他（待补充）"），描述不能兜底。

## 6. 风格三词与跨车去重

- 每台车 **恰好 3 个**，来自词表，**分属 3 个不同簇**
- 每个词必须带 `evidence`，回指图上可指认的图形（线条/孔阵/分割/折角/比例）
- **去重是确定性的，不靠提示词**：
  1. 生成第 N 台时，把"本报告已用词"注入提示词
  2. 生成后校验：同簇重复、跨车复用 → 拒绝重生成
  3. 报告级均衡：各簇使用次数 `max - min ≤ 1`

**复用价值**：三个词同时供单车页页眉与竞品总览页（主图 + 型号 + 风格词 + 主色条），一次生成两页受益。

## 7. 生成流程与 provider 抽象

```
intent(车 + 部位) → 取主图 → prompt 组装(词表+已用词+文风规则) → provider → analysis.json → 校验 → 落库
```

provider 三态，契约一致，切换只改配置：

| provider | 用途 | 状态 |
|---|---|---|
| `api` | 真实 VLM（当前 `deepseek-flash`，image 输入） | ✅ 已实测 |
| `mock` | 固定夹具，跑单测/CI，零成本 | 待建 |
| `manual` | 人工/AI 助手回填，冷启动与金标产出 | 机制已有先例 |

**密钥纪律**：只从 `.env` 或运行时环境变量读；`.env` 已被 `.gitignore` 覆盖；**不得 COPY 进镜像、不得进前端**。

## 8. 校验（check_analysis）

schema 校验之外，必查项：

- region/part 字段互斥（region 不许有 term，part 不许有 gesture）
- term ∈ 词表；part_family ∈ 四族；`visible=not_visible` 时描述字段为空
- style_tags：数量=3、簇互异、词在簇内、evidence 非空、不与已用词冲突
- 句长与禁用词扫描
- bbox：数量 4、范围 0–1000、区域内可见性一致

校验失败 → 记录原因 → 重生成一次（带失败原因）→ 仍失败则进 `needs_review`，不阻塞整批。

## 9. 实测记录（2026-10-31，探针，非产品代码）

| 项 | 结果 |
|---|---|
| 模型 | `deepseek-flash`，image 输入可用 |
| 单台成本 | 约 4,000–7,000 tokens，一次调用 20–40 秒 |
| JH6 | 通过：三词 厚实/硬朗/规整；5 部件全出；踏步 `not_visible`，未编 |
| 欧曼银河 | 通过：三词 敦实/刚直/数字感；跨车零复用 |
| 发现 | ①「数字感」借词错配 → 词表 v0.2 已加 guidance 并换词 ②构型名两次跑不一致 → 需词表化 ③族判定漂移 → 已收紧规则 ④两台车踏步均判 partial → 侧视补证列为 v0.2 |

## 10. 渲染契约（供下一模块）

一车一页的数据形态：

```
page = {
  header: {brand, model, style_tags[3], brand_color},
  hero: {asset_id, view},
  annotations: [region 的 character_lines → 主图引线],
  parts_grid: [{crop_asset_id, term, form, cmf, intent}] × 3–4,
  footer: {model, source}
}
```

`parts_grid` 的图来自裁图（只从原图裁，不从裁图再裁，遵守 `data-model-spec` D1）。

## 11. 验收

| 指标 | 目标 |
|---|---|
| schema 校验通过率 | 100% |
| 三词合规率（数量/簇/词表/evidence） | 100% |
| 跨车重复率（14 台车 42 词） | 0 |
| `not_visible` 诚实率（人工抽查） | 100%（宁可空缺，不许编） |
| 人工可读性（设计师 5 分制） | ≥4 |
| 单台耗时 | ≤60 秒 |

## 12. 未决

1. **可见性稳定性**：同一张 JH6 主图三次运行，`step` 分别被判 `not_visible` / `partial` / `full`。需要在实现期定：低温度/固定 seed、`full` 需人工抽检、或把可见性判定降级为"建议值 + 人工确认"。
2. 侧视补证（v0.2）：主图 `partial/not_visible` 时是否自动拉同车侧视图
3. 跨车对比结论页是否属于本模块（当前判定：不属，归报告规划）
4. 词表是否开放设计师自定义（当前：可改 JSON，但需版本号与变更记录）
