# 数据与测试文件变更记录

> 目的：换机器/新会话时知道哪些测试产物被重算、哪些结论是有效的、哪些是历史污染数据。
> 原则：**只追加，不改写历史**；作废的实验保留目录，但在本文件和 `EXPERIMENTS-INDEX` 里标清楚。

## 2026-11-16

### 53. S2-01 视觉身份探针：No-Go（2026-11-16）

- 方法：本地 UForm3（与 `gate.py` 同权重，离线）对 335 个 image+model 资产做
  “真型号 vs 随机另一型号 vs truck”三选一；标签来自 `asset_meta.model`（搜索目标，非人工真值）。
- 结果：3-way top-1 **11.0%**（随机 33.3%）、真 vs 随机 pairwise **51.9%**（95% CI 46.6–57.2）、
  文本先验校正后 52.5%、1 图/型号子集 48.4%；truck 占 top-1 的 77.0%。
- 结论：**不把视觉身份接进 VERIFY**；CLIP 继续只做 keep/drop + scene/view。
  重开条件：image-to-image 参考嵌入或铭牌 OCR，预注册 ≥100 样本/≥10 类目。
- 产物：`scripts/probe_visual_identity.py`、`data-test/evals/visual-identity-20261116.json`、
  `docs/visual-identity-probe-20261116.md`；全程离线，约 28s CPU。

### 52. BL-010 P0 定向验证（2026-11-16）

- 3 份 brief：`v-brand`（只要陕汽 8 台）、`v-exclude`（不要北奔 10 台）、`v-pin`（必须含 X3000 8 台）。
- 结果：
  - brand 查询 `陕汽 沙漠牵引车 6x6` 出现，候选含 3 台陕汽系；
  - pinned 查询 `X3000 沙漠牵引车` 出现，候选含德龙 X3000；
  - `v-exclude` **首次复现 BC-S01-014**：`-"北奔"` 被前 4 条 LLM negative 截断 → 修
    `planning.negative_terms`（用户排除项优先）+ 回归测试；重跑后 query 含 `-"北奔"`。
- `v-brand` 真跑（8 槽）：**7/8 交付、missing 1、degraded 4、state FAILED**；7 台里 3 台陕汽系
  （通力 STL5250TSM、德龙 X3000 ×2）→ 品牌约束生效；缺 1 台是 **plan 池 7 < 需求 20**，
  归 D2 池供给，不是接线 bug。
- 指纹：`summary.config` 新增 `session_patches`（生产必须 0）与 `s0_mechanism/s0_version`（CLI 落盘）。
- 产物：`data-test/briefs/m43v/`、`data-test/plans/m43v-*`（gitignored）、
  `data-test/runs/m43v-v-brand/`、`data-test/evals/m43v-v-brand.json`。

### 51. 交付清单透明化：出处 + 证据等级 + 边界与缺口（S3-03/S3-05）

- `scripts/build_delivery_manifest.py`：`DELIVERY.json` 每个交付车型新增
  `source_url`（取 `state.asset_meta` 代表图 url，缺失为空串）和 `evidence_grade`
  （`accepted/probable/unknown/degraded`，由 `state.verifications` 的
  `accepted/identity` 与 `target.degraded_fill` 归一；不新增数据源）。
- `DELIVERY.md`：用户交付表新增“出处 / 证据等级”两列；新增“边界与缺口”小节，
  只渲染已有数字（degraded、citation_only、无图交付车型、`summary.delivery.unavailable` 归因）。
- 向后兼容：旧 `DELIVERY.json`（无新字段）仍可渲染；无网络、无 LLM、无新依赖。
- 测试：`tests/test_manifest.py` **5/5**；`tests/test_delivery_manifest.py` **3/3** 不回归。
- 影响面：只改交付清单脚本 + 测试 + 文档；未改 `src/`、`stages.json`、正式链路。

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

### 21. 交接同步与台账（2026-11-14）

- 台账补录 6 个 suite 目录：`run_ledger --check` = **107 条，0 issue**；HANDOFF/DEPENDENCIES 同步为 107。
- HANDOFF §0.0 增加 2026-11-14 收敛验收（P0–P4）结果、价值判断、调整/不调整清单与下一步；
- CURRENT-ARCHITECTURE：生产默认补 slots/search_key、词表静默、topup 默认 2（4 为 opt-in）、
  回退图纪律；§7 增加 30 run 验收快照；
- CODE-INDEX：补 `run_fulltest/eval_fulltest/eval_fulltest_repeats/eval_plan_snapshot`、
  `tests/test_no_legacy_tables.py`、`test_briefing.py`，以及 topup/slots/search_key 口径；
- DEPENDENCIES：测试数 47/16/16、台账 **107**（原写 108 是笔误；`run_ledger --check` 实测 107 条）；
- 历史文档（association/module-map/superpowers 等）里仍可能出现旧路径 `data/part_taxonomy.json`，
  以 `docs/vocabulary-policy.md` 与 `data/legacy/` 为准，不再逐个回填历史稿。

### 22. 安全脱敏（2026-11-14）

- P3 证据（`p7-screen-r3-20261114/c3-tractor/run/{fetch_log,state}.json*`）里出现 11 处
  `wx<16hex>`（第三方图片 URL 中的 AppID，按项目规矩视为敏感标识）；已用
  `scan_secrets.py --fix` 替换为 `wx-REDACTED`，复扫 0 hit。
- 注意：含该标识的 `388171a` 已在远程历史中（5 处）；本次只清理当前 HEAD。
  是否改写历史（force push）需单独决定；AppID 本身是公开标识，不等同密钥。
- 流程教训：提交前扫描不要用管道（`| tail` 会掩盖退出码），应单独跑并看 exit code。

### 23. 代码版本溯源加固（2026-11-14）

- 复核结论：P0–P3 运行时的工作树代码内容 == `d0a4cec`（`git diff` 为空；源码 mtime 03:07–03:09，
  首跑 03:17），因此实验结论不受“漏提交”影响；`388171a` 窗口不可复现，`d0a4cec` 起恢复。
- `engine._summary` 增加 `config.code_version`（git short sha），今后 run 自带代码版本；
  `retrieval_engine 47/47`。
