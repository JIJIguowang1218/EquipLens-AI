# 检索实验日志（含开源技术验证）

> 用途：每个“假设 → 做法 → 数据 → 结论”留一条，避免重复试错，也方便面试/汇报时讲“我们怎么判断该不该用某个技术”。
> 只记录会影响决策的实验；日常调试不进这里。日期均为本地时间。

## 0. 汇总

| # | 日期 | 实验 | 结论 | 采纳 |
|---|---|---|---|---|
| E1 | 11-09 | W1 网页检索基线（10 查询 × 360） | 单源、每查询 ~7 候选、可用率低 | 背景 |
| E2 | 11-09 | 门卫标签 v2→v3→v4 + 分层（概览/部件/参考） | 误杀“背景多车”13 张修复；可用 17/8 | ✅ |
| E3 | 11-09 | CDN 缩放后缀升图（`!600`→`!1200`、`w_640`→`w_1280`） | 13 张里 10 张升到 1200×800 | ✅ 默认开 |
| E4 | 11-09 | Scrapling（开源抓取框架）技术验证 | 不解决我们的三个阻塞点 | ❌ 不接入 |
| E5 | 11-09 | 来源页回访（搜索命中 → 回访文章页抽图） | 机制可用，但当前来源池产出低，净收益不明确 | ⏸ 仅 opt-in |
| E6 | 11-09 | W1 复跑（升图 + 门卫 v4） | 部件可用 18，越过 ≥10 验收线 | ✅ |
| E7 | 11-09 | 边界清单 + 52 张金标 | 门卫精确率 100%、漏 1 张（客车误判） | ✅ 基线 |
| E8 | 11-10 | M1 最小 loop（沙漠牵引车） | 跑通 DONE 3/3；暴露 2 个结构 bug（已修） | ✅ 骨架通 |
| E9 | 11-10 | M1b 隔离重跑（C01 / 12 槽 / 实时发现） | 12 候选 → 6 台全覆盖（50%），车槽 6/12 | ⚠️ 检索召回是瓶颈 |

---

## E3 CDN 缩放后缀升图

**假设**：低清不是源站只有小图，而是 360/CDN 默认给了缩放版，改参数能拿到母图。

**做法**：`imagesearch.upgrade_image_url()` 把 URL 里的 `!600`/`!550` 换成 `!1200`（搜狐 `w_640`→`w_1280`），下载时先试大图、失败回落原 URL。

**数据**（13 张带后缀的参考图，联网实测）：

| 结果 | 数量 |
|---|---:|
| 升到 1200×800 并进入部件可用 | 10 |
| 升级后仍留参考层（scene=multi） | 1 |
| 源站 401/403，回落原图 | 2 |

真细节校验：抽 3 张对比“`!1200` 版”和“`!600` 上采样到 1200”的高频能量，比值 **1.95 / 2.18 / 1.59**（文件 55KB→177KB），说明 CDN 侧有更大母图，不是放大。

**结论**：采纳，默认开启。**未验证**：其他 CDN 是否也接受改参（搜狐已补测通过；pstatp 等未覆盖）。

---

## E4 Scrapling 开源框架验证

**假设**：引入反检测抓取框架，能提升抓取成功率、降低被封。

**做法**：装 `scrapling==0.5.1`（仅验证，不接入），四项对照——页面抓取/解析、百度图片接口、CDN 无后缀原图、浏览器会话。

**数据**：

| 项 | 现有 requests | Scrapling | 结论 |
|---|---|---|---|
| 360che 文章页 | 200，30 张图 | 200，31 张图 | 无差别 |
| 百度 `acjson` | 200 + `antiFlag:1` | 200 + `antiFlag:1` | 伪装 TLS 指纹无效 |
| kcimg 无后缀原图 | 401 | 401 | 不是指纹问题 |
| 浏览器会话后取原图（Playwright 带 cookie） | — | 401 | 是签名 URL，浏览器也救不了 |

**结论**：
1. 我们的三个阻塞点（百度服务端封禁、CDN 401、单源）它都解决不了，**不接入**；
2. 值得借鉴的是它的工程形态：抓取层抽象（HTTP 优先、浏览器兜底）、AutoThrottle 自适应限速、断点续爬；
3. 真正的启发是“**去来源页批量取图**”（一篇文章页 30 张、7/8 可升 1200），于是有了 E5。

**未验证**：Cloudflare 类挑战站点（我们当前目标里没有）。

---

## E5 来源页回访（搜索找页 → 回访抽全页图）

**假设**：图片搜索每条结果都带来源页 `link`；回访文章页能一次拿到 10–30 张同款图，单位产出应高于“每查询 1.8 张可用”。

**做法**：
1. `_search_360` 保留 `source_url`；
2. `harvest_source_page()` 抓页 → `HTMLParser` 抽 `<img src/data-src>` → 绝对化/去重/去图标 → 升图；
3. 页面优先级：资讯站（360che / chinatruck / sohu / yoojia / cn357）加分，B2B 商品页（alibaba / dealer / cmo2o）直接排除；
4. 先按 `limit` 截断搜索命中，再挂回访结果（保证 A/B 公平）。

