# FILL 职责审计：overview 不该塞回 fill

日期：2026-11-12

## 结论

用户的质疑成立：**overview/整车资格不是 FILL 的原始职责**。  
P0 把 scene/overview 规则塞进 `_state_fill`，是职责错位，不应作为长期架构。

## 原职责（文档）

`docs/retrieval-state-machine.md`：

| 状态 | 目的 |
|---|---|
| FILL | **占槽/备选/族去重** |
| VERIFY | **身份核验**（confirmed/probable/unknown）；不通过不占槽。（② 可见性 / ③ 原厂已归档，见 `docs/killed-strategies.md` K1/K2） |

FILL 只应该消费“哪些 target 有资格”，不应该自己判断“图是整车还是局部”。

## 现在哪些模块涉及

| 模块 | 已有什么 | 缺什么 |
|---|---|---|
| `gate.assess_from_gate` | `scene`、`overview_candidate`、`part_candidate` | 没有变成交付资格；只是标签 |
| `RuleVerifier` | 标题/型号/构型 | 不看 scene/overview |
| `_state_fill` | 占槽、配额、priority/role、asset 去重 | 不是 scene 判断的正确位置 |
| `render_fetch_audit` | 展示 | 只展示，不决定 |
| analysis | 部件分析 | 不参与检索占槽 |

所以不是“已有模块接管了”，而是：

> **scene/overview 的计算在 gate，但“整车交付资格”这个决策没有归属。**

## 正确分层

1. **gate/VERIFY**：计算 `delivery_scope = overview | part | reference`；
2. **Verification/Asset**：携带这个资格；
3. **FILL**：只消费资格 + 配额 + priority + 去重，不重新看 scene；
4. **UI/audit**：显示 part-only，供人审；
5. **产品策略**：决定 part-only 是否允许占主槽/备选。

## P0 的处理

- 硬 overview 规则已弃用（10/12 或 composition 变差）；
- 当前 `part_only` 只是 **FILL 里的临时标记**，不是最终架构；
- 后续应把该判断上移到 VERIFY/gate，FILL 只读结果；
- 在迁移前，不宣称 part-only 已解决。

## 教训

- 新增交付规则前，先查 `docs/retrieval-state-machine.md` 的职责表；
- 不要把 gate 的语义标签直接塞进 fill；
- 新字段/新规则必须有生产路径测试；
- 文档/索引要同步，但不能替代职责边界。

## 附：scene 标签到底怎么来的

- 模型：UForm3 image-text english small，本地 CPU，零样本；
- 标签只有 3 个：single_vehicle / multi_vehicle / part；
- `SCENE_LABELS` 与图片算相似度，取 max，没有阈值、没有部件检测器；
- gate 的 keep 标签里**故意保留部件特写**，所以 part 图可以过门卫；
- 视角分类更弱（top1-top2 中位数 ~0.003），只作提示。

因此 scene=part 不是“可靠部件识别”，只是三个英文文本标签的竞争结果。  
把它当整车交付硬门槛，会误杀；把它当审计提示，仍有用。  
当前产品以整车为主，但现有 gate 并没有强制“必须有整车图”；它只是允许部件图，且 fill 从未消费 scene。

## 结论更新

- scene 不是“被现有筛除机制吞没”，而是**从未接入交付**；
- 作为交付硬规则，它落后且不可靠；
- 作为 audit/warning 可以保留；
- 不应再往 FILL 堆 scene 规则；如果产品需要整车资格，应在 VERIFY 做可靠的整车判定，或继续人审。

## 澄清：标签一直存在，缺的是“消费标签的策略”

之前说“没引入 scene”不准确。准确说法：

- gate 一直计算 `scene`，并在 fetch_log/audit 中可见；
- `gate.assess_from_gate` 也计算了 `overview_candidate/part_candidate`；
- 但 `live_fetch` 对 gate-pass 图**全部建 Asset**，不检查 `overview_candidate`；
- `_state_verify` 只看身份/构型；
- `_state_fill` 只看 accepted，不读 scene；
- 所以标签存在，但没有进入交付选择。

`multi_vehicle` 也一样：gate 里会限制 candidate 标志/给 hint，但 fill 不消费。
这不是“标签没算”，是“标签到交付的线没接”。