- topup4 改动在 P3 尾声（06:03），默认仍 2，P2/P3 未使用；安全脱敏仅改 URL。

### 24. 名录草稿归档（2026-10-31 产物，2026-11-14 收编）

- 22 份 `roster-generate` 草稿（`status=pending_lock`，**从未锁定**）从 `data-test/` 根目录
  迁入 `data-test/corpus/roster-drafts-20261031/<类目>/`，附 `README.md` + `MANIFEST.json`
  （每个文件的时间/数量/sha256）。
- 类目分布：`沙漠牵引车` 18 次（候选 4–12，经历 12→10→4→11→6）、`牵引车` 4 次（候选 4）。
  当天 `src/equiplens/roster.py` 无提交，波动不是代码回归，**不可作基线**；
  生产/评测仍用 T13–T15 锁定名录。
- 这批 run 当时没有进 `test-log` 或本文件，属补登记——用途只能从时间与内容反推，
  不要为它编实验编号。

### 25. 口径清理（2026-11-14，审计轮）

> 目的：防止旧口径/已毙策略/过期数字被下一任当成"未完成"重新提出来。
> 全部为文档与注释改动，**不动生产行为**（唯一代码改动是守卫测试多一条断言）。

- **数字**：`retrieval_engine` 46/46 → **47/47**（`EXPERIMENTS-INDEX` E49、`backlog` B1、
  `optimization-round-20261114` 两处）；§21 的"台账 108" → **107**（笔误，实测 107）。
- **已毙/已收口不再当 TODO**：
  - `HANDOFF` §3 顶部加历史声明：§3 是 2026-11-08 快照，④⑤⑥（L1.5 清单/图片证据库/身份校验）
    已由 `retrieval_engine` 以另一种形态交付，**不要重新排期**；
  - `v1-retrieval-convergence-decision` 不变量 2 标注 **K5 已弃**（硬性 overview 门槛不成立）；
  - `optimization-round-20261114` 的"下一批建议"从 **D1**（已作废：rank 看不到图）改为 **D1a**；
  - `HANDOFF` 下一步"wide+来源护栏"补前置条件：**不是**重提 A1（来源自动降权已否决，误伤 10.7–54%）。
- **路径/产物名**：`skills/association/{SKILL.md,judging-rules.md}` 的
  `data/category_profiles.json` → `data/legacy/category_profiles.json`（并注明静默）；
  `SYNC-MANIFEST` 的 `data/*.json` → `data/**/*.json`（含 legacy 三表）、
  `SUITE-SUITE-SUMMARY.md` → `SUITE-SUMMARY.md`。
- **索引**：`optimization-index` 的 A4/B1/A1 轮次日期 11-13 → **11-14**；
  `CODE-INDEX` 补 7 个辅助模块、5 个实验/评估脚本、守卫计数改 4。
- **权威性**：`CURRENT-ARCHITECTURE` 的"5 输入交付（权威）49/50"改为**历史基线（填槽修复前）**，
  与 HANDOFF §0.0 的"不能当最终数字"一致。
- **词表政策**：`vocabulary-policy` §3 新增"已知偏差"——`textrun.load_profiles()` 仍默认加载
  `category_profiles`（无门控）、`style_vocabulary.json` 未纳管、旧链路模块自带词表；
  §6 守卫新增"主链 `retrieval_engine` 不得 import 旧链路模块"，`vocabulary_guard` **4/4**。
- **本轮未修（需拍板/单独立项）**：
  - `run_ledger` 把 23 个**有内容**的套件目录标成 `empty`（如 `ab-negative-20261113` 有 900 文件），
    `INDEX.md` 表体 84 行 vs 头部 107 条；
  - `retrieval_engine/web.py` `replan()` 硬编码 `"6x6"` 与 `"沙漠 6x6 牵引车 车型 品牌"`，
    对消防/扫路等类目套用了沙漠牵引车预设；
  - `planning.SERIES` 含品牌名 `HOWO`（注释自己写着"不要放品牌名"）；
  - `briefing.DEFAULT_NEGATIVE`（客车/SUV/房车…）无条件并入每条 brief 的 negative；
  - `source_registry` 在旧 text 链里靠 `trust`/`skip_domains` 影响评分与跳源，
    与"运维配置不参与准入"的口径不符。
- 影响面：纯新增归档，不改代码、不动任何 run；`data-test/corpus/**` 已在 `.gitignore` 白名单内。

### 26. 词表删除与参数去固定化（2026-11-14，用户批准）

**删除**（sha256 见 `docs/vocabulary-policy.md` §3；文件与引用一并清零）：

| 删除项 | 代码处理后 |
|---|---|
| `data/legacy/part_taxonomy.json` | `analysis.load_taxonomy()` 返回 `{}`；`make_ui_fixtures.py` 归档（缺表即显式退出） |
| `data/legacy/category_profiles.json` | `textrun.DEFAULT_PROFILES` 删除；`load_profiles()` 默认空，仅显式 `--profiles` 读外部文件 |
| `data/legacy/brand_aliases.json` | `imagesearch` 的 `LEGACY_BRAND_PATH`/环境开关删除；`BRAND_GROUPS` 恒为 `()`；`web.RuleVerifier.fallback_series` 删除 |

- 守卫强化：`tests/test_no_legacy_tables.py` 4/4——全量扫 `src/` 禁止出现三个表名/`data/legacy`，
  三表必须**不存在**，品牌组必须为空，主链不得 import 旧链路模块。
- 旧测试按新口径修正：`test_textrun` 用内联档案夹具（13/13）；`test_analysis` 的 3 条
  “词表在场”断言改为“去表化后自由填写/缺部位文案/显式 slot”（14/14，此前 11/14 长期红）。

**参数去固定化**（真实业务输入决定，不再写死）：

- `assemble_brief` / `generate_brief` / `scripts/build_brief.py --slots` **不再默认 12**；
  缺台数直接 `ValueError`，`build_brief` 的 `--slots` 改为必填；