**数据**（同一 10 条查询，公平 A/B）：

| 口径 | 候选 | 下载 | 门卫 | 概览 | 部件 | 参考 | 预筛拦 | 耗时 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 无回访（v5） | 72 | 49 | 39 | 26 | 18 | 13 | 0 | 83s |
| 回访 1 页 | 128 | 103 | 66 | 29 | 18 | 37 | 24 | 106s |
| — 其中 page 通道 | 56 | 54 | 36 | 5 | **3** | 21 | 24 | — |

**结论**：
- 机制本身可用（直接测 360che 文章页：8 张全部升到 `!1200`）；
- 但 360 的 `link` 池以经销商页/资讯页为主，抽出来的多是 640px 缩略图和导航图标（56 张里 24 张被预筛拦），**page 通道只贡献 3 张部件可用**；
- 总部件 18 与基线持平、耗时 +23s，**净收益不明确**，因此**默认关闭（`--harvest 0`）**，保留 opt-in 供后续调优。

**下一步可调**：只回访已确认高产的站（360che/chinatruck 文章页）、从站点图集列表批量抓（不依赖 360 的 link）、对 pstatp 等 CDN 补升图规则。

**未验证**：回访的限速/robots 合规细节；页面数增加后的边际收益（harvest=2 的早期数据因截断 bug 作废，已删）。

---

## E6 W1 复跑（升图 + 门卫 v4）

**做法**：10 查询 × 360，`limit=8`，升图默认开。

**数据**：72 候选 / 49 下载 / 39 门卫 / **26 概览 / 18 部件 / 13 参考**；18 张部件里 11 张来自升图；83s。

**结论**：部件可用首次越过 W1 的 ≥10 验收线。**未验证**：18 张自动判定未做人工复核。

---

## E7 边界清单 + 金标

**做法**：把 \|margin\| < 0.01 的 9 张唯一图逐张列出（keep/drop 分数、尺寸、结论），人工确认；再把 52 张唯一图整体标成金标。

**数据**：9 张里 8 张判定正确，1 张（960×1280，J6G）被误判成“客车”；门卫放行 43/43 全为可用，漏检 1/44。

**产物**：`data-test/evals/image-gate-52-20261109.json`（可用 18 / 低清可用 26 / 坏图 8）。

**结论**：作为回归基线；也说明“边界样本应进复核队列”，而不是继续调阈值。


---

## E8 M1 最小 loop（沙漠牵引车，2026-11-10）

**假设**：现有状态机 + 真实 360 检索，能跑通“任务单 → 候选 → 检索 → 核验 → 填槽 → 缺口判定”。

**做法**：用 T19 的 C01 任务单（前脸/踏步/大灯/前轮拱/防护栏/保险杠）转成引擎 brief（`brief-m1-desert.json`），3 车槽 / 2 单元（exact 2 + environment 1），手动给 3 台候选车型，跑 `--web-only`。

**数据**（三次运行）：

| run | 车槽 | u-exact | u-env | fetches | 结果 |
|---|---|---|---:|---:|---:|---|
| v1 | 0/3 | 0/2 | 0/1 | 5 | FAILED |
| v2 | 0/3 | 0/2 | 2/1 | 15 | FAILED |
| v3 | **3/3** | 3/2 | 3/1 | 22 | **DONE** |

**暴露并修复的 bug**：
1. 资产按 `asset_id` 全局去重 → 一张整车图只能挂一个部件，多部件单元永远填不满（v1 只有 5 个资产）；
2. `_add_targets` 按车型名覆盖 → 后一层（environment）把前一层的 `unit_id` 抢走，exact 证据清零（v2）；
3. Windows `os.replace` 偶发 `WinError 5` → 状态写盘加重试。

**结论**：loop 骨架能收敛；但候选车型是“人工给的”，不是“发现”的；验收不看部件可见性。详见 [`loop-m1-desert.md`](loop-m1-desert.md)。

**未验证**：真实“新车型发现”（需接 SearXNG/Tavily 或官网图集）；证据落库（本轮未传 `--evidence-db`）。


---

## E9 M1b：隔离重跑（C01，12 车槽，实时发现）

**假设**：不依赖任何历史数据，只靠实时检索 + 现有 loop，能填满 C01 的 12 个车槽。

**做法**：清空库；候选由 `discover_models` 从实时 360 抽取（通用 6×6 语汇 + 品牌查询，标题需含 6x6/六驱/全驱）；brief 车槽 12；下载图存 `images/`；证据写 `evidence.db`。

