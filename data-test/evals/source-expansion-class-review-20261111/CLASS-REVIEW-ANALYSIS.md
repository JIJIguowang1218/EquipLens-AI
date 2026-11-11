# 类目词 query 盲评 33 张

## 标注

| 判断 | 33 张 |
|---|---:|
| 是目标车 | 29 |
| 不是 | 4 |
| 不确定 | 0 |

accepted 18 张：

- 是目标车：17
- 不是：1（v1 Arocs/Zetros 多车文章，图是 Arocs）
- **raw precision = 17/18 = 94.4%**

## 需要复核的标签

v19–v21 标为“矿山霸王 70T 是目标车”，但标题是：
- `中车大同 CR330E 矿用自卸车`
- `中车大同 CR240E 高原型电传动矿用自卸车`
- `巨无霸矿用自卸车大盘点`

它们不是 HOWO 矿山霸王。如果这 3 张实际不是目标，class query accepted precision 应为 **14/18 = 77.8%**，仍需你确认。

## 与 alias query 对比

| 指标 | alias query | class query |
|---|---:|---:|
| 盲评 accepted | 23 | 18 |
| accepted 目标 | 16 | 17（raw） |
| precision | 69.6% | **94.4% raw / 77.8% 调整后** |
| target accepted | 8 | 7 |
| target overview | 1 | 2 |

类目词 query 的 **precision 明显更好**，target accepted 只少 1 个；但样本小，且 v19–v21 标签待复核。

## 主要残余错误

v1：

- 标题同时提到 `Zetros` 和 `Arocs`；
- 图是 Arocs，不是 Zetros；
- 标题里有目标词，所以 verifier accepted。

这是**多车型文章/封面图**问题，不是车身类型 guard 能解决的；需要图文对齐/视觉核验，或对“标题含多个车型”降级。

## 结论

1. **类目词 query 保留为候选策略**：precision 优于 alias，overview 2 vs 1；
2. 不上 body/tonnage 硬 guard；
3. 下一步优先处理：
   - 多车型标题/封面图（v1）；
   - unknown 目标图 recall（12 张目标图在 sample 内 unknown）；
   - v19–v21 标签复核。
