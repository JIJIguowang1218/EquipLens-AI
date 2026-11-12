# 续接文档：进度与待补信息

| 属性 | 内容 |
|---|---|
| 更新日期 | **2026-11-12** |
| 当前阶段 | **检索 v1 收敛：P0 交付不变量 + 第一次用户交付准备**。整体框架以 `docs/CURRENT-ARCHITECTURE.md` 为准；扩源线已收口。 |
| 用途 | 新会话 / 新成员 / 换电脑从此接续，不必重读全部讨论历史 |
| 最新提交 | 见 `git log -1`；工作树状态以 git 为准。整体框架/生产/实验边界见 `docs/CURRENT-ARCHITECTURE.md`。 |

> ## ⚠️ 新会话先读
>
> 1. `docs/CURRENT-ARCHITECTURE.md`（当前整体框架、生产/实验/已收口）
> 2. `docs/v1-retrieval-convergence-decision.md`（为什么停止扩源）
> 3. `docs/EXPERIMENTS-INDEX.md`（实验→数据→脚本→commit）
> 4. `docs/DEPENDENCIES.md`（依赖/模型/key/DB）
> 5. `docs/OPTIMIZATION-METRICS.md` + `data-test/evals/METRICS.csv`（优化统计边界）
>
> ## ⚠️ 新会话第一件事
>
> **先提醒用户提供 DeepSeek API key（`sk-...`）**，再开始跑真实检索。
> 仓库里**没有** key，也不要提交 key（`.env.*` 已 gitignore；key 文件在仓库外）。
>
> - 放置位置：`~/.equiplens/deepseek.env`
>   （Windows：`C:\Users\<用户名>\.equiplens\deepseek.env`）
> - 内容一行：`DEEPSEEK_API_KEY=sk-...`
> - 同一个 key 同时用于 Chat / Search / Fetch；按**成功调用**计费 $0.75/1000 次
> - 没有 key 时：门卫/抓取测试仍可跑（本地 CLIP 不花钱），但 `scripts/plan_candidates.py`、引用核验、重规划全部不可用；跑 loop 需加 `--no-citation`，且不能用 `--plan`
> - 单轮 12 槽实测成本：规划 $0.005 + 引用核验 $0.019 ≈ **$0.024**


## 0.0 当前进度与下一步（2026-11-12）

- 检索 v1 收敛：停止 Query/Source/Platform 扩源；normal 默认 360 优先，relevant 不足时百度/Bing 兜底（口径以 `imagesearch.search_images_ex` 代码为准）。
- P0：asset 去重、attempt 日志、`part_only` 软标记、code prefilter 可选；
  hard overview 已否（10/12 或 composition 变差），`loop-p0c` 12/12 保持 baseline composition。
- Platform 完整 loop 对照失败：Baidu union 丢 HF8066、unknown 暴增；只保留 opt-in/降级候选，不默认。
- code prefilter 独立验证：12/12 构成不变，accepted 236→224；可选。
- 360+Baidu 定向补位试跑未命中；专门来源 360che 反爬、lmjx 超时，暂不接。
- 下一步：
  1. 第一次用户交付（N 主 + 4 备，N = 用户输入槽数；beta + 人审）；
  2. feedback router + 短期 session；
  3. LangGraph 只做 feedback/session spike，不重写核心；
  4. 不恢复已收口扩源策略；不把 fixture/预制 brief 当用户输入。


### 0.0.1 新对话/新设备：实验记录模板（必须）

每次正式实验（不仅是新设备）在 `data-test/evals/METRICS.csv` 追加一行，至少：

```text
experiment_id, date, commit, brief_id, plan_id,
query_mode, platform_mode, sample_size,
delivery, degraded, citation_only, bonus,
verified_accepted, unknown,
human_precision, human_recall,
cost_usd, latency_sec, source, caveat
```

没有这些字段的实验，只能算探索，不能拿来做“优化提升”统计。  
初始 vs 最终的边界见 `docs/INITIAL-VS-FINAL.md`。

## 0.1 换电脑 30 分钟接续（2026-11-10）

### 1) 拉代码与 Python

```bash
git clone ssh://git@ssh.github.com:443/JIJIguowang1218/EquipLens-AI.git
cd EquipLens-AI
git log --oneline -1        # 应为当前 HEAD（本文档不锁定 commit）
```

- Python **3.11**（本项目在 3.11.5 上验证；不要用 3.13）
- Windows PowerShell 示例：
  ```powershell
  py -3.11 -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install -U pip
  pip install -r requirements.txt
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  ```
- macOS/Linux：`python3.11 -m venv .venv && source .venv/bin/activate`，其余同上。
- 依赖说明（`requirements.txt`）：
  - `pillow` 图片解码；`jsonschema` 契约校验
  - `uform[onnx]`：门卫模型 `unum-cloud/uform3-image-text-english-small`（约 **59MB**，首次运行自动下载，`gate.py` 已默认 `HF_ENDPOINT=https://hf-mirror.com`）
  - `torch` + `transformers`：Chinese-CLIP 探针（旧线，跑当前 loop 不必须，但 requirements 里保留；装 CPU 版，别拉 CUDA）
  - `crawl4ai`：旧渠道实验用；当前 loop 不依赖
- **不需要** pytest：所有测试是 `check()` 脚本，失败退出码 1。

### 2) 自检 + 全量测试（约 2–4 分钟，除模型首次加载外不联网）

```bash
PYTHONPATH=src python scripts/check_env.py             # Python/依赖/key/模型/文件自检
PYTHONPATH=src python scripts/run_ledger.py --check    # run 台账完整性（缺 RUN.json 会报）
PYTHONPATH=src python tests/test_planning.py           # 9/9（planner 纯函数）
PYTHONPATH=src python tests/test_retrieval_engine.py   # 28/28
PYTHONPATH=src python tests/test_imagesearch.py        # 13/13（全 monkeypatch，不联网）
PYTHONPATH=src python tests/test_gate.py               # 11/11（首次会加载 CLIP，约 59MB）
PYTHONPATH=src python tests/test_run_ledger.py         # 7/7（含 needs_review 不变量）
```

预期结果：`planning: 9/9`、`retrieval_engine: 28/28`、`imagesearch: 13/13`、`gate: 11/11`、`run_ledger: 7/7`。

历史遗留失败（与本轮无关，换机器仍可能看到）：`test_analysis` 11/14、`test_query` Q-10、`test_workflow` W-10（后两个因 `data-test/equiplens.db` 是空库）。

### 3) 跑一轮完整检索（含在线规划）

```bash
# 3.0 先生成任务单（API；不允许手工代写）
PYTHONPATH=src python scripts/build_brief.py   --input "沙漠牵引车（前脸、登车踏步、大灯、前轮拱、防护栏、保险杠）；沙漠/油田工况；6×6；12 台"   --class "沙漠牵引车" --slots 12 --out data-test/briefs/brief-c01-auto.json

# 3.1 现场生成候选（需要 key；输出 plan.json + api_log.jsonl）
PYTHONPATH=src python scripts/plan_candidates.py \
  --brief data-test/evals/task-briefs-20261109/brief-m1b-global.json \
  --out data-test/runs/plan-m1b-global/plan.json

# 3.2 跑 loop（隔离：空库 + 只用 plan + 新 run 目录；图片落 images/）
PYTHONPATH=src python -m equiplens.retrieval_engine \
  --brief data-test/evals/task-briefs-20261109/brief-m1b-global.json \
  --web-only \
  --plan data-test/runs/plan-m1b-global/plan.json \
  --run-root data-test/runs --run-id loop-m1b-global-v2b \
  --evidence-db data-test/runs/loop-m1b-global-v2b/evidence.db

# 3.3 生成审核页
PYTHONPATH=src python scripts/render_fetch_audit.py data-test/runs/loop-m1b-global-v2b
```

- 单轮 12 槽约 **8–12 分钟**、成本 **≈$0.02–0.03**
- `--web-only` 会走 `NullLibraryAdapter`（库内 0 候选），不会读历史数据
- 想复现 T38 的 12/12，用 `loop-m1b-global-v2` 的同一 plan；**新 run 必须换 run_id + 新目录**（隔离要求）

### 4) 图片与 run 产物的 Git 边界

- **`images/` 不进 git**（只提交 `state.json` / `summary.json` / `*.jsonl` / `evidence.db` / `audit.html` / `REPORT.md`）。
- 所以新机器上打开旧的 `audit.html` 会**看不到图**——要么把原机器的 `data-test/runs/<run>/images/` 整个拷过来，要么按 §3 重跑重新生成。
- `audit.html` 是相对路径引用 `images/...`，拷贝时保持目录结构。

### 5) 关键文件地图

| 用途 | 路径 |
|---|---|
| 门卫（预筛 + CLIP v4 + 分层） | `src/equiplens/gate.py` |
| 图源/下载/升图/相关性护栏 | `src/equiplens/imagesearch.py` |
| 网页世界 + 规则核验（身份三档） | `src/equiplens/retrieval_engine/web.py` |
| 状态机 + 交付守卫 | `src/equiplens/retrieval_engine/engine.py` |
| CLI（`--web-only/--plan/--evidence-db`） | `src/equiplens/retrieval_engine/cli.py` |
| 任务单生成（API + skill + 校验） | `scripts/build_brief.py`、`src/equiplens/briefing.py`、`skills/task-brief/`（SKILL.md + references + evals） |
| 在线规划（Search→LLM→出处校验） | `scripts/plan_candidates.py` |
| 意向排序（N primary + 4 backup，N=brief 槽数） | `scripts/rank_plan.py`；`--pin` 可强制保留 |
| LangGraph 迁移计划（暂不迁） | `docs/langgraph-migration-plan.md`；分支/feature flag/并行回归 |
| 规划核心（查询计划/校验/归并/coverage，可单测） | `src/equiplens/planning.py`（测试 `tests/test_planning.py`） |
| 审核页（四档徽章） | `scripts/render_fetch_audit.py` |
| run 台账（RUN.json / INDEX） | `scripts/run_ledger.py`；约定见 `data-test/runs/README.md` |
| 外国品牌召回诊断 | `scripts/diag_foreign_search.py` |
| 任务单 | `data-test/evals/task-briefs-20261109/brief-m1b-global.json`（12 槽：国产 8 + 国际 4） |
| 金标（门卫 52 张） | `data-test/evals/image-gate-52-20261109.json` |

## 0.2 当前进度（2026-11-10，T36–T39）

