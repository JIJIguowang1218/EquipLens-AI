# 数据与测试文件变更记录

> 目的：换机器/新会话时知道哪些测试产物被重算、哪些结论是有效的、哪些是历史污染数据。
> 原则：**只追加，不改写历史**；作废的实验保留目录，但在本文件和 `EXPERIMENTS-INDEX` 里标清楚。

## 2026-11-12（交接版）

### 1. 台账语义变更（影响所有 `RUN.json` / `INDEX.*`）

- `scripts/run_ledger.py` 改为：机器统计写 `auto_conclusion`，`conclusion` 只放人工/报告结论；
  `needs_review` 只看人工结论。
- 迁移旧记录：55 个 `RUN.json` 被重写（机器结论移入 `auto_conclusion`），`INDEX.json/md` 全量重建；
- 结果：`needs_review` 从“虚低（5）”变成真实 29+；之后每轮新 run 都会带 `auto_conclusion`。

### 2. run 产物被重算/重渲染的目录

| 目录 | 变更 | 原因 |
|---|---|---|
| `data-test/runs/verify-contract-20261112/` | `summary.json` 重算（补 `delivery.backup`、`timings`、`downloads`）；`audit.html` 重渲染 | 契约/备份/计时改动后回填 |
| `data-test/runs/verify-yield{,2,3}-20261112/` | `summary/state/fetch_log` 新增；`DELIVERY.*` 生成；`audit.html` 重渲染 | 拉黑/早停/归因验证 |
| `data-test/runs/delivery-20261112/`（baseline） | 新增 5 case；`SUITE.json`、`SUITE-SUITE-SUMMARY.md` | 5 输入交付测试（**结论已作废**，见下） |
| `data-test/runs/delivery-20261112-q1/` | 新增 | 短查询对照（**受 negative 污染**） |
| `data-test/runs/delivery-20261112-q12/` | 新增 | 短查询 + 补查对照（**受污染**） |
| `data-test/runs/delivery-20261112-mergefix/`、`-negfix/`、`-intentfix/` | 新增（c1 单点诊断） | 合并规则 / negative / 查询意图三次定位 |
| `data-test/runs/delivery-20261112-clean/` | 新增 | **修复后权威基线**（negative 短词 + 查询意图恢复） |

### 2.1 套件汇总文件改名（Windows 大小写冲突）

- 原 `SUMMARY.json/md` 放在 `delivery-*` 套件目录下，Windows 大小写不敏感，
  `run_ledger.py` 会把 `SUMMARY.json` 当成 run 的 `summary.json` 读（list 崩溃）。
- 已改名为 **`SUITE-SUMMARY.json/md`**；`run_ledger.py` 同时加了“非 dict 直接忽略”的防御。
- 旧 `SUMMARY.*` 已删除；`SUITE-SUMMARY.*` 已提交。

### 3. 结论有效性

- **有效**：`delivery-20261112-clean/SUITE-SUMMARY.md`；c1 的 `intentfix`（10/10+3/4）作为第二样本。
- **作废/仅存档**：`delivery-20261112`、`-q1`、`-q12` 的交付数字与成本对比——brief 的 negative 被 LLM 写成整句，
  查询被污染；保留目录仅用于追溯。`EXPERIMENTS-INDEX` 的 E34/E35 已标注修正，E37 为 clean 复跑。
- **单轮波动**：同一代码 c1 两次 9/10 与 10/10，n=1 的差异不能当回归。

### 4. 测试文件改动（代码仓内）

| 文件 | 改动 |
|---|---|
| `tests/test_planning.py` | 新增：候选池下限、查询压缩、补查询、人审合并规则、negative 只收短词 |
| `tests/test_retrieval_engine.py` | 新增：part_only 契约、attempts 真实计数、预算真实计数、交付台数跟随输入、备选 4 台、降级兜底、早停、缺图归因、计时 |
| `tests/test_imagesearch.py` | 新增：死图床拉黑 |
| `tests/test_run_ledger.py` | 新增：机器摘要不抵人工结论 / 人工结论关闭待复核 / 旧结论迁移 |
| `tests/test_pricing.py`、`test_delivery_manifest.py`、`test_bad_domains.py`、`test_dedupe_review.py` | 新增套件 |
| `tests/test_briefing.py` | 未改；但 brief 生成 prompt 已要求 negative 只写短词 |

### 5. 未入库/不同步的产物（换机器会缺）

- 所有 `data-test/runs/**/images/`：已在 `.gitignore` 用 `data-test/runs/**/images/` 忽略；
  审核页/ `DELIVERY.md` 里的图片引用换机器会 404，需要重跑或从原机拷贝；
- `data-test/equiplens.db`、`data-test/ab-images/`、`prompt` 缓存等历史 DB/素材：不同步；
- API key：`~/.equiplens/deepseek.env`，换机器需自备（另一台已有 key）。

### 6.1 安全事件：WeChat AppID 进入公开仓库（2026-11-12）

- **告警**：GitHub 提示 commit `340ae47`（当前已改写为 `d811f41`）含 “Tencent WeChat API App ID”。
- **事实**：不是 API 密钥，而是第三方图片 CDN URL 里的 `wx<16 hex>`（公众号 AppID，公开标识）；
  出现在 `delivery-20261112-clean/c3-tractor/run/` 的 `fetch_log.jsonl`、`state.json`、`audit.html`。
- **风险**：AppID 单独不能调用接口（需 AppSecret），无 DeepSeek key / GitHub token / 私钥泄露；
  `git grep sk-`、`ghp_`、`AKIA`、私钥头均为 0。
- **处置**：三个文件已把 AppID 替换为 `wx-REDACTED`；**改写 340ae47..HEAD 四个提交并 force-push**
  （旧 HEAD `3a77ab4` → 新 HEAD `6d45c12`，提交哈希已变）。
- **影响**：旧 clone（包括另一台电脑）不能直接 `git pull`，需重新 clone 或 `git fetch && git reset --hard origin/main`。
- **防复发**：新增 `scripts/scan_secrets.py`（扫 git 跟踪文件：WeChat AppID / `sk-` / GitHub PAT / AWS key / 私钥头）
  与 `tests/test_no_secrets.py`；提交前跑一遍。

### 6. 复核方法（新机器上可自检）

```bash
PYTHONPATH=src python scripts/run_ledger.py --check     # 应 0 issue
PYTHONPATH=src python scripts/monitor_bad_domains.py     # 刷新死图床监测（只统计）
PYTHONPATH=src python scripts/summarize_delivery_suite.py --base data-test/runs/delivery-20261112-clean
```
