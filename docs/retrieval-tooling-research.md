# 检索模块工具对标调研报告（GitHub 开源社区）

| 文档属性 | 内容 |
|---|---|
| 文档版本 | v0.1（调研报告，供选型决策） |
| 执行日期 | 2026-10-14 |
| 目的 | 为检索模块（FR-1.2，P1.5 提前启动）提供工具选型输入；合成 PRD 开放问题 #2（来源与合规边界）的决策选项单 |
| 关联文档 | docs/architecture-discussion.md（§3 检索交互范式、§7 前次对标）；docs/HANDOFF.md（§3 专项菜单）；docs/data-model-spec.md（license/vocab/来源体系） |
| 方法 | GitHub API 按星标排序检索（9 个检索词）+ 重点项目 README 深读（raw 文件直取，单请求 30 秒超时、失败不重试）。星数为当日快照 |
| 执行记录 | 检索词 9 个中 2 个触发 API 限流（clip+image-search、trafilatura，共享出口 IP，未重试）；WebFetch 通道 ECONNRESET 改用 raw.githubusercontent.com 后全部成功（5/5）；CLIP 搜图层沿用前次对标结论（架构稿 §7.3）不再重查 |

---

## 1. 轮 1：搜索渠道层

| 项目 | 星数 | 状态 | 要点 |
|---|---|---|---|
| searxng/searxng | ~38.4k | 活跃 | 自建元搜索引擎，聚合多个搜索引擎结果，无追踪；AGPL-3.0；文档 docs.searxng.org |
| searx/searx | ~13.6k | 更新放缓（2026-05） | SearXNG 的前身，已被 SearXNG 取代 |
| benbusby/whoogle-search | ~11.6k | 活跃 | 单引擎（Google）自托管代理壳，非聚合 |

**对标结论**：SearXNG 是"渠道聚合层"的默认答案——一次部署获得 Google/Bing/DDG 等多渠道聚合输出，且**支持图片搜索频道**与 JSON 输出（settings.yml 配置项，细节待部署时按官方文档核实），把我们"多渠道检索"从自研变成配置问题。AGPL-3.0 对"自用部署"无传染问题（不做 SaaS 分发即可）。

## 2. 轮 2：抓取与抽取层

| 项目 | 星数 | 状态 | 要点 |
|---|---|---|---|
| firecrawl/firecrawl | ~191k | 活跃 | AI 抓取 API：/scrape（页面→Markdown）、/extract（→结构化 JSON）、/search（联网搜索）、/serp（搜索结果页转数据）、/answer（带来源问答）；MCP 支持；开源自部署 + 云服务双形态 |
| D4Vinci/Scrapling | ~87.4k | 活跃 | 自适应抓取框架（页面变更后自动重定位元素） |
| unclecode/crawl4ai | ~85.5k | 活跃（v0.9.4, 2026-09） | "给 LLM 的爬虫"：pip install + `crawl4ai-setup`（装浏览器）；AsyncWebCrawler → LLM 友好 Markdown；Docker Server / CLI / MCP；开源自托管永久免费，另有云版 |
| apify/crawlee (+python 版) | ~26.1k + ~9.6k | 活跃 | 爬虫自动化库（Node/Python），浏览器自动化与队列管理 |

**对标结论**：抓取层不需要自研。Crawl4AI 的**开源自托管**路线最适合我们（单机本地原则 + 无云依赖 + Python 原生），`/scrape`→Markdown 供文本参数抽取、图片 URL 连同 DOM 上下文一起产出（图文对应的物质基础）。Firecrawl 的 /extract（→结构化 JSON）是名录/参数抽取的范式参考，但其星数异常膨胀，仅作方向参考（沿用前次对标局限原则）。

## 3. 轮 3：图片批量获取与授权层

