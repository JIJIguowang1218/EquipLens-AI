# Recovery / 扩源策略收口（2026-11-12）

> **2026-11-12 追加**：交付不足**不得**用换源/扩源解决；先降级交付（probable/unknown、低清、泛称 + degraded）。
> 本节"如果以后重开"仅作为流程记录，**当前不批准重开**。

## 结论

**停止继续叠 recovery 策略；不接入生产；normal run 不改。**

## 这条线属于哪一层

当前 recovery 实验 = **Query 层 + Source 层**，不是 Platform 层：

| 层 | 做了什么 | 状态 |
|---|---|---|
| Query | alias query、类目词 query、model core | 已测；class vs alias 不显著（p≈0.726） |
| Source | 360 搜索结果 + 回访文章/图集 harvest | 已测；能提量，但身份/车身错误多 |
| Platform | 百度/必应/官网/出口商等新平台 | **未测** |

“整车槽/去重/overview”属于交付策略，不是扩源层级。

## 为什么不继续

- class query precision 77.8% vs alias 69.6%，Fisher p≈0.726，不显著；
- C-aerial holdout 0/6，没有泛化证据；
- body/tonnage hard guard 误杀 8 张目标图；
- 多车型标题只 1 例，不值得专门规则；
- 继续加策略的误杀风险 > 边际收益。

## 不做什么

- 不上线 class query；
- 不上线 body/tonnage guard；
- 不写多车型标题专用规则；
- 不为单个品牌/车型加 query 或来源规则；
- 不把 harvest 接进 normal run。

## 如果以后重开

只允许一个变量、预注册：
- 目标层：Platform（新平台/官网），不要再混 Query/Source；
- 样本：8–10 brief / 150–250 图 / ≥2 holdout；
- 指标：accepted precision、target recovery、overview 率、成本；
- 先定阈值，不通过就停；
- 不叠加 guard/query 规则。

## 接下来建议

1. 收口这条线，保留数据/脚本/结论；
2. 回到正常产品线（normal run 不动）；
3. 若业务明确需要扩源，下一步只做 **Platform 层可行性**，先验证 1 个新平台，不做多平台大而全。
