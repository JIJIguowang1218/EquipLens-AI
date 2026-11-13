# 远程同步清单（新电脑接手）

更新：2026-11-13

## 会同步（git）

- 全部生产代码：`src/equiplens/**`
- 入口/脚本：`scripts/**`（含实验脚本，但见 CODE-INDEX 标注）
- 技能：`skills/**`
- 测试：`tests/**`
- 契约：`schemas/**`
- 配置/词表：`data/*.json`
- 文档：`docs/**`
- 评测结论/数据：`data-test/evals/**`
- run 的轻量轨迹：`data-test/runs/**/state.json`、`summary.json`、`fetch_log.jsonl`、`events.jsonl`、`audit.html`、`RUN.json`
- 交付与监控产物：`DELIVERY.md/json`、`SUITE.json`、`SUITE-SUITE-SUMMARY.md`、`dedupe-review.html`、`data-test/evals/bad-domains-monitor.*`
- 2026-11-13 实验数据：`data-test/runs/ab-negative-20261113/`（含 `SEARCH-LEVEL.json`、
  `AUDIT-DELIVERY-TIMING.md`、`DELIVERY-AUDIT.json`）、`ab-plan-concurrency-20261113/`、
  `ab-rank-20261113/`、`verify-fillfix-20261113/`；这些目录的 `images/` 仍不同步
- 台账：`data-test/runs/INDEX.json/md`（由 `run_ledger.py` 生成；语义见 `DATA-CHANGELOG.md`）
- 测试夹具：`data-test/retrieval-fixtures-20261109/**`（P1 测试必需）
- 人工审核页：部分 `review.html` + 其中跟踪的缩略图

## 不同步（gitignore / 不入库）

- API key：`~/.equiplens/deepseek.env`（仓库外；新电脑必须自备）
- Python venv、`__pycache__`
- UForm3 模型缓存（首次运行自动下载，约 59MB）
- 大多数 `data-test/runs/**/images/` 原图（版权/体积）；`.gitignore` 规则 `data-test/runs/**/images/`
- `data-test/equiplens.db`、`data-test/ab-images/`、`data-test/ui-fixtures/`
- `tmp/`、输出视频/PPT 中间产物

## 依赖/统计入口

- 依赖：`docs/DEPENDENCIES.md`、`requirements.txt`
- 优化统计：`docs/OPTIMIZATION-METRICS.md`、`data-test/evals/METRICS.csv`
- DB 说明：`data-test/equiplens.db` 是测试素材库，不是测试结论

## 新对话/新设备必做

- 正式实验按 `HANDOFF.md` 0.0.1 的 KPI 模板记录；
- 初始 vs 最终只按 `docs/INITIAL-VS-FINAL.md` 的受控口径比较；
- 不要把候选级 precision、run 级 delivery、case 级 PASS 混成一个数字。

## 已知的“重算/作废”数据（换机器前必读）

- `delivery-20261112`、`-q1`、`-q12`：brief negative 污染，**交付结论作废**，仅存档；
- `delivery-20261112-clean`：修复后权威基线；
- 多个 `RUN.json` 在 2026-11-12 被 `run_ledger.py` 重写（机器结论移入 `auto_conclusion`）；
- 详见 `docs/DATA-CHANGELOG.md`。

## 新电脑缺什么

1. DeepSeek key（否则规划/引用/重规划不可用）；
2. Python 3.11 + requirements + UForm3 模型下载；
3. `data-test/runs/**/images/` 原图：run 的 state/log/audit 在，但图片不一定在；
4. 若审核页图片未跟踪，HTML 会缺缩略图；需要重新抓或看原图 URL；
5. 旧数据库/演示夹具（如 `data-test/equiplens.db`、`ui-fixtures`）不在仓库。

## 结论

- **主体代码可拉取并跑**，但新电脑必须装环境 + 自备 key + 首次下载模型；
- **测试结论 JSON/MD/大部分审核页在仓库**，但不是所有图片都在；
- **不能声称“所有测试过程和结果都同步”**：原图、DB、部分中间产物不同步；
- 包装前按 `CODE-INDEX.md`/`CURRENT-ARCHITECTURE.md` 走，不要依赖未同步的 run 图片。
