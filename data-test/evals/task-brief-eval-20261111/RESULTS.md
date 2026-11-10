# task-brief 必要性 A/B（自动检查）

| case | arm | status | parts | custom | axes | assumptions |
|---|---|---|---:|---:|---|---:|
| known-parts | with_skill | ok | 5 | 0 | True | 7 |
| known-parts | without_skill | ok | 1 | 1 | True | 2 |
| unknown-parts | with_skill | ok | 4 | 4 | True | 7 |
| unknown-parts | without_skill | ValueError: brief 生成失败（已重试）: 无法确定 request.class：用户输入里没有车型类别，也没有 --class 兜底 |  |  |  |  |
| ambiguous-category | with_skill | ok | 2 | 2 | True | 6 |
| ambiguous-category | without_skill | JSONDecodeError: Extra data: line 1 column 1775 (char 1774) |  |  |  |  |

> 人工 rubric 必须另填：品类/基型/构型、对象分类、关系轴、设计轴、未知部件、是否编造。
