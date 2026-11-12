# data-test/runs 运行台账约定

> 目的：任何人在任何时候（包括换机器、隔几周回来）都能回答：
> **这次跑的是什么阶段、输入是什么、结果如何、结论在哪、对应哪个测试编号。**

## 1. 目录是什么

| 目录形态 | 含义 | 必须有的东西 |
|---|---|---|
| `loop-*` | 一次完整检索 loop（brief → plan → fetch → gate → verify → fill） | `state.json` / `summary.json` / `events.jsonl` / `RUN.json` |
| `plan-*` | 只跑 planner（不抓图） | `plan.json` / `api_log.jsonl` / `RUN.json` |
| `plan-ab*-YYYYMMDD/` | 一组 A/B 规划实验 | 子目录 `A1.../plan.json`；根 `RUN.json` 列出子实验 |
| `filter-*` / `web-smoke-*` / `web-reassess-*` | 筛选/冒烟专项实验 | `report.md` 或 `report.json` / `RUN.json` |
| `run-*` | 旧文本检索批次（L3/runner） | `summary.json` / `report.md` / `RUN.json` |
| `_archive/` | 归档，不参与索引 | — |

**不删除历史目录。** 空目录、旧嵌套目录只标 `empty` / `archived`，由索引列出。

## 2. 每个目录一个 `RUN.json`

由 `scripts/run_ledger.py` 生成，字段：

| 字段 | 说明 |
|---|---|
| `run_id` | 目录名 |
| `kind` | `run` / `plan` / `plan-set` / `diag` / `empty` / `archived` |
| `stage` | `loop` / `plan` / `search` / `gate` / `eval` / `engine` / `text-retrieval` |
| `date` | 目录名里的 `YYYYMMDD`，没有则用修改时间 |
| `status` | `summary.state` / `state.final_state` |
| `brief_id` | 本次用的任务单 id |
| `git_commit` | 生成台账时的代码提交 |
| `metrics` | 交付、图数、门卫、degraded、API 成本等 |
| `conclusion` | **一句话结论**（人工写：RUN.json 或 REPORT.md 的「结论」段；索引优先显示） |
| `conclusion_source` | `stored`（RUN.json 里原有的结论）/ `report`（从 REPORT.md 抽的）/ `auto`（机器统计） |
| `auto_conclusion` | 机器按 status/metrics 生成的摘要，**不算人工结论** |
| `report` / `audit` / `summary` | 证据路径 |
| `needs_review` | **还没有人工结论**（= `conclusion` 为空；机器摘要不会把它清成 false） |

**结论写在哪**：优先改 `RUN.json.conclusion`（一句话），详细过程写 `REPORT.md`。
`INDEX.md / INDEX.json` 是生成物，不要手改。
> 注意：`auto_conclusion` 是机器统计，不能当复核结论；要清掉 `needs_review` 必须写 `conclusion` 或 REPORT.md 的「结论」段。

## 3. 命令

```bash
# 只检查（不写文件）：缺 RUN.json / 缺 INDEX 会列出
PYTHONPATH=src python scripts/run_ledger.py --check

# 补 RUN.json + 重建 INDEX（保留已有 conclusion；--force 会覆盖）
PYTHONPATH=src python scripts/run_ledger.py --write
PYTHONPATH=src python scripts/run_ledger.py --write --force
```

## 4. 命名约定（新实验）

- 完整 loop：`loop-<主题>-YYYYMMDD`，同一天多轮加 `-v2/-v3`；
- 只规划：`plan-<主题>-YYYYMMDD`；
- A/B：`plan-ab<序号>-YYYYMMDD/`，子目录 `A1/B1`；
- 专项筛选/冒烟：`filter-*` / `web-smoke-*`；
- 不要再用 `recompute`、`test`、`tmp` 这类无语义目录名。

## 5. 图片与 Git

- `images/` 不进 git（版权/体积）；`audit.html` 用相对路径引用它。
- 换机器看 audit 需要把原机器 `images/` 拷过来，或按 §3 的命令重跑。
- 提交 run 时只提交：`RUN.json` `state.json` `summary.json` `events.jsonl` `*.jsonl` `evidence.db` `audit.html` `REPORT.md`。

## 6. 与 test-log / 实验日志的关系

- `docs/test-log.md`：测试编号（T1…T41）— 做了什么、数据、结果、遗留；
- `docs/retrieval-experiments-log.md`：E1…E15 — 假设、方法、数据、结论；
- 本目录：**原始产物** + `RUN.json` 一句话结论；
- 三者互相引用：test-log 行里写 run 目录，RUN.json 里写 brief/plan，索引里给链接。