- `page_budget` 只写 `{vehicle_slots}`（删 `total=20`、`part_pages=2` 两个死键）；
- `budget` 改为 `{max_queries: 3*slots+4}`（12 台时 = 40，与旧值一致；删 `max_rounds`/`max_models` 死键）；
- `stop_rules` 置空（全链不消费）。

**生产预设清理**：

- `retrieval_engine/web.py`：`replan()` 去掉写死的 `6x6` 与 `"沙漠 6x6 牵引车 车型 品牌"`，
  改由 `replan_queries(failed, brief)` 从任务单 `class/configuration` 派生；无 class 时只按失败车型发问
  （新增单测 `test_replan_queries_follow_brief_not_preset`）；
- `planning.SERIES` 移除品牌名 `HOWO`（新增断言：HOWO 两台车不得因品牌名被并成一台）；
- `briefing.DEFAULT_NEGATIVE` **保留**：产品负责人 2026-11-14 确认“大类排除”不算穷举表，
  已登记到 `vocabulary-policy` §2 允许例外。

**台账**：`run_ledger` 新增 `suite`（套件，指标在子 run）与 `artifacts`（有产物无 summary）两类，
`empty` 从 22 降到 **0**；`INDEX.md` 表体恢复为 **107 行**（此前 84 行 + 23 条“empty”）；
`--write` 补了 12 个 `RUN.json`，`--check` = 107 records / 0 issue。

**回归**：engine 48/48、planning 16/16、briefing 6/6、analysis 14/14、guard 4/4、
textrun 13/13、imagesearch 16/16、gate 11/11、ledger 8/8、association 12/12。

### 27. 车型标识归一化 + 第一段可核验性（2026-11-14）

**动机**：`HF 8066`（空格）、`CPD50-B`（2 位码）、`XS265HS`（标题写 XS265）在第二段被判
“不是同一台”；同时 `code in title` 是子串匹配，`RS45（B921）` 会用括号里的 `B921` 命中 `B921RR`。
第一段和第二段各写了一套正则，口径不一致。

**改动**（新增 `src/equiplens/identity.py`，两段共用）：

- 主码 = 括号外的第一个强标识；括号内是底盘/备注时不算主身份，但**括号外没有码时兜底使用**（北奔写法）；
- 允许字母/数字之间的空格、连字符、点；拒绝 `4X2`/`8方`/`340Hp`/`3.0T`/`12CUBIC`/`371HP`（构型与规格不是码）；
- 尾部后缀按同族处理：`XS265HS` ≈ `XS265`；**尾部 ≥3 字符视为上装/变体编码，必须整串匹配**
  （`EQ5253JSQZM` 不等于 `EQ5253CCYF2`）；点分段保留（`TGM18.290` 不等于 `TGM18.320`）；
- 匹配 = 左边界严格、右侧允许字母、不允许数字（`XS265` 命中 `XS265HS`，不命中 `XS2650`）；
- 【第二段】`RuleVerifier` 改用 `code_in_title()`；**不做主题判断**（电池/配件/航模页归门卫，见本轮结论）；
- 【第一段】`validate_extraction` 校验 `slots.model_code`（假码清空并计数 `dropped_invalid_code`），
  候选新增 `verifiable` / `code_core`，plan 的 `pool` 新增 `verifiable` / `verifiable_share`；
  **合并去重仍用完整码**（核心码合并留待下一步，避免把不同上装并入一台）。

**离线回放**（`scripts/evaluate_identity_match.py`，30 个 run / 1676 个资产，冻结证据、不联网）：

| 指标 | 数值 |
|---|---|
| 旧 confirmed 资产 | 345 |
| 新增可 confirmed（gained） | **59** |
| 失去 confirm（lost） | **0** |
| 已交付车辆因此获得 confirmed 图 | **16 / 270**（33.0% → **38.9%**） |

- 16 台里 10 台是干净修复（HF 8066 / RS45 / TGM18.290 / EQ2102 / J4.0-5.5XN 等）；
  4 台是尾部变体（XS265HS↔JSIV、HC228D↔228i、SR20MA↔SR20M、SR22-G↔SR22M），
  按产品负责人 2026-11-14 的规则（后缀是配置差异）放行，建议交付前抽检；
  2 台命中的是配件/电池页（cpd50j 马达、森泉电池）——**属于门卫职责，不归核验**，
  是否要加 gate v5 的“配件/商品”反例另行评估。
- 旧子串误命中（`B921RR`/`AP620H`/`M618A`/`LSS23022`）全部不再 confirmed（lost=0 说明它们原本
  也另有合法证据，或本来就未被交付使用）。

**实验条件**：回放只读 `data-test/runs/p7-screen{,-r2,-r3}-20261114/*/run/{state,summary}.json`；
30 个 run 的生产代码内容 == `d0a4cec`（见 §23），本轮改动只涉及核验匹配函数，不重跑检索、不触网。

**测试**：identity 10/10、planning 17/17、engine 48/48、briefing 6/6、analysis 14/14、
textrun 13/13、imagesearch 16/16、guard 4/4、ledger 8/8。

**数据**：`data-test/evals/identity-match-20261114.json`（gained/lost/delivered_flips 明细）。

### 28. 标识归一化的端到端验证（2026-11-14）

**条件**：3 个 case（c1 沙漠牵引车 / c4 叉车 / c5 压路机），复用 `p7-screen-20261114` 的
**冻结 brief + plan-ranked**（候选集合与基线完全一致），只换核验代码；实时抓取（有网络、
外网抖动），跑法与 `run_fulltest.py` 的 loop 段一致（`--web-only --plan --run-root --run-id run`）。
**这是单次 run，不是重复实验**：交付/备选与基线一致，因此只作“无回归”记录，不作效应量。

| case | 交付 | 备选 | degraded | confirmed | hits | 耗时(s) |
|---|---|---|---|---|---|---|
| c1 基线 → 新 | 10/10 → 10/10 | 4/4 → 4/4 | 9 → **8** | 1 → **2** | 365 → 365 | 148 → 178 |
| c4 基线 → 新 | 6/6 → 6/6 | 4/4 → 4/4 | 5 → **4** | 1 → **2** | 255 → 260 | 249 → 230 |
| c5 基线 → 新 | 14/14 → 14/14 | 4/4 → 4/4 | 5 → **3** | 9 → **11** | 930 → 924 | 392 → 359 |
| **合计** | **30/30 → 30/30** | **12/12 → 12/12** | **19 → 15** | **11 → 15（+36%）** | 1550 → 1549 | — |

