# Platform 层盲评结果

## 标注

pending accepted 33 张：

- 是目标车：29
- 不是：2（v1/v2，360 的 TAZ4413）
- 不确定：2（v4/v15）

并入旧标签后，union accepted 49 张：

| 平台 | accepted | 目标 | 不是 | 不确定 | precision |
|---|---:|---:|---:|---:|---:|
| 360 | 15 | 12 | 2 | 1 | **80.0%** |
| Baidu | 34 | 32 | 1 | 1 | **94.1%** |
| Bing | 0 | 0 | 0 | 0 | — |
| **union** | **49** | **44** | **3** | **2** | **89.8%** |

排除 uncertain：

- 360：12/14 = 85.7%
- Baidu：32/33 = 97.0%
- union：44/47 = 93.6%

## target 级

union 有 9 个 target 出现 accepted：

- 其中 8 个至少有 1 张目标图；
- **1 个是假阳性 target**：M1 HOWO TAZ4922，只有 360 的两张 TAZ4413 错图。

所以：

- union target 覆盖 9，但**正确 target 覆盖 8/23**；
- 360 单独 5 个 target，其中 TAZ 那个是错的，正确 4；
- Baidu 单独/联合覆盖 8 个 target，precision 看起来最好。

## 结论

1. Platform 层有实质增量信号：Baidu 补了 360 没有的 target，且 accepted precision 94.1%；
2. 但这是 **候选级 probe**，query 固定 class query，不是 normal 完整 loop；
3. 下一步可以做一个 **完整 loop 对照**：360 vs 360+Baidu，其他参数完全一致；
4. 不混 query/guard；normal 仍不改，直到完整 loop 通过。
