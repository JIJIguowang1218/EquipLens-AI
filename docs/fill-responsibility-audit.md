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
| VERIFY | 三证核验（身份/可见性/原厂）；不通过不占槽 |

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
