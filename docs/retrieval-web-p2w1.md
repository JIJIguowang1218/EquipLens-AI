# 网页检索适配器（P2-W1，2026-11-09）

| 属性 | 内容 |
|---|---|
| 阶段 | **检索中**（`EXTERNAL_DISCOVER → FETCH → VERIFY`） |
| 模块 | `src/equiplens/retrieval_engine/web.py` + `evidence.py` |
| 状态 | P2-W1 骨架完成：空库、网页 world、规则核验、证据落库、CLI |
| 测试 | `tests/test_retrieval_engine.py` **13/13** |
| 真实网络 | 默认不跑；`--web-only` 才走 360 |

---

## 1. 360 适配器是什么层面的东西？

**它是“搜索/发现层”的适配器，不是 360 浏览器，也不是 360 网页。**

```
层 1  搜索/发现   WebWorld.external_targets / imagesearch._search_360
        ↓ 返回 title / url / thumbnail（不下载图）
层 2  抓取/门卫   WebWorld.fetch / imagesearch._download_and_gate
        ↓ 下载 bytes → 预筛（确定性）→ CLIP 门卫 → 视角（只作 hint）
层 3  规则核验    RuleVerifier（标题/构型/分辨率；视角不符记 warning）
层 4  证据落库    EvidenceStore → image_evidence
```

> 2026-11-09 更新：层 2 的“外观”环节改为 `gate.assess_from_gate` 分层判定
> （概览 ≥800 / 部件 ≥1200，视角不否决）；层 3 的 `wrong_view` 硬缺陷同时降为
> warning。理由与实测见 [image-filter-pipeline.md](image-filter-pipeline.md) §7。
>
> 2026-11-09 二次更新：层 2 拆成**两段**——`gate.prefilter`（确定性：尺寸/字节/格式/
> 长宽比/近空白）先跑，不通过就不进 CLIP；98 张回放里 57 张被第一段拦下，CLIP 推理量
> 减半。见 [image-filter-pipeline.md](image-filter-pipeline.md) §8。

- `_search_360` 请求的是 360 图片搜索的 HTTP 端点（`so.com` 的图片搜索），**不是** 360 浏览器；
- 它返回的是图片结果元数据（标题、URL、缩略图），不是图片本身；
- 下载/门卫在下一层，和搜索层分开；
- 所以“360 适配器”= 一个 `SearchAdapter`，不是“用 360 浏览器打开网页”。

## 2. 我们测过哪些网页/通道？

| 通道 | 类型 | 项目实测 | 现在能不能当主力 |
|---|---|---|---|
| **360 图片** | 直连 HTTP | 唯一稳定；德龙 6X6 查询 10/12 相关 | ✅ 当前主力 |
| **百度图片** | 直连 HTTP | `antiFlag: Forbid spider access`、验证页 | ❌ 不可靠 |
| **Bing 图片** | 直连 HTTP | 中文图返回壁纸/人物，相关 0/12 | ❌ 不可靠 |
| **百度 SERP** | 网页搜索 | 真浏览器也被拦；`site:` 定向实测无效 | ❌ 不可靠 |
| **Bing SERP** | 网页搜索 | RSS 拆词、HTML 无有效锚点 | ❌ 兜底也不可用 |
| **SearXNG** | 元搜索聚合 | **本项目未实测**；GitHub 项目，自托管 | ⚠️ 待 P2-W2 评估 |
| **Searqon** | 自托管聚合 + 反爬 | 本项目未实测；源为 SearXNG/DuckDuckGo/Wikipedia/arXiv，**无 360/百度** | ⚠️ 适合文本/通用，不是中文图主力 |
| **Tavily / Exa / Serper** | 付费 API | 本项目未实测 | ⚠️ 待 P2-W2 对照 |
| **Firecrawl** | 抓取/清洗 | 不解决“搜图” | 用于页面内容，不是图源 |

证据来源：[retrieval-diagnosis-20261103.md](retrieval-diagnosis-20261103.md) §2/§3、[imagesearch.py](../src/equiplens/imagesearch.py)、[runner.py](../src/equiplens/runner.py)。

## 3. SearXNG 和 360 是什么关系？