- 交付车型集合逐台对比：**added/removed 均为空**（只改身份档，不换车）；
- 档位变化：c1 `HF 8066` probable→confirmed；c4 `CPD40-B` unknown→confirmed；
  c5 `XS265HS`、`HC 228D` probable→confirmed；
- c4 的 `CPD40-B` 命中的两条来源含电池适配页（标题），按职责归【门卫】——本轮只记录，不据此改核验；
- 成本：本轮 plan 冻结，只付 loop 段（manifest 口径 ¥0.13 / ¥0.13 / ¥0.23），
  与基线含 plan 的 ¥0.42–0.51 **不可直接比**；
- 台账：新增 `verify-identity-20261114` suite 记录，`run_ledger --check` = **108 条 / 0 issue**。

**数据**：`data-test/runs/verify-identity-20261114/<case>/{run/summary.json,run/DELIVERY.md}`。

### 29. 标识归一化的全类目筛查（2026-11-14，真实链路）

**条件**：`scripts/run_fulltest.py --cases data-test/evals/fulltest-20261114/CASES.json`，
10 个 case（6 known + 4 holdout）走**完整生产链路**：`plan_candidates`（LLM 规划+抽取，
并发 4、extract-mode=model、topup 2、glean 0）→ `rank_plan`（LLM）→ `retrieval_engine`
（web-only、下载 4 路）→ `build_delivery_manifest`。输入为 API 生成的冻结 brief（非手写），
无 legacy 环境变量，网络实时抓取。**与 p7-screen-20261114（r1）对比时注意：plan 是新生成的，
候选池与基线不完全相同**，所以下面同时给“同资产反事实”隔离匹配本身的效果。

| 指标 | 基线 r1 | 本轮 | 变化 |
|---|---:|---:|---:|
| 交付 | 90/90 | **90/90** | 持平 |
| 备选 | 38/40 | 37/40 | −1（h4 1/4，池 14） |
| degraded | 61/90 (67.8%) | **55/90 (61.1%)** | **−6（−6.7pp）** |
| confirmed（交付台） | 29/90 (32.2%) | **35/90 (38.9%)** | **+6（+6.7pp）** |
| known degraded | 40/62 (64.5%) | **0.574** | −7.1pp |
| holdout degraded | 21/28 (75.0%) | **0.698** | −5.2pp |
| no_hits | 2 | **0** | — |
| 成本（peak, ¥） | 4.681 | 4.347 | plan 波动 |
| 耗时合计 | ~2215 s | 2186 s | 持平 |

**隔离匹配本身的效果**（同一批新资产，仅把匹配函数换回旧正则）：
交付台 confirmed 旧 31 → 新 35（**+4**：h1 +2、c2 +1、c4 +1）；全资产旧 104 → 新 143。
其余 +2 来自 plan/抓取波动，不是匹配。**严格化的代价**：全 10 case 仅 2 个资产
旧能命中、新拒绝（h2 `CLW5250TQZZ` vs 标题 `CLW5250TQZZ3/5`），**0 台交付受影响**。

**表现变差的 case 归因**：
- `s6-mixer` degraded 10→12：新 plan 里带码候选（AXOR3236/SY5255GJB2E/CR412）抓到的标题
  基本不含码（“三一12方搅拌车”这类），属来源标题问题，不是匹配更严；
- `h4-crane-truck` degraded 5→7、备选 2/4→1/4：池仅 14 台（本来就 short），属已知供给波动。

**判定**：交付无回归、身份强度提升（+6 台），Go 仍为 true；h4/s6 的波动落在历史已知的
候选池波动范围内，但本轮低于其 3 轮基线区间，报告如实记录，不当作机制回归。

**数据**：`data-test/runs/p8-idmatch-20261114/`（`SUITE.json`、各 case 的 plan/summary/DELIVERY）；
评估：`data-test/evals/fulltest-eval-p8-idmatch-20261114.json`；台账 **109 条 / 0 issue**。

### 30. 标识归一化：三轮全类目（2026-11-14，r2/r3 补齐）

**条件**：与 §29 完全相同（同一 `CASES.json`、生产默认参数、真实网络、每轮重新 plan）。
三轮是**独立 run**，不是冻结 plan，因此差异同时含“匹配变化”和“plan/抓取波动”。

| 轮 | 交付 | 备选 | degraded | confirmed |
|---|---:|---:|---:|---:|
| r1 | 90/90 | 37/40 | 55（61.1%） | 35（38.9%） |
| r2 | 90/90 | 39/40 | 50（55.6%） | 40（44.4%） |
| r3 | 89/90 | 34/40 | 53（58.9%） | 36（40.0%） |
| **本轮 3 轮合计** | **269/270** | **110/120** | **158/270（58.5%）** | **111/270（41.1%）** |
| 基线 3 轮（p7-screen r1–r3） | 270/270 | 116/120 | 181/270（67.0%） | 89/270（33.0%） |

**净变化**：confirmed **+22 台（+8.1pp，相对 +24.7%）**；degraded **−23 台（−8.5pp）**；
交付 **−1 台**、备选 **−6 槽**。

**逐 case 三轮 confirmed 均值/极差**：c1 2.0（2–2）、c2 5.3（4–7）、c3 7.0（6–8）、
c4 2.7（2–3）、c5 11.7（11–12）、s6 0.7（0–2）、h1 1.7（1–2）、h2 1.3（1–2）、
h3 2.0（1–4）、h4 2.7（1–4）。

**回归项归因（不掩盖）**：
- r3 交付 89/90、备选 0/4 的 `h4-crane-truck`：**plan 池只有 9 台**（required 20），
  目标 `CA5250JSQP62K1L5T1E6` 被 gate/verify 全拒 + 28 次 blocked → `state=FAILED`；
  这是候选供给问题，与匹配无关（该 run 的 plan 在 `plan.json.pool` 可见）；
