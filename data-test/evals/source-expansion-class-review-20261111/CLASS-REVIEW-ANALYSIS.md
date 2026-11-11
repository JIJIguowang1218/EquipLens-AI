# 类目词 query 盲评 33 张（v19–v21 已更正）

## 更正后标注

| 判断 | 33 张 |
|---|---:|
| 是目标车 | 26 |
| 不是 | 7 |
| 不确定 | 0 |

accepted 18 张：

- 是目标车：14
- 不是：4（v1 + v19/v20/v21）
- **precision = 14/18 = 77.8%**

## 与 alias query 对比

| 指标 | alias query | class query |
|---|---:|---:|
| accepted | 23 | 18 |
| accepted 目标 | 16 | 14 |
| precision | 69.6% | **77.8%** |
| target accepted | 8 | 7 |
| target overview | 1 | 2 |

Fisher exact（14/18 vs 16/23）：**p ≈ 0.726**，差异不显著。  
所以不能因为 77.8% > 69.6% 就认为 class query 更好；样本太小。

## 残余错误

- v1：标题同时含 Zetros/Arocs，图是 Arocs；多车型文章误收。
- v19–v21：用户原标目标，复核为误标；CR330E/CR240E 不是矿山霸王。
- 目标图 unknown：26 张目标图里 14 张 accepted，12 张 unknown；但这是抽样，不是总体 recall。

## 结论（按“不要堆策略”原则）

1. **不新增多车型标题规则**：v1 只有 1 例，不显著。
2. **不新增车身/吨位硬 guard**：之前已证明误杀。
3. **不因为 class query 77.8% 就上线**：与 alias 差异不显著，C holdout 仍 0。
4. 当前 recovery 保持实验状态；normal 不变。
5. 如果还要继续，只做一次 **预注册 confirmation**（8–10 brief / 150–250 图），不再加策略；否则停止这条优化线。