**SearXNG 是聚合器，360 是直连图源。它们不是替代关系，而是同一层里的两种适配器。**

```
Engine 只认 SearchAdapter 协议
  ├─ DirectAdapter：360 / 百度 / Bing（直连某个图搜端点）
  ├─ AggregatorAdapter：SearXNG / Searqon（内部再扇出到多个引擎）
  └─ PaidAPIAdapter：Tavily / Exa / Serper（付费检索 API）
```

- **SearXNG**：自己不做图片搜索，而是聚合 70+ 引擎；返回归一化结果。它能不能给中文工程车图，取决于启用了哪些引擎、这些引擎是否被反爬；
- **Searqon**：自托管“搜索+抓取+清洗”，4 层反爬；源里没有 360/百度，中文图覆盖未知；
- **Tavily/Exa/Serper**：更偏文本/网页搜索；图搜能力要单独验证；
- **Firecrawl**：抓页面内容，不是“找图”。

**结论**：SearXNG 可以作为一个 `SearchAdapter` 接进来，但不能假设它能替代 360；需要用同一批中文工程车查询做对照（P2-W2 E5），看 blocked 率、相关率、成本。

## 4. 降级策略在哪？

现在有三层，但**还不完整**：

| 层 | 策略 | 位置 | 状态 |
|---|---|---|---|
| **查询层** | 型号+工程车 → 型号 → 品牌+构型 → 英文名 | `imagesearch.search_model_images` | ✅ 已有 |
| **通道层** | 360 → 百度 → Bing（累加去重） | `imagesearch.search_images_ex` | ⚠️ 只是“并列尝试”，没有健康度/熔断 |
| **层级层** | exact → environment → platform → cross | `retrieval_engine` `DEGRADE` | ✅ P1 已有 |
| **文本层** | auto → 延迟百度 → Bing | `runner.py` | ✅ 已有（但 Bing 实测不可用） |
| **来源层** | 域名信任/升降级 | `source_registry.json` + `domainbench.py` | ✅ 文本用 |
| **新引擎通道层** | 源健康、熔断、24h 缓存、换源 | P2-W2 计划 | ❌ 还没做 |

**现在的真实情况**：360 是单点；百度/Bing 实际上死了；新引擎只做了“层级降级”，还没做“源健康/熔断/缓存”。P2-W2 要把通道层补齐。

## 5. P2-W1 这次写了什么

| 文件 | 内容 |
|---|---|
| `src/equiplens/retrieval_engine/web.py` | `NullLibraryAdapter`、`WebWorld`、`RuleVerifier`、`live_fetch`（360） |
| `src/equiplens/retrieval_engine/evidence.py` | `EvidenceStore`：写 `image_evidence` |
| `src/equiplens/retrieval_engine/cli.py` | `--web-only`、`--models`、`--evidence-db` |
| `tests/test_retrieval_engine.py` | 13 个测试（含网页-only、规则核验、证据落库） |

### 跑法

```bash
# 网页-only（真实 360；默认不跑测试）
PYTHONPATH=src python -m equiplens retrieval-run \
  --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
  --web-only --models "豪沃6X6,德龙X3000" \
  --run-root data-test/runs --run-id web-smoke \
  --evidence-db data-test/runs/web-smoke/evidence.db
```

### 重要规则

网页结果写进 `image_evidence` 时是 **`candidate`（E1 / identity=probable / origin=unknown）**，不是 `verified`。只有**身份核验**达到 confirmed/probable 并人审通过，才能升级为可信库（可见性/原厂已归档，K1/K2）。

## 6. 下一步 P2-W2

1. 接 SearXNG / Tavily / Exa 适配器（对照，不替换）；
2. 源健康：成功/被拦/空结果计数；熔断；24h 查询缓存；
3. E5 源路由实验：20 条查询 × 5 源，选主/备；
4. 只有 360 稳定时，才把它当主源，其余当补充。

> P2-W2 骨架已落在 [`retrieval-sources-p2w2.md`](retrieval-sources-p2w2.md)：源健康/熔断/24h 缓存 + SearXNG/Tavily 适配器；真实 E5 还需实例/API key。

---

