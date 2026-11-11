# 360 + Baidu 互补设计（评估，不实现）

## 目标

360 为主体；只对 **preferred target 未占槽** 的情况，用 Baidu 做定向补位，不做全量 union。

## 机制

1. 先跑 normal 360 loop；
2. 找出 primary/preferred target 中未占槽的；
3. 只对这些 target 发起 Baidu 定向查询（同 query，先过 `_relevant` + code prefilter）；
4. 若 Baidu 有 accepted 证据：
   - 替换最低优先级的 accepted target（backup/pool），
   - 不挤掉已占槽的更高优先级 target；
5. 若没有证据，保持原交付。

## 现有数据支持

- 360 baseline 缺 rank2 泰安、rank4 沙漠越野；
- Baidu（未预筛）曾 accepted rank2/4；
- 360 已有 rank6 HF8066；
- 因此“360 主体 + Baidu 补 rank2/4”理论上可得到更完整的 top12，而不是像 union 那样丢 HF。

## 风险

- Baidu 补位图可能错；必须 verifier + code prefilter + 人工抽样；
- 替换策略会影响已交付 target，需要明确“只替换低优先级 backup/pool”；
- 需要 run-level 记录 `platform=baidu, reason=backfill`；
- 不能全量 union；不能默认启用。

## 状态

只评估；没有实现，也没有跑完整互补 loop。
