# code prefilter 完整 loop 对照（360，独立于 Platform）

同一 M1 brief / plan / 12 槽，唯一变量：`--code-prefilter`。

| 指标 | 360 baseline | 360 + code prefilter |
|---|---:|---:|
| 交付 | 12/12 | **12/12** |
| fetch 行 | 324 | 324 |
| gate pass | 264 | 256 |
| verifications | 256 | 248 |
| accepted | 236 | 224 |
| unknown | 20 | 24 |
| degraded | 8 | 8 |
| 交付构成 | 12 台 | **完全相同 12 台** |

## 结论

- code prefilter 在完整 loop 中**没有丢失任何交付 target**；
- 它移除了 12 张 accepted 的同品牌错 code 图（accepted 236→224）；
- gate/unknown 小幅变化；
- 核心交付构成不变，说明它是**低风险的精度 prefilter**，不是会换车的策略。

## 规则边界

只在：
- target 是 `identity_kind=code`；
- target 有 code；
- 标题有 code；
- 标题 code 中没有 target code

时拒绝。标题无 code / 多 code 含目标 / generic target 都不拒。

## 未验证

- 被移除的 12 张 accepted 是否全部是错图（需要人工标签）；
- 但过去 run 的模拟中，移除例子都是 DFV2223 vs DFV2163、ND5250 vs T105 等明确不同型号；
- 当前无“真 target 被拒”的证据。
