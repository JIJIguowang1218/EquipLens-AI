# task-brief 必要性 A/B（自动检查）

| case | arm | status | parts | custom | regions | axes | assertions |
|---|---|---|---:|---:|---:|---|---|
| C01 | v2_method | ok | 4 | 0 | 1 | True | PASS |
| C01 | v1_format | ok | 9 | 0 | 2 | True | parts 9 not in [3,5] |
| C02 | v2_method | ok | 4 | 1 | 2 | True | PASS |
| C02 | v1_format | ok | 8 | 1 | 2 | True | parts 8 not in [3,5] |
| C03 | v2_method | ok | 5 | 0 | 2 | True | PASS |
| C03 | v1_format | ok | 5 | 0 | 4 | True | PASS |
| C04 | v2_method | ok | 4 | 0 | 1 | True | PASS |
| C04 | v1_format | ok | 5 | 1 | 2 | True | PASS |
| C05 | v2_method | ok | 4 | 0 | 1 | True | PASS |
| C05 | v1_format | ok | 12 | 1 | 4 | True | parts 12 not in [3,5] |
| C06 | v2_method | ok | 5 | 5 | 0 | True | PASS |
| C06 | v1_format | ok | 34 | 23 | 3 | True | parts 34 not in [3,5] |
| C07 | v2_method | ok | 5 | 5 | 3 | True | PASS |
| C07 | v1_format | ok | 5 | 5 | 4 | True | PASS |
| C08 | v2_method | ok | 5 | 3 | 3 | True | PASS |
| C08 | v1_format | ok | 14 | 3 | 4 | True | parts 14 not in [3,5] |
| C09 | v2_method | ok | 5 | 3 | 2 | True | PASS |
| C09 | v1_format | ok | 14 | 3 | 4 | True | parts 14 not in [3,5] |
| C10 | v2_method | ok | 5 | 4 | 1 | True | PASS |
| C10 | v1_format | ok | 18 | 7 | 4 | True | parts 18 not in [3,5] |

> 人工 rubric 必须另填：品类/基型/构型、对象分类、关系轴、设计轴、未知部件、是否编造。
