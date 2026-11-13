# 当前整体技术框架（单一事实源）

更新：2026-11-12  
用途：任何打包/封装/新会话先读这里，避免把旧策略、fixture、预置假数据带进产品。

## 1. 当前产品阶段

**检索模块 v1 收敛中；第一次用户交付准备阶段。**

- 正常检索：360 主通道，**N 槽（N = brief.request.page_budget.vehicle_slots，用户输入）**，意图排序，gate v4，RuleVerifier，fill，audit，交付 **N 主 + 4 备**；
- 已停止继续扩源（Query/Source/Platform 实验收口）；
- 第一次交付定位 **beta + 人审**，不是无人值守生产；
- 下一步：feedback router/session → LangGraph feedback spike。

## 2. 生产路径（normal）

```text
task-brief@v2 (API)
  → plan_candidates (Search + LLM 抽取 + provenance)
  → rank_plan (intent：N primary + 4 backup，N=用户输入槽数)
  → retrieval loop:
       LIBRARY_SEARCH → EXTERNAL_DISCOVER(360)
       → FETCH → VERIFY(gate v4 + RuleVerifier)
       → FILL → GAP_CHECK → DONE/FAILED
  → fetch_audit.html / state / evidence
  → analysis (vision, separate module)
```

**交付口径（2026-11-12 定）**：交付 = **N 主 + 4 备**。

- `N` 来自 `brief.request.page_budget.vehicle_slots`（用户输入，不写死）；
- 备选 4 台在**提交阶段**按优先级取（有核验图 > 有任意图；再按 pinned / 规划角色 / 意向名次），**没有图的车型不进备选**；
- **缺图不可交付（P0）**：主槽满但备选有图数 < 4 时，`GAP_CHECK` 把"备选缺口"当成 gap，从**既有 plan 池**继续抓（不新增规划、不重跑 planner），最多 3 轮；plan 耗尽才 `backup.short`；
- 补抓轮不经过主槽 FILL、也不受主检索 `max_queries` 闸门限制（否则会把已满的 12/12 误判成 FAILED）；
- **图片可得性（2026-11-12）**：按 host 学习下载失败（403/404/DNS/连接），连续 3 次即拉黑、后续直接跳过；
  单个目标连续 8 张硬失败即早停（把预算让给下一个候选）；
- **候选池下限**：`planning.pool_requirement = ceil(1.6 × (slots + backup))`；12 主 + 4 备 → ≥26，20 主 + 4 备 → ≥39；
  `plan_candidates` 的 `--limit/--per-query` 默认按此自动推导（用户显式传值则尊重），不足时打 WARN 并写入 `plan.pool`；
  池子仍不足时默认追加 **2 条**同义查询（`--topup 2`，可用 0 关闭），补到的候选仍走出处校验；
- **死图床监测**：`scripts/monitor_bad_domains.py` 汇总历次 run 的下载失败（按 host/错误类型），输出
  `data-test/evals/bad-domains-monitor.{json,md}`；**只做长期观测，生产不读取**；单轮内拉黑仍由 `DomainHealth` 负责；
- **缺图归因**：`summary.delivery.unavailable` 逐台给出 `no_hits / all_download_failed / gate_or_verify_rejected / not_delivered / not_fetched`，
  `summary.downloads` 给出 hits/downloaded/failed/blocked/gate_pass/拉黑域名。
- 审计页对入选备选显示「备选 · 已入选」。

代码位置总索引见 `docs/CODE-INDEX.md`。

关键文件：

| 环节 | 文件 |
|---|---|
| brief | `skills/task-brief/SKILL.md`、`src/equiplens/briefing.py`、`scripts/build_brief.py` |
| plan | `src/equiplens/planning.py`、`scripts/plan_candidates.py` |
| intent rank | `scripts/rank_plan.py` |
| loop | `src/equiplens/retrieval_engine/{engine,web,contracts,state}.py` |
| gate | `src/equiplens/gate.py` |
| verifier | `src/equiplens/retrieval_engine/web.py`（`RuleVerifier`） |
| audit | `scripts/render_fetch_audit.py` |
| analysis | `src/equiplens/analysis.py`、`docs/superpowers/specs/2026-10-31-analysis-schema-design.md` |
| eval | `data-test/evals/`、`scripts/eval_task_brief.py` |

## 3. P0 交付不变量（2026-11-12）

已实现：

- **交付台数 = 用户输入**：`page_budget.vehicle_slots`（主）+ `backup_slots`（默认 4）；
- **每一台交付/备选都必须有 ≥1 张可用图**；备选不够就从 plan 池补抓（2026-11-12，P0）；
- **交付优先于质量（P0，2026-11-12）**：任何情况下都要交付 N 主 + 4 备；图/身份不够时**降级填充**
  （probable/unknown 身份、低清、泛称）并在 `delivery` 标 degraded；**不得用换源/扩源解决**——
  扩源已收口，未获明确批准不得重开。
