# task-brief 评测（10 案例）

按 Agent Skills 官方评测方法：**with_skill vs previous version / without skill、断言、人工 grading、汇总**。
这里主对照是 **v2 方法 vs v1 只给格式**；no-method 仅作参考。
参考：<https://agentskills.io/skill-creation/evaluating-skills>

## 案例集

`evals.json` 10 个案例，全部是“品类 + 3–5 个部件 + 工况/构型”，**不写具体车型**：

| id | 品类 | 部件数 |
|---|---|---:|
| C01 | 沙漠牵引车 | 5（1 region + 4 part） |
| C02 | 重型吊车（口语类目） | 5 |
| C03 | 矿用翻斗卡车 | 5 |
| C04 | 随车起重运输车 | 5 |
| C05 | 重型长途牵引车 | 5 |
| C06 | 履带式挖掘机（新） | 5 |
| C07 | 轮式装载机（新） | 5 |
| C08 | 混凝土搅拌车（新） | 5 |
| C09 | 环卫压缩车（新） | 5 |
| C10 | 高空作业车（新） | 5 |

## 跑法

```bash
PYTHONPATH=src python scripts/eval_task_brief.py \
  --out data-test/evals/task-brief-eval-20261111
```

每个 case 跑两次：`v2_method`（方法引导）和 `v1_format`（只给输出字段/枚举，不给方法）。
`--arms` 可加 `no_method` 做裸基线，但不作为主对照。
产物：每 case 的 brief、`results.json`、`RESULTS.md`（自动断言）、`REVIEW.md`（人工评分表）。

## 自动断言

- schema 通过；
- 部件数 3–5；
- 每件有 `design_axes`；
- 需要 region 的案例有 region；
- 词表外案例至少有 1 个 `custom_*`；
- 至少 1 条 assumption。

自动断言只能证明“结构可用”，**不能证明分析对**；语义对错由 `REVIEW.md` 人工评分。

## 判定

如果 v2 在 10 个案例上没有稳定优于 v1（语义 rubric 盲评），或差异只来自“部件数量”这种格式约束，
就不把 v2 方法文字当必要组件，只保留 schema + 校验。
