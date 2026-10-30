# 确定性闸门评估 v1（T18-roster 265 段）

- 金标：模型逐段判定（V/P/G=可用 63，C=剔除 202）
- 闸门：**精确率 93.1%** / 召回率 85.7% / F1 0.893 / 假阳性 6.9%
- 混淆：TP 54 / FP 4 / FN 9 / TN 198

## 分档通过率

| 金标档 | 段数 | 闸门通过 |
|---|---:|---:|
| V | 9 | 9 |
| P | 33 | 31 |
| G | 21 | 14 |
| C | 202 | 4 |

## 拒绝理由 Top

- config_line: 116
- no_concrete_evidence: 55
- no_design_content: 19
- passenger_car: 13
- enterprise_pr: 2
- option_list: 2
