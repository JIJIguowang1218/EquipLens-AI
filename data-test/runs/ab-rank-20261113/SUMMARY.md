# rank 小 A/B：LLM vs 确定性排序

> 同一份 plan；只改 rank 方式；loop 用固定 ranked plan。

| case | 臂 | 交付 | 备选 | degraded | 成本¥ | 耗时s | 目标数 |
|---|---|---:|---:|---:|---:|---:|---:|
| c1-desert-tractor/with | llm | 10/10 | 4/4 | 9 | 0.22 | 371.2 | 25 |
| c1-desert-tractor/with | deterministic | 10/10 | 4/4 | 9 | 0.21 | 241.3 | 25 |
| c2-reach-stacker/with | llm | 10/10 | 0/4 | 4 | 0.12 | 257.1 | 16 |
| c2-reach-stacker/with | deterministic | 10/10 | 0/4 | 4 | 0.12 | 254.8 | 16 |

## 排序重合

- c1-desert-tractor/with：全量重合 25/25，top10 Jaccard 0.25
- c2-reach-stacker/with：全量重合 16/16，top10 Jaccard 0.54