| 件 | 状态 | 关键结果 / 产物 |
|---|---|---|
| T36 核验重构 | ✅ | 身份三档 confirmed/probable/unknown；只拒构型矛盾；引用页可整台占槽；plan9 **12/12**，38 图 / 34 过门卫，7 台 degraded |
| T37 交付守卫 + 外国品牌召回 | ✅ | `summary.delivery`（required/delivered/missing/degraded/citation_only/status）；审核页双口径；`_relevant` 修 4 个 bug（多构型 AND、纯数字型号码、中外品牌别名、构型必须在标题）；`alias_query` 变体 |
| T38 独立测试（含外国品牌） | ✅ | 新 brief（国产 8 + 国际 4）；现场 7 Search → 23 候选（13 外国品牌）；v1 暴露配额 bug（20/12），修复后 v2 **12/12**，**5 台外国品牌占槽**（Zetros/Actros/H6066/T-Way/Kerax）；**8 台 degraded、1 台 citation_only** |
| T39 审核页四档 | ✅ | `已交付·已核验 / 已交付·未核验 / 备选·未占槽 / 未过门卫`；`delivery.bonus`；明确“分辨率只分档、不淘汰” |
| T40 planner v2 | ✅ | 逐查询抽取、`source_query` 出处校验、coverage 报告；出处 0/24→100%，但重复运行重合仅 26–31% |
| T41 去重 + 废弃 fallback | ✅ | 车型级 identity（同款合并、同品牌不同型号码不并）；去重移除 25–35% 变体；`discover` fallback 删除调用、CLI 拦截；A/B n=3 显示进口查询无增量；完整 12 槽 **12/12、无同款重复占槽** |
| T42 文件治理 / run 台账 | ✅ | 每 run 落 `RUN.json`；`INDEX.json/md` 自动生成；空目录/旧嵌套只标记；`recompute` 已清；新增 `data-test/runs/README.md` 与 `tests/test_run_ledger.py`（4/4） |
| T43 brief API 化 | ✅ | `briefing.py` + `build_brief.py`：LLM 输出分析字段，代码补配额/预算/tiers 并做双校验；产物带 `brief_meta.json`；手工 brief 标 legacy |
| T44 skill 必要性 A/B | ✅ | `task-brief@v2`（工程分析方法）+ `evals/evals.json` + `eval_task_brief.py`；with vs without：known-parts 5 vs 1 部件、口语类目 without 崩溃；n=3，待扩样与人工 rubric |
| T45 generic 只标不删 | ✅ | A2 plan 跑 12 槽：**12/12**，3 台 generic 占槽，82 唯一图/76 过门卫；审核页显示身份并可按泛称筛选；无候选被删 |
| T46 10 案例 skill A/B | ✅ | 5 旧 + 5 新品类（挖掘机/装载机/搅拌车/环卫压缩车/高空作业车），全部 3–5 部件、无具体车型；**v2 vs v1 只给格式**：自动断言 10/10 vs 3/10；人工 PASS/FAIL/证据见 `data-test/evals/task-brief-eval-v1b-20261111/review.html` |
| T47 意向排序 + 12+2 | ✅ | `rank_plan.py` 文本排序 12 primary/2 backup；`unit_quotas` 预留、补位不抢 primary；HF8066 rank6 占槽；完整 12/12，backup 仅在 primary 无图时补位 |
| T48 失败统计 + 先验接线 | ✅ | 4 run 失败统计：403/DNS + 拼图/多车/客车；12 条失败 URL 重放 **0/12**（同 URL 重试无用）；`analysis` 接收 kind/location/family/why 作为待验证先验；`WebWorld` 部件兜底 query + 阶梯日志 |
| T49 扩源/换源小测 | ⚠️ | 3 个无图目标：长 query 0；短 query/harvest 过门卫 34 张，但身份仅 1 张 probable；扩源能提量，但必须具体 query/来源页 + 核验 |
| T50 文件索引 | ✅ | `docs/EXPERIMENTS-INDEX.md`：E17b/E19/E20/E21/LangGraph/generic 的结论→数据→脚本→commit；扩源核对页 README/RESCUE；file:// 标注丢失原因 |
| T51 harvest 元数据 | ❌ 否定 | 首次 A/B 混淆 base/harvest；只取 harvest 图 21 张 A/B/C 均 0 通过；收益来自 base 标题，不采纳，代码回退；先修 query/来源相关性 |

最近 run：

- `data-test/runs/loop-m1b-global-v2/`：最终 12/12（79 唯一图 / 77 过门卫 / 43 进交付包 / 34 备选）
- `data-test/runs/loop-m1b-global-20261110/`：v1，保留作“配额未约束 → 20/12”的 bug 证据
- `data-test/runs/loop-ab4-a2-20261111/`：T41 去重后 plan 的完整 12 槽（82 唯一图、7 degraded、1 citation_only）
- `data-test/runs/loop-c01-plan9/`：T36 的 12/12（国内沙漠车，7 台 degraded）

细节见 [`test-log.md`](test-log.md) T36–T41、[`retrieval-experiments-log.md`](retrieval-experiments-log.md) E10–E15。

## 0.3 待讨论 / 待拍板（新会话先和用户确认）

1. ~~**34 张“备选图”是否随包交付**~~ **已定（2026-11-12）**：备选固定 **4 台**（按优先级从候选池取，不额外规划/检索）；其余素材仍留在 `images/` 与审核页“备选·未占槽”，不随包。备选缺图时在 `delivery.backup.short/images` 里显式暴露。
2. **`citation_only` 收紧**：TAZ4922 有 0 张核验通过的图，仅靠引用页占槽。建议改成“至少 1 张 unknown 级图”或标“待补图”，但会减少交付数（与“不能少交付”冲突），需要拍板。
3. **外国品牌是否默认搜**：已按“先控流程”做完并重测——planner v2 出处 100%；E15 A/B n=3（per-query 8、车型级去重后）里，加 `进口 {class} {conf} 车型` 的 B 组外国候选 16–20%，没有超过 A 组 18–24%，且会偶发丢 KAMAZ/TB800。**结论：不默认加进口查询**；要补外国车，应在 brief 里明确目标市场，或先有车型名再做“型号→图”检索（见 E15）。
4. ~~**隐藏的国产品牌名单**~~ **已处理（2026-11-11）**：`discover.py` fallback 已废弃，`WebWorld` 无 plan/models 直接报错，CLI 在联网前拦截 `--web-only` 无 `--plan/--models`；T32/T33 的“实时发现”只能当历史口径，不能再用于“360 有没有外国车”的结论。
5. **degraded 是否可接受**：12/12 里 7–8 台只有 probable 图；T41 的完整 run 里 3 台是 generic（OTTC、中东版、东风 400 马力）。要提高 confirmed 需要回访官网/公告页图集（外国车标题普遍不写 4051/3343），或限制 generic 占比，成本与优先级待定。
6. **质量排序未实现**：计划中的 `score = 4×res_high + 2×res_standard + margin + citation`、top-N 激活还没写；当前占槽基本按发现顺序。
7. **下载失败仍高（不是新问题）**：2026-11-10 起就有记录（E20/T48、`retrieval-experiments-log.md` 的失败表：403/DNS 为主，无图目标 2–12 台/轮）；**12 条失败 URL 阶梯重放 0/12**，结论是"同 URL 重试无收益，恢复必须换源/换查询"。**但扩源已收口：交付不足时先走降级填充，不换源**（2026-11-12 拍板）。
   - 已做（2026-11-12）：单轮内按 host 拉黑（连续 3 次）+ 目标级早停（连续 8 次失败，跨部件累计）；
     长期观测见 `scripts/monitor_bad_domains.py` → `data-test/evals/bad-domains-monitor.md`（只统计，不参与生产）；
   - 待做：跨 run 持久化黑名单（等监测数据积累后再定）；
   - 交付侧已加保护：缺图车型不进备选，备选不足从 plan 池补抓（2026-11-12）。

## 0.4 本轮新增的“不要误判”边界

- **已毙/归档策略先查 [`docs/killed-strategies.md`](killed-strategies.md)**：三证②可见性已归档（挪到人机交互）、三证③原厂已毙、`retrieval_strategies.json` 已删；再提之前先看判决。
- **通道口径以代码为准**：360 优先，relevant 不足时百度/Bing 兜底（`search_images_ex`）；不是"360 独占"。
- **缺图不可交付（P0）**：交付 = N 主 + 4 备，每一台都必须有 ≥1 张可用图；备选不够时 loop 从既有 plan 池补抓（不新增规划），plan 耗尽才报 `backup.short`。
- **必须交付、降级优先（P0，2026-11-12）**：凑不齐时用**降级填充**（probable/unknown、低清、泛称）并标 degraded，
  **不换源、不重开扩源**；扩源未获明确批准不得再启动。当前 unknown 兜底填充未实现，short 会如实报。
- **`budget_used.queries` 是真实搜索请求数**（含查询阶梯）；`budget_used.models` 才是累计候选车型数，也是 `brief.budget.max_queries` 实际约束的量。

- **分辨率不参与淘汰**：门卫预筛下限 320（不是 800）；`res_standard`（≥800）/`res_high`（≥1200）/`reference_candidate` 都只是标签。低清只记 `low_resolution` warning。
- **“过门卫”≠“交付”**：过门卫=预筛+CLIP；进交付包=车型占槽且图写进 `state.assets`；已核验=另有 accepted 的 `verifications` 记录。审核页四档就是这三个口径。
- **单元 quota 是硬上限**：`_state_fill` 同时受 unit quota 与全局槽位约束；v1 的 20/12 就是这里漏了。
- **degraded 只统计占槽车型**：不要把“抓过图但没占槽”的车型算进交付质量。
- **外国品牌不是 360 没有图**：E10 证明是相关性护栏 bug（多构型 AND / 纯数字型号码 / 中外品牌无别名 / 构型必须在标题）+ 拉丁查询在 360 返回垃圾；修完后 Zetros/Arocs/Volvo 都能进漏斗。
- **规划候选必须带引用**：LLM 不许凭记忆补车型；外国品牌能否出现取决于检索结果覆盖（E12），不是模型知识。
- **去重单位是“车型”，不是“品牌”**：同一品牌多台不同型号码（东风 EQ2251AX / EQ2220AX / DFV5253…）必须都保留；只合并同型号的不同写法（TAZ4922 的 3 种写法）。`planning.model_identity` 负责这条，别再加品牌上限。
- **brief 不再手工写**：新实验必须用 `scripts/build_brief.py` API 生成；`brief-m1-*.json` 是 legacy 手工输入，只能复现历史 run。
- **`part_views.json` 已毙掉（2026-11-11）**：不做部件→视角静态表/检索前视角预判；视角由用户看图判断，模型不因视角等待或过滤。
- **`part_axes.json` 不建静态表**：关系轴（exact/environment/platform/cross）由 `task-brief@v2` 按对象输出 `relation_axis`；设计轴（form/structure/cmf…）是“看什么”，两者不是一回事。
- **`discover.py` fallback 已废弃**：`--web-only` 没有 `--plan`/`--models` 会直接报错；不要再写“WebWorld 会自动实时发现”这种文档。T32/T33 的国产-only 结果来自这份 18 品牌名单，不能当 360 的真实分布。
- **进口查询不是默认项**：E15 n=3 显示它不增加去重后的外国车型数，反而偶尔丢掉 KAMAZ/MOL；默认查询保持现状。
- **`data-test/equiplens.db` 是空库**：库内检索当前恒为 0 候选，属预期。

## 0.5 读什么（按顺序）

1. 本文件 §0.1–§0.4（环境、进度、待拍板）
2. [`test-log.md`](test-log.md) T36–T41（每轮改了什么、数字、失败点）
3. [`retrieval-experiments-log.md`](retrieval-experiments-log.md) E10–E12（外国品牌、独立测试、默认品牌比例）
4. [`loop-m1b-global-v2/REPORT.md`](../data-test/runs/loop-m1b-global-v2/REPORT.md)（隔离性、5 台外国车、8 台 degraded、34 张备选）
5. [`image-filter-pipeline.md`](image-filter-pipeline.md) §8–§10（两段式门卫、v4、CDN 升图）
6. [`GLOSSARY.md`](GLOSSARY.md)（门卫 v4、res_standard/res_high、plan/citation/replan、占槽/备选）

---

## 0.9 历史快照（2026-11-08，UI 暂停期；仅追溯，不代表当前状态）

**阶段**：**UI 设计暂停**——暗色高保真 v3.3 是暂停点（待产品负责人评审，不再继续迭代）；主线切回**主体功能复盘**，已归档 11-08 专家咨询并逐条评估，下一步按 [`retrieval-strategy-review-20261108.md`](retrieval-strategy-review-20261108.md) 的 P0 推进。React 实现、接后端、部署均未开始。

**为什么暂停 UI**：视觉层已收敛到"评审可看"状态（v3.3），继续打磨的边际收益低于把主体功能（清单、证据库、身份校验）跑通；UI 的下一步是"评审 + 接真实数据"，不是再改配色。

**前情**：11-05 浅色高保真 v1（`docs/ui-hifi/`）；11-06 暗色 v2；11-07 四轮评审迭代到 v3.3（v3 结构/配色 → v3.1 字号与图标位置 → v3.2 尝试卡片边缘发光，已推翻 → v3.3 发光收回右栏并改为“漏光”，S2 全部常开）；11-08 归档专家讨论、暂停 UI、转入主体功能复盘。

