# 标题 code 不一致 prefilter：离线影响评估

规则（仅在 target 为 code 类型时）：

- target 有 code；
- 标题有 code；
- 标题 code 中没有 target code → 拒绝下载；
- 标题无 code / 多 code 含目标 / generic target → 不拒绝。

## 过去 run 的离线模拟

| run | code target 数 | 丢失 target | 被移除 accepted assets |
|---|---:|---:|---:|
| intent-test3 | 6 | 0 | 5/20 |
| generic-test | 8 | 0 | 5/29 |
| platform 360 | 6 | 0 | 3/21 |
| platform Baidu 未预筛 | 5 | 1（TAZ4922，且是 TAZ4413 错图） | 2/11 |
| platform Baidu 预筛后 | 6 | 0 | 6/24 |

被移除的 accepted 例子：

- 天锦 `DFV2223GP6DJ` 接受 `DFV2163GP6D1` → 明确不同型号；
- ND5250 接受 `T105/WTC5141` → 明确不同型号；
- TAZ4922 接受 `TAZ4413` → 明确不同型号。

## 与 `_relevant` 的关系

- `_relevant` 是下载前的宽松护栏（品牌/车型词/构型）；
- code prefilter 只在“双方都有 code 且不一致”时拒绝；
- 有重叠，但 code prefilter 能抓住 `_relevant` 放过的同品牌不同型号；
- 风险：
  - 多车型标题/变体 code；
  - 标题 code 是别名/系列；
  - target code 抽取错误；
  - 标题 code 不是目标但图其实是目标。

## 结论

- 当前样本中，code prefilter **没有丢失真 target**；只移除 accepted 的错型号；
- 但样本小，且依赖 code 抽取；
- 建议作为**独立 prefilter**验证，不和平台/guard 混一起；
- 先离线/小样本，再决定是否进 normal。