**数据**：
- 发现 12 台候选（德龙X3000 / 德龙F3000 / 汕德卡C7H / 东风天锦 / 红岩杰狮 / 解放J5M / 德龙X5000 / CJ3250D41E / 东风天龙 / 解放J5P / 江淮格尔发 / 欧曼BJ5257TCX）；
- 20 张图过两段式门卫，18 条证据落库；
- **6 台完整覆盖 3 个部件**，车槽 6/12，FAILED（缺口 exact 6/8）；
> **更正（2026-11-10 复核）**：本文早前写的“6/12 台完整覆盖”**不成立**——当时的“部件通过”只由 `RuleVerifier` 的标题/构型/分辨率规则判定，**没有部件可见性检测**，同一张图可以同时算作 5 个部件的证据。可靠口径是：**12/12 台各有 ≥1 张过门卫图；其中 9/12 台有 ≥1 张 ≥800 概览图**。部件覆盖要等 P4 视觉，暂不作为验收。

- 24 queries / 57 fetches / 57 verifies，10.8 分钟。

**结论**：loop 全链路（发现→抓取→门卫→核验→填槽→缺口→降级）在隔离条件下跑通；瓶颈是**“候选名 → 同款图”的召回**（经销商/二手页占比高）和低清，不是 loop 结构。

**未验证**：部件可见性（当前一张图可同时满足 3 个部件）；真实扩源后的召回提升。

---

## E10 外国品牌为什么进不了漏斗（2026-11-10）

**假设**：Zetros / Arocs / Volvo FMX / KAMAZ 在 360 上没有图，所以 loop 永远收不到。  
**实测**：不是没图，是**护栏在搜索阶段就把它们清零了**。用 `scripts/diag_foreign_search.py` 只读 360，记录每通道 `raw`（360 返回）与 `rel`（过相关性护栏）：

| 车型 | 规划器 query | 360 raw | rel | 手写 query | rel |
|---|---|---:|---:|---|---:|
| Zetros 4051 AS | `Zetros 4051 AS 6x6` | 12 | **0** | `奔驰 Zetros 6x6 牵引车` | **6** |
| Arocs 6×6 / 8×8 | `Arocs 6x6` | 12 | **0** | `奔驰 Arocs 6x6 牵引车` | 0（AND bug） |
| Volvo FMX | `Volvo FMX 6x6` | 12 | **0** | `沃尔沃 FMX 6x6` | 0（品牌语言） |
| KAMAZ 6520 | `KAMAZ 6520 6×6` | 12 | **0** | `KAMAZ 6x6` | 3 |
| MOL-Brec TB 800 | `MOL-Brec TB 800 6x6` | 12 | 0→9 | — | “800ml”正文误命中 |

**四个根因（都在 `imagesearch._relevant`）**：
1. **多构型 AND**：`Arocs 6×6 / 8×8` 要求标题同时出现 `6x6` 和 `8x8`，任何标题都过不了；应改成“任一命中、明确冲突才拒”。
2. **纯数字当型号码**：`_distinctive` 把 `800` 当唯一代码，导致 `800ml` 的医学正文被当成 MOL 车型。
3. **中外品牌无别名**：模型名是 `Volvo/KAMAZ`，标题是`沃尔沃/卡玛斯`，`brand in title` 永远 False。
4. **构型必须出现在标题**：中文标题常写“六驱”或干脆不写，被一刀切判不相关。

**修复**：构型改“冲突才拒”（兼容 6驱/六驱）；`_distinctive` 必须字母+数字；加 22 组中外品牌别名；车辆词补英文；新增 `alias_query`/`query_variants`（拉丁型号 → 中文品牌改写，如 `Zetros 4051 AS 6x6` → `zetros 6x6 卡车`）。

**验证（真实抓取，不调 API）**：Zetros 6 张图 / 6 张 probable、Arocs 5/5、Volvo 6/6，全部通过核验进入漏斗；修复前这 3 台各 0 张。  
**结论**：此前“外国品牌 360 内容稀缺”的判断**只对了一半**——内容确实少，但第一道闸门先把自己挡死了。  
**未验证**：整轮 12 槽里塞外品牌后的真实交付率；规划器 query 仍会生成 360 不友好的拉丁型号码（已由变体兜底，最好在 planner 阶段就改写）。

---

## E11 独立测试：外国品牌 12 槽全链路（2026-11-10）

**目的**：T37 的外国品牌召回修复只在单车型抓取里验证过；本轮按“独立测试”跑完整 loop：新 brief、新 plan、新 run 目录、空库、无人工种子。

**隔离**：两个 run 目录开跑前都不存在（`test ! -e`）；`--web-only` 走 `NullLibraryAdapter`（事件 `库内候选 0 个`）；未传 `--models`；候选全部来自本次 7 次 Search（89 条结果 → 23 候选，11 个外国品牌）。

**结果（v2）**：**12/12 DONE**（exact 8/8、intl 4/4），外国品牌占 **5 台**：Zetros、Actros、H6066(MOL)、T-Way(IVECO)、Kerax(Renault)。79 唯一图 / 77 过门卫 / 316 成功抓取；API $0.024。

**v1 的意外收获**：第一轮跑出 **20/12**——单元 quota 只用于计算缺口，没有约束 `_state_fill`，12 槽被塞成 20 台。修复（quota + 全局双上限）后 v2 才回到 12。同时发现 `degraded` 把“抓过图但没占槽”的车型也算进去（一度 17 > 12），已限定为占槽车型，并新增 `citation_only`。