**一句话结论**：UI 停在"静态可评审"；主体功能停在"文本检索与闸门可跑、清单未实现、图片证据不可复用"。下一阶段不是换框架，是补 L1.5 清单 + 图片证据库 + 身份校验。

### 最近工作（2026-11-08/09）

| 件 | 状态 | 产物 / 关键决定 |
|---|---|---|
| 专家讨论归档 | ✅ | `docs/discussions/EquipLens讨论11-8.md`（逐字副本，256 行，sha256 与 Obsidian 原文一致） |
| 专家意见逐条评估 | ✅ | [`retrieval-strategy-review-20261108.md`](retrieval-strategy-review-20261108.md)：13 条逐条评估——采纳 4 条（部件-环境相关性、三证核验、分析裁判、证据库）、部分采纳 5 条、不采纳 4 条；给出 P0/P1/P2 |
| UI 设计暂停 | ✅ | 本节 + `docs/ui-hifi-dark/README.md` 状态行；v3.3 冻结，等评审 |
| 主线切换 | ✅ | 下一阶段按 review 文档 P0 走：L1.5 M0–M2 → 图片证据库 v0 → 身份校验对照实验 |
| 开源 AI 搜索调研 | ✅ | [`research-ai-search-20261109.md`](research-ai-search-20261109.md)：9 条借鉴（含第二推荐）、LangGraph 只做检索 loop、检索中独立模块与 loop 设计 |
| 检索中 P0–P1 | ✅ | [`retrieval-p0-p1.md`](retrieval-p0-p1.md)：契约 + 状态机 + 检查点/事件 + 假适配器 + CLI；`tests/test_retrieval_engine.py` 10/10；演示 `data-test/retrieval-fixtures-20261109/` |
| 检索中 P2-W1 | ✅ | [`retrieval-web-p2w1.md`](retrieval-web-p2w1.md)：空库 + `WebWorld`（360）+ 规则核验 + `image_evidence` 落库 + `--web-only`；测试 13/13 |
| W1 网页冒烟 | ⚠️ 未达标 | 10 查询 / 68 候选 / 门卫 31 / **自动 2、人工约 1 真正可用**；360 分辨率瓶颈；见 [`web-smoke-20261109/report.md`](../data-test/runs/web-smoke-20261109/report.md) |
| W1-HD 复跑 | ⚠️ 未达标 | 接入“高清/大图”后：73 候选 / 门卫 35 / **自动 4、人工 3**；仅 C7H 有高清，仍低于 ≥10；见 [`web-smoke-hd-20261109/report.md`](../data-test/runs/web-smoke-hd-20261109/report.md) |
| 检索中 P2-W2 | ✅ 骨架 | [`retrieval-sources-p2w2.md`](retrieval-sources-p2w2.md)：源健康/熔断/24h 缓存 + SearXNG/Tavily 适配器 + 路由；测试 5/5；真实联调缺实例/key |
| 图片筛选复盘 | ✅ | [`image-filter-pipeline.md`](image-filter-pipeline.md) + [`image-usability-definition.md`](image-usability-definition.md)：**全 FAIL 是展示 bug**；可用口径拆两层；视角是噪声，不能当门槛 |
| 图片筛选 v3 | ✅ | 门卫补 4 反例 + `gate.assess_image` 分层 + 引擎视角降 warning；53 张同字节重评：门卫 34→31、**概览 13 / 部件 6**（旧“可用”4）；[`web-reassess-20261109/report.md`](../data-test/runs/web-reassess-20261109/report.md)；测试 7/7 |
| **W1-v5 复跑（达标）** | ✅ | 接入 CDN 升图（`!1200`）+ 门卫 v4 + 参考层后重跑 10 查询：72 候选 / 49 下载 / 39 门卫（54%）/ **概览 26 / 部件 18 / 参考 13**，**部件可用首次越过 ≥10 验收线**；18 张部件里有 **11 张来自升图**；见 [`web-smoke-v5-20261109/report.md`](../data-test/runs/web-smoke-v5-20261109/report.md) |
| 两段式门卫 + 98 张回放 | ✅ | 新增 `gate.prefilter`（确定性第一段，零模型）+ `check_v2`（同字节 A/B）+ `reference_candidate`（低清参考层）；预筛否决不进 CLIP。**门槛教训：800→320**（按 800 会白丢 18 张门卫放行的低清真车图）。98 文件 / **52 张唯一图（sha1 去重）**：v2 33 → v4 43（新拦截 3）、概览 17 / 部件 8 / 参考 26 = 43，闭合；[`filter-98-20261109/index.html`](../data-test/runs/filter-98-20261109/index.html)（逐张标签变换 + fail 原因 + 标签词典 + 合并同图）；`tests/test_gate.py` 11/11 |
| 门卫 v4：背景多车修复 | ✅ | keep 集加第 4 条「主体一台 + 背景另有停车」；`scene=multi_vehicle` 从硬拒降为 hint（只进参考层）。13 张“多车队列”误杀 **13/13 恢复**，9 张真坏图仍拒、31 张原通过不丢；唯一图可用 13/6 → **17/8**。实验表见 [`image-filter-pipeline.md`](image-filter-pipeline.md) §9 |
| CDN 后缀升图 | ✅ | `imagesearch.upgrade_image_url`：把 `!600`/`!550` 换成 `!1200` 再下载，失败回落原图。13 张带后缀参考图里 **10 张升到 1200×800 → 部件可用**（2 张 401/403 回落，1 张仍因 scene=multi 留参考层）；抽检高频能量是上采样的 1.6–2.2 倍（真细节）。预期唯一图部件可用 **8 → 18**，待 W1 复跑确认；`test_imagesearch` 9/9 |
| **M2 在线规划 loop（C01/12 槽）** | ✅ 12/12 | DeepSeek Search 生成 23 个带引用候选（含外国品牌）；引用核验 19/25 命中；loop 新增“池排空→重规划（≤2 次）”；47 图 / 42 过门卫 / 12 槽 DONE；API 成本 $0.023。见 [`loop-c01-plan4/REPORT.md`](../data-test/runs/loop-c01-plan4/REPORT.md) |
| **M1b 隔离 loop（C01/12 槽）** | ⚠️ 6/12 | 不读库/历史，候选只来自实时 360：12 台 → 20 张过两段门卫 → 18 条证据 → **12/12 台各有 ≥1 张过门卫图**；早前“6/12 完整覆盖”已更正（部件通过无可见性检测）；瓶颈是“候选名→同款图”召回（经销商页）与低清。见 [`loop-c01-isolated/REPORT.md`](../data-test/runs/loop-c01-isolated/REPORT.md) |
| **M1 最小 loop** | ✅ 骨架通 | 用 T19 的 C01（沙漠牵引车）转 brief，`--web-only` 跑真实 360：**DONE 3/3 车槽**，20 事件 / 6 queries / 22 fetches。过程中修了 2 个结构 bug：资产-部件绑定（一张图只能挂一个部件）、跨层抢证据（environment 覆盖 exact 的 unit_id）。见 [`loop-m1-desert.md`](loop-m1-desert.md)；`test_retrieval_engine` 15/15 |
| 来源页回访（实验） | ⏸ 负结果 | 搜索命中带 `link` → 回访文章页抽图 → 升图。公平 A/B：候选 72→128、下载 49→103，但 page 通道 56 候选只出 **3 张部件**（24 张图标被预筛拦），总部件仍 18、耗时 +23s → **净收益不明确，默认关闭，保留 `--harvest` opt-in**。详见 [`retrieval-experiments-log.md`](retrieval-experiments-log.md) E5 |

### 前端 UI 进度（暂停点，最新文件）

| 项 | 状态 | 文件 |
|---|---|---|
| 四页静态高保真 S0–S3 | ✅ v3.3 | `docs/ui-hifi-dark/{index,s0,s1,s2,s3}.html` |
| 样式/令牌 | ✅ | `hifi.css`、`s0.css`–`s3.css`、`fonts/` |
| 交互脚本/假数据 | ✅ | `hifi.js`、`data.js` |
| 设计依据 | ✅ | `DESIGN.md`（v3.3 §4.6 漏光 / §4.7 手风琴）、`CONFORMANCE.md`（§9–§12 四轮增量）、`README.md` |
| 截图 | ⚠️ 仍是 v2 | `shots/` 为 11-06 产物；v3.x 需在含 `data-test/ab-images/` 的机器上 `python docs/ui-hifi-dark/shot.py` 重出 |
| 浅色对照版 | ✅ 保留 | `docs/ui-hifi/` |
| React 工程 / 接后端 / 移动端 | ❌ 未开始 | — |

**暂停点判据**：1440/1366/1280 三档无横向溢出、无控制台报错、无破图；S1 八卡三行放下；S2 五卡常开；dock 中心偏差 0.0px。**未解决**：S2 相邻框标签可能重叠；`shots/` 未更新。

### 最近工作（2026-11-07，UI 迭代，保留备查）

| 件 | 状态 | 产物 / 关键决定 |
|---|---|---|
| 暗色高保真 v3 | ✅ 待评审 | `docs/ui-hifi-dark/`：清单/部件卡改序号槽卡结构；面板头加 12px 单色图标；关联度改单色阶梯 `#C7F14F/#AFD463/#93AE5E/#848D99`（跨类灰）；未选改压暗不透明；S2 图片 contain 贴边 + 框层按内容矩形；状态条黑白旋转环/静态 ◉ |
| 未选态根因 | ✅ | 半透明（`.fg opacity .46`）让暗底透上来；改为亮度/饱和 + 同色遮罩，`opacity` 恒 1 |
| S2 贴边根因 | ✅ | `.fg` 只有 max-width/max-height，原图小于画布时不放大（667×500 在 736×560 内四周留白 35/35/30/30）；改 `object-fit:contain` 并重算框层 |
| 框层精度 | ✅ | 扣掉 1px 边框偏移后，1440/1366/1280 三档偏差 ≤0.02px |
| 文档 | ✅ | `DESIGN.md` 升 v3、`CONFORMANCE.md` 增 §9 增量、`README.md` 增 v3 章节、本节同步 |
| 暗色高保真 v3.1 | ✅ 待评审 | 二轮反馈：面板头图标被 `.hd span` 误当 chip（黑框靠右）→ 改 `.cnt` 专用类；右栏字号整体上调（序号 11、名称 13.5、标签 10、原因 11）；关联度加同色辉光；S1 卡片改手风琴展开证据 |
| 暗色高保真 v3.2 | ✅ 待评审 | 三轮反馈「发光要的是卡片边缘、要显眼」：发光从记号改挂到卡片边框（同色边线 + 2px 近场环 + 30px 光晕，按档位递减）——**v3.3 已推翻这套做法** |
| 暗色高保真 v3.3 | ✅ 待评审 | 四轮反馈：① 主图区不要发光，只有右栏 → 车辆卡回中性表面；② 右栏不能「先描粗边再发光」→ 改为背后光斑 `::after` + `blur(12px)` + 三层负扩散，边线只留 15% 档位色；③ S2 全部常开同高 196px，点击只做选中 + 该部件框发光（含点框反向选中） |

**v3 的五条评审反馈**：① 未选车半透明与背景糊在一起；② 面板头左侧要有简约符号；③ 右栏条目「没有设计」，且关联度位置/方式/颜色都不搭；④ S2 第二辆车四边不贴边；⑤ 检索中/分析中要有旋转符号、完成后换静态符号，风格黑白克制。

### 现在能做什么

