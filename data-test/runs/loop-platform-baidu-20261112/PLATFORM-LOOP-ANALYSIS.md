# Platform 完整 loop 对照：360 vs 360+Baidu

同一 brief（M1 desert）、同一 plan-ranked、同一 12 槽/配额/gate/verifier；唯一变量是平台通道。

| 指标 | 360（normal） | 360+Baidu |
|---|---:|---:|
| 交付 | 12/12 | 12/12 |
| fetch 行 | 324 | 608 |
| 下载成功 | 284 | 508 |
| 过门卫 | 264 | 452 |
| 唯一 sha1 | 69 | 111 |
| 核验 accepted | 236 | 100 |
| 核验 unknown | 20 | 284 |
| degraded | 8 | 12 |
| citation_only | 1 | 2 |
| bonus | 18 | 38 |
| exact / env | 8/4 | 8/4 |

## 交付构成

360：

- code 6 / series 2 / generic 4
- 包含 **HF8066**、豪沃6×6 等 primary/backup。

360+Baidu：

- code 5 / series 2 / generic 5
- 新增：泰安五岳、沙漠越野重型；
- **丢掉 HF8066** 和豪沃6×6；
- HF8066 有 assets，但 verifications 为空，最终未占槽。

## 结论

1. **交付数量不变（12/12）**，但**构成变差**：丢了一个强 primary（HF8066）。
2. Baidu 把候选量翻倍（fetch 324→608、gate 264→452），但核验 unknown 从 20→284；
   accepted 从 236→100。
3. 平台增量没有转化为更好的交付，反而让验证/占槽被低质候选挤占。
4. 这不是“平台精度差”，而是 **候选量增加后，验证/优先占槽没有保护 preferred**。
5. normal 默认不受影响（Baidu 是 opt-in）；但 Platform 层整条线不应直接接入。

## 下一步

- 不接 Platform；
- 如果要重试，必须先有“preferred target 的验证/占槽保护”，而不是再扩平台；
- 或者收口 Platform，回到 normal。