- `s6-mixer` 三轮 confirmed 0/2/0、备选 4/4/2：带码候选的**标题不带码**（来源问题），
  三轮都如此，属该类目的结构性短板；
- `h1` confirmed 2/1/2：标题写法波动。

**判定**：身份强度提升在 3 轮上稳定（+8.1pp），交付/备选的小幅下降由 h4 池短与 s6 标题导致，
不是匹配回归；Go 判定三轮均为 true（h4 单轮 7/8 不改变 holdout 交付率 27/28）。

**数据**：`data-test/runs/p8-idmatch-r2-20261114/`、`p8-idmatch-r3-20261114/`；
评估：`data-test/evals/fulltest-eval-p8-idmatch-r2/r3-20261114.json`；台账 **111 条 / 0 issue**。

### 31. 邻近构型检索（提案，2026-11-14）

产品负责人提出“主交付 = 精确车型 + 少量邻近构型参考（如沙漠牵引车配普通牵引车）、
按用户确认的配额分配，证据不足时第一段回环补邻近”。已写成设计分析
[`docs/adjacent-scope-design-20261114.md`](adjacent-scope-design-20261114.md)：
四层阶梯（exact/environment/platform/cross_vehicle，UI v3 §9 已有）→ 轴约束生成邻近
（不查表）→ 用户确认配额（默认 8+2）→ 有界回环（≤1 次、增量 ≤25%）→ 增量交付。
**未实现、默认关闭**；需产品负责人拍板 §12 的 5 件事（默认比例、邻近是否进正式交付、
是否允许自动回环、人审门槛、吊车域是否由轴约束自然得出）。


### 32. 外部咨询收录与评估（2026-11-15）

- 原文逐字归档：`docs/external/2026-11-15-doubao-retrieval-consult.md`（微信转发，**外部意见、未核实**，
  归档时已加提示，不作为实现依据）；
- 评估：`docs/doubao-consult-review-20261115.md`——事实核查（豆包 image `Count` **≤5**、
  免费 **500 次/月/账号**且与 Global 共用、接口**非 OpenAI 兼容**、image 结果**无正文**）、
  逐条采纳判断（视觉证据与通道接入“部分采纳”，LLM 型号冷启动“仅作查询种子”）、
  Loop 的反馈分类与节点路由、护城河/定位评估、预注册实验 V1–V5；
- 影响面：**纯文档**，不改代码、不改默认、不新增 run。


### 33. S0 输入识别评估与冷启动探针（2026-11-15）

- 新增**逐阶段决策台账**：`docs/external/doubao-consult-decisions.md`——把外部意见按
  S0 输入 / S1 第一段 / S2 第二段 / S3 交付 / S4 Loop / S5 产品拆成 51 条，
  每条列“专家意见 / 我们的对应 / 状态（待评·测试中·测试完成·采纳·改进·不采纳·已归档）”，
  决策日志 append-only；
- 新增 S0 评估：`docs/input-recognition-design-20261115.md`——TaskSpec 结构、文本/图片输入解析、
  TaskSpec→brief/plan 映射、多轮与歧义、能力边界；
- **V6 冷启动探针**（`scripts/probe_cold_start.py`，数据 `data-test/evals/cold-start-probe-20261115.json`）：
  10 类目 × `deepseek-flash` 生成 65 个型号，搜索可证实 **56（86.2%）**，
  与三轮真实检索池重合仅 **5（7.7%）**；专业类目衰减明显（消防 2/6、扫路 4/6）。
  结论：冷启动**只做查询种子**（证据门槛后才入池），不做权威型号池；
- **V8 初测（临时原型）**：20 条输入（历史 10 + 合成 10）测 TaskSpec 解析：intent 20/20、
  数量 19/19、class 19/20；暴露 4 个 schema 缺口（environment 缺失、modify 的 delta 语义、
  软/硬偏好未分离、class 同义/子类未规范化）。临时资产在 `tmp/s0-probe-20261115/`（gitignored，
  **未入库**，复用需申请），结论已写入 S0 设计文档 §4.5；
- 决策台账更新：S0-01 → 测试完成；S0-06 → 归档并改为 S3-05（交付透明化）；S0-02/04/05 加限定说明；
- 影响面：**纯文档 + 临时脚本**；不改 brief/plan/engine，不新增 run。


### 34. Badcase 登记册（2026-11-15）

- 新增 [`docs/badcases/README.md`](badcases/README.md)：编号规则 `BC-<模块>-<序号>`、
  状态机（open/fixed/verified/by-design/product-decision）、最小复现输入必须标 `[test]`；
- 新增 [`docs/badcases/S0-01-input.md`](badcases/S0-01-input.md)：S0-01 的 12 条 badcase：
  - open：scope vs backup（BC-S01-001）、部件 vs 视角（002）、class 别名（003）、
    品牌配额自动估计（004）、policy 枚举（005）；
  - product-decision：“同类参考”歧义（006）；
  - by-design：缺类目提问（007）、未指定替换型号自动另选（008，产品负责人确认）、
    文本“(图)”要求补图（009）；
  - verified：class/environment 拆分（010）、modify delta（011）、软/硬偏好（012）。
- 本轮**纯文档**：不改 `src/`、不改默认值、不新增 run；50 条基准输入仍在 `tmp/`（未入库）。


### 35. S0-01 v0.4 原型修复（2026-11-15）

- 按 badcase 顺序修复 5 条：scope/backup/delta 三分（BC-S01-001）、部件 vs 视角（002）、
  class 别名（003）、brand_quota 自动估计（004）、policy 固定枚举（005）；
  BC-S01-006 规则拍板（有上下文“同类”→scope.adjacent；无上下文“加”与“参考”并存→1 个 blocking 问句）；
- **定向回归 10 条新输入**（未复用旧 50 条，无需再次授权）：10/10 通过；
  临时记录 `tmp/s0-probe-20261115/regress-v4.md`（未入库）；
- badcase 状态：001–005 → `proto-fixed`（待生产），006 → `by-design`；
- 影响面：**仅临时原型 + 文档**；未改 `src/`、默认值，未新增 run。


### 36. S0-01 生产化：TaskSpec 规范化 + 50 条全量回归（2026-11-15）

