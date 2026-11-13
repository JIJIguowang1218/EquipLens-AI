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

### 7. negative A/B 数据（2026-11-13）

- 新增 `data-test/runs/ab-negative-20261113/`：5 个 case × with/without，
  brief 复用 `delivery-20261112-clean`，loop 为真实执行（10 次）；
- 内容：`AB.json`、`AB-SUMMARY.md`、`SEARCH-LEVEL.json`、每个 case 的
  `QUERY-DIFF.json`、`with/`、`without/`（各含 plan/rank/run/audit）；
- `images/` 照旧不入库；`data-test/runs/INDEX.md` 由 `run_ledger.py` 重新生成；
- 结论与限制见 `docs/negative-ab-20261113.md`；E38 已登记；
- **不改生产默认**：`negative` 保留，`build_query_plan(use_negative=False)` 仅 A/B 开关；
- 新增：`scripts/ab_negative.py`、`scripts/plan_candidates.py --no-negative`、
  `tests/test_planning.py` 的“只去后缀”用例。

### 8. 交付缺口/耗时审计（2026-11-13）

- 新增 `data-test/runs/ab-negative-20261113/AUDIT-DELIVERY-TIMING.md`、
  `DELIVERY-AUDIT.json`、`README.md`：逐 run 的规划/有图/交付/缺口统计与
  plan/rank/loop/FETCH/DISCOVER 耗时；
- 新增 `docs/delivery-audit-20261113.md`：unit 配额锁死的根因与修复方向；
- 结论：4 个正选缺口 run 全部"有图 ≥ N"，不是取图能力问题；
  `degraded_fill` 被执行但被 unit 配额挡住；
- 不改任何 run 数据；修复与实验提交见 `dc9f136`（E40/E41/E42）。

### 9. 填槽修复与并发实验（2026-11-13）

- 修复 `engine._fill_pass`：本 unit 满时允许借其它 unit 空槽；`_delivery` 正选未满时
  不把有图车算作备选；
- 验证 `data-test/runs/verify-fillfix-20261113/`：复用原 plan 复跑 c2 两臂，
  8+2→**10+0**、9+4→**10+4**；
- A 测试 `data-test/runs/ab-plan-concurrency-20261113/`：plan 串行 518.3 s →
  4 路并发 155.3 s（3.34×），`plan_candidates.py --concurrency` 默认仍 1
  （当晚改为默认 4，见 §12）；
- rank A/B `data-test/runs/ab-rank-20261113/`：LLM vs 确定性交付一致，
  确定性 rank 省 20–40 s；`rank_plan.py --deterministic` 仅实验开关；
- 下载基准 `data-test/runs/ab-negative-20261113/c5-roller/DOWNLOAD-CONCURRENCY.json`：
  4 路 2.9×、8 路 3.1×；未改生产 loop；
- 新增 `docs/concurrency-experiments-20261113.md`。

### 6. 复核方法（新机器上可自检）

```bash
PYTHONPATH=src python scripts/run_ledger.py --check     # 应 0 issue
PYTHONPATH=src python scripts/monitor_bad_domains.py     # 刷新死图床监测（只统计）
PYTHONPATH=src python scripts/summarize_delivery_suite.py --base data-test/runs/delivery-20261112-clean
```

### 10. 台账口径修正（2026-11-13，P4）

- 旧 `run_ledger.py` 重建索引时，用**生成时**的 HEAD 和目录 mtime 覆盖每条 run 的
  `date`/`git_commit`：80 条历史记录被统一写成 `dec466a`，6 个 plan/diag 目录的日期被改成 2026-11-13。
- 已改为优先读该目录 `RUN.json` 里的 `date`/`git_commit`；新增单测
  `tests/test_run_ledger.py::test_run_date_and_commit_are_preserved`（8/8 通过）。
- 重建后 `INDEX.json/md`：80 → **84** 条，补进 `ab-negative-20261113`、
  `ab-plan-concurrency-20261113`、`ab-rank-20261113`、`verify-fillfix-20261113`；
  （同日晚组合回归后再生成 → **87** 条，见 §11）
  历史 run 的日期/提交回到真实值；**未改任何 `summary.json`/`state.json`**。
- 仍存缺口：上面 4 个套件目录没有根级 `summary.json`/`plan.json`，台账归类为 `empty`
  （有记录、无指标）；要显示指标需让 `run_ledger.py` 读 `SUITE-SUMMARY.*`，留待后续。

### 11. 组合回归数据（2026-11-13，P0）

- 新增 `data-test/runs/delivery-20261113-regress/`：复用 clean 的 5 份**冻结 brief**，
  plan `--concurrency 4` 重跑、loop 串行；主 48/50、备选 15/20、峰值 ¥2.093。
- 新增 `delivery-20261113-fillfix-c1/`：c1 用 clean 原 plan 单跑 = **10/10 + 1/4**，
  用来隔离“填槽修复”本身（排除 plan 波动）。