**质量口径**：12 台里只有 4 台有 confirmed 图，**8 台 degraded**；1 台（TAZ4922）**citation_only**（零核验通过的图，仅引用页）。外国品牌 5 台里仅 H6066 有 confirmed。

**结论**：外国品牌进入并占槽成立；但“12/12”必须和 degraded/citation_only 一起读。  
**下一步**：收紧 citation_only（至少 1 张 unknown 级图或改“待补图”）；官网/公告页图集提升 confirmed 比例。

---

## E12 默认规划里外国品牌占多少？（2026-11-10）

**问题**：不额外设置时，任务单 → Search → LLM 候选，能否自然产出外国车型？

**对照**（同一套 planner，唯一差别是 brief 里有没有“国际品牌”研究单元）：

| plan | brief | 候选 | 外国品牌 | 占比 |
|---|---|---:|---:|---:|
| `plan-c01` | C01 沙漠牵引车（无国际单元） | 16 | 4（奔驰/MOL/KAMAZ） | 25% |
| `plan-c01-v2` | 同上 | 15 | 4（奔驰/MOL） | 27% |
| `plan-m1b-global` | 国产 8 槽 + 国际品牌 4 槽 | 23 | 13（奔驰×3/MOL×2/KAMAZ/Scania/IVECO/Renault/TATRA/Steyr/TITAN） | 57% |

**机制**：planner 的 prompt 已写“包含国产与外国品牌”，但同一条规则要求“只能从检索结果推断、不许凭记忆补充”。中文查询 + 中文图库/网页 → 结果天然偏国产，LLM 只能从里面挑；所以默认会有一些外国品牌（主要是奔驰/MOL，因为中文页面常提），但**不会自然覆盖俄系/欧系小众品牌**。

**结论**：不需要品牌白名单；需要的是**查询覆盖**（一个“进口/国际品牌 + 类目 + 构型”的通用查询，或 brief 里的国际单元 scope）。T38 就是靠这条把外国候选从 4 提到 13。  
**建议**：把 `进口 {class} {conf} 车型` 设为默认查询之一（成本 +$0.00075/次），不用任何品牌名单；是否默认化由产品决定。

---

## E13 A/B：默认查询 + 一条“进口”覆盖查询（2026-11-11）

**假设**：在 C01 brief（只有类目/工况/构型/部件，无任何车型名单）上，给 planner 多加一条 `进口 沙漠牵引车 6×6 车型`，能提高外国品牌候选占比，且不明显降低候选有效率。

**做法**：同一份 `brief-m1-desert.json`，同一 key；A = 现有 6 条查询（4 条模板 + 2 个 unit scope），B = A + 1 条进口查询。只跑 planner（Search + LLM 抽取），不抓图。各跑 2 次估计方差。

| 组 | 查询 | 去重结果 | 候选 | 外国品牌 | 占比 | 前 12 个里的外国 |
|---|---:|---:|---:|---:|---:|---:|
| A | 6 | 70 | 24 | 6 | 25% | 4 |
| A2 | 6 | 70 | 16 | 4 | 25% | 3 |
| B | 7 | 85 | 24 | 11 | 46% | 8 |
| B2 | 7 | 84 | 24 | 9 | 38% | 3 |

- 两次 A 的外国占比都是 25%，两次 B 38–46%：**方向一致，B 更高**。
- 但**同组两次的候选重合度极低**：A∩A2 = 2/16（12%）、B∩B2 = 4/24（17%）、A∩B = 3/24。也就是说，同一批查询、同一 brief，LLM 抽出来的车型名单几乎换了一遍。
- `plan.json` 里 24/24 候选的 `query` 字段为空（prompt 没要求输出来源查询），无法归因“这条候选来自哪条查询”。

**结论**：
1. “进口”查询确实把外国品牌占比从 25% 拉到 ~40%，但**单次 A/B 不足以把收益全归给查询**——抽取环节的方差比查询效应还大。
2. 当前 planner 不可复现，这是“流程可控”的核心障碍：不是查询模板问题，是**抽取+归因**问题。
3. 在把进口查询设为默认前，必须先做：① 候选必须带 `source_query` 且 URL 必须属于该查询结果；② 抽取温度 0 / 按查询分块抽取；③ 固定候选排序规则。

**产物**：`data-test/runs/plan-ab-20261111/{A,A2,B,B2}/{plan.json,api_log.jsonl}`。

---

## E14 planner v2：逐查询抽取 + 出处校验后的 A/B（2026-11-11）

**改动**（`src/equiplens/planning.py` + `scripts/plan_candidates.py`）：
1. 查询计划带 `query_id / dimension / purpose`（base/model/environment/english/unit/extra）；
2. 每条查询单独 Search、单独让 LLM 抽候选（temperature 0，每条最多 6 个）；
3. 候选必须带 `source_query_id`，且 `sources` 必须属于该查询自己的结果集（跨查询 URL 直接丢弃）；
4. 同车型跨查询合并，保留 `source_queries`；输出 `coverage`（每个维度多少候选、缺哪些维度）。