- 新增 `src/equiplens/taskspec.py`：`normalize()`（固定 policy 枚举、软字段不得进 hard、
  自由词降级、modify→delta、brand_quota/foreign_ratio/origin/powertrain 归一、parts 去重、
  provided 无 model 过滤、提问最多 1 条且必须有 blocking）、`validate()`、`to_brief()`；
  **不含领域实体词表**；类目别名只能通过显式 `alias_map` 传入（policy §5）；
- 新增 `tests/test_taskspec.py`：19/19，不调网络；
- **V9 全量回归**（50 条授权复用：历史 10 + 合成 40）：50/50 通过、`validate` 0 问题；
  核对采用等价口径（环境同义、吨位进软约束、前脸可作 view、日系进 exclude）；
  临时审核稿 `tmp/s0-probe-20261115/bench-review-v4.md`（未入库）；
- badcase：001–005 升 `verified`，新增 013（无图却产出 provided）并修复；006 保持 by-design；
- 影响面：新增模块 + 单测 + 文档；未改 `briefing.generate_brief`、未改默认、未新增 run；
  `to_brief()` 已提供但**尚未接入主链**（合并语义留待 S0-05 session 设计时确认）。


### 37. A2：TaskSpec v0.4 接入正式链路 + 状态机索引（2026-11-15）

- 新增 `src/equiplens/taskspec_llm.py`：S0-01 的正式 LLM 抽取（v0.4 prompt），
  出口固定走 `taskspec.normalize/validate`；
- `src/equiplens/briefing.py` 新增 `apply_taskspec()`：把 TaskSpec 的 class/env/config/台数
  覆盖到 brief，并写 `brief.s0={mechanism:"taskspec",version:"v0.4"}` 与 `brief.taskspec`；
  `generate_brief(..., use_taskspec=True)` 时先 parse 再覆盖；
- `scripts/build_brief.py`：**默认走 TaskSpec**；`--legacy-brief` 显式回退旧的一次性解析
  （静默、无告警）；`--slots` 改为可选（TaskSpec 已给台数时可省）；
- 新增状态机索引：[`docs/STAGES.md`](STAGES.md) + [`docs/stages.json`](stages.json) +
  `scripts/check_stages.py`（6 阶段、0 问题）；S0 active=taskspec-v0.4，旧路径标 silent；
- 冒烟：`build_brief.py` 12 台沙漠牵引车 → `s0=taskspec`、class 正确、台数 12、
  parts/units 正常（临时产物 `tmp/s0-probe-20261115/smoke/`，未入库）；
- 测试：`test_taskspec` 21/21、`test_briefing` 6/6、`vocabulary_guard` 4/4、
  `check_stages` 0 问题；
- 影响面：S0 主路径切换；旧路径保留但默认不可达；未改 S1/S2/S3，未新增 run。


### 38. 换机器检查、待办与 S0-05 规划（2026-11-15）

- 新增 `scripts/check_machine.py`：一次跑状态机、S0/S1 相关单测、台账、密钥扫描；
  默认 9 项、`--full` 追加引擎/图片/分析；输出正式阶段版本（S0=taskspec-v0.4 等）；
- 新增 `AGENTS.md` + `docs/COMMANDS.md`：触发词“检查主体代码索引/新机器检查/换电脑检查”
  对应固定命令 `PYTHONPATH=src python scripts/check_machine.py`；
- 新增 `docs/BACKLOG.md`：BL-001（`generate_brief` 库默切换 TaskSpec + 改评估脚本）、
  BL-002（S1/S2 legacy 标注）、BL-003（S0-05 开发）；
- 新增 `docs/s0-05-session-loop-plan-20261115.md`：两层状态机、F1–F9 节点映射、
  patch 契约、打断语义、去重/幂等、Router、编排选型、T1–T16 测试计划、M1–M6 里程碑、
  V10–V12 实验与 6 个拍板点；
- 影响面：**纯文档 + 检查脚本**；不改 `src/` 行为、不改默认、不新增 run。


### 39. S0-05 Session 状态机与 Router 测试（2026-11-15）

- 新增 `src/equiplens/session.py`：Session 状态机（IDLE/ANALYZING/CLARIFYING/PLANNING/
  RUNNING/PAUSED/DELIVERED）、Patch（白名单 target）、soft/hard 打断、checkpoint 应用、
  交付去重、最大轮次、JSON 持久化；**未接引擎**（S4 仍 planned）；
- 新增 `tests/test_session.py`：**11/11**（创建/软补丁/破坏性确认/暂停恢复/幂等/非法 target/
  交付去重/轮次上限/持久化/分类规则）；
- 临时测试（`tmp/s0-05/`，未入库）：
  - 规则 router 调参集 28/28，但 **holdout 仅 7/14**（同义改写脆弱）；
  - LLM 探针 holdout **9/14**，hard 判定 13/14，但“同款更多图”会误判成加车型；
  - 结论：M3 采用 **LLM 提议 + 规则守卫 + 歧义提问**，规则不再单独决策；
- 新增 badcase：BC-S05-001/002 open，003/004/005 product-decision；
  参数按建议默认：max_rounds=5、delta 查询 25%/抓取 20%、提问 1 条/轮、JSON 持久化；
- 影响面：新增会话原型 + 单测 + 文档；不改 S0–S3、不改默认、未新增 run。


### 40. S0-05 两轴语义与交付编辑策略（2026-11-15，拍板后修订）

- 拍板：**约束强度**与**打断类型**分开——排除项（不要品牌/挂车）是 `enforce=hard` 的硬约束，
  但 `hard=False` 的 soft 打断（checkpoint 应用 FILL 过滤 + 下一轮负词），不取消在途、不重排配额；
  只有范围/数量/构型/重置才 hard 打断；
- 交付编辑：目标明确（“第 3 张/该型号”）→ **不确认**，旧资产标 `superseded` 并补新图，
  **交付前不物理删除**；目标不明确 → 1 个问题；“全部/整批重来” → 1 个问题；
- `session.py`：Patch 增 `enforce` 字段；clear destructive → hard=False/confirm=False；
  ambiguous → confirm=True；reset → hard=True/confirm=True；新增品牌替换分支；
