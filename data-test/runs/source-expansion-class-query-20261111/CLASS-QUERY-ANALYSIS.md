# 类目词 query 扩源：同一批 23 target

## 做法

- 同一批 23 个失败车型；
- query 从 `brief.class` 生成类目词（搅拌车/矿用自卸车/高空作业车/牵引车）+ 简化 model core；
- 仍用 harvest=2、同一 verifier、全局 URL 去重；
- 不针对品牌/车型写规则；没有硬 body/tonnage guard。

## 结果（verifier 口径，未人工确认）

| 指标 | alias query（旧） | class query（新） |
|---|---:|---:|
| search hits | 199 | 209 |
| unique URLs | 165 | 179 |
| gate pass | 93 | 95 |
| gate-pass unknown | 70 | 75 |
| 图级 accepted | 23 | 18 |
| target 级 accepted | 8 | 7 |
| target 级 overview | 1 | 2 |
| pending 图 | 44 | 82 |

- 类目词没有明显提升 target accepted（8→7），overview 从 1→2；
- gate-pass unknown 仍高（75/95）；
- 82 张新图未标注，不能直接比较 precision/recall。

## 盲评抽样

- accepted pending 全部 18 张；
- unknown pending 分层抽 15 张（每 brief 3 张）；
- 共 33 张，隐藏 accepted/identity。

## 结论

- 目前只能说：**类目词 query 没有明显优于 alias**，但 pending 标签未齐，不能下结论；
- 需要 33 张盲评，算 accepted precision + unknown 目标率；
- 若仍无改善，下一步应优先修来源/视觉核验，而不是继续换 query 词。
