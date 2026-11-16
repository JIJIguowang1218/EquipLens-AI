# Router 标签口径与冲突审计（2026-11-17）

> 目的：P3 之前先固定“每个标签到底指什么、什么时候不用”，避免重标/测试集内部互相冲突。
> 标签集合以 `src/equiplens/session.py::ALLOWED_TARGETS` 为准；本文件只定义口径，不新增标签。

## 1. 规范定义（按使用频率）

| 标签 | 只用于 | 不要用于 |
|---|---|---|
| `plan.quantity` | **总量**：总共/一共/总数、数量改成/调到 N | 每款张数、同一台车补图 |
| `plan.quantity_per_model` | **每款/每台**图片数：每款 6 张、从 4 调到 6、不够补到 N | 总量、同车补图 |
| `fill.quota` | **同一台车/同款/已出现型号**要更多图（无显式总数） | 新品牌/新车型、总量 |
| `plan.add_targets` | 增加**新品牌/新车型/新车系** | 只改构型、只补同款图 |
| `plan.negative` | 排除品牌/车型/属性/场景偏好（硬约束） | 范围比例、构型切换、能力外 |
| `scope.ratio` | 范围/类目/精确-邻近比例/“只看某类” | 单纯排除某品牌、构型 |
| `plan.configuration` | 驱动/构型/高顶平顶/双备胎/涉水喉等配置 | 部件细节图、单张图纠错 |
| `fetch.filters.views` | 拍摄角度（正脸/侧面/45°/车尾/顶部/内饰视角） | 部件细节、场景 |
| `fetch.parts` | 具体部件细节图（格栅/大灯/保险杠/吊臂/支腿/底盘/悬挂） | 构型配置、普通视角 |
| `fetch.filters.quality` | 清晰度/分辨率/糊/翻拍/屏幕反光等**画质要求** | 水印/印刷/天气/原图（能力外） |
| `verify.blacklist` | 单张图**身份/型号不对**、不能进交付 | 普通“删一张”、画质差 |
| `delivered.remove` | 从交付**移除/降级**某张或某批，不要求补新图 | 替换、身份拉黑 |
| `delivered.replace` | 用新图**替换**已交付的某张 | 只删除、只拉黑 |
| `fill.replace` | **过渡标签**：补位替换（空位/缺图） | 新标注不再使用；等价语义优先 `delivered.replace` |
| `delivery.report` | 生成/更新报告、PPT、页面结构 | UI 操作问题（→ guide）、版式超默认（→ explain） |
| `session.pause` / `resume` | 暂停/继续当前 run | 附带修改（必须同时出修改标签） |
| `session.reset` | 整批重来/全部重新选 | 删除单张/单批 |
| `action=guide`（非 target） | 界面已有功能，用户问“在哪/怎么操作” | 系统做不到（→ explain） |
| `action=explain`（非 target） | 能力外/越界/版式超默认 | 能做但用户没说清（→ clarify） |

## 2. 已知冲突与裁决

### 2.1 数量四义
- 显式总数/凑够 N → `plan.quantity`；
- 每款/每台张数 → `plan.quantity_per_model`；
- 同款/这台/型号代码 + 加图（无总数）→ `fill.quota`；
- 新品牌 + “图也多来几张” → `plan.add_targets` + `fill.quota`（给新 target 补图）。
- **冲突裁决**：显式总数 > 每款张数 > 同车补图；一句话同时出现时最多保留两个，按执行顺序。

### 2.2 交付编辑四标签
- 明确第 N 张 + “换” → `delivered.replace`；
- “删/去掉/不要了” → `delivered.remove`；
- “不是这个型号/错了/不能进” → `verify.blacklist`（是否补图由后续决定）；
- “补一张/补位” → 用 `delivered.replace`；`fill.replace` 仅兼容旧数据。
- **冲突裁决**：身份错优先 blacklist；明确替换优先 replace；“删了再补”= remove + replace 两个动作（或 replace + replenish）。

### 2.3 范围 / 排除 / 构型
- “只要沙漠版，普通版不要” → `scope.ratio` + `plan.negative`（范围 + 排除）；
- “8x8 不要，只要 6x6” → `plan.configuration` + `plan.negative`；若“要补 6x6 型号”→ 再加 `plan.add_targets`；
- “高顶的，平顶不要” → `plan.configuration` + `plan.negative`；
- “6x6 换 8x8” → `plan.configuration`，不加 negative。

### 2.4 部件 / 视角 / 配置
- “大灯特写/底盘细节图” → `fetch.parts`；
- “要正脸/45 度/内饰视角” → `fetch.filters.views`；
- “双备胎/涉水喉/高顶” → `plan.configuration`；
- **冲突裁决**：出现“细节图/特写”优先 parts；出现配置词且无图 → configuration。

### 2.5 报告 / UI / 能力外
- “PPT 在哪导出/格式按钮在哪” → `action=guide` + UI 位置，不产生 patch；
- “出 PPT/加一页竞品对比” → `delivery.report`；
- “每款两页/换封面/加目录”（超出默认一车一页）→ `action=explain`；
- 水印/印刷/天气/原图/周报 → `action=explain`（unsupported/out_of_domain）。

### 2.6 暂停 + 附带要求
- “先停一下，等我把品牌加上” → `session.pause` + `plan.add_targets`；
- 暂停**不吞掉**修改；修改存 `pending_on_resume`，恢复时确认。

### 2.7 整批 vs 单张
- “全部重来/整批重新选” → `session.reset`；
- “删掉第 2 张/去掉一张” → `delivered.remove`。

## 3. 标签卫生规则

1. 新测试集只用上表主标签；`fill.replace` 不再新增，仅兼容旧数据；
2. 一个动作一个标签；复合最多 3 个，按执行顺序；
3. 同一句不要既写 `delivered.remove` 又写 `delivered.replace`，除非明确“删了再补”；
4. 能力外/UI 引导用 `expect_feasibility` / `expect_action` 表达，不塞进 target；
5. 任何标签冲突先按 §2 裁决；无法裁决 → `clarify`，不硬猜。

## 4. 现有 holdout 的冲突处理（2026-11-16 重标）

- #17：`plan.negative + plan.add_targets`（当前漏 add，BC-S4-010）；
- #18：`scope.ratio + plan.negative`；
- #27/#47/#63/#97：`verify.blacklist`（允许 `delivered.remove` 等价）；
- #34/#37：`plan.quantity_per_model`；
- #43：`delivered.replace` + 需确认；
- #55：`plan.quantity`；
- #56：`plan.negative + plan.configuration`；
- #67：`delivered.replace`（不再拆画质）。