- **看 UI**：打开 `docs/ui-hifi-dark/index.html` 走 S0→S1→S2→S3；不带参数时 S1–S3 走 loading。只作评审/视觉基准，不再改。
- 复核 S1：8 卡三行（主图区无发光）；选中/未选/备选三态；右侧清单 8 条记录卡滚动，卡边按档位漏光。
- 复核 S2：右侧 5 条部件卡常开同高；点卡/点框双向选中并各自发光；S3 纸页。
- 重出截图：`python docs/ui-hifi-dark/shot.py`（Playwright + Chromium；需 `data-test/ab-images/`）。
- **看主体功能**：读 [`retrieval-strategy-review-20261108.md`](retrieval-strategy-review-20261108.md) §1 事实基线、§5 瓶颈排序、§6 P0/P1/P2；再读 [`discussions/EquipLens讨论11-8.md`](discussions/EquipLens讨论11-8.md)。

### 下一步（历史，2026-11-09；当前待办以 §0.3 为准）

1. **筛选线收口（已评估，不再调参）**：边界 9 张人工确认 → 门卫 0 阈值合理；CDN 升图收益 10/13；来源页回访净收益不明确。筛选侧到此为止，只保留金标回归。
2. ~~**打通最小 loop（手写任务单）**~~ ✅ 2026-11-10：M1 跑通 DONE 3/3，暴露并修复 2 个结构 bug；下一步是让 `EXTERNAL_DISCOVER` 真的“发现”候选（而不是吃 `--models`），并把证据落库。
3. **扩源（按 loop 暴露的缺口做）**：不先盲扩；loop 说缺“吊车/矿卡/部件特写”再补对应源，E5 实验留作方法。
4. ~~**L1.5 M0–M2**~~（历史）：brief 已由 `build_brief.py` 生成；`part_views.json` 已于 2026-11-11 毙掉（K3），`part_axes.json` 不建静态表（K4），见 `docs/killed-strategies.md`。
5. **P3 库内检索 / P4 部件级视觉**：`asset_part_feasibility` + 人工录入；100 张标注对比 CLIP/SigLIP2/DINOv3。
6. **UI 恢复条件**：产品负责人评审 v3.3 通过，且主体功能能产出真实清单/图片后再接；React 工程暂不启动。

### 已知边界（不要误当 bug）

- **UI 已暂停**：v3.3 是冻结版本，不再是“待办”；除非评审明确要求，不再改视觉。
- S1 清单 8 条在 456px 可视区内滚动（内容 1082、单条 124px），约 3.6 条可见；每条是独立卡，不是横线。
- S2 五张部件卡常开、匀高 196px，右栏内容 1014 / 可视 715，**三档视口都要滚动**（约 3.6 张可见）；这是“全部展开”的结果，不是 bug。
- S1 卡片展开是手风琴，同时只开一张；展开后本行变高，同行其它卡不被拉伸（`align-items:start`）。
- S2 相邻框标签可能重叠；选中框 `z-index` 置顶，但“标签跟随框左上角”的定位逻辑未改。
- S1 判断句是 block，`innerText` 多一个 DOM 空白；文案没有变化。
- 半透明压暗只用于图片；卡片/记录本身的不透明度始终是 1。
- 暗色版和浅色版共用 `data.js` / 图片路径；目录同层，`../../data-test/...` 不需要改。
- skill 安装在用户目录，不在仓库内；换机器/换会话需要重装，或直接读 [DESIGN.md](ui-hifi-dark/DESIGN.md) 的审查结论。
- `docs/ui-hifi-dark/shots/` 仍是 v2 截图（当时用真实现拍渲染）；v3.x 需在含 `data-test/ab-images/` 的机器上重出。
- 右栏漏光靠 `.rrow::after`（`z-index:-1` + `blur`），不拦截点击；主图卡不参与发光。
- **本 checkout 的 `data-test/equiplens.db` 是空库（0 资产）**；诊断文档里的 63 台/629 图是历史口径，真实素材需在含图机器上确认。
- **L1.5 只剩设计**：`part_views.json` 已毙（K3）、`part_axes.json` 不建静态表（K4）；brief 已 API 化，但 `coverage()`/惰性放闸未实现；不要按设计稿误以为已可跑。
- **分析模块未验收**：“能有效分析”目前是主观判断，缺金标评测；在把它当“证据裁判”前必须先做 50 张校准（见 review §3.5）。
- **视角不可当门槛**：`classify_view` 的 top1−top2 中位数 ~0.003（6 个标签几乎同分）；它只输出 `exterior_hint`，主图挑选仍需人工/后续视觉模型。
- **门卫单标签 verdict 在 ±0.001 上会翻转**：53 张同字节重评里 3 张由过变拒（2 拼图 + 1 内饰），其中 1 张只是边界（±0.001）；下一步做阈值扫掠，不要继续加标签硬调。
- **两段式第一段只挡硬事实**：`gate.prefilter` 只判字节/解码/格式/长宽比/近空白/缩略图级过小（长边 <320），不判语义。**不要把它设成 800**：按 800 会拦掉 30 张唯一图，其中 18 张 CLIP 门卫会放行（17 张部件特写），等于白丢素材；800/1200 的判断属于分层（概览/部件/参考）。
- **门卫 v4 对“真·多车队列”没有金标**：新 keep 标签「主体一台 + 背景另有停车」救回了 13 张经销商场地/新闻图，但本批 98 张里**没有纯队列样本**（被拒的 2 张是拼图），所以不能证明它不会放过“一堆车”。缓解：`scene=multi_vehicle` 只进参考层、概览/部件仍要求单主体；等主体检测（P4）再放开。
- **金标已落库**：`data-test/evals/image-gate-52-20261109.json`（52 张：可用 18 / 低清可用 26 / 坏图 8，含 1 张人工确认的“客车”误杀），以后换模型/标签先跑它。
- **“同图重复”按字节 sha1 判**，不按 URL：98 行 → 52 张唯一图（46 行重复），其中 1 对 360 URL 返回同一张图；对照页的“合并同图”按钮就是按这个口径收成 52 张。
- **旧冒烟批次的 PASS/FAIL 画廊按门卫 v2 生成**（`data-test/runs/web-smoke-*/all-downloads.html`），不随 v3 重刷；对照数字看 `web-reassess-20261109/report.md`。
- **回归里 3 个历史失败与本轮无关**：`test_analysis` 11/14（构型词表/缺部件/prompt 三项）、`test_query` Q-10、`test_workflow` W-10（后两个因 `data-test/equiplens.db` 空库）；`analysis` 三项待单独排查。
- **W1 冒烟批次没有任务单、也没有状态机事件**：`retrieval_web_smoke.py` 的输入是 10 条手写 `(查询, 车型)` 对（每种车 侧视/前脸 各一条，`limit=8`、`hd=True`），直接调 `imagesearch`，不经过 `textrun`/任务单/`events.jsonl`；可追溯信息只有 `report.json`（每查询 hits/gated/diag + 每行 title/url/尺寸）与 `all-downloads.json`。带状态机与检查点的是引擎入口（`--web-only`），两者不要混为一谈。

### 读什么

- **M1 loop 记录**：[`loop-m1-desert.md`](loop-m1-desert.md)（输入、三次运行轨迹、2 个 bug、未解决问题）
- **实验日志**：[`retrieval-experiments-log.md`](retrieval-experiments-log.md)（CDN 升图 / Scrapling 验证 / 来源页回访 的假设-数据-结论；含负结果）
- **术语/代号**：[`GLOSSARY.md`](GLOSSARY.md)（W1、门卫 v2/v3/v4、批次名、页槽、状态机、可用口径；看其他文档前先看这个）
- **本轮主线**：[`retrieval-strategy-review-20261108.md`](retrieval-strategy-review-20261108.md)（专家意见评估 + P0/P1/P2）
- **检索技术调研**：[`research-ai-search-20261109.md`](research-ai-search-20261109.md)（开源 AI 搜索、部件检索、LangGraph 边界、检索中 loop）
- **检索状态机**：[`retrieval-state-machine.md`](retrieval-state-machine.md)（Mermaid 图 + 状态表 + 检查点 + 失败分类）
- **建设路线**：[`retrieval-build-plan-20261109.md`](retrieval-build-plan-20261109.md)（P0–P6；直接实现 vs 需测试取舍）
- **P0–P1 实现记录**：[`retrieval-p0-p1.md`](retrieval-p0-p1.md)（契约、状态机、夹具、跑法、已知限制）
- **P2-W1 网页适配器**：[`retrieval-web-p2w1.md`](retrieval-web-p2w1.md)（360 层面、通道对照、降级位置、网页-only 跑法）
- **P2-W2 源路由**：[`retrieval-sources-p2w2.md`](retrieval-sources-p2w2.md)（健康/熔断/缓存、SearXNG/Tavily 适配器、E5 计划）
- **可用性口径**：[`image-usability-definition.md`](image-usability-definition.md)（新旧策略为什么数字差很多；门卫 vs 分辨率）
- **筛选管线**：[`image-filter-pipeline.md`](image-filter-pipeline.md)（每步谁负责；检索中 vs 检索后；全 FAIL 展示 bug 与归因；§7 v3 实测）
- **筛选 v3 实测**：[`web-reassess-20261109/report.md`](../data-test/runs/web-reassess-20261109/report.md)（同一批 53 张图的新旧口径对照）
- **两段式 + 98 张回放**：[`filter-98-20261109/report.md`](../data-test/runs/filter-98-20261109/report.md) / [`index.html`](../data-test/runs/filter-98-20261109/index.html)（逐张：预筛结论、v2/v3 裕量与竞争标签、fail 原因）
- **原始讨论**：[`discussions/EquipLens讨论11-8.md`](discussions/EquipLens讨论11-8.md)
- UI 设计：`docs/ui-hifi-dark/DESIGN.md`；对照/验证：`docs/ui-hifi-dark/CONFORMANCE.md`；入口/文件：`docs/ui-hifi-dark/README.md`；浅色版：`docs/ui-hifi/`；结构基线：`docs/ui-interaction-spec-v3.md` + `docs/ui-mock/v4/`
- 检索设计：`docs/roster-expansion-design.md`（L1.5）、`docs/retrieval-diagnosis-20261103.md`（瓶颈/优化优先级）、`docs/retrieval-module-design.md`、`docs/text-retrieval-design.md`
- 分析契约：`docs/superpowers/specs/2026-10-31-analysis-schema-design.md`

## 0.0a 2026-11-03/04 快照（历史：低保真、产品说明书与检索线）

> 以下是 2026-11-03/04 的历史状态，保留用于追溯；当前进度以 §0.1–§0.3 为准。

**阶段**：竞赛提交告一段落，转入**前端重做 + 检索优化 + 部署**。Python 侧（检索/分析/排版/导出）不动，重点是网页端重做。

**今日（11-03）完成**：

| 件 | 状态 | 关键产物 |
|---|---|---|
| 检索能力诊断（技术讨论） | ✅ 归档 | `docs/retrieval-diagnosis-20261103.md`：图片通道**只剩 360 可用**（百度 `antiFlag`/验证页、Bing 相关 0/12）；真短板是"**型号身份不可验证**"（门卫只判是不是工程车）；computer use 不改 IP 与验证码，不换；DSH 侧边栏技术上支持（`ctx.sidebarRightTabs` 公开席位），留作 L0→L1 叠加层 |
| 界面与交互规格 v2 | ✅ 待评审 | `docs/web-interaction-spec-v2.md`：**五界面 / 七状态**、逐界面版面+控件+状态+动效+跳转、技术栈定稿；v1 已标注作废 |
| 视觉语言样张 ×3 | ✅ **产品负责人："风格非常好"** | `docs/ui-mock/`（`s0` 立项台 / `s1` 结果筛选 / `s1r` 检索中）——墨色外壳 + 纸色成品、左侧测量轨、裁切标记、等宽型号；`shot.py` 可重渲 |
| 开发流程约定 | ✅ | **先低保真**（只做布局/状态/跳转/交互编排，不做精修）；**等待功能区与状态编排经产品负责人确认后**才进高保真 |

**2026-11-04 进展（低保真静态稿迭代）**：

