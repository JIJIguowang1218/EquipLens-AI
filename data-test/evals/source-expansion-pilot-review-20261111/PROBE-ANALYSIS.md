# 扩源 pilot 结果（30 候选 / 24 failed / 100 图）

## 样本与选择

- 5 个 brief：M1、M1B（已有 plan）+ A 矿用自卸、B 搅拌车、C 高空作业车（新生成 plan）。
- 每个 brief 取 plan 前 6 个候选，共 30 个 target。
- base：plan 的 `source_query`，搜 4 张，门卫+核验；通过则不算 failed。
- expansion：只对 base 失败的 target，用通用 `alias_query(model)` + `harvest=2`，搜 6 张。
- 无品牌/车型特判；不按某个 target 改 query。
- C 是 holdout，不参与策略选择。

## 结果

- base 失败：**24/30**。
- expansion 后核验通过：**9/24**（37.5%，仅 verifier 口径）。
- 仍有 **15/24** 未通过。

| brief | base 失败 | expansion 核验通过 |
|---|---:|---:|
| M1 | 6 | 3 |
| M1B | 3 | 0 |
| A 矿用自卸 | 4 | 2 |
| B 搅拌车 | 5 | 4 |
| **C 高空作业车（holdout）** | **6** | **0** |

## 解释

- 信号：M1/A/B 有恢复；B 最强。
- **C holdout 0/6**：没有证据表明策略跨品类泛化；不能接生产。
- M1B 0/3：样本小，但不支持泛化。
- “核验通过”只是标题证据，不等于人工确认；100 张盲评页待用户标注。
- 失败原因可能包括 alias query 太泛、来源页不相关、图片门卫拒绝；需要人工标注后再分类。

## 下一步

1. 人工盲评 100 张，确认 9 个“通过”是否真是目标、15 个“未通过”是否真不是。
2. 按 brief 看：C 失败是 query 问题还是来源问题；不要把 C 的结果用于调参。
3. 若 M1/A/B 的人工 precision 也高，再考虑扩到 8–10 brief / 150–250 图；否则先修 query/来源。