- **降级兜底已实现（2026-11-12）**：正常 FILL 只用 accepted 图；等所有层级/候选耗尽后，
  `DEGRADE` 调 `_degraded_fill` 用任意过门卫的图把槽填满，target 标 `degraded_fill`，
  `delivery.degraded_fill` 列出这些车；只有“连图都没有”才会 short/FAILED。
- 全局 asset 去重：已占槽 target 用过的 asset 不再给其他 target 占槽；
- 每个 target 的 fetch/verify/filled/`assets` attempt 写入 `state.attempts`（`assets` 为真实入库资产数，2026-11-12 修复此前恒 0）；
- `part_only` 标记（**2026-11-12 定案：只作审计/排序信号，不参与交付门槛、不拦截、不再作为待拍板项**）：`scene` 是门卫侧标签（single_vehicle / multi_vehicle / part），用于区分整车/多车/局部；FILL 只从 scene 派生这个标记。字段已进 `Target` 契约（dataclass + `to_dict`/`from_dict` + schema）。是否把交付资格上移到 VERIFY 属内部重构，不是阻塞项；
- code prefilter（可选，`--code-prefilter`）：code target 且 title code 明确不一致时下载前拒绝。

**未采用**：

- 硬性“part-only 不得占槽”：实测会把 12/12 降到 10/12，且改变 composition；当前只打标，供人审/后续排序。
- Platform union / Baidu 默认启用：完整 loop 对照失败（丢 HF8066、unknown 暴增）。
- body/tonnage 硬 guard：误杀目标。
- harvest 元数据：控制变量后无收益，代码已回退。

## 4. 生产 / 实验 / 已收口

### 生产默认

- 360 平台（**通道口径以代码为准**：`imagesearch.search_images_ex` 先取 360；360 的 relevant 数不足 `limit` 时依次用百度、Bing 兜底。百度在 2026-11-12 修复过一次返回类型 bug，修复后确实会参与兜底。`--platform-extra baidu` 是另一条独立实验路径，默认关）；
- gate v4 + RuleVerifier；
- intent rank；
- N 槽 = 用户输入（`page_budget.vehicle_slots`），不是固定 12；
- code prefilter 默认 **关闭**（实验通过但未默认）。

### 实验（不默认）

- `--platform-extra baidu`：仅实验/降级候选；
- `--code-prefilter`：低风险 prefilter，待产品决定；
- `--require-overview` 不存在；part_only 只标记。

### 已收口

- Query/Source/Platform 扩源；
- harvest title 元数据；
- body/tonnage guard；
- 多车型标题专用规则；
- specialized source 直接 harvest（360che 反爬、lmjx 超时）。

详见 `docs/recovery-strategy-closeout.md`、`docs/v1-retrieval-convergence-decision.md`。

**已毙/归档策略逐条判决（含"不许再提"清单）见 [`docs/killed-strategies.md`](killed-strategies.md)**。
2026-11-12 新增判决：三证②部件-可见性归档（挪到人机交互）、三证③改装-原厂毙、
`data/retrieval_strategies.json` 与 `--strategy` 删除（加载后从不消费）。

### 已归档、不再读取的配置（2026-11-12）

- `Brief.stop_rules` / `Brief.strategy_ref`：**只解析、不消费**；schema 保留仅为兼容旧 brief；
- `Brief.negative`：**在 `build_query_plan` 消费**（每条 query 追加 `-"短词"`），只影响搜索，不影响门卫/核验/占槽；
- unit 级 `budget` / `stop`：同上；
- `.env` 的 `LLM_MONTHLY_BUDGET_CNY`、`LLM_MAX_IMAGES_PER_CALL`：代码无引用，已从 `.env` 删除；
- 停止条件实际由代码决定：tier 耗尽、槽位满、`budget.max_queries`。注意该键名是历史命名，**实际约束的是累计候选车型数**（`budget_used.models`）；`budget_used.queries` 是真实搜索请求数，目前只做成本/延迟观测，不参与停止判断（2026-11-12）。

## 5. 数据与“不许假信息”规则

- 所有 brief 必须由 API 生成，不允许手工代写；
- eval 输出与 run 数据必须来自实际执行；fixture 必须标注 `fixture`；
- 打包时禁止用 `data-test/evals/*` 的预制 brief 当真实用户输入；
- 禁止把 `plan.json`、fixture、mock 图片当生产数据；
- `data-test/runs/INDEX.md` 是 run 台账；`docs/EXPERIMENTS-INDEX.md` 是实验索引；
- 若某策略已收口，不得在打包时恢复默认。

## 5.5 交付与监控（2026-11-12）

交付物分三层，不要混：