| 项目 | 星数 | 状态 | 要点 |
|---|---|---|---|
| rom1504/img2dataset | ~4.5k | 维护中 | URL 清单 → 图片数据集：下载+缩放+打包，单机 20 小时 1 亿 URL；**url+caption 配对数据集支持**；**默认遵守 X-Robots-Tag: noai/noimageai/noimageindex 头**（可用参数关闭） |
| WordPress/openverse | ~0.4k | 活跃（monorepo） | 开放授权（CC 等）媒体搜索引擎：Catalog（Airflow 抓取）+ Ingestion + **Django REST API**（api.openverse.org/v1/）+ 前端 |

**对标结论**：两个互补选项。img2dataset 证明"URL 清单→带元数据图片集"是已解决工程问题，且其**合规默认值设计**（遵守 noai 头）值得照抄进我们的抓取礼仪；Openverse 提供授权干净的图源 API（授权元数据可直接对接我们的 license 字段），但**预判风险成立**：CC 图库中工程机械照片覆盖度必然稀疏，Openverse 定位是"授权合规的主力补充源"而非主源。

## 4. 轮 4：检索 Agent 编排层

| 项目 | 星数 | 状态 | 要点 |
|---|---|---|---|
| khoj-ai/khoj | ~37.7k | 更新中 | 自托管"第二大脑"，联网+个人知识问答 |
| assafelovic/gpt-researcher | ~30.1k | 活跃 | 首个开源 deep research agent：Plan-and-Solve + RAG、**并行化 agent 工作**、带引用报告、**领域定制 research agent 套件** |
| virattt/dexter | ~27.7k | 活跃 | **垂直领域**（金融）自主深研 agent——垂直化的实证案例 |
| Alibaba-NLP/DeepResearch | ~20.0k | 更新中 | 通义 DeepResearch，开源深度研究 agent |

**对标结论**：借鉴范式而非引框架（与架构稿 §7.2 结论一致）。三个可抄的设计：① GPT-Researcher 的"计划→并行子任务→汇总引用"正是我们"任务树+缺口驱动补检"的成熟版；② 其"领域定制 research agent"证明垂直化（工程车辆）是正路；③ dexter 证明"垂直窄域 + 结构化输出"的 agent 比通用型更可信。

## 5. 专题：图片与文本抓取的对应性（检索策略新增设计点）

四条配对证据链，强度递减，对应我们 schema 的绑定证据体系：

| 手段 | 内容 | 落到我们哪里 |
|---|---|---|
| ① 结构化抽取 | Crawl4AI/Firecrawl 的 /extract：图片连同其 DOM 上下文（车型标题、参数区块）一起结构化输出 | Source 记录 + 页面上下文字段 |
| ② 页面共现 | 同一页面上的主图与型号文案同现（img2dataset 的 url+caption 配对是同原理的规模化） | 对号证据 `co_occurrence_labeled`（T2 强关联） |
| ③ 视觉验证 | 抓回后做区域匹配/CLIP 校验（裁剪图是否真在主图上、图文是否相符） | `region_match`（T1 级，PoC 已验证可行：距离 3/180 vs 中位 90） |
| ④ alt/caption 文本 | 图片 alt 属性、图注——img2dataset 默认保留 | 挂 Source.note，辅助筛选 |

结论：**图文对应不是新问题，是我们已设计的绑定证据体系在抓取阶段的自然延伸**——抓取时保留①②的证据材料，入库后用③复核，筛选时用④加权。

## 6. 筛选策略的社区方法（对标要点 2）

从本轮项目中提炼三个可借鉴机制：① img2dataset 生态的**概率过滤范式**（laion-aesthetic 数据集按 pwatermark<0.8 / punsafe<0.5 / aesthetic>7 过滤——证明"每张图带多个质量概率分，按阈值筛选"是成熟做法，对应我们 M1 的 quality_flags + M4 打标置信度）；② Scrapling 的**自适应重定位**（页面改版后选择器自动修复——对我们价值有限，我们非长期监控场景）；③ GPT-Researcher 的**来源多样性约束**（防止结果集单一来源偏置）。