**A/B（C01 brief，各跑 2 次，只跑 planner）**：

| 组 | 查询 | 候选 | 外国候选 | 占比 | 有出处 | 前 12 外国 |
|---|---:|---:|---:|---:|---:|---:|
| A | 6 | 27 | 7 | 26% | 27/27 | 3 |
| A2 | 6 | 23 | 7 | 30% | 23/23 | 3 |
| B | 7 | 27 | 8 | 30% | 27/27 | 3 |
| B2 | 7 | 26 | 9 | 35% | 26/26 | 3 |

- **出处问题解决**：v1 是 0/24，v2 是 100%。
- **可复现性改善有限**：同组重复运行重合 A∩A2 = 6/23（26%）、B∩B2 = 8/26（31%），比 v1 的 12–17% 好，但仍远不足以说“稳定”。
- **进口查询的边际收益变小**：v1 里 B 比 A 高 13–21 个点；v2 只高 4–5 个点。原因是逐查询抽取时，每条查询各自出 6 个，进口查询只新增 4–5 个候选，不会挤掉其它查询的产出。
- **候选级占比被“品牌变体重复”放大**：A 的 7 个外国候选里 4 个都是“梅赛德斯-奔驰(…)”的不同写法；按**去重品牌**看，A/A2 都是 3 个（奔驰/MOL/KAMAZ），B 是 3 个，B2 是 4 个（多雷诺）。所以“外国候选占比”不是好指标。

**成本**：Search 6/7 次（$0.0045 / $0.00525）；Chat 6/7 次（token 另计，单次约 3k prompt tokens）。

**结论**：
1. 出处与覆盖报告已经可控；但“同一 brief 跑两次得到不同名单”仍存在，不能把单次 A/B 当结论。
2. 逐查询抽取削弱了“加一条查询就能显著改变品牌结构”的效果——它更像“补充召回”，不是“重排优先级”。
3. 指标要改成：**去重品牌数 / 品牌覆盖率 / 单品牌有效候选数**，而不是候选级外国占比。
4. 下一步：① 品牌/车系级去重（现在“奔驰(…)”变体占坑）；② A/B 至少 n=3 并用品牌覆盖做指标；③ 再决定进口查询是否默认。

**产物**：`data-test/runs/plan-ab2-20261111/{A,A2,B,B2}/{plan.json,api_log.jsonl}`；测试 `tests/test_planning.py` 6/6。

---

## E15 车型级去重 + 废弃 discover fallback + A/B n=3（2026-11-11）

**改动**
1. `planning.model_identity`：型号码优先（TAZ4922/DFV5253/K-65959/TB800）→ 车系+数字（Zetros 4051 vs 3643）→ 车系（Arocs）→ generic。**同品牌不同型号码不合并**。
2. `merge_candidates` 按 identity 合并，保留 `model_variants / source_queries / dimensions`；`dedupe` 统计输入/唯一/移除/generic。
3. `discover.py` fallback 废弃：`WebWorld` 无 plan/models 直接报错；CLI 在联网前拦截 `--web-only` 无 `--plan/--models`。
4. planner 默认 `--per-query 8`；coverage 增加 `slots / pool_shortfall`。

**效果验证（离线回放旧 plan）**：A 27→20、B 27→21；TAZ4922/DFV5253/Zetros 4051 的变体合并，Zetros 4051 vs 3643、EQ2251AX vs EQ2220AX、DFV5253 vs DFV2223 均保持分开（无过度合并）。

**A/B n=3（C01 brief，per-query 8，各跑 3 次）**：

| 组 | 候选池 | 去重前→后 | 去重移除 | 外国候选 | 占比 | 池缺口 |
|---|---:|---:|---:|---:|---:|---:|
| A1 | 17 | 25→17 | 8 | 4 | 24% | 0 |
| A2 | 26 | 35→26 | 9 | 5 | 19% | 0 |
| A3 | 22 | 30→22 | 8 | 4 | 18% | 0 |
| B1 | 25 | 33→25 | 8 | 4 | 16% | 0 |
| B2 | 20 | 31→20 | 11 | 4 | 20% | 0 |
| B3 | 18 | 28→18 | 10 | 3 | 17% | 0 |

- 去重稳定移除 **8–11 条同款变体（约 25–35%）**；6 次池子 17–26，**没有一次低于 12 槽**（per-query 6 时曾出现 11，已由 8 修复）。
- 重复运行重合：A 77–82%、B 50–70%（v2 是 26–31%）。
- **进口查询没有带来外国车型增量**：A 18–24%、B 16–20%；B 只是偶尔多出 Zetros 3643/雷诺，同时会丢 KAMAZ/TB800。结论：**不默认加进口查询**；要补外国车，应在 brief 明确目标市场，或先有车型名再做“型号 → 图”检索。

