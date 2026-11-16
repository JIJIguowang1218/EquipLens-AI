# tmp 原始实验资产清单（待归档，BL-013）

> 2026-11-16 产品负责人要求：**数据必须任意机器可取**；临时代码可不入库。
> 下列文件目前只在另一台机器的 `tmp/`（gitignored）；归档到 `data-test/evals/` 后请更新本表。

| 资产 | 路径（另一台机器） | 用于 | 状态 |
|---|---|---|---|
| V8 混乱输入 20 条 + 原型 | `tmp/s0-probe-20261115/bench-review-v4.md`、输入集 | S0-01 解析初测 | 待归档 |
| V9 50 条全量回归 | `tmp/s0-probe-20261115/bench-review-v4.md` | S0-01 v0.4 回归 50/50 | 待归档 |
| V10/V11 router 调参集与 dev30 | `tmp/s0-05/corpus.json`、`dev30-results.json` | S0-05 router 选型 | 待归档 |
| V12 新 holdout 24 条与报告 | `tmp/s0-05/holdout.json`、`holdout24-report.md` | router 验收 23/24 | 待归档 |
| V14 live router 冒烟 | `tmp/s0-05/live_router_smoke.json` | 意图冒烟 | 待归档 |
| V15 会话脚本（参考） | `tmp/s0-05/live_session.py` | M4.2 live 会话 | 可归档（代码可选） |

归档要求：只放**数据/报告**（JSON/MD），图片与 DB 仍不同步；归档后在 `EXPERIMENTS-INDEX` 的数据列改成本仓库路径。