- **S0 立项台重做**（`docs/ui-mock/s0.html`）：左栏整列顶到顶部（logo + 名称 + 最近）；阶段进度改为顶栏五段横线、占满工作区宽度；单个自然语言输入框（车型/部件/数量一并由模型解析）+ 独立"上传图片（可选）"；已删预算时间、版本、本地运行、高级设置、底栏；流式布局，1440 以外可缩放、窄屏收起左栏。
- **S1 检索中静态稿**（`docs/ui-mock/s1.html`）：左栏不变；搜索框转为置顶的"检索中"条；左区卡片网格（**每行 3 辆**，多出的在卡片区内滚动，不滚整页），每卡含主图（单击/右键循环）、图片数、关联程度、名称与构型；右区上为关联分析散文、下为清单横条（含关联原因）；确认按钮 sticky 底部，内容少时随内容、内容多时浮在卡片上方；`?s=start|mid|done` 三态（占位 / 部分返回 / 完成，完成态 = 6 推荐选中 + 2 备选灰卡）。
- **关联分析文案结构定稿**（跨阶段沿用，写进 `docs/ui-interaction-spec-v3.md` §9）：四层顺序 `exact → environment → platform → cross_vehicle`；一段散文陈述关联事实，**不写素材与放闸、不写检索先后**。高保真与接后端时按此结构生成，不得回退成流程日志或论文腔。
- **S2 素材与分析台静态稿**（`docs/ui-mock/s2.html`）：状态条改为分析；左侧画布拉伸到控件行上方、内嵌 16:9 照片（letterbox），左右箭头切车，控件行 `上一辆 / 图 n/N / 下一辆`，胶片式车辆缩略条紧贴底部按钮上方（点击跳转、当前高亮、备选灰化）；右侧部件分析一部件一横条，**按分析 schema 组织**（`term` 词表构型名 / `part_family` / `form` ≤2 句 / `cmf` / `intent` ≤1 句），并叠加四态（已框定 / 本图可见·待框选 / 在图 N 框选 / 本图不可见）；点行高亮图上框、点框同步右侧；切图后原图框保留；选中待框选部件可拖拽新建框、已有框可拖动调整；底部`确认并开始排版`沿用 sticky 贴底。
- **部件分析已回到分析 schema**（此前 S2 只用一句泛泛描述，未按约定）：字段与文风依据 `docs/superpowers/specs/2026-10-31-analysis-schema-design.md` §2.2 / §5，槽位与构型名取自 `data/part_taxonomy.json`，排版参照 `scripts/build_report_page.py` 的部件块（编号 + term + fam + form + cmf）。
- **S3 排版与导出静态稿**（`docs/ui-mock/s3.html`）：状态条改为排版；左侧单页画布（16:9 纸色成品页，块可点选/拖动，选中框+四角手柄，选中对象名显示在状态条）；右侧竖向页面预览（PPT 幻灯片栏位置，当前页描边、点击跳页，12 页：封面/方法/8 车型/总览/封底）；底部改为 `暂存` + `导出`，导出调 `showSaveFilePicker()` 弹系统保存对话框（取消不写文件，接口不可用则下载兜底）。
- **底部常驻输入框（dock）与阶段名**（四页统一）：底部动作坞只在中间栏内——收起时一行 `‹ 上一步 | 主行动（居中） | 输入框（占其右侧）`；点输入框展开为大框，主行动上移到右侧并出现"系统预判：回到 X · 只重做 Y"（只说步骤，不说时间），Enter 提交、失焦且空则收回。顶部进度条补阶段名：走过的灰显、当前纸色、未到不显示（回退后仍灰显）。`‹ 上一步` 只读，不改数据；修改只走输入框，一次确认。规则与回退判定表见 v3 §1.4 / §6。
- **四页静态稿齐了**：S0/S1/S2/S3 均已按同一套骨架（左栏 + 阶段名进度 + 状态条 + 底部动作坞）改造完毕，`docs/ui-mock/` 下 `s0.html`–`s3.html` 为当前版本；均已截图核对、无 JS 报错、无横向溢出。
- **本轮明确不做（已记录）**：用户就地改分析文本（高保真再做）、空状态/失败态（待定义）、键盘体系（需动态测试）——见 `docs/ui-interaction-spec-v3.md` §11。
- **交互文档换版**：新建 **`docs/ui-interaction-spec-v3.md`（当前唯一权威）**，覆盖 S0/S1/S2 的布局、状态、框选联动与关联文案结构；`docs/web-interaction-spec-v2.md` 顶部标注**已归档、不得据此实现**；`docs/ui-mock/README.md` 与本节续接指引同步改口径（先读 v3）。
- **待办（高保真阶段）**：~~层级颜色改为用户可读的明示色（绿/黄/橙 + 图例）~~ ✅ 2026-11-06 暗色 v2 已用四色索引（精确绿 / 环境青 / 平台橙 / 跨类玫瑰；无图例，靠文字标签）；框选缩放与轮廓吸附仍未做。

**前端技术栈（11-03 定）**：React 19 + TypeScript + Vite；CSS Modules + 设计 token（不用组件库）；Motion 做跨界面 morph；TanStack Query + SSE；React Router。框选用原生 `<img>` + SVG 覆盖层。**选 React 的关键理由**：DSH 侧边栏面板本身是 React 组件，日后编排台/交付台可原样复嵌进 harness，不必写第二套 UI。

**页面模型**：`S0 立项 → S1 检索/筛选 → S2 素材/分析 → S3 编排（框选/版面）→ S4 交付`；等待态（`retrieving`/`analyzing`/`composing`）**不单独成页**，是同路由的整屏 morph。判据：对象、主动作、空间模型三者都变才算一个新界面。

**待产品负责人拍板（4 项；未定则按建议默认推进低保真）**：

1. 基调：墨色外壳 + 纸色成品（**建议**，样张即此）vs 全浅色；
2. 框选：预置框微调为主（**建议**，快）vs 从零手画（自由，每页多 30–60 秒）；
3. 部件数：固定 5 个（**建议**：前脸/格栅/保险杠/轮眉/踏步）vs 3–8 自定；
4. 交付物：PPTX 必做，PDF + 网页册是否本期做（**建议**都做，各约 0.5 天）。

### 0.0b 2026-10-31 快照（历史，检索线）

**阶段**：文本检索 + 图片检索都可跑；关联清单（L1.5）已定为"模型自由判断 + 证据强制 + 校验兜底"，**skill 不再承载判断**（细节见 `docs/association-skill-archive.md`）。下一步是整体测试（闸门→runner→audit→报告），VLM 仍后置。

**10-31 完成**：

| 件 | 状态 | 关键数字 / 文件 |
|---|---|---|
| L3 闸门接入 `text-run` grade | ✅ | 双轨指标；离线回放 6,806 段，过闸 3.6%，A 字 4,028→1,810（保留 44.9%） |
| 关联清单 schema + 证据层 | ✅ | `skills/association/`（schema + `check_list` + `evidence_check`）；recommended 必须 E3，12 台硬要求 |
| skill 四轮 A/B | ✅ | v1 B 5/96 → v2 82/96（但 89% 是方向）→ 相关性打平（100% vs 100%，直证 19/18，层覆盖 9/6）→ 证据 11/12 vs 11/12 |
| **skill 降级** | ✅ | `SKILL.md` v1.0-downgraded：六条纪律转为可选 checklist；保留 schema/证据/校验/评测集 |
| 图片通道修复 | ✅ | 百度 `antiFlag`/验证页、Bing 污染；新增 **360 图片**通道；`_relevant` 护栏（非车词/型号代码/构型/品牌）；查询阶梯 |
| 门卫接入 + 外观判定 | ✅ | `gate.check_exterior()`（门卫 + 视角∈hero_45/side/front/rear）；105 判定→70 张（detail 19 / interior 3 / 门卫 13） |
| 实图核对 | ✅ **合格待测** | 23 车型、70 张图、22 个有图；产品负责人目测"没什么问题"，**未逐条打分**（`data-test/ab-images/review.html`） |
| 运行元数据 | ✅ | schema `run_meta`（model_id / prompt_version / evidence_index_version / run_at） |

其余层状态（10-30 已就绪，见 §0.1 与 §1）：L1 `build_plan`（query_meta 分层/预算轮转）、L2 `corpus`（按查询给词、site 开关默认关）、L4 `runner`（重试/降级链/断点）、L6 `audit` + `domainbench`。

**关键结论**：判断质量打平，**证据基础设施（E3 索引）与图片通道/门卫才是质量来源**；skill 的价值只剩 schema + 校验 + 可追溯。

**下一步（按序）**：

1. **整体测试（T19）**：闸门→runner→audit→报告全链路，带"闸门阈值扫掠"（放行率 × 精确率），主指标用"过闸 A 字/千字 + 页槽填充"；
2. **补证据索引**：扩到 39 车型（每型号 1 次 SERP），并跑"无证据"案例（压缩式垃圾车）验证"缺证据会不会编"；
3. **实图命中率**：当前记"合格待测"，需要逐条判定时填 `data-test/ab-images/verdicts.csv` 重跑 `scripts/image_ab_score.py`；
4. **VLM 启动**仍等整体测试结果（D7）。

**待产品负责人拍板**：P1–P3（文本爬取时机 / 关联分析层级 / skill 形态，见 §3.1）；主图是否强制 2 视角、分辨率下限 R、备选是否跑文本（设计稿 §9）。

**当日档案索引**：`docs/association-skill-archive.md`（skill 全过程）、`docs/association-evidence-ab-plan.md`（证据层与 A/B v3 规划）、`data-test/evals/ab-20261031/`（A/B 数据与评分：`EVIDENCE-AB.md`、`RELEVANCE.md`、`IMAGE-AB.md`、`scores*.json`）、`data-test/ab-images/review.html`（实图核对页）。

## 0. 部署形态（2026-10-17 讨论）

产品负责人确认方向：产品期采用**云端部署**（用户主机晚上断电, 不能当线上服务器）。共识框架：①"本地模型"=自托管模型（权重文件装进服务器环境即上云）, 用户永远只请求网页服务、零下载; ②分层原则——高频廉价判断（CLIP 门卫/探针）本地或服务器自托管, 低频高价值判断（VLM）走云 API; ③开发期单机, 演示期轻量云主机或内网穿透。正式结论待架构方案定稿（PRD 开放问题 #5 有了初步答案）。

## 0.1 AI 产品分层与当前研究层（2026-10-23 起协作约定）

产品负责人要求：以后按"AI 产品分层"方式共同优化，每轮明确研究哪一层。分层与当前状态：

| 层 | 职责 | 是否用 LLM | 当前状态 |
|---|---|---|---|
| L0 目标/任务书 | 定义找什么、不要什么（system prompt/任务说明） | 是 | 人类文档已有，未变成模型任务书 |
| L1 查询规划 | 意图识别（类别/车型/目标/约束/歧义）+ 查询改写/拆解/扩展 | **是（已验证）** | T18-pre 文章命中率 40%→100%；T18-broad 证明歧义与选源必须先做 |
| L2 检索执行 | 搜索、抓取、robots、配额 | 否 | 已实现，稳定 |
| L3 结果质检 | 段落抽取、类目相关性、来源质量 | **是（当前重点）** | 闸门 v1 已实现：对象锚定+主题排除+具体性，假阳性 6.9%/召回 85.7% |
| L4 迭代控制 | 缺口检测、换词/加源/停止 | 是 | runner 已实现（重试/降级/断点），待整体测试 |
| L5 结构化沉淀 | Facts/Descriptions 抽取 | 是 | 未实现，随 M4/下游 |
| L6 评估 | 策略 A/B、指标与回归 | 部分 | 运行台账 + 评测集 v1 + audit + domain-bench 已建 |

**当前研究层：L3 已收口（闸门接线、双轨指标、离线回放），进入 L1–L6 整体测试**。`intent.json` 与 `plan.json` 分开建 schema；L1 决定"问什么、去哪类源、问多少、排除什么"，L2 按计划确定性执行，L4 决定"是否再查/停止"。L2 已稳，暂不重做；每轮测试须写明：研究层、对照变量、验收指标。