**下游验证（A2 plan 跑完整 12 槽）**：`loop-ab4-a2-20261111` **12/12 DONE**（exact 8、env 4），12 个占槽车型 **identity 全部不同（无同款重复占槽）**；82 张唯一图 / 304 次抓取 / 7 台 degraded / 1 台 citation_only / bonus 29 张；引用 API $0.01875。说明去重没有伤到资料数量与交付。

**副作用/待观察**：候选里 generic（无型号码）占 35–56%，A2 交付里 3 台是 generic（OTTC、中东版、东风 400 马力）；它们能占槽但身份只能到 probable/unknown，是 degraded 的主要来源。下一步应限制 generic 占比或要求 generic 也必须带品牌+车系证据。

---

## E16 brief 生成 API 化：不再手工代写（2026-11-11）

**问题（严重）**：此前 T31–T41 的 `brief-m1-desert.json` / `brief-m1b-global.json` 是**人根据口述手写的**，不是 API 生成。测试因此只覆盖了“brief 之后”的链路，brief 生成、类目/工况/构型推断、部件→视角映射全部未被测试；8/4 配额、4 个部件、负词也都是人工决定。

**改法**：
1. 新增 `skills/task-brief/SKILL.md`（`task-brief@v2`）：先教 LLM 做工程分析（品类/基型/构型/工况/设计对象+设计维度），再输出 `request/regions/parts/assumptions/negative`；词表只做参考、不做准入，未知部件保留为 `custom_*`；
2. 新增 `src/equiplens/briefing.py`：LLM 输出 → 代码补 `brief_id/page_budget/research_units/tiers/budget/strategy_ref` → `validate_brief` + JSON Schema 校验；
3. 新增 `scripts/build_brief.py`：`--input` → DeepSeek Chat → `brief.json` + `brief.json.meta.json`（raw_input/model/skill_version/attempts/usage/llm_payload）；
4. 手工 brief 标为 **legacy**（`data-test/evals/task-briefs-20261109/README.md` §6），仅用于复现历史 run。

**实测（C01）**：输入“沙漠牵引车（前脸、登车踏步、大灯、前轮拱、防护栏、保险杠）；沙漠/油田工况；6×6；12 台” → API 生成：

- parts：`step/headlamp/wheel_arch/side_guard/bumper`（5 个，含用户点名的保险杠；未把“前脸”硬拆）；v2 复跑加入“涉水喉”后生成 `custom_9d3f2a7c`，保留原词并标 `taxonomy_status=new`
- regions：`front_face`（整体造型维度）
- units：exact 8 / environment 4；7 条 assumptions（含“前脸不单独建槽”“防护栏映射为侧防护”）
- 校验通过；`plan_candidates` 在该 brief 上产出 19 个候选（6 查询 / 61 结果）

**代码审计（同类问题）**：
- 已废弃：`discover.py` 的 18 个国产品牌 fallback；
- legacy、非当前运行路径：`retrieval_web_smoke.py`（手写查询对）、`run_roster_crawl.py` / `rerun_roster_textrun.py` / `roster_judge_sheet.py`（旧名录文本检索与评测）；
- 合法测试夹具：`data-test/retrieval-fixtures-*`、`tests/synthetic_data.py`、`make_ui_fixtures.py`（不得进运行时）；
- 规则/领域数据（非假参数）：门卫标签、品牌别名、`planning.SERIES`、`briefing.DEFAULT_NEGATIVE`、配额 2/3 规则——应记录为规则，不允许冒充 AI 输出。

**未解决**：brief LLM 的稳定性（同一输入多次生成是否一致）、`research_units` 的 2/3 规则是否应由产品确认、L1.5 的页槽/超量推荐仍未实现。

**关键认识**：`part_taxonomy.json` 是参考词表/规范输出词汇，不是用户输入准入；分析输入靠“位置+功能+形态+环境+设计维度”的工程方法（skill §1–§3），不是查表。

---

## E17 task-brief skill 必要性 A/B（2026-11-11）

**问题**：`task-brief@v2` 的方法引导是否真的有用？还是只是“写给评委看的 md”？

**方法**：用 `skills/task-brief/evals/evals.json` 的 3 个 case（已知部件 / 词表外部件 / 口语类目），同一提示分别跑 `with_skill` 与 `without_skill`（`--no-skill`，只去掉方法引导），比自动检查和人工 rubric。

**自动检查结果**：

| case | arm | 部件数 | custom | 全有 design_axes | assumptions |
|---|---|---:|---:|---|---:|
| known-parts | with_skill | 5 | 1 | ✅ | 8 |
| known-parts | without_skill | 1 | 1 | ✅ | 3 |
| unknown-parts | with_skill | 4 | 4 | ✅ | 9 |
| unknown-parts | without_skill | 7 | 4 | ✅ | 2 |
| ambiguous-category | with_skill | 2 | 2 | ✅ | 7 |
| ambiguous-category | without_skill | 崩溃（parts 不是对象） | — | — | — |