## 7. W1 冒烟结果（2026-11-09，已跑）

命令：

```bash
PYTHONPATH=src python scripts/retrieval_web_smoke.py --limit 8 \
  --out data-test/runs/web-smoke-20261109
```

结果（10 查询 × 8 候选）：

| 指标 | 数值 |
|---|---:|
| 候选 | 68 |
| 下载成功 | 47 |
| 门卫通过 | 31（45.6%） |
| 长边 ≥1200 | 4 |
| **可用（门卫 + ≥1200 + 外观视角）** | **2（2.9%）** |
| 耗时 | 48.5s |

> 2026-11-09 口径已改：不再用「外观视角」当硬门槛。同一批 53 张图（两批去重）
> 按新口径重评为 **概览 13 / 部件 6**（旧可用口径 4）；详见
> [`web-reassess-20261109/report.md`](../data-test/runs/web-reassess-20261109/report.md)。

**结论：未达 W1 验收（≥10 张可用），360 单源不够。人工抽查还发现：自动判为“可用”的 2 张里，1 张其实是多车拼图（1580×1000），真正单台高清只有 1 张（C7H，1707×1280）。**

### 发现的真实问题

1. **360 返回的其实是缩略图**：`_search_360` 之前取 `imgurl`/`thumb`，不是 `img` 原图；已改为 `img`（原图）优先，并补 `width/height/channel/referer`。
2. **分辨率是主瓶颈**：360 结果大量 400–800px；68 张里只有 4 张 ≥1200，2 张自动判“可用”，人工复核后真正可用约 1 张。这直接影响部件裁图和分析。
3. **下载失败 21/68**：原图 URL 有热链/超时/非图片；需要缩略图回退、重试、源健康。
4. **门卫通过≠可用**：46% 门卫通过，但多数分辨率不够；还混入 `detail/interior` 和多车拼图；门卫 margin 很低（可用两张仅 0.0012 / 0.0056），CLIP 对“单台/拼图”不可靠。
5. **身份仍不可靠**：标题里出现同品牌其它型号（如 J6G 查询命中 J7），规则护栏不够。

### 对计划的修正

- **不要现在做 E1 视觉实验**：只有 2 张可用图，标注样本不足；
- **P2-W2 先做源扩展**：SearXNG/Tavily/Bing 高清/官网，配合“高清/大图”查询阶梯；
- **下载回退**：原图失败时回退缩略图（低清，但可用于身份/覆盖）；
- **360 定位**：仍是当前最稳的单源，但不能作为唯一来源。

产物：[report.md](../data-test/runs/web-smoke-20261109/report.md)、[report.json](../data-test/runs/web-smoke-20261109/report.json)、[review.html](../data-test/runs/web-smoke-20261109/review.html)、[MANUAL-REVIEW.md](../data-test/runs/web-smoke-20261109/MANUAL-REVIEW.md)。

### 7.1 HD 阶梯复跑（2026-11-09）

已把“高清/大图”接进 `imagesearch`：
- `search_model_images(..., hd=True)`：工程车 → 型号 → 高清 → 大图；
- `search_images_hd(query, ..., hd=True)`：原查询 → 高清 → 大图；
- 结果按 `width>=1200` 优先返回。

同样 10 条查询复跑：

| 版本 | 候选 | 门卫 | 自动可用 | 人工可用 | 耗时 |
|---|---:|---:|---:|---:|---:|
| 基础阶梯 | 68 | 31 | 2 | 1 | 48.5s |
| **+ 高清/大图** | **73** | **35** | **4** | **3** | **78.8s** |

人工复核：4 张自动可用里 1 张仍是多车拼图；真正可用 3 张，**全部是汕德卡 C7H**，其余 4 个车型 0 张。

产物：[web-smoke-hd-20261109/report.md](../data-test/runs/web-smoke-hd-20261109/report.md)、[MANUAL-REVIEW.md](../data-test/runs/web-smoke-hd-20261109/MANUAL-REVIEW.md)。

**结论**：HD 阶梯有增益（1→3 张），但仍远低于 W1 验收（≥10），覆盖也不均衡；360 单源 + 查询阶梯不够，P2-W2 必须扩源。
