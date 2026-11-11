# 扩源漏斗：同一批 24 个失败 target（去重后 23）

## 阶段计数

| 阶段 | base | expansion |
|---|---:|---:|
| search hits | 28 | 199 |
| URL 重复（全局去重跳过） | 16 | 34 |
| unique URLs | 12 | 165 |
| 下载失败 | 6 | 19 |
| gate 拒绝 | 1 | 53 |
| gate 通过 | 5 | 93 |
| gate 通过但核验 unknown | 5 | 70 |
| 核验 accepted（图级） | 0 | 23 |
| target 级 accepted | 0 | 8 |
| target 级 overview accepted | 0 | **1** |
| target 级 part-only | 0 | **7** |

## 关键结论

1. **base 几乎没产出**：12 个 unique URL，0 accepted；长 plan query 召回很差。
2. **expansion 能搜到很多**：199 hits → 165 unique；但：
   - 19 下载失败；
   - 53 gate 拒绝；
   - 93 gate pass 里 **70 张核验 unknown**；
   - 只有 23 张 accepted。
3. **8 个 target 级 accepted 里，7 个是 part-only，只有 1 个 overview**。
   如果整车槽要求 `scene=single_vehicle`，实际“整车恢复”只有 **1/23**，不是 8/23。
4. 所以 recall 最大漏损在 **核验 unknown**（75/93 gate-pass），其次是 gate（53/165）和下载（19/165）；不是“再搜更多”就能解决。
5. 全局 URL 去重有效：base 16 个重复、exp 34 个重复；不 dedupe 会继续放大重复图和错误统计。

## 人工标注状态

- 93 张 gate-pass 图里：
  - 已有标签：target 29、not 12、uncertain 7、空 1；
  - **pending 44**（新图，尚未人工确认）；
- accepted 的 23 张里：7 张已有“是目标车”，16 张 pending。
- 因此 8/23 的 target 恢复数**不能当最终 precision/recall**；需要补 44 张盲评。

## 下一步

1. 补 44 张 pending 盲评（含 16 张 accepted）→ 计算 accepted precision / target recall。
2. 修 `_state_fill`：整车槽要求 overview，part-only 不得单独占槽。
3. 保留全局 URL/车型去重。
4. 针对 70 张 gate-pass unknown：判定是“标题没证据”还是“不是目标”；再决定核验证据怎么补，不放宽门卫。
5. 不扩大样本，先修这条漏斗。