- 测试：`test_session` **14/14**；调参集 28/28 按新口径重跑（调参集非泛化证据，
  holdout 仍以 M3 hybrid 复测为准）；
- badcase：BC-S05-003/004/005 → `by-design`；001/002 仍 open；
- 影响面：会话原型 + 文档；未接引擎、未改 S0–S3、未新增 run。


### 41. Router 同义改写策略（2026-11-15）

- 新增 [`docs/s0-05-router-strategy-20261115.md`](s0-05-router-strategy-20261115.md)：
  根因拆解（词法规则/缺上下文/动作边界/硬软混用/安全策略）、四层方案
  （LLM 提议 + context digest + 规则守卫 + 歧义提问）、动作 schema、模型与成本、
  分层 holdout 评估（A 同义/B 指代/C 多意图/D 删除/E 范围）、M3.1–M3.5 与验收门槛；
- 明确不写“同义词→target”词表；修正方式为“动作定义 + few-shot 例子”，
  且新 holdout 只用于验收、不参与调参；
- 影响面：**纯文档**；未改代码/默认，未新增 run。


### 42. S0-05 Router M3.1–M3.3：LLM 提议 + 上下文 + 守卫（2026-11-15）

- 新增 `src/equiplens/session_router.py`：动作 schema（16 个 target，非实体表）、
  LLM 提议 prompt（含 8 个语义示例）、context digest、确定性守卫（白名单/hard/enforce/
  删除确认/最多 3 target/低置信提问）、无 key 回退规则版；
- `Session` 支持注入 router；`interrupt` 自动带 `context()`（class/targets/delivered/last_patches）；
- 新增 `tests/test_session_router.py`：14/14（不联网）；
- **dev30 四变体**（临时 `tmp/s0-05/`，dev 用于调参）：
  - 规则 15/30；LLM 无上下文 29/30；LLM+上下文 **30/30**；+守卫 **30/30**；
  - hard 30/30、destructive/confirm 12/12；
  - 修正两处 prompt/guard：“只要/仅限”归 scope.ratio；plan.negative 不再覆盖已有的 hard；
- 说明：dev30 已参与提示词迭代，**不作为泛化证据**；M3.4 将用新 holdout 只跑一次；
- 影响面：新增 S4 原型模块 + 单测；未接引擎、未改 S0–S3、未新增 run。


### 43. S0-05 M3.4 新 holdout + M3.5 接入（2026-11-15）

- **M3.4 一次性 holdout（24 条，新写，未参与调参）**：
  - LLM + context + 守卫：**23/24（95.8%）**，hard 23/24、target 23/24、
    destructive/confirm **8/8（100%）**；
  - 规则版：13/24（同义/指代仍弱）；
  - 达到验收门槛（destructive 100%、hard ≥90%、target ≥80%），未据此调 prompt；
  - 唯一失败 H-14“这个不够，再补”：被判 `plan.quantity`，期望 `fill.quota`，
    登记 **BC-S05-006**（open），下一轮在新 dev 修、用新 holdout 验收；
- **M3.5**：`session_router.make_router(api_key)` 工厂，可直接注入 `Session`；
  `tests/test_session_router.py` **15/15**；
- 影响面：S4 原型 + 文档；未接引擎、未改 S0–S3、未新增 run。


### 44. S0-05 M4 初步：Session × FakeWorld（2026-11-15）

- `RetrievalEngine` 新增 `step()`（单状态推进），`run()` 改为循环调用；引擎 48/48 仍通过；
- 新增 `tests/test_session_engine.py` **4/4**：
  - engine 跑两步后“崩溃”，新实例同 run_root/run_id 续跑完成；
  - Session 在 engine step 之间 checkpoint，软补丁生效且不阻塞引擎；
  - 交付编辑目标明确不确认，旧资产 superseded、不物理删除；
  - 新增品牌走 delta run：只抓新 target，交付只增不减；
- **未覆盖**（M4.1）：单张纠错（verify.blacklist 后旧资产标 superseded）、
  “只重跑受影响 target”的真实 brief 变更（当前用 delta run 模拟）、3 个 live case；
- 影响面：引擎新增只读 step API；Session 仍为 S4 原型，未接正式 CLI/引擎默认；未新增 run。


### 45. S0-05 M4.1：纠错定位与 live 冒烟（2026-11-15）

- `Session.apply_pending` 支持**资产定位**：`asset_index`（第 N 张，含中文数字“第三张”）
  只降级目标资产，不再“删一张=全标 superseded”；同一消息多 patch 用**同一快照**，
  避免 `verify.blacklist` 后再按新列表错位；
- `verify.blacklist` 记录具体资产；`fill.replace`/`delivered.*` 共用定位；
- 测试：`test_session` **15/15**、`test_session_engine` **6/6**（新增纠错只降一张、
  删除只降一张）；引擎 48/48；
- **live router 冒烟 3 条**（真实 API）：`fill.quota`、`pause+scope` 稳定；
  多意图“第三张图换个正脸，另外再补两台重汽的”在两次调用间 target 组合有波动
  （置信度 0.72–0.82），不据此改 prompt；
- 未覆盖（M4.2）：全 live 检索会话（进度/打断/续跑）、真实 brief 增量重排、
  3 个 live case 的完整指标；
- 影响面：S4 原型 + 文档；S4 仍 planned，未接正式 CLI/引擎默认，未新增 run。


### 46. S0-05 M4.2：3 个 live 检索会话（2026-11-15）

- 用真实 `WebWorld` 跑 3 个冻结 brief/plan（h3 扫路车、h2 清障车、c4 叉车），
  Session 在 FETCH 边界 checkpoint，随后续跑、交付、纠错/删除：
  | case | 秒 | 查询 | 交付 | degraded | 版本 | 编辑 |
  |---|---:|---:|---:|---:|---:|---|
  | h3-sweeper | 180.6 | 36 | 6/6 | 2 | 4 | 纠错/删除各 1 张，均只降目标 |
  | h2-wrecker | 308.2 | 48 | 6/6 | 5 | 4 | 同上 |
  | c4-forklift | 215.8 | 39 | 6/6 | 3 | 4 | 同上 |
  | **合计** | **704.6** | **123** | **18/18** | **10（55.6%）** | — | — |