- 新增 `delivery-20261113-planvar/c1/`：同 brief 的 plan 并发 1 与 4 各跑一次，均 19 候选，
  排除“并发导致池缩水”的嫌疑（回归里的 12 是搜索/LLM 轮次波动）。
- `scripts/run_delivery_suite.py` 增 `--concurrency / --reuse-brief / --cases`；
  `--reuse-brief` 不重新生成 brief，回归可复现。
- 未改任何既有 run 数据；`images/` 照旧不入库。


### 12. 并发切默认（2026-11-13 晚）

- `plan_candidates.py --concurrency` 默认 1 → **4**；`--concurrency 1` 仅作串行对照臂；
- `retrieval_engine` 新增 `--download-workers`（默认 **4**）：`web.live_fetch` 只并行下载 I/O，
  结算严格按原顺序（拉黑/早停/fetch_log/计数与串行等价）；1 = 串行对照臂；
- `summary.config` 新增 `download_workers / plan_concurrency / rank_method / platform_extra /
  code_prefilter`：任何 run 都能自证并发配置，没有这一项不参与横向对比；
- 本次只改代码与文档，**未跑检索实验**；单测 `retrieval_engine 41/41`、`imagesearch 14/14`、
  `planning 14/14` 全绿（新增“并发下载保序且不重复下载”）。

### 13. 来源分级字段与判死链复盘（2026-11-13）

- `Asset` 契约新增 `query_tier / source_query`（图片来源查询档位）；`asset_meta` 同步；
  `fetch_log.jsonl` 增加 `query_tier`；`summary.delivery.query_tiers` 统计交付图来源分布。
- 本次只改契约与记录，**不改交付判定**；`imagesearch 15/15`、`retrieval_engine 43/43`。
- 复盘文档：`docs/query-kill-chain-20261113.md`（判死链 9 项、品牌表来源 `c44e0e3`、
  去表化替代方案）。
- 未跑检索实验；未改任何既有 run 数据。

### 14. 判死链去表化修复（2026-11-14）

- `normalize_query`：型号码改为在**原始串**上抽取（括号内码不再丢）；纯描述名去构型/驱动词后截短；
- `alias_query`：无品牌/车系/型号时返回空（不再生成“牵引车/卡车”噪声查询）；
- `_brand_group`：开头词优先、括号外子串匹配、拉丁车系可作兜底（修“把沃尔沃发动机当品牌”）；
- `RuleVerifier`：新增“拉丁车系 + 构型”双证据 → probable，不再要求品牌表命中；
- 离线回放（不联网）：1135 车型 993 个查询键变化；76 个括号码全部修复；4337 条命中中
  旧放行→新拒绝 **0**；4456 个 unknown 资产 382 个可升级（8.6%）。
- 测试：`imagesearch 16/16`、`retrieval_engine 44/44`；**未跑检索 loop**，未改既有 run 数据。
- 文档：`docs/query-kill-chain-20261113.md`；复现：`scripts/evaluate_kill_chain_offline.py`。

### 15. 判死点端到端与配置补记（2026-11-14）

- `query_tier`：缓存命中时补记主查询键，避免来源档位为空；
- `summary.config.rank_method`：LLM rank 的 plan 没有 `ranking.method` 时记为 `llm`；
- 端到端（冻结 plan，只改代码）：c1 9/10→**10/10**（备选 2→1、degraded 8→9）；
  c2 10/10、备选 2→**3**、degraded 6；数据 `data-test/runs/p2-identity-20261114/`；
- 新增机制待尝试清单：`docs/backlog-mechanisms-20261114.md`（A/B/C/D/E 五组，含冻结/解冻协议）。

### 16. 调研与落地测试（2026-11-14）

- 调研报告 3 份：`docs/research/{rag-candidates,entity-matching,retrieval-eval}-20261114.md`，
  索引 `docs/research/README.md`；结论进入 `docs/backlog-mechanisms-20261114.md` F1–F7。
- **Gleaning 补抽已测**：5 份 brief、每份 8 查询 ×2 抽取，新增候选 **0** → 不采纳
  （输入是标题+280 字摘要，不是全文；代码保留 `--glean` 默认 0）。
- **归一化 key 去重已离线测**：96 份 plan / 2140 候选，19 组重复（0.9%）、15 份 plan 受影响；
  当前簇内多码 0 例；模糊合并会误并 `XS143J`/`XS143` → 只做归一化展示/去重，保留型号码硬校验。
- **search_key 正式启用**（仅末档兜底）：前三档 0 命中才触发，`query_tier` 可监控。
- 本轮只跑 plan/离线分析，未跑检索 loop；`planning 15/15`、`retrieval_engine 47/47`。

### 17. 健康检查修复（2026-11-14）

- `test_delivery_manifest`：「图片存在才校验数量」——`images/` 是 gitignore 的，
  新 clone 无文件时只校验结构，避免把“没同步图片”误判成代码回归（现 3/3）。
