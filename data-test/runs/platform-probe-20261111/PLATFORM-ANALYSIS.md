# Platform 层 A/B（同一批 23 target，query 固定为类目词）

## 设计

- 23 个失败 target；
- query 固定为 class query（类目词 + model core），不随平台变化；
- 同一门卫/核验；
- 比较 360 / Baidu / Bing / union（去重后）；
- 不改 normal run 参数；只调用平台通道函数。

## 结果（verifier 口径，未人工确认）

| 平台 | hits | gate pass | 图级 accepted | target 级 accepted |
|---|---:|---:|---:|---:|
| 360 | 138 | 94 | 15 | 5 |
| Baidu | 132 | 128 | 34 | 8 |
| Bing | 138 | 14 | 0 | 0 |
| **union** | 408 | 236 | 49 | **9** |

- union target accepted 9，overview 3；
- 360 单独 5 个 target，Baidu 单独 8 个；union 新增 4 个 360 没有的 target：
  M1 泰安五岳、Zetros、Mining King、CT105K；
- Bing 在这批 query 上 accepted=0，暂时无价值。

## 重要限制

- 这是 **Platform 单变量**，query 固定为 class query；不是 normal run 的 plan query；
- 不能直接和 normal run 12/12 对比；normal 是完整 loop/配额/交付，这里是候选级 probe；
- Baidu accepted 34 张，pending 未人工确认，可能 precision 低；
- 33 张 accepted pending 已生成盲评页。

## 下一步

1. 盲评 33 张 accepted，算 360/Baidu/union precision；
2. 若 Baidu precision 可接受，Platform 层保留为候选；
3. 不把 Platform 与 Query/guard 混在一起；
4. normal run 仍不改。