**自由度原则（2026-10-23）**：写死不变量（robots/配额/账本/检查点/schema），内容知识放数据（来源注册表/类目档案/词表），判断放模型（意图/查询/选源/段落/停止）。长尾类目不枚举：通用层 + 类目档案叠加，新类目走"侦察 → LLM 提议 → 人工确认 → 缓存"；缺档案时用通用层兜底并标记 `profile_missing`。**禁止再往代码里加类目/站点特判**（现有 `BRANDS`/`VEHICLE_WORDS`/`SYNONYMS`/`BLOCK_URL_RE` 列为技术债，逐步迁到数据）。

## 1. 已完成

| 产出 | 位置 | 状态 |
|---|---|---|
| 项目总览 | `README.md` | 与 PRD 同步 |
| PRD v1.0 | `docs/PRD.md` | 定稿，含 8 个开放问题 |
| 报告增强研讨稿 | `docs/report-enhancement-proposal.md` | v0.1 待讨论 |
| 架构方案研讨稿（一） | `docs/architecture-discussion.md` | v0.2（交互范式已确认 / workflow-agent 分层 / skill 清单） |
| 数据模型规范（单车素材管理） | `docs/data-model-spec.md` | v0.1 定稿，待产品负责人逐字段复核 |
| 数据层骨架 | `schemas/equip-data.schema.json`、`db/schema.sql`、`src/equiplens/` | 可用：建库 / 导入导出 / 确认撤销 / 派生查询 |
| 数据层第一档测试 | `tests/test_data_layer.py`、`docs/test-report-data-layer.md` | 2026-10-10 执行，27/27 通过 |
| P1·M1 导入与判重 | `src/equiplens/ingest.py`、`src/equiplens/cli.py`、`tests/test_ingest.py` | 2026-10-12 完成：9/9 通过 + 27/27 回归 |
| P1·M2 确认工作流 | `src/equiplens/workflow.py`、CLI 子命令、`tests/test_workflow.py` | 2026-10-12 完成：11/11 三轮稳定 |
| P1·M3 库内检索 | `src/equiplens/query.py`、`tests/test_query.py`、规范 v0.2 | 2026-10-12 完成：组合过滤/聚类/相似检索/文字搜索/词表提名池 |
| 检索模块工具对标调研 | `docs/retrieval-tooling-research.md` | 2026-10-14 完成 |
| 检索模块设计研讨稿 | `docs/retrieval-module-design.md` | 2026-10-14 完成：D12/D13/D14 + R0–R7 + S1–S5 |
| M3.1 补丁 | `src/equiplens/doctor.py` 等 | 2026-10-14 完成：9/9 + 回归 58 项全绿 |
| 检索 R0 脚手架 | `src/equiplens/retrieval.py`、`review.py` 等 | 2026-10-14 完成 |
| 检索 R1 图文检索核心 | `src/equiplens/channels.py` 等 | 2026-10-14 完成 |
| 真实渠道（R7 首半段） | `src/equiplens/webchannel.py` 等 | 2026-10-14 完成 |
| 实时审核服务（意见 #10） | `src/equiplens/reviewserver.py` 等 | 2026-10-15 完成 |
| 数据分库与测试台账 | `docs/test-log.md`、`data-test/` | 2026-10-15/16 完成 |
| CLIP 门卫与判向体系 | `src/equiplens/gate.py` 等 | 2026-10-15/16 完成 |
| T7/T8 批次 | batch-roster2/gener-20261015 | 2026-10-15 完成 |
| 名录驱动搜图 | `src/equiplens/imagesearch.py` 等 | 2026-10-15 完成 |
| 判向探针 v2 | `src/equiplens/probe.py` 等 | 2026-10-17 完成 |
| 判向收口 | 规范 v0.2.5 | 2026-10-17 完成 |
| R2 首半：名录生成器 | `src/equiplens/roster.py` 等 | 2026-10-17 完成 |
| 搜图并行化 + T13 | `imagesearch.py` 等 | 2026-10-17 完成 |
| T14/T15 扩大检索 | roster.py 同义词、批次 craneH/L + r3loader | 2026-10-18 完成 |
| 调研语料采集批（T16） | `src/equiplens/corpus.py`、`tests/test_corpus.py` | 2026-10-22 完成 |
| **T17 语料重爬与设计文本筛选** | `data-test/corpus/batch-corpus-20261023{a,b}/`、`design-passages-20261023.md`、`review-corpus-20261023.html`、`docs/text-retrieval-design.md` | 2026-10-23 完成：10 篇 / 42,743 字；**A 类设计分析 2,698 字 = 6.3%**（叙述性正文 12.5%）；策略 v0.1 |
| **T18-pre LLM 查询规划预实验** | `tmp/corpus-plan-3-llmplan.json`、批次 batch-corpus-20261023c-llmplan | 2026-10-23 完成：设计语汇查询使有 A 段文章 **4/10→8/8**；`grade_batch.py` |
| **T18-broad 多车型放宽预实验** | 批次 batch-corpus-20261023d-broad | 2026-10-23 完成：起重机被爱采购商品页淹没；装载机命中学术文但豆丁只有预览；"翻斗车" vs "装载机"歧义实证；好文被 URL 规则误拦 |
| **T18-blind 编排器首跑 + 留出类目盲测** | `src/equiplens/{runlog,strategy,passage,textrun}.py`；`data/{source_registry,category_profiles}.json`；`schemas/{intent,text-plan}.schema.json`；`data-test/runs/` | 2026-10-23 完成：intent→档案→计划→执行→段落评估→低信度重规划→报告闭环；每次运行 events.jsonl + summary.json + report.md；CLI `text-run`；随车吊盲测 3 篇 / A 198 字 / 1.8% → replan→stop；高空作业车 v3 第 2 轮 6.6% → ok |
| **T18-budget 隐藏预算帽修复** | `textrun.py` 配额模型、`corpus.py` SERP 诊断、schema 上限 | 2026-10-23 完成：修复 `per=min(3,…)`、`quota≤查询数`、`schema quota≤10` 三个暗帽；`max_fetch` 真正生效（6→60 线性缩放）；`serp_looks_blocked` 诊断 |
| **T18-budget-curve 预算-产出曲线** | `data-test/runs/BUDGET-CURVE-20261023.md`、`data-test/runs/INDEX.md`（14 条） | 2026-10-23 完成：在线 4 档被百度验证页全拦；离线近似 **q3≈6 篇 A 2,068 字（5.2%）**，边际由"高产出源"决定；Bing RSS/HTML 不可用已记录 |
| **T18-eval L3 评测集 v1** | `data-test/evals/l3-relevance-v1.json` | 2026-10-23 完成：盲测 7 篇 A 级文章逐篇标注四级（A_cat/A_comp/A_gen/C），**关键词假阳性率 43%**（3/7 是空洞营销/竞赛攻略/毕设代做）；A_cat 真实产出仅 2,410 字（51%） |
| **T18-roster 全名录大规模文本筛选测试** | `data-test/runs/T18-ROSTER-20261030.md`、`data-test/evals/review-roster-20261030.html`、批次 `batch-corpus-roster-*-20261030` | 2026-10-30 完成：4 类目 39 车型（T13–T15 锁定名录），61 篇/3.65M 字正文，265 段模型判定；**V 3.2% / P 12.9% / G 9.2% / C 74.8%**（候选段口径）；39 车型仅 8 个有 V/P 素材（HOWO MAX/JH6/J6G/豪沃6X6/QY25K5C/QY35K5/SAC16000S/金刚S1 EV）；**A 档假阳性 40.4% 复现 L3 v1**；C 档 47% 是汽车之家首页/报价页 |
| **检索计划查询分层 + 信源定向 + 配置行过滤（待办1/2）** | `textrun.build_plan`（query_meta）、`corpus.collect_corpus`（按查询给词）、`passage.CONFIG_LINE_RE`、`source_registry.preferred_domains` | 2026-10-30 完成：查询按 vehicle/component/macro 三类配 relevant_terms；`site:` 定向 360che/21-sun；报价配置行判 C；回归候选段 **265→162（-39%）**，测试全绿 |
| **L4 执行 loop（runner）：重试+降级链+断点** | `src/equiplens/runner.py`、`tests/test_runner.py`，`textrun.execute` 已接入 | 2026-10-30 完成：Temporal 式重试语义（有限尝试/退避）、通道降级链（auto→延迟重试百度→Bing）、单元契约验收、状态 JSON 原子写续跑；runner 6/6 测试通过，真实小批 run-smoke-runner 验证 ok（2 篇/9 候选/auto 通道） |
| **误杀抽样检测（audit）** | `src/equiplens/audit.py`、`tests/test_audit.py`、`data-test/evals/audit/` | 2026-10-30 完成：C 档按"域×长度"分层抽样 + 强语汇/型号护栏队列 + 加权漏杀率估计（含 Wilson 95% 上界）；T18-roster 四批实测 C 档 6,076 段，抽样 23 条全判 C（估计漏杀 0%，95% 上界 14.3%），护栏 166 条抽查 12 条 0 命中；text-run 收尾自动生成 audit-sheet.json/md（run-chain2b 验证） |
| **确定性闸门 v1（L3）** | `src/equiplens/l3gate.py`、`tests/test_l3gate.py`、`data-test/evals/l3-gate-v1.{md,json}`、CLI `gate-batch` | 2026-10-30 完成：对象锚定 + 主题类型排除 + 具体性要求（部件/形态证据）；T18-roster 265 段金标评估：**精确率 93.1% / 召回 85.7% / 假阳性 6.9%**（关键词基线 40.4%）；实盘批次通过 5/750 |
| **域名基准与发现通道（domain-bench）** | `src/equiplens/domainbench.py`、`tests/test_domainbench.py`、`data-test/evals/domain-bench-20261030*/` | 2026-10-30 完成：同查询跨站点对照（A/千字、抓取成功率、robots），产出排行榜+升降级建议；首跑 18 域名/24 页发现 **www.yoojia.com（89.5 A/千字）并入库 high**；复测 26 域名/42 页（yoojia 定向 71.8/千字）确认；提案门槛改为新增需 ≥2 页/≥5K 正文、降级需 ≥3 页/≥15K |
| **闸门接入 text-run grade（10-31）** | `passage.gate_passages`/`grade_batch(gate_l3=)`、`textrun` 双轨指标、`strategy` 按过闸后判低信度、`scripts/replay_gate.py`、`data-test/evals/gate-replay-20261031.md` | 2026-10-31 完成：**基线 A 与过闸 A 同批并列**（`a_chars` / `gated_a_chars`、保留率、段通过率、拒绝理由分布），控制层改用 `gated_*`，无闸门指标的离线调用保持原口径；离线回放 4 批 6,806 段 → 过闸 248 段（3.6%），A 4,028→1,810 字（保留 44.9%）；吊车两类保留仅 20%（关键词 A 多为营销/参数）、沙漠牵引车 66%；textrun 13/13 |

## 2. 关键结论（30 秒版）

1. 现状流程是"人工 + 通用网页 AI"半自动；产品价值 = 流程产品化（闭集匹配、裁图、排版、溯源、合规）；
2. 车型识别重构为两阶段**闭集匹配**（名录 → 照片对号），FR-1.1 验收口径需改；
3. 素材不足是常态 → FR-1.2 优先级上调；竞品集 = 同类 + 近似类目；
4. FR-3 特征线规格已具体化；PRD 两处遗漏：封底、素材充分性评估；
5. 模块版图五块：素材资产库 + 检索 + 分析整合 + 报告规划 + 排版；统一分析 schema（结构/设计/意图三维度）是四模块公共合同；
6. 知识沉淀走进化式（数据飞轮）；检索模块"对话为壳、结构化对象为核"；
7. 部署形态定为**单机本地（SQLite + 文件系统）**；单车数据模型定稿；
8. 检索模块调研：四层栈均无需自研；
9. **文本检索（2026-10-23）**："车型名+评测/外观"查询产不出设计文本（6.3%）；LLM 查询规划提升文章命中率（40%→100%）；**关键词段落打分假阳性 43%**；预算边际由"高产出源"决定而非篇数；部件类型学归下游分析整合模块。