**复跑修正（同一天、加防御性解析后重跑 6 次）**：known-parts `5 vs 1`；unknown-parts with_skill `4`，without_skill 因 `request.class` 缺失失败；ambiguous with_skill `2`，without_skill 返回非法 JSON。两次复跑说明 **without_skill 的失败/波动比 with_skill 大**，但样本仍太小。

**人工抽检**：
- with_skill 的 known-parts：class/base_platform/构型都有推理；5 个部件各带 relation_axis/design_axes/why；regions 有 front_face/side；
- without_skill 的 known-parts：class=`traction_truck`、base_platform 空，只有 1 个部件、design_axes 全是 `form_gesture`、无 region；
- without_skill 的 unknown-parts **部件更多**（7 个），但全是 `form_gesture`/`exact`，把侧防护/下护板/踏步也补进来了；with_skill 只保留用户点名的 4 个，且每个有环境/结构/人机轴——**“多”不等于“对”**。

**结论**：
1. 方法引导在“完整性、对象分类、设计维度、假设记录”上有可见差异，尤其 known-parts 从 1 个部件到 5 个、口语类目从崩溃到可解析；
2. 自动检查不够，必须人工 rubric；n=3、单次运行，不能证明泛化；
3. 泛化测试必须用 skill 里没出现过的品类（矿山自卸车、汽车起重机）和词表外部件；下一步扩到 10–20 个 case、每 case 跑 2 次，评“品类/基型/构型、对象分类、关系轴、设计轴、未知部件、是否编造”，再决定 skill 是否保留/怎么改。

**产物**：`data-test/evals/task-brief-eval-20261111/{RESULTS.md,results.json,*.json}`；运行器 `scripts/eval_task_brief.py`。

### E17b 10 案例复跑（2026-11-11）

把 5 个旧案例（C01–C05，来自 `BRIEFS-5`）+ 5 个新品类（C06 挖掘机 / C07 装载机 / C08 搅拌车 / C09 环卫压缩车 / C10 高空作业车）统一成 10 个“品类 + 3–5 部件”的 prompt，全部不含具体车型；`with_skill` vs `without_skill` 各跑一次。

| 组 | 自动断言通过 | 典型失败 |
|---|---:|---|
| with_skill | **10/10** | 无 |
| without_skill | **1/10**（仅 C03） | 7 个 case 只出 1 个部件；多数无 region；C06 出了 10 个部件 |

自动断言只覆盖 schema/部件数/design_axes/region/custom/assumption；**语义质量仍需人工**，评审表在 `data-test/evals/task-brief-eval-20261111/REVIEW.md`（10 行 × 7 个维度）。
**v1 格式组复跑（同一天，20 次）**：v2 方法自动断言 **10/10**；v1 只给格式 **3/10**（C03/C04/C07），其余 7 个都因“部件数 8–34 个，超出 3–5”失败。v1 倾向把词表里所有相关件都加上，v2 会按用户点名收敛。人工语义仍看 `review.html` 的 PASS/FAIL/证据与“优先采用”。

限制：v1 的失败主要是“部件数量/范围”而不是语义；要证明 v2 的分析质量更好，必须看人工 rubric（对象分类/关系轴/设计轴/是否编造），不能只看自动断言。

---

## E18 generic 只标不删：12 槽实测（2026-11-11）

**原则**：generic（无型号码）不是废品；品牌/车系正确、图过门卫、能看出造型就可用。低清只标 `low_resolution`；不设配额、不删候选。

**做法**：用 T41 的 A2 plan（26 候选，其中 9 个 generic）跑完整 12 槽；新代码把 `identity_kind` 从 plan → Target → state → 审核页，只展示和筛选，不参与淘汰。

**结果**：
- **12/12 DONE**（exact 8、environment 4），`missing=0`；
- 目标身份分布：code 13 / series 2 / generic 9；
- **交付里 3 台 generic 占槽**（OTTC 越野牵引头、中东版 6×6、东风 6×6 沙漠卡车）；
- 82 张唯一图 / 76 过门卫 / 392 次抓取；`degraded=8`、`citation_only=1`、bonus 32；
- 没有候选因 generic 被删；审核页可按“泛称车型”筛出。

**结论**：generic 只标不删在 12 槽上可行；它不会自动降低交付数，但会增加 degraded（3 台泛称交付里没有 confirmed 图）。下一步若要提高质量，应做“排序/证据补强”，不是限额。

---

## E19 意向排序 + 证据准入 + 12 主/2 备（2026-11-11）

**问题**：HF8066 这种强关联车有 confirmed 图却不占槽；当前占槽 = 规划顺序 + citation + 配额，不是设计意图。

**实现**：
1. `scripts/rank_plan.py`：只用文本（用户 request + 候选 reason/source）让 LLM 给 12 primary + 2 backup + 其余 pool，输出 `intent_rank/intent_band/intent_reason/role`；不看图片。
2. `WebWorld` 按 `pinned > primary > backup > intent_rank > citation` 排 plan；`unit_quotas` 预留每个 unit 的 primary（exact 8、env 4），unit 的补位只能取 replacement（backup/pool），不抢别的 unit 的 primary。
3. `_state_fill` 按 `pinned > role > intent_rank` 填，门卫/核验仍是准入；backup 只在 primary 没图时补位。
4. `--pin` 用户关键词强制 primary；`Target` 带 intent 字段进入 state/audit。