## 7. PRD 开放问题 #2 决策选项单（供产品负责人拍板）

| 选项 | 组合 | 合规性 | 覆盖度预判 | 成本 |
|---|---|---|---|---|
| **A. API 优先** | SearXNG 自建聚合（含图片频道）+ Openverse API + 图库 API | 高：全部走正规接口 | 工程车实拍图偏少，名录/参数覆盖好 | SearXNG 自部署零费用；图库 API 免费层 |
| **B. API + 受控抓取** | A + Crawl4AI 自托管抓取厂商官网/展会页（尊重 robots/X-Robots-Tag，img2dataset 式默认合规头） | 中：抓取礼仪齐备但仍是爬虫 | **实拍图主力来源**（厂商官网图质量最高） | 抓取耗时；需维护 |
| **C. 全开放抓取** | 不限渠道直抓搜索结果页 | 低（搜索结果页抓取处于灰色地带） | 最大 | 反爬对抗成本高 |

**我的推荐**：B。名录/参数走 A（结构化 API），实拍图主力走厂商官网受控抓取（图质最高、来源可信度分级最高档），Openverse 作合规补充源。

## 8. 推荐技术栈组合（初判，待拍板后写入设计研讨稿）

```
渠道层    SearXNG（自建，聚合多引擎+图片频道）      [轮1]
抓取层    Crawl4AI 自托管（页面→Markdown/结构化）    [轮2]
图片层    img2dataset 式下载器思路（URL清单+元数据） + Openverse API（合规补充源）  [轮3]
编排层    自研轻量任务树（借 GPT-Researcher 范式：计划→并行子任务→汇总引用），不引框架  [轮4]
对应性    抓取留证据(①②) → 入库区域匹配复核(③) → alt/caption 加权(④)   [专题5]
筛选      确定性规则先行（可信度分级/分辨率/质量标记/哈希去重），概率分后置   [专题6]
```

## 9. URL 索引（保留供复核与后续抓取）

| 项目/资源 | 地址 |
|---|---|
| SearXNG | https://github.com/searxng/searxng ｜ 文档 https://docs.searxng.org |
| Firecrawl | https://github.com/firecrawl/firecrawl |
| Scrapling | https://github.com/D4Vinci/Scrapling |
| Crawl4AI | https://github.com/unclecode/crawl4ai ｜ 文档 https://docs.crawl4ai.com |
| Crawlee (Node/Python) | https://github.com/apify/crawlee ｜ https://github.com/apify/crawlee-python |
| img2dataset | https://github.com/rom1504/img2dataset |
| Openverse | https://github.com/WordPress/openverse ｜ API 文档 https://api.openverse.org/v1/ |
| GPT-Researcher | https://github.com/assafelovic/gpt-researcher ｜ 文档 https://docs.gptr.dev |
| Khoj | https://github.com/khoj-ai/khoj |
| Dexter（金融垂直案例） | https://github.com/virattt/dexter |
| 通义 DeepResearch | https://github.com/Alibaba-NLP/DeepResearch |
| CLIP 搜图参考（前轮） | https://github.com/haltakov/natural-language-image-search 等，见架构稿 §7.3 |

## 10. 局限说明

- 星数为 2026-10-14 快照；Firecrawl/Scrapling/Crawl4AI 星数增长异常（191k/87k/85k 远超常见开源项目增速），仅作方向参考，不作为选型依据（沿用架构稿 §7.4 原则）；
- SearXNG 的 JSON API 与图片频道为已知配置能力，README 未直接载明，**待部署实测核实**；
- Openverse 的工程机械类目覆盖度是预判（未实测查询），部署后应先跑一次真实查询验证；
- 2 个检索词限流未执行（clip+image-search、trafilatura），前者由架构稿 §7.3 覆盖，后者为单库工具不设独立轮次；
- 商业闭源产品（Tavily、Brave API、Serper 等）本轮未直接调研，选项单中的"图库 API 免费层"表述基于常识，选型前应实测配额与条款。