- 结果：`data-test/evals/session-live-20261115.json`（临时脚本 `tmp/s0-05/live_session.py`）；
- **关键限制**：
  1. 中途 checkpoint 的“都要正脸”只入 patch，**未改变引擎本轮检索**；真正“打断→增量重排”
     仍未实现（M4.3）；
  2. brief 增量/只重跑受影响 target 仍是 delta run 模拟；
  3. 编辑后“第 N 张”按**活跃列表**取号，登记 BC-S05-008（product-decision）；
- S4 仍 `planned`；未新增正式 run。


### 50. M4.3 A/B：5 case 基线与 session 对照（2026-11-16）

- 统一基线：新建 5 份 brief（`data-test/briefs/m43/`）+ 5 份 plan（`data-test/plans/m43-*.json`；
  **plan 是 gitignore 的可再生中间产物**，重跑 `scripts/plan_candidates.py` 即可得到同参数计划），
  两个臂共用同一 brief/plan；基线 `m43-base-*`（`-m equiplens.retrieval_engine --json`），
  session 臂 `m43-sess-*`（`scripts/run_session_case.py`，在第 2 个真实 FETCH 边界打
  `plan.add_targets` patch）。
- 结果（交付/备选/degraded/查询/耗时）：
  | case | base | session | degraded | patch 轮 Δ查询 | 占比 | base 秒 | sess 秒 | 耗时增幅 |
  |---|---|---|---|---:|---:|---:|---:|---:|
  | c1-desert | 10/10 + 4/4 | 10/10 + 4/4 | 7 -> 7 | 6 | 9.5% | 256.0 | 193.2 | -24.5% |
  | h2-wrecker | 6/6 + 4/4 | 6/6 + 4/4 | 5 -> 5 | 3 | 7.7% | 172.3 | 191.1 | +10.9% |
  | h3-sweeper | 6/6 + 4/4 | 6/6 + 4/4 | 4 -> 2 | 3 | 8.3% | 304.1 | 160.3 | -47.3% |
  | c4-forklift | 6/6 + 4/4 | 6/6 + 4/4 | 3 -> 4 | 3 | 5.3% | 395.4 | 235.5 | -40.5% |
  | c5-roller | 14/14 + 4/4 | 14/14 + 4/4 | 7 -> 5 | 3 | 5.3% | 248.4 | 171.4 | -31.0% |
- 四项门槛：exact 完整 **5/5**、重复交付 **0**、patch 轮增量查询 **3–6 条（4.5%–9.5% ≤25%）**、
  耗时 **4 降 1 升（最差 +10.9% ≤20%）** → **M4.3 PASS**。
- 数据：`data-test/runs/m43-{base,sess}-*`、`data-test/evals/m43-*.json`、`m43-ab-compare.json`。
- **S4 仍 `planned`**：A/B 只证明 patch 语义成立；session 尚未接生产入口（`build_brief`/
  交付链路，M6），按“active = 真实业务使用”的口径不提前切。
- 影响面：S0-05 原型 + 引擎 `apply_patches` + 新增两个脚本；未改 S0–S3。

### 49. BL-010 P0：TaskSpec 品牌/指定车型/排除项接线（2026-11-16）

- `taskspec.to_brief` 增加 `brands_include/brands_exclude/models_pinned/constraints`；
  `briefing.apply_taskspec` 透传到 `brief.request`。
- `planning.build_query_plan`：用户指定品牌生成 `brand` 维度查询（≤6 条）、指定车型生成 `pinned` 查询（≤6 条）；
  `negative_terms` 合并 `request.brands_exclude` + `constraints.exclude`。
- engine CLI：`pins` 默认取 `brief.request.models_pinned`（仍可与 `--pin` 合并）。
- 测试：`taskspec 22/22`、`planning 19/19`、`briefing 7/7`。
- 未做（P1）：`brand_quota/foreign_ratio` 软配额执行 + 交付披露；`scope` 邻近设计。

### 48. M4.3：Session patch 接入引擎（2026-11-15）

- `engine.apply_patches(state, patches)`：`fetch.filters.views/parts/quality` 写进 brief（views 只产生核验
  warning，不做硬过滤——视角不否决是 K3 已定案）；`plan.negative` 追加 `brief.negative` 并成为 FILL 过滤集；
  `plan.add_targets` 新增 Target 并让本轮只抓新增 target（delta）。
- `session.apply_to_brief(brief)`：同一套 patch 语义的纯函数版本；`session_router` 新增 `values` 结构化值透传。
- 测试：`test_session_engine` **12/12**（新增 views/quality/parts/negative/add_targets 五条）；
  `test_session` 15/15、`test_session_router` 15/15 不回归。
- **未做（需另一台机器资产）**：M4.2 三 case 的 live 复跑与四项指标（delta 查询 ≤25%、重复交付 0、
  exact 完整 100%、耗时增量 ≤20%）；S4 仍 `planned`。
- 影响面：S0-05 原型 + 引擎 `apply_patches`；未接正式 CLI/默认链路，未新增 run。

### 47. 交付编号口径与续接清理（2026-11-15）

- 拍板 **BC-S05-008**：交付资产用稳定 `seq`（原始编号），新资产 `seq+1`，旧编号不回收；
  删除/替换只标 `superseded`，不物理删除；“第 N 张”永远指 `seq=N`；
- `Session` 实现 `next_seq`/`seq`，`apply_pending` 按 `seq` 定位；新增
  `test_original_index_after_supersede`；`test_session_engine` **7/7**；
- 续接文档清理：`HANDOFF.md` 顶部“当前断点”设为权威（> STAGES > 历史章节），
  标记 §0.0/§0.1 为历史，补 M4.3 范围、seq 口径、push 状态与待办；
  `CURRENT-ARCHITECTURE.md` 顶部加 2026-11-15 覆盖说明，避免旧“feedback router/LangGraph”描述误导；
- 影响面：Session 原型编号语义 + 文档；未接引擎、未改 S0–S3、未新增 run。