## 3. 下一步（按序执行）

### 3.0 当前主线（2026-11-08 更新；旧计划保留作对照）

> 状态已按“UI 暂停 + 主体功能复盘”更新；更细的“最近工作 / 已知边界”见 §0.9，本轮评估见 [`retrieval-strategy-review-20261108.md`](retrieval-strategy-review-20261108.md)。

| 序 | 事 | 状态 | 出口条件 |
|---|---|---|---|
| ① | **前端低保真 + 高保真 v1/v2/v3.3**：S0–S3 四页 | ✅ 2026-11-05/06/07 | `docs/ui-mock/v4/`（结构）+ `docs/ui-hifi/`（浅色）+ `docs/ui-hifi-dark/`（暗色 v3.3）均可走通 |
| ② | **UI 评审 + 视觉收口** | ⏸ **暂停**（2026-11-08） | 等主体功能产出真实清单/图片后再评审；v3.3 冻结，不再迭代 |
| ③ | **主体功能复盘**：专家意见评估 + 瓶颈排序 | ✅ 2026-11-08 | review 文档；P0 三件已定义 |
| ③.5 | **检索中 P0–P1**：契约 + 状态机 + 检查点 + 假适配器 | ✅ 2026-11-09 | `tests/test_retrieval_engine.py` 10/10；夹具演示 DONE（slots 3/3） |
| ③.6 | **图片筛选 v3**：门卫反例 + 分层口径 + 视角降级 | ✅ 2026-11-09 | `tests/test_gate.py` 7/7；53 张重评（概览 13/部件 6） |
| ④ | **P0-1 L1.5 清单**：M0–M2（数据 + `env_relevance` + `coverage()` + 惰性放闸） | 待开工 | 离线单测通过；决策链可审计 |
| ⑤ | **P0-2 图片证据库 v0**：`image_evidence` 表 + 查库优先 | 待开工 | 第二次查询命中库内记录 ≥50% |
| ⑥ | **P0-3 身份校验**：`region_match` 或候选聚类（二选一） | 待开工 | T14 四组错配拦截 ≥3 组，误杀 ≤10% |
| ⑦ | **接后端 / React / 部署** | 未开始 | 等 P0 完成后再排；UI 恢复条件见 §0.9 |

**流程铁律**：低保真阶段只回答"这一屏放什么、什么状态、怎么跳"，**不碰**字号/阴影/动效曲线；高保真阶段才回答"好不好看"。样张（`docs/ui-mock/`）是视觉参考，不是实现起点。**2026-11-08 追加**：UI 暂停期间，任何"改视觉"的请求先记录、不执行，优先补主体功能（L1.5 清单 / 证据库 / 身份校验）。

### 3.0.1 检索线与既有计划（2026-10-31 及以前，保留）

1. ~~M3.1 / R0 / R1 / 真实渠道 / 名录搜图 / 泛化测试~~ ✅；
2. ~~判向探针~~ ✅（2026-10-17 收口）；
3. ~~扩大检索测试 T13–T15~~ ✅（2026-10-18，三类目泛化验证通过）；
4. **文本检索线（R2 后半，2026-10-31 阶段主线；现已收口，保留作追溯）**：
   - ~~第 0 步语料采集（T16）~~ ✅
   - ~~第 0 步复盘（T17：设计分析 6.3%，策略 v0.1）~~ ✅
   - ~~T18-pre LLM 查询规划预实验~~ ✅（文章命中率 40%→100%）
   - ~~T18-broad 多车型放宽~~ ✅（暴露来源污染/歧义/误拦）
   - ~~T18-blind 编排器首跑 + 留出类目盲测~~ ✅（随车吊 1.8%→stop；高空作业车 6.6%→ok）
   - ~~T18-budget 隐藏预算帽修复~~ ✅
   - ~~T18-budget-curve 预算-产出曲线~~ ✅（q3≈6 篇 A 2,068 字；边际由高产出源决定）
   - ~~T18-eval L3 评测集 v1~~ ✅（假阳性 43%）；10-30 产品负责人逐篇裁决（意见 #20）：指向性标准=对象锚定
   - ~~T18-roster 全名录大规模文本筛选~~ ✅（10-30：39 车型/265 段判定，V 3.2%/P 12.9%/G 9.2%；A 档假阳性 40.4% 复现）
   - ~~确定性闸门~~ ✅（10-30：`l3gate.py` 对象锚定+主题排除+具体性；假阳性 6.9%、召回 85.7%；CLI `gate-batch`）
   - ~~`l3gate` 接入 `text-run` 的 grade 阶段~~ ✅（10-31：双轨指标 + 离线回放 6,806 段/过闸 3.6%/A 字保留 44.9%；`scripts/replay_gate.py`）
   - ~~关联分析与清单推荐模块设计~~ ✅（10-31：设计稿 v0.2 → skill v0.1 → 四轮 A/B → **降级为 schema+证据+校验**，全过程见 `docs/association-skill-archive.md`）
   - **下一步（10-31）**：①整体测试（闸门→runner→audit→报告全链路，带阈值扫掠，主指标=过闸 A 字/千字 + 页槽填充）②补证据索引到 39 车型 + 跑"无证据"案例 ③实图命中率（合格待测）④按结果再议 VLM
   - 信源定向：选 B（放弃 query 级 site 定向，保留域名信任加权）
   - 关联分析（10-30 新需求，见 §3.1 P2/P3）：缺口评估 → 关联提案（带依据/置信度/注意事项）→ 用户确认 → 检索
   - → T18 部件专项（12 部件 × 3 车型）→ T19 主题趋势 → T20 跨类目——仍只验证检索策略，不建类型学
   - **类型学与分析写作规范归下游分析整合模块**

### 3.1 决策台账（2026-10-30）

**已定**：

| # | 决策 | 记录 |
|---|---|---|
| D1 | 产品期云端部署；开发期单机 | 2026-10-17，§0 |
| D2 | 按 AI 分层协作（L0–L6），每轮写明研究层/对照变量/验收指标 | 2026-10-23，§0.1 |
| D3 | 自由度原则：写死不变量 / 知识放数据 / 判断放模型 | 2026-10-23，§0.1 |
| D4 | 指向性标准=对象锚定；三分类 V/P/G/C；L3 评测集逐篇裁决 | 意见 #20 |
| D5 | 战略：VLM 看图为主，文本换岗为语汇/定调/事实辅助 | 意见 #21 |
| D6 | 确定性闸门现在做（选 A） | 意见 #22；`l3gate` 假阳性 6.9% |
| D7 | VLM 后置：检索模块做完 + 整体测试后再议 | 意见 #22 |
| D8 | 信源定向选 B：放弃 query 级 site 定向，保留域名信任加权 | 意见 #22；site 实测无效 |

**待决（P1–P3）**：

| # | 问题 | 建议默认 |
|---|---|---|
| P1 | 文本爬取启动时机：清单确认后即后台启动 vs 图片确认后 | 清单确认后即启动（省墙钟；删车型则丢弃结果） |
| P2 | 关联分析层级：L1–L3 默认纳入、L4 逐条确认 vs 全部逐条确认 | L1–L3 默认、L4 逐条 |
| P3 | 关联 skill 形态：先文档+人工扮演 vs 等 VLM/API 就绪一起做 | 先文档+人工扮演（零成本验证） |
5. **交互层**（文本线核心能力之后）：选车确认包 + 意见 #15/#16 改进项一体建造；
6. **判向定位**（已收口）：嵌入式元数据；
7. 搁置事项：D10/D11 维持暂按推荐；data-export/import；M5 配额数值。

### 3.2 待设计：关联分析与检索清单推荐（2026-10-31 产品负责人提出）

**问题**：用户给定"车型类别 + 部件要求"后，先要产出一份**要检索的清单**（命中哪些车型/哪些相邻车型/哪些部件线索）。难点在于不是每个车型都有充足样本。

**已给的判断（原话要点）**：
- 沙漠牵引车本质是较常规的卡车头，其**踏步、防护栏、底盘**才是因沙漠环境而设计的部件；
- 所以沙漠牵引车样本不足时，**沙漠环境用车、牵引车、卡车头都应进入考虑**（可能都要：沙漠用车给特种设计参照，卡车头给基型参照，牵引车检索结果未必合适）；
- **部件级需求可以不限车型**（例："踏步的构型"可跨车型取），但这依赖分析，**规则系统覆盖不了各种情况**（尤其特殊情况）。

**暂定结论**：这是一个**独立的小模块**（关联分析 → 推荐清单），进检索之前跑，与 T18 的 `textrun`（检索执行）解耦。设计要点待讨论：关联维度（环境/用途/构型/部件/平台）、清单排序与配额、LLM 提议 + 人工确认的形态、清单 schema 与落账。与 P2（关联分析层级：L1–L3 默认纳入、L4 逐条确认）同一个问题域，讨论定稿后回写本节与 §3.1。

**2026-10-31 产品负责人补充的硬约束（页数预算 + 版式，决定模块形态）**：
- 报告约 **20 页**；**一车一页**（1~2 张主图 + 3~4 个部件裁图 + 分析文本框，排布紧凑），整车页 **10~14 个**；
- 部件补充是**一种部件集中放一页**（图上+文本框为一个单元，可排 5~6 个），整车分析做完后才需要，**是否单独成页需用户确认**；
- **"证据"= 图片，不是文本**：部件图全部从主图裁出，不需要多视角；文本可由分析模块生成（网上专业分析少、宣传多），**文本不是门槛**、只作定调/语汇加分；
- 由此两档判据：整车页＝≥1 张合格主图＋1 张备用、请求部件 ≥3 个可裁；专项页＝该部件在 ≥5 台车主图上可裁；
- 清单要**超量推荐**（推荐 N + 备选 2~3），爬完展示超出、自动定稿正确数量、超出作备选（转正才占页槽）；
- 仍有效的两条默认：**放宽上限=基型平台（跨车型部件需用户勾选）**；覆盖度判据已从"文本段数"改为图片口径（见设计稿 §3.3）。

**设计稿**：`docs/roster-expansion-design.md`（**v0.2**，2026-10-31）——部位在 intent 与 `build_plan` 之间（L1.5），含页槽模型、四轴阶梯、惰性放闸（触发=主图/可裁不足，不再是文本）、页槽排序与备选转正、最小代码改动清单；待确认参数 = 主图是否强制 2 视角 / 分辨率下限 R / 备选是否跑文本 / extra 基数 / 专项页 K。

**skill 已落地（2026-10-31）**：`skills/association/`（SKILL.md + schema + 3 脚本 + references + evals），校验脚本 `check_list.py`/`slots.py`/`inventory.py`，回归 `tests/test_association.py` 10/10；样例清单 `data-test/evals/sample-association-list-desert.json`（9 推荐 + 3 备选 + 2 排除，缺口如实报）。**预注册 A/B 判据**：`skills/association/evals/cases-20261031.json`（3 个输入 + rubric），用于"无 skill vs 有 skill"对照。

**A/B 首轮结果（2026-10-31，8 例）**：`data-test/evals/ab-20261031/REPORT.md`。判断质量两臂打平（6.00 vs 5.88，未达预注册的 +0.5）；合规性 B 好（硬错误 0 vs 1，schema 8/8 过）；**可用性 B 差得多（页槽填充 5/96 = 5% vs A 89/96 = 93%）**。根因：`inference 未验证不得进推荐` 这条纪律对**没有档案/名录的冷启动类目**是死结——这类目全部候选都是 inference，于是推荐位恒为 0，而这正是模块的核心场景。

