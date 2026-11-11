# 360 主体 + Baidu 定向补位：试跑结果

## 设计

- 输入 360 baseline（12/12）；
- 找出未占槽的 primary/backup：
  - rank2 泰安五岳
  - rank4 沙漠越野
- 只对这些 target 走 Baidu，先 `_relevant`；失败后尝试一次“类目+品牌词”fallback；
- 若 accepted，提议替换最低优先级 accepted backup（rank13/14）。

## 结果

两个 target 的 Baidu 定向查询：

- 原 query：0 hits（`_relevant` 过滤后）；
- class/brand fallback：仍 0 hits；
- **没有 accepted 证据**。

原因：

- 长 query 在 Baidu 返回 12 条，但 `_relevant` 全过滤；
- 短 query（如“牵引车 泰安五岳”）能返回目标，但当前 fallback 拼成“牵引车 泰安五岳 油田专用”，仍被过滤；
- 需要更精确的 query 适配/来源页，不是简单补位。

## 结论

- 360+Baidu 定向补位**设计合理，但当前实现没有成功补位**；
- 不能据此说补位无效；需要独立调 query/来源；
- 不能把 Baidu 全量 union 当作补位。

建议下一轮：

1. 固定“360 主体”；
2. 对 missing preferred 用**目标类别 + 品牌短 query**（不是长 plan query）；
3. 只对缺失 target 查 Baidu，过 `_relevant` + code prefilter；
4. 若 accepted，只替换最低优先级 backup；
5. 单独评估，不混 Platform union。