**A2 plan 实测**：26 候选 → primary 12 / backup 2；HF8066 被排到 **rank 6**。跑 12 槽：
- **12/12 DONE**（exact 8、env 4）；HF8066 **占槽**；
- primary rank 2/4 没有抓到图（assets 为空）→ backup 13/14 补位；
- 身份：code 6 / series 2 / generic 4；degraded 8、citation_only 1；72 唯一图 / 66 过门卫；无候选因 generic 被删。

**结论**：LLM 的文本意向排序可以作为“先抓谁/先给谁”的先验，但不能作为终审；必须 evidence 准入。unit 配额预留是必要的，否则 exact 的补位会抢走 environment 的 primary（test2 就出现了 backup 抢槽、primary 9–12 没交付）。

**未解决**：ranker 只跑一次、无人工复核；12+2 的“2 备”是否要展示给用户、pin 的 UI 还没做；HF8066 仍有低清 warning。

---

## E20 失败原因 + 阶梯重放 + 部件先验接线（2026-11-11）

**统计**（`data-test/evals/failure-stats-20261111.md`）：

| run | fetch | 下载失败 | 过门卫 | 无图目标 | 主要失败 |
|---|---:|---:|---:|---:|---|
| intent-test3 | 328 | 40 | 264 | 4 | connection 20 / 403 16 / redirect 4；门卫：拼图 12、多车 4、客车 4 |
| generic-test | 392 | 52 | 316 | 5 | 403 28 / connection 20；同上门卫 |
| m1b-v2 | 372 | 56 | 308 | 2 | 403 48 / connection 4 / 404 4 |
| c01-plan9 | 176 | 24 | 136 | 12 | connection 12 / 404 8 / 403 4；拼图 16 |

**阶梯重放**：从 intent3 取 12 条失败 URL，用当前下载阶梯重下：**0/12 成功**，`tries=2` 就停在 DNS/403。说明同一 URL 重试无收益，恢复必须换源/换查询，不是加下载次数。

**接线（已改）**：
- `analysis._normalize_slots` 保留 `kind/location/part_family/why`；`build_prompt` 把它们作为“检索先验（假设，不是图上结论；不符以图为准）”写进对应 slot；
- `WebWorld.live_fetch` 在基础 query 无命中时，用 `part.label + target.query` 再做一次部件兜底查询；fetch_log 记录 `tries/url_used/upgraded/part_query`，后续 run 可统计阶梯成功率。

**未验证**：部件兜底查询是否真的提升命中；analysis 先验是否造成确认偏误；新 run 才有阶梯数据。

---

## E21 扩源/换源小测：能捞到图，但身份是瓶颈（2026-11-11）

对象：intent3 里 3 个无图目标——泰安五岳、沙漠越野重型牵引车、K-65959。

1. **原长 query + harvest=2**：3 个目标都是 base 0 hits、harvest 0 hits；长描述名在 360 上直接不可检索。
2. **短 query / alias**：能出结果；`五岳 油田牵引车` 的 harvest 出 10 张过门卫图，`K-65959 6x6` 出 12 张，`沙漠运输车 6x6` 出 2 张。
3. **身份核验**：34 张过门卫图里，只有 **1 张** `probable`（重汽泰安五岳 TAZ4413 全驱牵引车）；K-65959 的泛 query 全是牧马人/兰博基尼/乌尼莫克等无关车。

结论：
- 扩源（短 query/来源页）能显著提高“过门卫图”的数量，但**不解决身份**；泛 query 会把无关车捞进来；
- 恢复必须“**具体车型 query/来源页 + 核验**”，不能只加 harvest；
- K-65959 这种冷门码，需要官网/公告/出口商来源，而不是通用图片搜索。

数据：`data-test/evals/source-expansion-*.json`。

### E21 澄清（避免误读）

- **“扩源不解决身份”不是说核验和获取混在一起**。核验仍是独立模块；扩源只改变“候选图从哪来”。测试里 34 张过门卫图中只有 1 张 `probable`，说明扩源增加了候选量，但新候选大多不是目标车型，**核验正确地把它们挡掉了**。所以扩源的收益是“有更多机会找到对的图”，不是“自动提高身份准确率”。
- **“泛 query”指的是测试中为了召回而用的短查询**，不是原 plan 的长描述名。原 query 很具体但 360 返回 0；改成“五岳 油田牵引车 / K-65959 6x6 / 6x6 沙漠卡车”后才出结果，这些短查询更泛，所以 harvest 会带进无关车。
- **本次扩源方式**：不是新接一个图片平台；是 **360 图片结果 + 回访结果里的来源页（article/gallery）抽整页图**，再配合短 query/alias。`search_images_ex` 本来就查 360/Baidu/Bing，但生产默认主要用 360；测试没有把 Baidu/Bing 当主源。