- 台账补录 9 个新 plan-set 目录的 `RUN.json`：`run_ledger --check` 从 9 issue → **100 条 0 issue**；
  HANDOFF/DEPENDENCIES 口径同步为 100。
- 已知历史遗留：`EXPERIMENTS-INDEX` 有 7 个编号重复（E17/E19/E24/E27/E34/E35/E37 各出现两行），
  属于早期编号冲突；不改编号（会破坏引用），后续新实验继续用 E59+。

### 18. 部件词表去命名化（2026-11-14）

- 问题：`briefing.py` 对内置于 `data/part_taxonomy.json` 之外的部件生成 `custom_<sha1>`，
  词表实际决定了命名；H3（扫路车）brief 出现 `custom_5a1c7e` 这类不可读 key。
- 修复：词表外部件 key 改为 `custom_` + 可读 slug（中文/字母/数字，≤16 字），label 保留原文；
  词表只用于“认识时显示原名/默认族”，不认识不拒绝、不改名。
- 回归：`tests/test_briefing.py` 增加“key 必须包含部件名”；H3 brief 已重新生成（可读 key），
  `fulltest-20261114/MANIFEST.json` 重算 sha256。
- 审计：`docs/vocabulary-audit-20261114.md` 列出全部表/列表（部件、类目、品牌、来源、风格），
  区分“危险（领域穷举）”与“可接受（通用词/模型标签）”；CODE-INDEX/README/PRD 口径已改。
- 待拍板：是否删除 `part_taxonomy.json` 与 legacy `category_profiles.json`。

### 19. 词表静默与主链去表化（2026-11-14）

**动作**（保留文件、未删除；路径与 sha256 已确认）：

- `data/part_taxonomy.json` → `data/legacy/part_taxonomy.json`（`0b4a521b…`）；
- `data/category_profiles.json` → `data/legacy/category_profiles.json`（`4f1e79a3…`）；
- `imagesearch.BRAND_GROUPS` 移出主代码 → `data/legacy/brand_aliases.json`（`a3bb257a…`），
  默认空；仅 `EQUIPLENS_ENABLE_LEGACY_BRANDS=1` 时加载（已验证 22 → 0）。

**主链改动**：

- `briefing`：不再读取部件表；part key 只按写法（ascii snake 保留，否则 `custom_<可读 slug>`）；
  prompt 里删除 `reference_parts`，改为 `no_vocabulary_note`；
- `analysis`：`load_taxonomy/taxonomy_with_when` 返回空（兼容旧脚本），不再标 `term_off_taxonomy`；
- `textrun`/`make_ui_fixtures`：显式指向 `data/legacy/`（旧链路）；
- `RuleVerifier`：`fallback_series` 仅在 legacy 品牌表加载时生效，避免“品牌命中 + 车名 token”被误判 probable。

**守卫**：`tests/test_no_legacy_tables.py`（3/3）检查主代码无 `part_taxonomy`、品牌表默认空、legacy 文件仍在。

**测试**：`briefing 5/5`、`planning 16/16`、`engine 47/47`、`imagesearch 16/16`、
`ledger 8/8`、`pricing 4/4`、`manifest 3/3`、`vocabulary_guard 3/3`。
**未跑检索 loop**：需先做“品牌表静默后”的 c1/c2 冒烟（见 full-test-design §6）。

### 20. P0–P4 完整测试（2026-11-14，无人值守）

- **P0** 品牌表静默后 c1/c2 冻结 plan 冒烟：c1 10/10+1/4（持平），c2 10/10+4/4（备选 +1）→ 无回归。
- **P1** 洒水车 brief：无 `reference_parts` 提示、部件 key 可读、schema/契约/plan（30 候选）全通过。
- **P2** 10 类目 ×1：6 已知 + 4 holdout **全部满额交付**；no_hits 2；成本 ¥1.82；Go=true。
- **P3** 10 类目 ×3（共 30 run）：交付率全部 1.000（极差 0）；备选 h4 极差 2、s6 ±1；
  degraded CV c5=0.374（绝对值 2–5/14 台）；预注册稳定性判定 **false**（备选/身份两项未达阈值）。
- **调整**：`top_up_queries` 增加通用查询（图集/参数/评测），`--topup` 上限 2→4（**默认仍 2**）。
  h4 备选 2/4→4/4 与 3/4；s6 两次 4/4；候选池上移但波动未消除 → 仅作紧供类目缓解。
- 数据：`data-test/runs/p7-screen-20261114/`、`p7-screen-r{2,3}-20261114/`、
  `p8b/p8c-topup4-20261114/`；汇总 `data-test/evals/fulltest-repeats.json`；
  报告 `docs/fulltest-report-20261114.md`。
- 测试：`planning 16/16`、`retrieval_engine 47/47`、`imagesearch 16/16`、`briefing 5/5`、
  `ledger 8/8`、`pricing 4/4`、`manifest 3/3`、`vocabulary_guard 3/3`。
- 未改其他生产默认；`search_key` 在 30 次运行中触发 0 次（符合末档兜底定位）。