1. **用户交付物**：N 台主交付车型的图（部件图按 part 分组）+ 任务单摘要；
2. **内部监控**：每台实现状态（交付/备选/缺图原因）、degraded/citation_only、下载质量、
   `timings`（每个状态耗时）、API 成本（峰/谷两口径）；
3. **可复用中间产物**：任务单 JSON（分析模块输入）、plan（优先级先验）、部件图（知识库候选）、
   `evidence.db`、`audit.html`。

工具：

- `scripts/build_delivery_manifest.py` → `DELIVERY.md/json`（三层分开列）；
- `src/equiplens/pricing.py`：DeepSeek 官网价（`deepseek-flash` 输入 ¥2/¥1、输出 ¥8/¥4 每百万 tokens；
  Search/Fetch ¥5/1000 次），峰时段为北京时间周一至周五 9:00–12:00、14:00–18:00，
  其余（含周末/节假日）空闲；同一份用量同时给"全峰/全谷"两个数；
- engine 写 `summary.timings` 与 `summary.elapsed_ms`，每步状态一条 `{state, ms, at}`。

## 6. 当前未决

1. code prefilter 是否默认：已独立验证不影响交付构成，待产品决定；
2. 360 单点 fallback：百度仅作降级，未实现 health/circuit；
3. 第一次用户交付的反馈 router/session；
4. LangGraph 迁移：只做 feedback spike，不做核心重写。

> `part_only` 已于 2026-11-12 定案（只标记、不拦交付），不再列为待决项。

## 7. 当前状态快照（2026-11-12）

- 最新完整 normal run：`loop-p0c-20261112`，12/12，degraded 8，citation_only 1；
- P0 硬 overview 试验：`loop-p0-20261112` 10/12（已放弃硬规则）；
- 平台对照：`loop-platform-{360,baidu,baidu-filtered}-20261112`，Platform 不接入；
- code prefilter 独立对照：`loop-code-prefilter-20261112`，12/12 构成不变。
- **备选补抓回归（2026-11-12）**：`verify-backup2-20261112`，12/12（构成与 baseline 完全一致）+ 备选 **4/4、20 图**；
  一轮补抓新增 6 个候选（plan 26 台用尽），`queries 114 / models 26 / fetches 316`；
- **5 输入交付（权威，2026-11-12）**：`delivery-20261112-clean`，主 49/50、备选 16/20、峰值成本 ¥2.064；
  5 个类目分别 9/10、10/10、10/10、6/6、14/14（c1 另一次 10/10 → ±1 波动）；
- **negative A/B（2026-11-13）**：`ab-negative-20261113`，with/without 均 48/50 主 + 18/20 备，
  交付零差异；30 条查询回放 20 条完全相同、平均 1.6/20 URL 变化；同配置重跑自带
  49/50↔48/50、16/20↔18/20、成本 ±12% 的噪声 → **negative 收益未证实，按规则保留**；
- **契约回归（2026-11-12）**：`verify-contract-20261112`，12/12、degraded 8、citation_only 1，与 baseline 同构成；
  `budget_used = queries 72 / models 20 / fetches 244 / verifies 244`（证明旧口径把 20 当查询数，实际 72）；
  `attempts.assets` 已真实计数（15 台 >0），`part_only` 5 台，`state.json` 过 schema 0 错误。

## 7.5 交接与数据变更

- 换机器：`docs/HANDOFF.md` §0.1 + `docs/DEPENDENCIES.md`；
- 哪些 run 被重算、哪些结论作废、测试文件改了什么：`docs/DATA-CHANGELOG.md`。

## 8. 测试保真规则（2026-11-12 加）

> 这一段是为了防止“fake Asset 让测试变绿、生产字段没接”的问题再次发生。

1. **新字段必须四件套**：
   - 生产 dataclass / dict；
   - `from_dict` / `to_dict`；
   - `schemas/`；
   - 至少一个使用真实序列化的测试。
2. **fill/排序/交付相关测试**不得只用裸 dict；必须经过 `Asset.to_dict → from_dict` 或真实 fixture。
3. **每个决策必须有对应 invariant test**；没有测试的决策不能标记“已验证”。
4. **测试通过前**必须确认它走的是生产路径；mock 只能 mock 外部 I/O，不能 mock 掉正在验证的契约。
5. **P0 案例**：
   - `Asset.scene/overview` 已加 `to_dict/from_dict`；
   - `tests/test_retrieval_engine.py` 增加 Asset 序列化与 `part_only` 测试；
   - `schemas/retrieval-state.schema.json` 增加 `asset_meta/attempts`；
   - hard overview 的两种实现都记录在 `P0-REVIEW.md`，不再口口相传。
6. **封装检查**以 `CODE-INDEX.md` 的生产/实验清单为准；任何实验脚本不得成为默认入口。
