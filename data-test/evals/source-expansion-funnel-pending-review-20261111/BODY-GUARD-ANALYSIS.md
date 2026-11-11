# 通用车身/吨位 guard：触发条件与 A/B 结果

## 触发条件（试图做的）

1. 从 `brief.request.class` 推断目标车身：mixer / dump / aerial / tractor / cargo；
2. 标题如果明确出现**另一种**车身，且没有目标车身 → `wrong_body`；
3. 标题有明确吨位且与目标吨位不符 → `wrong_tonnage`；
4. 只在 recovery 路径使用，normal 不动。

## 结果：硬拒不可接受

| 版本 | accepted 总数 | 其中目标 | precision | 被拒目标图 |
|---|---:|---:|---:|---:|
| 不 guard | 23 | 16 | 69.6% | 0 |
| 激进 guard（含吨位硬拒） | 12 | 9 | 75.0% | **8** |
| 保守 guard（只硬拒单一车身，吨位仅 warning） | 22 | 15 | 68.2% | 1 |

- 激进版把 precision 提到 75%，但**误杀 8 张目标图**，recall 损失不可接受。
- 保守版几乎不拒，precision 反而略降（68.2%）。
- 典型误杀：
  - `OTTC认证-客车卡车...` 被当成 bus；
  - `150吨级别矿山霸王` 被 70T 吨位 guard 拒；
  - `T5G 牵引车` 被搅拌车目标拒（人工标为目标，说明标题/图关系本身有噪声）。

## 额外发现

- 只要求 `scene=single_vehicle` 的 overview 子集：8 张 accepted，5 target / 2 not / 1 uncertain，precision **62.5%**；
- 所以“整车槽只收 overview”能减少 part 图，但不能单独解决 precision。

## 结论

1. **不要上线硬 body/tonnage guard**；误杀目标图。
2. 把 body/tonnage 作为 **warning/排序信号**，不作为 accepted 门槛。
3. 当前扩源属于 **Query 层 + Source 层**；Platform 层（百度/必应/官网）还没接。
4. 下一步优先：
   - query 用类目词（搅拌车/矿用自卸/高空作业），不要泛 alias“卡车”；
   - 去重 + overview 占槽；
   - 对 accepted 错图做人工/视觉复核，而不是标题硬规则。