**skill v0.2（2026-10-31 修订）**：新增 `status=provisional`（方向级可占槽，必填 `verify_by`；未验证的**具体型号名**仍不得占槽）；schema 补 `profile_status`/`gap_kind`/`blocking_scope`/`why_not_ready`/`confirmed_by`/`fact_status`；`check_list` 改为"方向可占槽、型号不可"，阻断支持部分范围；判据升级为 `RUBRIC-v2.md`（`fill_rate ≥0.85` + 硬错误 =0 + schema 8/8 为主指标，六维降为质量门槛）。

**v0.2 复跑（B2，同日，8 例）**：`data-test/evals/ab-20261031/scores-v2.json`。**fill_rate 82/96 = 85.4%（v1 为 5.2%）**、硬错误 0、schema 8/8、六维 5.50（A 5.875）。结论：**过交付门槛，但是"名义填充"——82 槽里 73 槽是 provisional，真正确认到车型的只有 9 槽（9.4%）**。下一步不是继续改 skill 文本，而是**补名录**（`roster_generation` 把 provisional 转 recommended）；v0.3 判据拟加 `verified_rate`（单例 ≥0.25、均值 ≥0.3）与 provisional 占比上限 0.6。

**相关性评测（2026-10-31，3 案例 65 条）**：`data-test/evals/ab-20261031/RELEVANCE.md`（+ `.html` 并排色块版）、池子 `relevance-pool.json`、脚本 `scripts/relevance_ab.py`。指标：车型精确率 **A 100% vs B 100%**；直证（label=2）**A 19 / B 18**；陷阱项被提出 **0 / 0**；层覆盖 **A 9/9 vs B 6/9**。结论：**skill 提升的是合规与可审计，不是"选得更准"**；B 因 `allow_cross_vehicle=false` 把平台/跨车型层压进 backlog，覆盖反而更差。评测池待产品负责人抽查（天锦是否 6×6、北奔 8×8、"厨余"是否算压缩式、80t 吨位门槛）后冻结为 v1。

**证据层与 A/B v3（2026-10-31）**：`docs/association-evidence-ab-plan.md`、`data-test/evals/ab-20261031/EVIDENCE-AB.md`。清单步骤原来**不检索**，车型无出处；v0.3 起每条占槽目标必须带 `evidence`（E3=标题含型号的详情页；provisional 至少 E1+verify_by），**12 台硬要求、弱关联尾巴标 weak**。沙案例实测：A 与 B 均 12 台、**证据有效 11/12（92%）**、强/弱 7/5、陷阱 0/0——**证据索引把两臂都拉高，skill 分差被抹平**；差异只剩标注方式（B 把北奔降 provisional、纯方向进 next_action）。结论：**证据基础设施 > skill 纪律**；skill 增量是 schema+校验+标注，不是选车。下一步：扩索引到 39 车型、跑"无证据"案例（垃圾车）验证 A 会不会编。

**图片检索通道修复（2026-10-31，实图核对时暴露）**：`imagesearch.py` 原来**静默返回无关图**——百度 acjson 返回 `antiFlag:Forbid spider access`、HTML 跳安全验证；Bing async/html 返回壁纸/梅西类无关内容；二者都被当成"成功"。修法（模块内，非脚本绕行）：①新增 **360 图片**通道（本环境唯一返回相关结果）；②`_relevant()` 相关性护栏 v2：非车词（战争/壁纸/漫画/车模/模型…）直接拒、型号代码（NG80/CA2191/X3000…）优先、**构型词必须一致**（6x6 不能是 6x2）、品牌必须出现；③通道状态 `ok/empty/blocked:X` 如实回传；④查询阶梯（型号+工程车 → 型号）。⑤`gate.py` 门卫（CLIP）此前**未接入抓图脚本**，且 `uform` 未安装→已安装并接入；⑥新增 `gate.check_exterior()`：整车主图 = 门卫放行 + 视角 ∈ {hero_45, side, front, rear}（部件特写/内饰不得当主图，但部件页仍可用 `check()` 保留特写）。实测 105 判定 → 70 张保留（detail 19 / interior 3 / 门卫拦 13）；北奔 NG80 改为真实 6x6 军卡图，解放"战争"污染消失。局限：门卫只判"单台工程车"，**不能判"是不是这一型号"**——型号身份仍靠标题+构型+人工复核。

**全过程档案（skill 从任务书到被毙）**：`docs/association-skill-archive.md`——时间线、四轮 A/B 与实图核对的目的/设计/数据、产品负责人评审意见、三次同类错误复盘、降级清单与执行记录。已按此执行降级（SKILL v1.0-downgraded）。

**2026-10-31 决策（实图核对后）**：
1. **视角交给交互**：不再用 CLIP 视角分数做排序/取舍（我原提的"hero_45 优先排序"撤销）；模块只记录 `view`/`score` 并在审核页展示，由人选主图。理由是 T12 已证 CLIP 判向边界不稳，不宜当决策依据。
2. **skill 降级**：预注册的 fallback 触发（图上 A 略好、B 仅多标签）→ 六条纪律从"硬规则"降为 `references/` 里的 checklist；保留 **schema + evidence 必填 + check_list 校验 + 评测集**。判断交还模型，**来源可追溯不变**（E3 门槛、URL/标题逐字校验、run 记录模型 id/时间/证据索引版本）。
3. **模型策略**：当前关联规划由大模型承担（强逻辑 + 长尾知识），**暂不做小模型替换**；但契约做成模型无关（schema/证据/校验/评测集），待有空再用同一评测集做小模型 A/B。成本判断：单案例规划 token 量很小，省钱空间在检索/抓图，不在规划模型。

**主线决策（2026-10-14）**：产品负责人选择**提前启动检索模块**——R0–R6 为主线，M4 VLM 打标延后。

可并行插入的专项菜单：FR-3 特征线 / 图像背景处理 / 铭牌 OCR 与闭集匹配。

**P1 里程碑总账**：

| 里程碑 | 内容 | 测试 | 成本 |
|---|---|---|---|
| M1 导入与判重 ✅ | 批量导入 → 解码尺寸 → sha256/感知哈希 → 原图落盘 → unbound 入库 | 9/9 + 27/27 回归 | 零 |
| M2 确认工作流 ✅ | 车型管理 / 对号 / 打标确认 / 拒绝 / 裁图 / 摘要 | 11/11 三轮稳定 | 零 |
| M3 库内检索 ✅ | 组合过滤 / 聚类 / 相似检索 / 词表服务 | 11/11 + 迁移测试 | 零 |
| M4 VLM 自动打标 | 模型网关薄封装；输出约束过 schema | mock 网关单元测试 | 起产生 API 费用 |
| M5 评测集 v0 + 第二档 | 历史散图 30–50 张黄金集；FR-1.1 验收指标 | 评测报告 v0 + 基线数字 | 需素材到位 |
| M6 收尾 | ingest 批处理 CLI、成本报表、使用文档 | 端到端演练 | 零 |

等产品负责人的输入：

0. **P1–P3（见 §3.1）**：文本爬取启动时机 / 关联分析层级策略 / 关联 skill 形态；
1. 文本 LLM provider/key/预算（暂缓，等整体测试后再定）；
2. VLM 选型 + API key + 预算量级（后置，整体测试后启动）；
3. M5 前：评测集素材 30–50 张历史散图 + 设计师标注标准答案。

## 4. 待补充信息（12 条，完整表述见研讨稿 §5）

| # | 问题 | 影响 |
|---|---|---|
| 1 | 汇报会上客户最常追问/质疑什么？ | 增强页型取舍 |
| 2 | 单次项目竞品数量与品牌家族数常态？ | 成本与版式 |
| 3 | "最重要品牌"默认清单认可度与增删？ | FR-1.2 / FR-4 / 市场格局页 |
| 4 | 近似类目类比链符合内部惯例吗？ | FR-4 竞品集定义 |
| 5 | 人工描一张特征线图平均耗时？ | FR-3 收益量化 |
| 6 | 情绪版意象图来源与工时？是否提前到 P1？ | 情绪版排期 |
| 7 | 封底内容构成？ | FR-5.3 |
| 8 | "指定部位"由谁确定？与附录 B 词表关系？ | FR-2.3 |
| 9 | 现用网页 AI 是哪个？满意/不满意点？ | 竞争基线与评测对照 |
| 10 | PPT 比例与母版源文件现状？ | FR-8 / 开放问题 #4 |
| 11 | 素材发通用网页 AI 是否被客户默许？ | NFR-7 卖点 |
| 12 | 各环节工时占比拆解？ | 开放问题 #1、MVP 优先级 |

## 5. 待拍板（3 项）

1. **MVP 是否内置第一期增页**（竞品总览 / 方法与来源说明 / 封底）；
2. **设计机会点页**是否加入；
3. **简版情绪版**是否提前到 P1。

## 6. 新会话续接指引

1. **先读**：§0.1–§0.5（2026-11-10 最新：换机、依赖、测试、待拍板）→ [`retrieval-strategy-review-20261108.md`](retrieval-strategy-review-20261108.md)（P0/P1/P2）→ [`discussions/EquipLens讨论11-8.md`](discussions/EquipLens讨论11-8.md)（原始讨论）→ `docs/module-map.md` → **`docs/ui-interaction-spec-v3.md`（界面与交互，当前唯一权威）**。
   - ⚠️ `docs/web-interaction-spec-v2.md` **已归档**（顶部有声明），只用于追溯早期设计，**不得据此实现**；两份冲突时以 v3 为准。
   - ⚠️ UI 已暂停（2026-11-08），`docs/ui-hifi-dark/` 是冻结的评审版，不是当前开发对象。
2. **若要碰检索**：先读 `docs/roster-expansion-design.md`（L1.5，清单/页槽/放闸）与 `docs/retrieval-diagnosis-20261103.md`（通道现状、阻碍归因、优化优先级）。
3. **前端现状**：高保真四页在 `docs/ui-hifi-dark/`（v3.3 静态，可走 S0→S3），浅色版在 `docs/ui-hifi/`；**正式前端工程（`webapp/`）尚未创建**。现行 `web/ui/index.html` 是旧版单页（770 行原生 JS），将被替换。旧低保真样张可重渲：`python docs/ui-mock/shot.py`（仅视觉参照）。
4. **代码地图**：`src/equiplens/{textrun,corpus,passage,l3gate,runner,audit,domainbench,strategy,runlog}.py`；检索中引擎 `src/equiplens/retrieval_engine/`（P0–P1）；
   测试 `tests/test_{textrun,corpus,l3gate,runner,audit,domainbench,retrieval_engine}.py`。
5. **跑测试**（全部可离线；当前检索三件套：`test_retrieval_engine` 18/18、`test_imagesearch` 12/12、`test_gate` 11/11）：
   `for f in tests/test_{gate,imagesearch,retrieval_engine,textrun,corpus,l3gate,runner,audit,domainbench,query,workflow,ingest,data_layer,m31,r0,r1}.py; do PYTHONPATH=src python $f; done`
6. **复跑检索**（必须用新 run_id，否则 runner 续跑会复用旧批次）：
   `PYTHONPATH=src python -m equiplens text-run scripts/intent-chain2.json --data-dir data-test --run-root data-test/runs --run-id <new-id>`
7. **闸门评估**：`PYTHONPATH=src python scripts/eval_l3gate.py`（结果 `data-test/evals/l3-gate-v1.md`）。
8. **误杀抽检**：`python -m equiplens audit-batch <batch_dir> --data-dir data-test`，再用 `audit-apply` 出报告。
9. **域名基准**：`python -m equiplens domain-bench scripts/domain-bench-queries.json --data-dir data-test`。
10. **已知坑**：百度间歇拦截（降级链 auto→延迟百度→Bing）；`site:` 定向默认关闭；复测必须新 run_id；A 档产出 ≠ 全部价值（163 等门户可能产 G 档）。
11. **台账**：`docs/test-log.md`（意见 #20–#23）、`data-test/runs/INDEX.md`、`data-test/evals/`。
