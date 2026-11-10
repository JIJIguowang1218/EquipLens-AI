# task-brief 必要性 A/B（自动检查）

| case | arm | status | parts | custom | regions | axes | assertions |
|---|---|---|---:|---:|---:|---|---|
| C01 | with_skill | ok | 4 | 0 | 1 | True | PASS |
| C01 | without_skill | ok | 1 | 1 | 0 | True | parts 1 not in [3,5]; regions < min |
| C02 | with_skill | ok | 4 | 1 | 2 | True | PASS |
| C02 | without_skill | ok | 5 | 4 | 0 | True | regions < min |
| C03 | with_skill | ok | 5 | 0 | 2 | True | PASS |
| C03 | without_skill | ok | 5 | 1 | 0 | True | PASS |
| C04 | with_skill | ok | 4 | 0 | 2 | True | PASS |
| C04 | without_skill | ok | 1 | 1 | 0 | True | parts 1 not in [3,5]; regions < min |
| C05 | with_skill | ok | 4 | 0 | 1 | True | PASS |
| C05 | without_skill | ok | 5 | 0 | 0 | True | regions < min |
| C06 | with_skill | ok | 5 | 5 | 1 | True | PASS |
| C06 | without_skill | ok | 10 | 6 | 0 | True | parts 10 not in [3,5] |
| C07 | with_skill | ok | 5 | 5 | 1 | True | PASS |
| C07 | without_skill | ok | 1 | 1 | 0 | True | parts 1 not in [3,5] |
| C08 | with_skill | ok | 5 | 3 | 3 | True | PASS |
| C08 | without_skill | ok | 1 | 1 | 0 | True | parts 1 not in [3,5] |
| C09 | with_skill | ok | 5 | 3 | 3 | True | PASS |
| C09 | without_skill | ok | 1 | 1 | 0 | True | parts 1 not in [3,5] |
| C10 | with_skill | ok | 5 | 4 | 2 | True | PASS |
| C10 | without_skill | ok | 1 | 1 | 0 | True | parts 1 not in [3,5] |

> 人工 rubric 必须另填：品类/基型/构型、对象分类、关系轴、设计轴、未知部件、是否编造。
