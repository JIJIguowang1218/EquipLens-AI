# 测试台账（评测与审核意见总账）

| 文档属性 | 内容 |
|---|---|
| 用途 | 所有测试轮次的正式记录：批次、规模、审核包索引、产品负责人意见、后续动作 |
| 规则 | ① 每轮测试必须在此追加一行 + 意见纪要；② 审核包 HTML 与决策归档 JSON 全部索引在 §2；③ 意见按修改日志式记录（原话摘要 + 落实去向）；④ **测试一律写入 data-test/（测试库=评测集），正式库 data/ 只在真实项目使用时填入**（2026-10-15 产品负责人指示，此前混用已纠正）；⑤ T7 起视角标签为机器猜测（查询词声称），人工审核可改；⑥ **审核操作一律走实时审核服务（review-serve）落账，禁止再要求手动导出文件**（意见 #10）；⑦ **临时文件管理**：一律进仓库根 `tmp/`（gitignore 内，用后即删）；测试数据在 `data-test/`、正式数据在 `data/`、缓存在 `data-test/cache/`——禁止临时产物与重要文件混放（意见 #10）；⑧ **每轮测试独立（意见 #14）**：名录冷启动（产品负责人只给类目，EL 检索生成名录→人锁定→搜图），不拿既有审核包/已接受素材当底子；指标按批次切（本轮口径与全库累计分列）；数据层判重并入（D5 同图多源）是幂等不是污染；旧待审包冻结留档 |
| 关联 | docs/HANDOFF.md；docs/test-report-data-layer.md；data-test/reviews/（决策归档） |

## 1. 测试轮次总账

| # | 日期 | 测试内容 | 批次/规模 | 审核包索引 | 结果 | 后续动作 |
|---|---|---|---|---|---|---|
| T1 | 2026-10-14 | 数据层第一档（合成） | 27 项检查 | tests/test_data_layer.py | 27/27 | — |
| T2 | 2026-10-14 | R1 机制验证（S1 夹具） | 8 项 + 回归 91 | data-test/s1-review/review.html（临时区） | 机制全通 | 夹具降级为回归用例 |
| T3 | 2026-10-14 | 真实爬取第一轮（官网首页） | batch-web-e4cb0142cb / 33 候选 | data-test/review-web-truck.html；决策归档 2 份 | 采纳 9/33 = **27%（基线 v0）** | 策略修正（见意见 #2） |
| T4 | 2026-10-15 | 真实爬取第二轮（深爬详情页） | batch-web-2079eb0c15 / 19 候选 | data-test/review-web-truck-r2.html | 仍有大量无关（意见 #3） | 上 CLIP 门卫 |
| T5 | 2026-10-15 | 真实爬取第三轮（门卫 v1） | batch-web-3b0ab92787 / 16 候选 | data-test/review-web-truck-r3.html | 8/8（50%）；意见 #4 全部落实 | 门卫 v2 + 速度修复 |
| T6 | 2026-10-15 | **名录驱动搜图（百度/Bing 双路）** | batch-roster-20261015 / 14 车型 69 候选 | data-test/review-roster.html | **型号对位准确（意见 #5）**；数量与角度不足 | 视角多样化 + 名录扩列 + 泛化测试 |
| T7 | 2026-10-15 | 视角补采 + 名录扩列（D11 提名池首用） | batch-roster2-20261015 / +117 候选（14 老型号补角度 41 + 6 新型号 34 + 视角标签机器猜测） | data-test/review-roster2.html | 待审 | 意见 #6 |
| T8 | 2026-10-15 | **泛化测试**（矿卡×3/起重机×3/沙漠×2） | batch-gener-20261015 / 34 候选；D11 新增 4 类目部件词（吊臂/支腿/货厢举升/回转平台，pending） | data-test/review-gener.html | 待审——验证"类目无关"承诺 | 意见 #7 |
| T12 | 2026-10-17 | **判向探针 v2（Chinese-CLIP 换底座, 意见 #11 路线 A）** | 训练 82→115 条人工方向标注；复查 59 张机器值图（过渡态 23 + v1 探针定向 36）；op-probe2×44 落账；**T12 复核完成：人工标注 29 条、终态全定向（库内 hero_45/side 清零）** | 判向复核页（review-serve --probe-file data-test/probe-suggest.json，实时落账）+ 评测报告 probe-eval-{uform,chinese-clip,chinese-clip-l}.json | 基线复现 35.4% → B/16 留一 59.8–61.0%；**实盘（人审为准）54.2%（32/59）**；重训 115 条留一反降至 51.8%（纠错样本集中难题, **天花板确认 50–60%**） | 定位调整（意见 #12）：判向=嵌入式元数据不再设独立审核关；probe-suggest 默认只出报告；人工下拉禁选过渡态；疑难定向归 M4 VLM |
| T13 | 2026-10-17 | **扩大检索测试·第 1 轮（沙漠牵引车, 意见 #14 冷启动流程）** | 类目词 → roster.py 检索生成名录：5 查询词 / 37 篇来源 / **12 候选**（产品负责人指示全量检索不裁剪）→ 12 台 × 4 视角 × 每视角 4 张 = 48 组查询约 4 分钟（搜图线程池并行化后, 旧串行同规模 12–16 分钟）→ **批次 batch-roster3-20261017：本批新增 114 张, 旧素材再发现并入 18 张（D5 判重生效）, 门卫拦截 96** | 名录归档 roster-沙漠牵引车-20261017-163313.json（锁定=全量）；检索报告 roster-search-report-batch-roster3-20261017.json；审核包 review-serve 实时落账 | **审核完成：整体准确度与质量可接受（产品负责人评）**；批次口径双全率 11/12 台（机器粗类标签待人审）; 发现 J6G 组双构型（意见 #15）; 视角标注搁置（嵌入式元数据路线） | J6G 错配 5 张待改绑/驳回；图题×查询词型号一致性检查列为改进项；第 2 轮=重型吊车+轻型吊车 |
| T14 | 2026-10-18 | **扩大检索测试·第 2 轮（重型吊车 + 轻型吊车）** | 两类目并行名录生成：**12 秒 / 28 秒**（上轮同类 3–4 分钟, 并行化后 15 倍提速）；重型吊车首版被卡车底盘污染（吊车文章总提底盘品牌）→ 加类目同义词扩展（吊车→起重机/汽车起重机/履带吊）重跑 9 秒改善；踢 4 条噪音（天锦/R770/PD1/PD100）后 **20 台 × 4 视角全量检索** → 批次 batch-craneH（重型 9 台, 新增 107 张）/ batch-craneL（轻型 11 台, 新增 92 张, 跨类目并入约 20）；**双端口审核包**（8765=重型 / 8766=轻型） | roster-重型吊车-{163542 污染版,163651 改善版}.json；roster-轻型吊车-20261018-163559.json；roster-search-report-batch-crane{H,L}-20261018.json | **审核完成（大致审毕, 产品负责人：检索能力测试优先）**；重型 9/9 全双全, 轻型 10/11 双全；**构型混杂发现（意见 #16）**：STC800C6/XCT8L4/QY16KC/QY25K5C 四组混入异构车辆, 类型簇实验证实小模型可察觉不可拦截 | 口径注意: 同车跨类目检索并入效应明显; 改进项（图题一致性+类型簇打标+选车确认包）随后 3 轮一并落地；第 3 轮=翻斗铲车 |
| T15 | 2026-10-18 | **扩大检索测试·第 3 轮（翻斗铲车）** | 名录 9 秒（43 篇来源, 同义词扩展生效: 翻斗铲车→翻斗装载机/自卸铲车）；**市场语义揭晓：文章把"翻斗铲车"落在自卸车/翻斗车**（福田金刚系列为主角）；踢 5 条发动机/挖机噪音（WD615/D10/MC07/HW12/E300）→ 7 台 × 4 视角约 2 分钟 → 批次 batch-r3loader-20261018：新增 74 张 / 并入 93 / 拦截 37 | roster-翻斗铲车-20261018-171251.json；roster-search-report-batch-r3loader-20261018.json；审核包 8765 | **审核完成：本批次型号与图像对得上**（对位准确, 无构型混杂发现——较 T13/T14 改善）；**语义偏差（意见 #17）：产品负责人给的"翻斗铲车"与 EL 实际检索的"自卸车"存在理解偏差, 记录在案后续再测**；6/7 台双全（机器粗类标签） | 语义校准待后续测试（类目词→同义词链路的意图对齐）；下一步=选车确认包+意见 #15/#16 改进项建造 |
| T16 | 2026-10-22 | **调研语料采集批（R2 后半前置·第 0 步"先爬后研"）**——新模块 corpus.py：四类信源（official/spec/review/industry）配额抓正文, SERP 走百度真浏览器（roster 机制复用）, **正文 markdown 落盘 + index.json 索引**（修复 R7"只留图不留文"教训） | 计划 tmp/corpus-plan-1.json（7 查询, 配额 12）；批次 batch-corpus-20261022b：**10 篇落盘**（official 3 / spec 2 / review 4 / industry 1, 单篇 4千–3.1万字）, 全程 50 秒 | data-test/corpus/batch-corpus-20261022b/index.json（含失败记录）；首轮 batch-corpus-20261022 全拒留档作教训；单测 test_corpus.py 6/6 | **语料可用**：详评含带形态锚点的设计描述（"在保险杠处, 带有液压式的蹬车踏板"）, 参数配置表齐全（Facts 料）；**教训两则已修**：①SERP 锚点全是 baidu/link 跳转, 对跳转 URL 做 robots 检查 17/17 全拒 → 增 resolve_redirect 先解析真实 URL 再 robots（robots 纪律本身不变）②百度验证码页被 BLOCK 正确拦截。**环境发现：本工作区缺 data-test/equiplens.db 真实测试库与缓存**（回归 W-10/Q-10 因此失败, 与代码无关；T15 审核服务在此工作区不可用） | 下一步：语料分布盘点 → 部件类型学归类（三模板）→ 分析写作规范 v0；修正项：official 配额实际落在 360che 聚合页——官网文本需 site: 限定或走 crawl-web 渠道 |
| T17 | 2026-10-23 | **T16 重跑 + 设计分析文本筛选（文本线第 0 步复盘）**——T16 语料目录被 `.gitignore` 的 `data-test/*` 挡住未同步, 本地缺失; 重建采集计划（7 查询 + 补充 5 查询）, official 改 `site:` 限定; 新增段落级人工定级（A=可用设计分析 / B=相关但偏工程市场内饰 / C=无关） | 批次 batch-corpus-20261023a + b：原始 12 篇, 跨批次去重后 **10 篇 / 42,743 字**（official 2 / spec 2 / review 3 / industry 3）；失败 7 条（robots 2 / URL 规则 5） | data-test/corpus/batch-corpus-20261023{a,b}/index.json；审核页 data-test/corpus/review-corpus-20261023.html；筛选产物 data-test/corpus/design-passages-20261023.md；策略 docs/text-retrieval-design.md | **A 类设计分析仅 2,698 字 = 6.3%**（叙述性正文口径 12.5%）；有 A 段文章 4/10, A≥500 字 3/10（08 子弹头/X7、09 浅谈重卡造型、10 江铃问答）, A≥1000 字仅 1/10（09）；**车型评测/官网/参数页设计分析≈0**；部件覆盖 7/12 提及、4/12 有形态描述, 翼子板轮拱/遮阳板/下护板/液位窗/示宽杆 **5 类零证据**；类目仅重卡, 吊车/装载机/矿卡零样本；**核心正例：09 的"京剧脸谱式设计 → J6→J7 家族化延续"**；复核验证 `site:` 修正生效（落到 sinotruk.com）；筛选脚本 tmp/extract_design_passages.py + tmp/build_design_passages.py 可复现 | **结论：查询模板（车型+评测/外观）天然产出性能配置文本, 设计分析须换设计主题词与设计媒体源；筛选必须段落级**；已建文本检索策略 v0.1（任务类型/信源分类/查询模板/评估指标）；下一步 T18 部件专项（12 部件×3 车型）→ T19 主题趋势 → T20 跨类目（三轮均为**检索策略验证, 不建类型学**；类型学归下游分析整合模块）；`.gitignore` 已加 `!data-test/corpus/**` 白名单, 待提交 |
| T18-pre | 2026-10-23 | **LLM 查询规划预实验（零成本：由对话模型充当 planner，不接 API）**——同一批车型/配额，把查询从“车型+评测/外观”换成设计语汇（前脸/格栅/大灯/家族化/CMF/造型演变），验证“把 LLM 放在查询规划层”的增益 | 批次 batch-corpus-20261023c-llmplan：8 篇落盘（official 0 / review 4 / industry 4），失败 5；8 组设计语汇查询 | data-test/corpus/batch-corpus-20261023c-llmplan/index.json；评分脚本 tmp/grade_batch.py | **有 A 段文章 8/8 = 100%（T17 为 4/10 = 40%）**；保守 A 字数 2,891 vs T17 2,698（文章少 2 篇, 单篇产出 361 vs 270 字）；但 A/清洗后正文仅 2.7%——网易页带入 80+ 推荐位、正文被 4 万字稀释；official `site:`+设计词 **0 命中**；部分行业文疑似 AI 生成 SEO 稿 | **结论：LLM 查询规划显著提升“文章级召回”，瓶颈从“找不到设计文”转移到“段落抽取 + 来源质量”**；下一层=L3 段落级 LLM 质检/清洗；正式 L1 需 API 网关（选型/预算待拍板） |
| T18-broad | 2026-10-23 | **多车型放宽预实验（输入→检索，看车型差异）**——同时查起重机、沙漠牵引车、自卸车/翻斗车、装载机；验证“同一套设计语汇查询跨类目是否成立” | 批次 batch-corpus-20261023d-broad：7 组查询，落盘 6 篇（review 2 / industry 4），失败 12 条 | index.json；tmp/grade_batch.py | **车型差异显著**：①重卡/自卸/沙漠牵引车能拿到好文（豪沃6X6沙漠油田图解、虎6G自卸图解, 部件级设计描述可用）②起重机查询被“百度爱采购”商品页淹没（17万/1.6万字, 0 设计段）③装载机命中学术专文标题（《立足于美学和人机工程学的装载机造型设计》）但豆丁只有摘要预览 ④“翻斗车”查询落到商品页，“装载机”查询才命中设计文——**歧义词直接改变结果类型** ⑤12 条失败中多条是好文章被 URL 规则误拦（沙漠孤鹰 H6066、豪沃V7-X 自卸、Paul80 沙漠卡车、解放长头越野） | **结论：L1 不能只改查询词，必须先做意图澄清 + 信源路由；L3 必须加来源可信度与域名白名单**；下一步做意图 schema（类目/车型/目标/约束/歧义）+ 查询计划 schema + 来源注册表；skill 只承载判断（歧义解释/选源/换词），不承载 robots/配额/账本 |
| T18-blind | 2026-10-23 | **留出类目盲测 + 运行轨迹（编排器首跑）**——用未建档的“随车吊”跑 `text-run`：通用层 → 低信度 → 自动重规划 → 再评估；随后用 LLM 起草的随车吊档案对照重跑 | 运行 run-suicheche-blind-v2（真盲测）与 run-suicheche-profile（草案档案）；每轮 6–7 查询 / 配额 3+3；轨迹含 stages/tools/llm/decisions | data-test/runs/run-suicheche-blind-v2/、run-suicheche-profile/（summary.json + events.jsonl + report.md + plan/grade per round）；批次在 data-test/corpus/batch-text-* | **真盲测：3 篇 / A 198 字（1.8%）/ 35 失败（blocked_url 22、robots 7），replan→stop**；**草案档案：第 1 轮 6 篇但 A=0**（查询被报价/经销商页占据：简书价格问答、湖北正胜/鑫力销售页），第 2 轮通用层 A=562（2.9%），仍 stop；**候选缓冲修复把单轮文章 1→6 篇**；运行时长 36–65 秒，token 估算 66/11（人工 planner，非 API）；`company/报价/价格` 标题降权规则已加 | **结论：档案也可能错，必须允许“低信度→退通用层→仍低→停并问人”**；通用层噪声大（混入豆瓣书、军工/越野文）；下一步 L3 加“类目相关性”维度、设计媒体源、坏文误拦复核；高空作业车留作下一盲测 |
| T18-blind2 | 2026-10-23 | **盲测收口：失败口径修正 + 重规划必须换查询**——把 blocked_url/source_skipped 从“硬失败”拆出（政策跳过≠抓取失败）；宽搜轮改为只跑与首轮不重叠的查询（工业设计/CMF/学术） | run-gaokong-blind-v3：两轮 6 查询 + 7 查询，配额 3+3；run-suicheche-* 对照保留 | data-test/runs/run-gaokong-blind-v3/（events/summary/report/plan/grade） | **高空作业车：第 1 轮 5 篇 A=947（2.9%）→ replan；第 2 轮 4 篇 A=1,723（6.6%）→ ok**；合并口径 9 篇 / A 2,670（4.5%）；硬失败 9 / 政策跳过 29；62 秒；token 估算 68/9。**修正前**第 2 轮把 blocked_url 计入失败（75%）→ 误判 stop，修正后 ok | 结论：**政策跳过与抓取失败必须分账**；**重规划必须产生不同查询**才叫重规划；下一步 L3 类目相关性 + 设计媒体/学术源；随车吊仍低（真盲测 1.8%），需重写草案档案 |
| T18-budget | 2026-10-23 | **预算敏感性 + 隐藏预算帽修复**——同一高空作业车，`max_fetch=10` vs `20`；检查预算是否真的放开查询丰度 | 修复前 `per=min(3, max_fetch/类型)` 且配额不超过查询条数 → 20 预算仍 3+3；修复后 `per=max_fetch/类型`、配额不再受查询条数限制 | `data-test/runs/run-gaokong-budget20/`（修复前）、`run-gaokong-budget20-v2/`（修复后，遇 SERP 空）；离线计划测试 8/8 | **修复前：20 预算只出 3+3 配额**；修复后计划为 **10+10**（离线测试 `sum(quota)==12/4` 通过）；另发现 schema `quota.maximum=10` 也是隐藏帽，已放开到 60；网络复跑遇百度 SERP 空/验证页，0 篇，已加 `serp_looks_blocked` 诊断并写入 report/events | **预算必须显式由 `max_fetch`/`per_type_quota` 控制，不能有隐藏 3 帽**；SERP 被拦要单独报，不能静默成“0 命中”；下一步做预算-产出曲线（per_type 1/3/6/10）再定默认值 |
| T18-budget-curve | 2026-10-23 | **预算-产出曲线（第一步）**——在线 4 档 `per_type_quota=1/3/6/10` 全被百度验证页拦住（每轮 SERP 6/6 blocked）；改用已有成功批次做离线近似曲线 | 在线 4 轮（q1/q3/q6/q10）均 0 篇、2–2.3 秒、SERP 6/6 被拦；离线样本 11 篇（高空作业车，去重 URL） | `data-test/runs/run-budget-q{1,3,6,10}/`（失败记录）；`data-test/runs/BUDGET-CURVE-20261023.md`（离线曲线）；`data-test/runs/INDEX.md`（14 条运行台账） | **离线：q1≈2 篇 A 252（3.7%）→ q3≈6 篇 A 2,068（5.2%）**；q6/q10 样本不足；第 10 篇单篇新增 1,926 字——**边际产出由“碰到高产出源”决定，不是篇数本身**；在线曲线因 SERP 被拦未完成；Bing RSS/HTML 实测不可用 | **初步结论：探测预算 q3（≈6 篇）足够看策略信号；生产预算从 q6 起，不做线性加篇**；下一步：SERP 恢复后补在线曲线，或接 Sogou/其他网页搜索；同时做 L3 类目相关性（随车吊 1.8% 的根因不是预算） |
| T18-eval | 2026-10-23 | **L3 评测集 v1**——盲测 7 篇 A 级文章逐篇标注四级（A_cat/A_comp/A_gen/C），建评测基准 | 7 篇（01/10/12/14/15/17/18） | `data-test/evals/l3-relevance-v1.json`；审核包 `data-test/evals/review-l3-v1.html` | 关键词假阳性 **43%**（3/7 空洞营销/竞赛攻略/毕设代做）；A_cat 真实产出仅 2,410 字（51%） | 产品负责人 10-30 审核：见意见 #20；闸门目标从"降假阳性"改为"对象锚定+具体性" |
| T18-roster | 2026-10-30 | **全名录大规模文本筛选测试**——T13–T15 锁定名录全部 4 类目 39 车型，爬取+筛选，验证指向性机制与各车型文本储备；三分类 V/P/G/C | 4 批 61 篇 / 3.65M 字正文；候选段 265 段 / 24.5K 字；模型判定 265 段 | `data-test/runs/T18-ROSTER-20261030.md`；`data-test/evals/review-roster-20261030.html`；批次 `batch-corpus-roster-*-20261030` | **V 3.2% / P 12.9% / G 9.2% / C 74.8%**（候选段口径）；39 车型仅 8 个有 V/P 素材；A 档假阳性 **40.4%**（复现 L3 v1）；C 档 47% 来自汽车之家首页/报价页 | 三项机修：配置行穿透、类目查询被车型名过滤误杀、轻型吊车 SERP 被拦；详见报告 §6/§8 |
| T18-runner | 2026-10-30 | **L4 执行 loop**——重试策略 + 通道降级链 + 单元契约验收 + 断点续跑；textrun.execute 接入 | runner 单元测试 6 项；真实小批 run-smoke-runner（2 篇/9 候选/auto 通道） | `src/equiplens/runner.py`、`tests/test_runner.py`、`data-test/runs/runs/run-smoke-runner/` | 首轮成功即 ok；被拦后自动换 Bing；全通道失败→failed+blockers；低产出→degraded；续跑跳过已完成单元 | 机制借鉴 Temporal/Crawlee/LangGraph 语义，不引框架运行时（见 `docs/agent-loop-mechanisms.md`） |
| T18-audit | 2026-10-30 | **误杀抽样检测**——C 档按域×长度分层抽样 + 强语汇/型号护栏队列 + 加权漏杀率（Wilson 上界），替代全量人工审核 | T18-roster 四批：C 档 6,076 段；抽样 23 条；护栏 166 条抽查 12 条 | `src/equiplens/audit.py`、`tests/test_audit.py`、`data-test/evals/audit/audit-report.md` | 抽样 23 条全判 C（均广告/报价/验证页）；**估计漏杀 0%，95% 上界 14.3%**；护栏抽查 0 命中 | 结论：配置行修复后规则层误杀风险低；护栏队列保留为常驻复核入口 |
| T18-domainbench | 2026-10-30 | **域名基准与发现通道**——同一组查询跨站点对照，按 A 产出/千字、抓取成功率、robots 分级，产出排行榜与升降级建议 | 10 条查询 / 18 域名 / 24 页 | `data-test/evals/domain-bench-20261030/`（report.md/leaderboard.json/proposals.json）；CLI `domain-bench` | 发现 **www.yoojia.com（A/千字 89.5，high）**，抽查为 PI 设计战略/CMF 解析转载；dealer.360che.com 32.9 medium 与注册表一致；百度系子域 0 产出 | 注册表新增 yoojia（high）；其余保持观察；建议加大每域页数复测一轮 |
| T18-domainbench-r2 | 2026-10-30 | **域名基准复测与通道修正**——换一组查询、每域 5 页；修正：记录 SERP 被拦/通道、信任分级只采信百度样本、子域不归并、新增/降级样本门槛；yoojia 定向验证 | 10 条查询 / 26 域名 / 42 页；yoojia 定向 2 页 | `data-test/evals/domain-bench-20261030-r2/`（含 yoojia-check.md）；`domain-bench-compare-20261030.md` | 首跑异常（全 0）根因=百度被拦退 Bing 抓到官网/商品页；修正后 tcv360 228/千字、news.sohu 163/千字均仅 1 页→不入库；**yoojia 复测 71.8/千字，与首轮一致，保留 high** | 提案改为保守：新增需 ≥2 页+≥5K 正文，降级需 ≥3 页+≥15K 正文；两轮自动提案均为 0 |
| T18-chain2 | 2026-10-30 | **新降级链实盘验证 + 误杀抽检自动收尾**——runner 通道 auto→延迟重试百度(4s)→Bing；text-run 结束自动生成 audit-sheet | 汽车起重机 / 4 篇 / C 档 733 段抽样 10；run-chain2b 自动抽检 766 段/10 样本 | `data-test/runs/runs/run-chain2/`、`run-chain2b/`（含 audit-sheet.{json,md}）、`data-test/evals/audit/run-chain2/` | 首轮 auto 成功（本次未被拦，降级链未触发；分支逻辑由 test_runner 6/6 覆盖）；A 531 字（0.6%）；抽检 10 条全 C，估计漏杀 0%（95% 上界 27.8%，样本小） | 实盘链路通；每批运行自带抽检包（summary.audit 记录 population/guard/sample）；降级链的"被拦恢复"待拦截时段自然验证 |
| T18-roster2 | 2026-10-30 | **全名录复测（验证 1+2）+ 两处流程修复**——4 类目×6 车型，预算 16 查询/6 抓取；修复预算截断轮转、明确车型时不再歧义阻塞 | 4 类目 / 各 2–6 篇 | `data-test/runs/runs/run-roster2b-*`、`data-test/runs/roster2-summary.json` | A 产出：沙漠 0（2 篇为无关 MPV/客车）、重型 0.56%、轻型 0.31%、翻斗 4.9%；**site: 定向实测无效**（百度全拦、Bing 只回栏目页） | 两处修复：①预算截断按信源类型轮转（定向查询不再被挤掉）②明确车型视为意图确认；site 定向改为注册表开关、默认关闭；信源定向待品牌名查询验证（需百度恢复）；复测必须用新 run_id（否则 runner 续跑会复用旧批次） |
| T18-gate | 2026-10-30 | **确定性闸门 v1**——对象锚定 + 主题类型排除 + 具体性要求；在 T18-roster 265 段金标上评估 | 265 段（V/P/G 63 vs C 202） | `src/equiplens/l3gate.py`、`tests/test_l3gate.py`、`data-test/evals/l3-gate-v1.{md,json}`、CLI `gate-batch` | 精确率 **93.1%** / 召回 85.7% / F1 0.893 / 假阳性 **6.9%**（关键词基线 40.4%）；实盘批次通过 5/750；拒绝理由：no_design_content 692、passenger_car 33、no_concrete 17、topic 3 | 剩余 FN 9 条为 G 档短论述（可后续放宽）；下一步接入 text-run 作为模型判定前置 |
| T18-assoc | 2026-10-31 | **关联清单（L1.5）：skill 四轮 A/B + 实图核对 + 降级**——无 skill vs skill（v0.1/v0.2/证据版）三轮 A/B + 相关性盲标 + 真实 `imagesearch` 抓图核对 | 8 案例 × 12 槽（两轮）；相关性池 65 条 / 3 案例；实图 23 车型 70 张（105 判定） | `docs/association-skill-archive.md`；`data-test/evals/ab-20261031/`（`EVIDENCE-AB.md`/`RELEVANCE.md`/`IMAGE-AB.md`/`scores*.json`）；`data-test/ab-images/review.html` | fill：v1 **5/96** → v2 **82/96**（但 89% 方向，verified 9.4%）；相关性 **100% vs 100%**（直证 19/18，层覆盖 9/6）；证据 **11/12 vs 11/12**；实图 **合格待测**（目测无明显问题） | **结论：判断打平，skill 降级为 schema+证据+校验**；同时修 `imagesearch`（360 通道/相关性/构型护栏）与接入 `gate.check_exterior`；新增 `run_meta` |
| T18-gatewire | 2026-10-31 | **闸门接入 text-run grade + 离线回放**——`passage.grade_batch(gate_l3=True)` 逐段过闸，同批输出"关键词基线 A"与"过闸 A"双轨指标（保留率/段通过率/拒绝理由）；`strategy` 改用 `gated_*` 判低信度；`scripts/replay_gate.py` 只读已落盘语料做 A/B 对照 | T18-roster 四批 6,806 候选段 / 568,409 字（离线，不触网）；textrun 测试 13/13 | `src/equiplens/{passage,textrun,strategy}.py`、`tests/test_textrun.py`、`data-test/evals/gate-replay-20261031.{md,json}` | **过闸 248/6,806 段 = 3.6%**；基线 A 4,028 字 → 过闸 A 1,810 字，**保留 44.9%**；分批次：沙漠牵引车 66.3%、翻斗铲车 77.9%、轻型吊车 20.1%、重型吊车 20.6%；拒绝理由 `no_design_content` 5,668 / `config_line` 547 / `topic_type` 136 / `passenger_car` 113 | 吊车两类保留率低=关键词 A 多为营销/参数文本，与"吊车设计文稀缺"一致，非闸门过严的信号；下一步=整体测试（带阈值扫掠），并并行讨论关联分析/清单推荐模块（HANDOFF §3.2） |
| T19-pre-brief | 2026-11-09 | **检索前任务单纸面测试（5 深度 + 20 广度）**——不联网/不查库，验证任务单能否稳定产出：工况/基础构型假设、区域 vs 部件粒度、部件位置、层级降级（删除每层配额）、验收标准 | 5 个真实输入 + 20 类目扩展（含 11 个开 environment 层、9 个不开的对照；29 个新部件实例） | `data-test/evals/task-briefs-20261109/`（README + BRIEFS-5 + CASES-20，MD/JSON 各一份） | 5/5 深度案例通过人工评审（v0.2 修订：location、region、base_platform）；20 例全部可产出任务单，未出现具体车型/预设配额；新部件 29 个待补词表 | 下一步：按 R1–R10 rubric 逐条打分；补 `data/category_profiles.json` 的 `base_platform`；进入检索中命中单演练 |
| T20-retrieval-engine | 2026-11-09 | **检索中 P0–P1：契约 + 状态机 + 检查点 + 假适配器**——任务单 v0.3、状态/事件 schema、策略骨架、证据表 DDL；状态机库内优先/外检/核验/填槽/降级/缺口；夹具 CLI | 10 个离线单元测试 + 1 个夹具演示（沙漠牵引车：库内 1 台 step 被拒 → exact 2 台 → environment 1 台） | `src/equiplens/retrieval_engine/`；`data-test/retrieval-fixtures-20261109/`；`schemas/task-brief-v3.schema.json` 等；`docs/retrieval-p0-p1.md` | **10/10 通过**；演示 DONE，slots 3/3，u-exact 2/2，u-env 1/1；事件 20 条；检查点/续跑/去重/降级均有测试 | 下一步 P2：`image_evidence`/`asset_part_feasibility` 落 SQLite + 50 条人工录入 + 库内检索接真实快照 |
| T21-web-adapter | 2026-11-09 | **检索中 P2-W1：网页-only + 360 适配器 + 规则核验 + 证据落库**——`NullLibraryAdapter`（空库）、`WebWorld`（型号候选→360→下载/门卫/视角）、`RuleVerifier`（标题/构型/视角/分辨率）、`EvidenceStore`（`image_evidence`）、CLI `--web-only`/`--evidence-db` | 13 个离线测试（含网页-only、坏资产拒绝、证据落库）；真实 360 未跑 | `src/equiplens/retrieval_engine/{web,evidence}.py`；`docs/retrieval-web-p2w1.md`；`tests/test_retrieval_engine.py` | **13/13 通过**；P1 的 10 个测试未回归；网页结果只写 `candidate/E1`，不自动 trusted | 下一步 P2-W2：SearXNG/Tavily 适配器 + 源健康/熔断/缓存 + E5 源路由对照 |
| T22-web-smoke | 2026-11-09 | **W1 网页检索冒烟（360，10 查询 × 8 候选）**——验证网页链路能否产出可用材料；下载/门卫/视角/分辨率/可用率 | 10 查询 / 68 候选 / 47 下载成功 / 31 门卫 / **自动 2 可用（人工复核真正单台高清约 1 张，另 1 张是多车拼图）**；48.5s | `scripts/retrieval_web_smoke.py`；`data-test/runs/web-smoke-20261109/{report.md,report.json,review.html,images/}` | **未达 W1 验收（≥10 可用）**；360 单源可用率 2.9%；分辨率瓶颈（仅 4 张≥1200）；下载失败 21/68；门卫 margin 低、拼图误判；标题有同品牌错型号 | 修正 `_search_360` 取原图 `img` + Referer；下一步 P2-W2 源扩展（SearXNG/Tavily/官网）+ 高清查询阶梯 + 缩略图回退；暂不做 E1 |
| T23-web-hd | 2026-11-09 | **W1-HD 复跑：高清/大图查询阶梯接进 imagesearch**——`search_model_images(hd=True)`、`search_images_hd()`；10 条同查询复跑 | 10 查询 / 73 候选 / 51 下载 / 35 门卫 / **自动 4、人工 3 可用**；78.8s | `src/equiplens/imagesearch.py`；`scripts/retrieval_web_smoke.py`；`data-test/runs/web-smoke-hd-20261109/` | 相比基础阶梯：人工可用 1→3；但 3 张全是 C7H，其余 4 车型 0；仍低于 ≥10；门卫仍误判多车拼图 | HD 阶梯保留；P2-W2 扩源（SearXNG/Tavily/官网）+ 下载回退 + 多车检测 |
| T24-source-router | 2026-11-09 | **P2-W2 源路由骨架：健康/熔断/24h 缓存 + SearXNG/Tavily 适配器**——`SourceRouter` 顺序回落；连续被拦熔断；查询缓存；SearXNG JSON 解析 | 5 个离线测试 | `src/equiplens/retrieval_engine/sources.py`；`tests/test_retrieval_sources.py`；`docs/retrieval-sources-p2w2.md` | **5/5 通过**；真实 SearXNG/Tavily 未联调（缺实例/key）；360 仍是唯一实测可用源 | 下一步 E5：20 查询 × 5 源对照；补下载回退与多车检测 |
| T25-gate-v3 | 2026-11-09 | **门卫标签集 v3 + 图片可用分层**——补内饰舱/网格拼图/网页截图/广告字 4 个反例；新增 `gate.assess_image`/`assess_from_gate`（概览 ≥800 / 部件 ≥1200，视角只作提示）；引擎 `RuleVerifier` 的视角从硬缺陷降为 warning；冒烟脚本输出两层口径 | 53 张 W1 实图离线重评（`scripts/reassess_smoke.py`）+ 4 查询联网复跑（25 候选） | `src/equiplens/gate.py`、`retrieval_engine/{web,contracts}.py`、`scripts/{reassess_smoke,retrieval_web_smoke}.py`、`tests/test_gate.py`；`data-test/runs/web-reassess-20261109/`、`web-smoke-v3-20261109/` | 门卫通过 v2→v3 **同字节重算 34→31**（3 张由过变拒：2 拼图、1 内饰；其中 1 张仅 ±0.001 边界；批次记录旧 PASS 36）；口径由“旧可用 4”改为 **概览 13 / 部件 6**；联网 4 查询：门卫 11、概览 6、部件 2、外观提示 8；视角 top1−top2 中位数 **~0.003** | 视角不得当硬门槛已落实；下一步：门卫阈值扫掠（放行率×精确率曲线）、下载回退、多车/拼图检测加强、扩源（SearXNG/Tavily/官网） |
| T26-two-stage-gate | 2026-11-09 | **两段式门卫 + 98 张全流程回放**——第一段 `gate.prefilter`（零模型：字节/解码/动图/宽≥350 且长边≥320/长宽比≤4/近空白 std<6），不通过不进 CLIP；`check()` 支持传标签集 + `check_v2()` 同字节 A/B；新增 `reference_candidate` 低清参考层；`imagesearch._download_and_gate`/`live_fetch`/冒烟脚本全部接预筛 | 98 个已下载文件（基础 47 + HD 51，1 个批次遗留）× 同字节重算标题护栏→预筛→v2/v3 门卫→视角→分层 | `src/equiplens/gate.py`、`imagesearch.py`、`retrieval_engine/web.py`、`scripts/{replay_filter_98,retrieval_web_smoke}.py`、`tests/test_gate.py`；`data-test/runs/filter-98-20261109/{report.md,index.html}` | 98 文件：预筛 0、CLIP 98、v2 62→v3 56、概览 22 / 部件 9 / 参考 34；**唯一 URL 53：v2 34→v3 31（新拦截 3）、概览 13 / 部件 6 / 参考 18 = 31 闭合**，与 T25 的 34→31 完全一致（v4 修正“背景多车”后为 33→43 / 概览 17 / 部件 8 / 参考 26，见 T27）；**门槛教训：初版把预筛下限设成 800，拦下 30 张唯一图，其中 18 张门卫会放行（17 张部件特写）→ 改 320，只挡缩略图级垃圾**；624×480 拼图裕量仅 −0.0011（边界）；`tests/test_gate.py` 11/11 | 对比页可按“预筛拦截/CLIP 拒绝/参考层/v3 新反例命中/标签有变化”筛选，并带 v2/v3 标签词典；下一步：阈值扫掠（复用逐图分数，单看边界样本）、下载回退（18 张 <800 多是 360 中图） |
| T27-gate-v4 | 2026-11-09 | **门卫 v4：修复“背景多车”误杀**——keep 集加第 4 条 `one truck in the foreground with other trucks parked in the background`；`scene=multi_vehicle` 从硬拒降为 hint（`background_vehicles`），只进参考层、不占概览/部件名额；同图去重改为字节 sha1 | 52 张唯一图 × 5 个标签变体的同字节对照实验（multi 13 / 真坏图 9 / 原通过 31 三组）+ 98 文件全量回放 | `src/equiplens/gate.py`、`tests/test_gate.py`、`scripts/replay_filter_98.py`；`data-test/runs/filter-98-20261109/{report.md,index.html}` | 变体 B（只加 1 条 keep、不动反例）**multi 恢复 13/13、真坏图仍拒 9/9、原通过 31/31**；C 放走 1 张真坏图、D/E 丢 6 张原通过；效果：52 张唯一 v2 33 → **v4 43**，概览 **17** / 部件 **8** / 参考 26，被拒仍 9 张；98 行 v2 62 → v4 80（概览 29 / 部件 13 / 参考 51）；`tests/test_gate.py` 11/11 | 边界：本批无“真·多车队列”金标，scene=multi 只进参考层是缓解不是证明；下一步阈值扫掠要把新 keep 标签的 ±0.01 边界一起看 |
| T28-cdn-upgrade | 2026-11-09 | **CDN 后缀升图（分辨率提升，零新请求源）**——`imagesearch.upgrade_image_url` 把 `!600`/`!550`/`!602`/`!360` 换成 `!1200`；`_download_and_gate` 先试大图、失败回落原 URL；`_fetch_image` 增加 HTTP 状态码检查 | 13 张带后缀的低清参考图联网实测 + 3 张高频能量抽检 + `test_imagesearch` | `src/equiplens/imagesearch.py`、`tests/test_imagesearch.py`、`docs/image-filter-pipeline.md` §10；`data-test/evals/image-gate-52-20261109.json`（人工金标 52 张） | **10/13 升到 1200×800 并进入部件可用**（2 张 401/403 回落、1 张仍因 scene=multi 留参考层）；高频能量是“600 上采样到 1200”的 **1.95/2.18/1.59 倍** → CDN 有更大母图，非单纯放大；预期唯一图部件可用 **8 → 18**（超 W1 ≥10 验收线）；`test_imagesearch` 9/9 | 需一次 W1 全量复跑用新批次确认字节变化对门卫分数的影响；再往下是扩源与任务单 |
| T29-w1-v5 | 2026-11-09 | **W1 复跑（接入 CDN 升图 + 门卫 v4 + 参考层）**——同一 10 条查询，验证“升图能不能把部件可用推过验收线” | 10 查询 / 72 候选 / 49 下载 / 39 门卫 / 26 概览 / **18 部件** / 13 参考；83.4s | `scripts/retrieval_web_smoke.py`；`data-test/runs/web-smoke-v5-20261109/`；`docs/image-filter-pipeline.md` §10 | **部件可用 18 ≥ 10，W1 验收达标**（v3 时代 4 查询只有 2）；18 张部件里 **11 张来自 `!1200` 升图**；下载失败 23（404×7 / 连接×7 / 403×5 / 502×1）；按车型部件：北奔 7、解放J6G 5、汕德卡 4、豪沃 1、德龙 1 | 下一步：多源对照（3 源 × 5 查询）、任务单驱动替换手写查询；本批输入仍是脚本内硬编码的 5 车型 × 侧视/前脸 |
| T30-source-harvest | 2026-11-09 | **来源页回访实验（负结果）**——`_search_360` 保留 `link`；新增 `harvest_source_page`/`extract_page_images`（HTMLParser 抽图）；页面优先级（资讯站加分、B2B 排除）；升图规则扩到搜狐 `w_1280` | 同 10 查询公平 A/B（先截断搜索命中再挂回访，避免候选虚高） | `src/equiplens/imagesearch.py`、`scripts/retrieval_web_smoke.py --harvest`、`tests/test_imagesearch.py`（11/11）；`data-test/runs/web-smoke-harvest1-20261109/`；[`retrieval-experiments-log.md`](retrieval-experiments-log.md) E5 | 候选 72→128、下载 49→103，但 **page 通道 56 候选只出 3 张部件**（24 张图标被预筛拦、多为 640px），总部件仍 **18**、耗时 +23s → **净收益不明确，默认 `--harvest 0`**；Scrapling 0.5.1 四项验证均无增益（百度 antiFlag / CDN 401 / 页面抓取），不接入 | 可调方向：只回访 360che/chinatruck 文章页、改从站点图集列表批量抓、补 pstatp 等 CDN 升图；下一步转为最小 loop |
| T31-loop-m1 | 2026-11-10 | **M1 最小 loop：沙漠牵引车**——用 T19 的 C01 任务单转引擎 brief（3 车槽 / exact 2 + environment 1 / 6 部件），`--web-only` 跑真实 360；修复 loop 两个结构 bug | 3 次运行（v1/v2/v3），手动候选 3 台，22 次抓取/核验 | `src/equiplens/retrieval_engine/{engine,state}.py`、`data-test/evals/task-briefs-20261109/brief-m1-desert.json`、`data-test/runs/loop-m1-desert-v3/`；[`loop-m1-desert.md`](loop-m1-desert.md) | **v3 DONE 3/3**（20 事件、2 次发现、1 次降级、6 queries / 22 fetches）；修复 ①资产-部件绑定（asset_id 全局去重 → `(asset, part)`）②跨层抢证据（`unit_ids` 合并）③Windows 状态写盘重试；`test_retrieval_engine` **15/15** | 候选车型仍是人工 `--models`，`EXTERNAL_DISCOVER` 未真发现；验收不看部件可见性；证据未落库（下轮补 `--evidence-db`） |
| T32-loop-isolated | 2026-11-10 | **C01 隔离检索 loop（12 车槽，实时发现，不读历史）**——`discover_models` 只从实时 360 抽候选；`WebWorld` 无 models 时自动发现；图片落 `images/`；`--evidence-db` 写 `image_evidence` | 12 候选 / 12 车槽 / 24 查询 / 57 抓取 / 10.8 分钟 | `src/equiplens/retrieval_engine/{discover,web,cli}.py`；`data-test/runs/loop-c01-isolated/{REPORT.md,events.jsonl,state.json,summary.json,evidence.db,images/}`；[`docs/loop-m1-desert.md`](loop-m1-desert.md) §7 | **12/12 台各有 ≥1 张过门卫图**（20 张图过两段式门卫、18 条证据落库）；早前写的“6/12 完整覆盖”无效（部件通过=规则判定，无可见性检测），车槽 6/12 FAILED（gap exact 6/8）；6 台失败原因：3 台检索结果全是经销商/二手页（0 张过门卫）、3 台只有低清；loop 两端反馈（GAP→DISCOVER→DEGRADE）均有事件记录 | 瓶颈在“候选名→同款图”召回与低清，不在 loop 结构；下一步：型号代码/官网图集召回、部件可见性、证据库接回 LIBRARY_SEARCH |
| T33-loop-c01-res | 2026-11-10 | **C01 隔离 loop 口径修正重跑**——分辨率标签改 `res_standard`(≥800)/`res_high`(≥1200)，RuleVerifier 低清降 warning、WebWorld 不再按分辨率丢弃；loop 验收改“每车 ≥1 张通过核验的图” | 空库 + 实时发现 12 候选 + 12 车槽，180 次抓取 | `src/equiplens/retrieval_engine/{web,engine}.py`、`gate.py`；`data-test/runs/loop-c01-res/{REPORT.md,audit.html,fetch_log.jsonl,images/}` | **12/12 车槽 DONE**；48 张唯一图（全局 46）、37 过门卫、**19 张 ≥800 / 12 张 ≥1200**；**9/12 台有 ≥1 张 ≥800**，F3000/欧曼/C7H 只有小图；120 条下载失败（403/404）；门卫仍 v4、两段式未改 | 身份/上装校验缺失（天锦混入高空作业车/冷藏车）；召回仍是瓶颈（每车 2–6 张） |
| T34-loop-plan | 2026-11-10 | **在线规划 + 引用核验 + 补位/重规划：12 槽交付**——plan 池接入 `EXTERNAL_DISCOVER`；`normalize_query` 长名转短键；`GAP_CHECK` 先 refill 池、池空再 `replan`（LLM+Search，≤2 次）；新增 `api_log`/`replan_log`/`citation_log` | 23 候选（15+4+4）/ 12 槽 / 160 次抓取 | `src/equiplens/retrieval_engine/{web,engine,contracts}.py`、`scripts/{plan_candidates,render_fetch_audit}.py`；`data-test/runs/loop-c01-plan4/{REPORT.md,audit.html,api_log.jsonl,replan_log.jsonl,citation_log.jsonl}` | **12/12 DONE**；47 图 / 42 过门卫 / 9 张 ≥800 / 5 张 ≥1200；引用核验 19/25 命中；API 35 次调用 **$0.02325**；修复上一轮 8/12 的三个 loop 缺陷（池未排空、不会重规划、长名当查询） | 图仍偏小、身份/上装校验缺失；重规划有成本，需预算上限 |
| T35-loop-quality | 2026-11-10 | **身份/完整性校验修复 + 交付缺口复核**——发现引擎重建 Asset 时丢 title/model，导致 RuleVerifier 的型号/构型校验被静默跳过（底盘图当整车通过）；修复后把“底盘/车架/驾驶室/配件”记为 `not_whole_vehicle` 警告、型号码缺失但品牌命中记 `identity_probable`；并复核 9/12 交付缺口 | 23 候选池 + 2 次重规划（+18/+2） | `src/equiplens/retrieval_engine/{engine,web}.py`；`data-test/runs/loop-c01-plan7/` | 修复前“通过”含底盘/错型号图；修复后 12 槽只交付 **9**（exact 8/8、env 1/4），81 图、API 34 次 $0.0218；证明**缺口根因是 360 对冷门底盘的召回**，不是门卫 | 硬性交付需定义“降级档”（probable identity / 仅部件图）并显式标记；下一步：交付守卫 + 排序 + 扩源（外国品牌 360 内容稀缺：Zetros 0 命中、Arocs 仅房车、MOL 误配） |
| T36-verify-redesign | 2026-11-10 | **核验重构（身份分级 + 只拒矛盾 + 引用页作证）**——修掉“品牌兜底后又无条件 wrong_identity”的 bug；身份分 confirmed/probable/unknown；构型任一命中即可；引用页命中可整台占槽；底盘图记 warning；重规划上限 2→4 | 同一批 31 个候选 / 12 槽；先用 plan7 状态离线回放，再实跑 | `src/equiplens/retrieval_engine/{web,engine}.py`；`data-test/runs/loop-c01-plan9/` | 离线回放：可占槽 9→**13**（恢复 6 台）；实跑 **12/12 DONE**（exact 9 + env 3），38 图 / 34 过门卫 / 10 张 ≥800 / 5 张 ≥1200；API 40 次 **$0.02625**；`test_retrieval_engine` 15/15 | 审核页尚未区分“过门卫/已占槽”；unknown 身份仍不进正式槽；图偏小 |
| T37-delivery-foreign | 2026-11-10 | **交付守卫 + 审核页双口径 + 外国品牌召回修复**——①`summary.delivery`（required/delivered/missing/degraded/status），不足时 CLI 退出码非 0；②审核页把「过门卫 / 入选交付 / 占槽车型」分开标（`data-sel`、✓车型、仅过门卫筛选）；③`_relevant` 修 4 个召回 bug：多构型 AND（Arocs 6×6/8×8 永远不相关）、纯数字当型号码（“800ml”误命中 MOL）、中外品牌无别名（Volvo→沃尔沃）、构型必须在标题出现；④新增 `alias_query`/`query_variants`，拉丁型号名补中文品牌改写；⑤RuleVerifier 复用品牌别名/车系判定 | 只读 360 的召回诊断（6 个外国车型 × 规划 query/手写 query）；Zetros/Arocs/Volvo 各跑真实 `live_fetch`（不调 API） | `src/equiplens/imagesearch.py`、`src/equiplens/retrieval_engine/{web,engine,cli}.py`、`scripts/render_fetch_audit.py`、`scripts/diag_foreign_search.py`；`data-test/runs/loop-c01-plan9/{summary.json,audit.html}` | 修复前 Arocs/Zetros/Volvo 的 360 raw 命中 **12 条但相关 0**（构型 AND + 品牌语言错配）；修复后 Zetros **6 图/6 probable**、Arocs **5/5**、Volvo **6/6** 全部进漏斗并通过核验；`_relevant` 回归 12/12、`test_retrieval_engine` **17/17**；plan9 交付 12/12 但 **7 台 degraded**（无 confirmed 图，靠 probable+引用兜底） | 规划器 query 仍会产出“Zetros 4051 AS 6x6”这种在 360 返回垃圾的写法（已由第 3 条变体兜住）；外国车型样本仍少，未做整轮 12 槽外品牌实跑 |
| T38-isolated-global | 2026-11-10 | **独立测试：含外国品牌的 12 槽全链路**——新 brief（国产 6×6 8 槽 + 国际品牌 6×6 4 槽）；`plan_candidates` 增加“按 research_unit scope 生成查询”，现场 7 Search + 1 Chat 产出 23 候选（11 个外国品牌）；全程 `--web-only`、无 `--models`、无历史数据 | 隔离断言（两个 run 目录开跑前均不存在）+ 新 plan + 新 evidence.db；v1 与 v2 两次运行 | `src/equiplens/retrieval_engine/engine.py`（单元配额硬上限、degraded 只算占槽车、`citation_only`）、`scripts/plan_candidates.py`、`data-test/evals/task-briefs-20261109/brief-m1b-global.json`、`data-test/runs/{plan-m1b-global,loop-m1b-global-20261110,loop-m1b-global-v2}/` | v1 跑出 **20/12**（配额未约束，u-exact 10/8、u-intl 10/4）→ 修复后 v2 **12/12 DONE**（exact 8/8、intl 4/4），**5 台外国品牌占槽**（Zetros、Actros、H6066、T-Way、Kerax）；79 唯一图 / 77 过门卫 / 316 成功抓取；API $0.024；`test_retrieval_engine` **18/18** | 12 台里 **8 台 degraded**（无 confirmed 图）、**1 台 citation_only**（TAZ4922 无核验通过的图，仅引用页）；u-env 0/4 未启用；下载失败 56 行 |
| T39-audit-package | 2026-11-10 | **审核页四档 + “备选图”不再被误读为丢弃**——①徽章改 `已交付·已核验` / `已交付·未核验` / `备选·未占槽` / `未过门卫`，明确分辨率只分档不淘汰；②新增“交付包 / 已核验 / 备选·未占槽”筛选与车型表列；③`summary.delivery.bonus` 统计未占槽车型的可用图（v2：9 车型 / 32 张资产，审核页 34 行） | 复核 v2 77 张过门卫图：43 进交付包、34 在备选；备选里 11 张 ≥800、5 张 ≥1200 | `scripts/render_fetch_audit.py`、`src/equiplens/retrieval_engine/{engine,cli}.py`、`data-test/runs/loop-m1b-global-v2/{audit.html,REPORT.md,summary.json}` | 备选 34 张里 Arocs 6、Steyr 6、豪沃TX 5、KAMAZ 65225 5、T105 4、Phoenix 3、五岳 2、TITAN 2、Scania 1；**没有一张是因为分辨率被删**（低清只记 warning） | 备选图默认不进交付包（只保留在 run/images 与审核页），是否作为“加分项”随包交付需产品定；`citation_only` 仍未收紧 |
| T40-planner-provenance | 2026-11-11 | **planner v2：逐查询抽取 + 候选出处 + 覆盖报告**——抽出 `equiplens/planning.py`（查询计划/校验/归并/coverage）；每条查询单独 Search + 单独 LLM 抽取（temperature 0，每条≤6）；候选必须带 `source_query_id` 且 URL 属于该查询；同车型合并保留 `source_queries` | C01 brief A/B 各 2 次：A 6 查询 / B 加 `进口 沙漠牵引车 6×6 车型` | `src/equiplens/planning.py`、`scripts/plan_candidates.py`、`tests/test_planning.py`、`data-test/runs/plan-ab2-20261111/` | 候选出处 **0/24 → 100%**；A 26–30%、B 30–35% 外国候选（v1 是 25% vs 38–46%）；同组重复重合 26–31%（v1 12–17%）；coverage 无缺口；`planning` 6/6 | 可复现性仍未解决（重复运行名单明显变化）；候选级占比被“奔驰(…)”变体重复放大，下一步做品牌/车系级去重 + n≥3 指标 |
| T41-model-dedupe | 2026-11-11 | **车型级去重 + 废弃 discover fallback**——`model_identity` 型号码/车系+数字/车系/generic 四级；同款变体合并、同品牌不同型号码不并；`dedupe` 统计；`discover.py` 不再被调用，CLI 拦截无 plan 的 `--web-only` | A/B n=3（per-query 8）+ 旧 plan 离线回放 + A2 plan 完整 12 槽 | `src/equiplens/planning.py`、`src/equiplens/retrieval_engine/{web,cli}.py`、`scripts/plan_candidates.py`、`tests/test_planning.py`、`tests/test_retrieval_engine.py`、`data-test/runs/{plan-ab4-20261111,loop-ab4-a2-20261111}/` | 去重移除 8–11 条/次（25–35%）；A 池 17/26/22、B 25/20/18，**均 ≥12 无缺口**；完整 run **12/12**，12 个占槽车型 identity 全不同（无同款重复占槽），82 唯一图、7 degraded、1 citation_only、bonus 29；`planning` 8/8、`retrieval_engine` 20/20 | 进口查询不再显示增量（B 16–20% vs A 18–24%），不默认；generic 占候选 35–56%，是 degraded 的主要来源 |
| T42-file-ledger | 2026-11-11 | **文件治理 / run 台账自动化**——`scripts/run_ledger.py` 扫描 49 个目录，补 41 个 `RUN.json`，生成 `INDEX.json/INDEX.md`；每个 run 带阶段/日期/状态/指标/结论/证据链接；空目录与旧嵌套只标记；清理空 `recompute`；新增 `data-test/runs/README.md` | 全量扫描 + `--check` + 4 条离线测试 | `scripts/run_ledger.py`、`tests/test_run_ledger.py`、`data-test/runs/{README.md,INDEX.json,INDEX.md,*/RUN.json}` | 49 条记录：run/plan/plan-set/diag 分类；待补结论从 50 降到 1；`run_ledger` 4/4；旧 INDEX（10-30 只覆盖文本 run）被替换 | test-log 仍有重复行、缺 stage 列；images 不入 git；历史 run 的结论是“标题/状态”不是人工结论，需逐条补 |
| T43-brief-api | 2026-11-11 | **brief 生成 API 化（纠正手工代工）**——`skills/task-brief/SKILL.md`（v2）先做工程分析（品类/基型/构型/工况/设计对象+设计维度）再输出 request/regions/parts/assumptions/negative；词表只做参考、未知部件保留 custom_*；`briefing.py` 代码补 page_budget/units/tiers/budget/strategy_ref 并做 `validate_brief` + JSON Schema；`build_brief.py` 产出 `brief.json` + `brief_meta.json`；手工 brief 标 legacy | C01 输入 → API 生成 5 parts + front_face region + 8/4 单元；再用该 brief 跑 planner | `skills/task-brief/SKILL.md`、`src/equiplens/briefing.py`、`scripts/build_brief.py`、`tests/test_briefing.py`、`data-test/briefs/brief-c01-auto.json(.meta.json)`、`data-test/runs/plan-c01-auto/` | API brief 通过 schema；含 `front_face` 与 5 个部件；v2 加入涉水喉生成 custom 部件；planner 19/22 候选；`briefing` 5/5；手工 brief 不再作为新实验输入 | brief 生成稳定性未测；2/3 配额是代码规则，需产品确认；区域/部件词表仍以 taxonomy 为准 |
| T44-skill-eval | 2026-11-11 | **task-brief skill 必要性 A/B**——`evals/evals.json` 3 个 case（已知/词表外/口语类目），`with_skill` vs `without_skill`；自动检查 + 人工 rubric；`task-brief` 加 YAML frontmatter、references/example、evals | 3 case × 2 arm，6 次 API 调用 | `skills/task-brief/{SKILL.md,references,evals}`、`scripts/eval_task_brief.py`、`data-test/evals/task-brief-eval-20261111/` | known-parts 5 vs 1 部件；口语类目 without 崩溃；unknown 7 vs 4（但 without 全 form_gesture/exact）；自动 schema 全过 | 自动检查不等于质量；n=3 单次，需扩到 10–20 case、每 case 2 次、人工 rubric；泛化要用未见品类 |

## 2. 审核包与决策归档索引

| 测试 | 审核包 HTML | 决策归档（data-test/reviews/） |
|---|---|---|
| T3 | data-test/review-web-truck.html | batch-web-e4cb0142cb-20261015-162935.json / …163124.json |
| T4 | data-test/review-web-truck-r2.html | （口头判定，纪要 #3） |
| T5 | data-test/review-web-truck-r3.html | （口头判定，纪要 #4） |
| T6 | data-test/review-roster.html | （口头判定，纪要 #5） |
| T7 | data-test/review-roster2.html | （待审） |
| T8 | data-test/review-gener.html | （待审） |
| T12 | review-serve 判向复核页（--probe-file data-test/probe-suggest.json）；离线无落账，禁用导出 | data-test/probe-suggest.json（59 建议）；data-test/probe-eval-{uform,chinese-clip,chinese-clip-l}.json（留一验证报告） |
| T17 | data-test/corpus/review-corpus-20261023.html（10 篇审核页）；data-test/corpus/design-passages-20261023.md（A/B/C 段级摘录） | 段落定级直接留档（A=可用/B=相关/C=无关），无需逐篇落账 |
| T18-eval | data-test/evals/review-l3-v1.html（7 篇四级判定审核包） | data-test/evals/l3-relevance-v1.json（判定理由留档）；产品负责人裁决见意见 #20 |
| T18-roster | data-test/evals/review-roster-20261030.html（63 条非剔除段 + C 档附录） | data-test/evals/roster-verdicts-20261030.json（265 段逐段判定） |

> 注：data-test/*.html 内嵌缩略图自包含可直接打开；决策归档 JSON 已随 git 同步。

## 3. 产品负责人意见纪要（修改日志式）

| # | 日期 | 轮次 | 意见（原话摘要） | 落实去向 |
|---|---|---|---|---|
| 1 | 2026-10-14 | T2 | 夹具图是噪声看不出来；想尽快真实爬取；真实场景是卡车前脸/吊车侧护板/轮拱；要全身照+相关文本为主，部件无文本解析也正常 | 提前 R7 首半段；检索策略定为"车级全身照为主、部件靠裁图" |
| 2 | 2026-10-14 | T3 | 大量无关内容（二维码、无关图）；没有国外品牌；文本爬了么 | URL 黑名单 + 首页不作图源 + 深爬 + 国外品牌 roots；text 仅证据级，参数归 R2 |
| 3 | 2026-10-15 | T4 | 还是大量无关；质疑筛选策略；官网图池定位卡车图有困难；问开源方案；真实流程是"先文章整理名录→百度图片搜图→关联图补信息" | 调研 CLIP 门卫范式（报告 §11）；实现百度/Bing 搜索渠道；名录先行流程 |
| 4 | 2026-10-15 | T5 | 客车混入；多车排列主体遮挡无法使用；慢，用户受得了么；小问题不该在这一步解决 | 门卫 v2（客车/多车反例标签）；文字证据闭环驳回/救回；速度修复（URL 预查重+页面缓存）；二级问题留 M4/排版前处理 |
| 5 | 2026-10-15 | T6 | **挺准，几乎没有对不上的型号**；但车型给的少、同车型角度图少；问该现在还是晚点解决；何时测沙漠牵引车/吊车/矿卡（泛化能力） | 见本台账 §4 评估结论 |
| 6 | 2026-10-15 | T7/T8 | **泛化能力不错，找的车型大致都是对的**，个别错的用户直接踢出；视角标签是英文看不懂，要求审核包中文呈现 | 审核包呈现层全量中文化（视角/材质/质量标记，落账仍用英文枚举）；错型号处理=审核驳出（现机制即可） |
| 7 | 2026-10-15 | T7 | 视角待审核（进行中） | T7 审核包已中文化重出，待审 |
| 9 | 2026-10-15 | T7 | 视角再评估：CLIP 判向仍大量错误，与人工标注不一致；要求找开源视角判定技术 | 调研结论：开源无即插即用（学术位姿重、轻量项目小）；路线=提示词集成→Chinese-CLIP 大底座→**人工标注训线性探针（标注即训练数据）**→VLM 疑难定向；URL 见台账 §2 补充索引 |
| 11 | 2026-10-16 | T7 标注会话 | **3/4 视角怎么能方向待定？左右人眼一眼就看出来** | 规范 v0.2.4：待定态=机器过渡态、**终态必须定向**；判向探针 v1 开训（87 条人工标注）：留一准确率 **36%**（零样本对照 1%，信号真实但特征弱）；已自动定向 36 张待定图（账本可撤销）；路线确认=Chinese-CLIP 大底座换特征+标注积累至 150+ 再训 |
| 12 | 2026-10-17 | T12 复核 + 流程复盘 | ①复核页仍见"3/4 方向待定"字样（实为历史展示行与下拉残留选项, 库内已清零）；②问小模型凭什么判方位、少量标注遇到没见过的车型（吊车等）泛化会不会碰瓶颈；③**提出整体交互流程**（输入车型+页面组成+量级 → EL 内部检索名录/图片文本只报进度 → **车辆级选车确认（主图+缩略图, 人选车快于 AI）** → 不行给备选/二轮检索, 行则进分析模块）；④判向成本大就该重想交互 | ①复核页原值行改历史口径 + **人工下拉移除过渡态选项**（HUMAN_VIEWS）；②机制解释+天花板数据（§5.1）回答：CLIP 靠全局外观统计无几何推理, 泛化瓶颈真实存在→判向降位为嵌入式元数据、VLM 路线兜底；③流程与 R0–R7/D12–D14 设计吻合, **"车辆级选车确认包"为缺失的新检查点, 列为 B 之后/伴随 B 的下一建造项**；④probe-suggest 默认不落账（--apply 显式） |
| 13 | 2026-10-17 | T12 后研讨 | **视角的必要粒度应由分析任务推导**：分析主图按用户输入的部件范围来（整车/局部/前脸…）, 多数场景不必分左右（少数如单边梯子矿卡才要）, 确认到"前45°或侧面"即可; 爬取后展示给用户的主图是简单判断 | 粗类实验（tmp 脚本, 结论入档）：合并左右留一 79.1%（多数类基线 80.9%, 分类口径仅"可用"）; **按车选主图排序: top-3 命中 26/26=100%, top-1 69.2%**——排序口径下判向直接可用; 规范 **v0.2.5**（粗类即合法终态, 左右细分按需/候选并陈）; 选主图拆解为五步（见 HANDOFF 下一建造项）, 判向=第 2/4 步的筛选与排序器 |
| 14 | 2026-10-17 | 扩大测试规划 | **测试要模拟真实情况**：应由产品负责人提供类目 → EL 检索生成车型名录 → EL 检索图片, 而不是让负责人从既有库勾选车型; **每次测试独立, 不受已有审核包影响**（此前说过, 本次立为规则） | 立台账规则⑧; 承认此前名录均为脚本手工拼（R2 未真正建过）——名录冷启动=**R2 首半（检索生成名录）正式立项**, 产品负责人仅提供类目一个词; 指标按批次独立结算; 旧待审包（T7/T8）冻结 |
| 15 | 2026-10-17 | T13 审核 | **J6G 组（8 素材）里明显有两台构型不同的车辆**; 同型号不同色允许; 整体准确度与质量可接受; 视角标注除外（搁置） | 图题证据拆解：长头越野卡车×2（第二构型）+ JH6/J6L/J6P 兄弟型号×3 混入, 真 J6G×3——T3 弱关联设计预期, 人工终审发现错配; 5 张待改绑/驳回（可撤销）; **改进项：入库时图题型号×查询词型号一致性检查, 错配打标前置提示**（选车确认包用）; 同型异构处理机制=选车确认包缩略图条 + D10 变体组 |
| 16 | 2026-10-18 | T14 审核 | **三一 STC800C6、徐工 XCT8L4/QY16KC/QY25K5C 组内明显有不同构型车辆**; 问成因 + 当前有哪些小模型判断步骤 | 成因分析（见 T14 结算）：①T3 搜索词声称+引擎对近似型号天然混淆 ②型号名本身覆盖多构型（连续改款/臂长配置）③门卫只判"是不是单台工程车"不判"是不是这台车"——型号级机器判定本就空缺（闭集对号留人工）④图题一致性检查未上线。**类型簇实验（UForm 零样本, 当场实测）**：四组均分裂为 吊车/纯卡车/(挖机) 多簇, 与人眼观察吻合——嵌入含类型信息但裕量仅 0.005–0.03、视角依赖强（吊车尾部像卡车）、否定提示词不可靠→**判不成硬规则, 定位=打标不拦截**（类型簇+图题一致性打标 → 选车确认包并排人审 → VLM 比对归 M4） |
| 17 | 2026-10-18 | T15 审核 | **本批次型号和图像对得上; 但"翻斗铲车"与"自卸车"在语义理解上有偏差**（记录, 后续再测） | T15 审核结账（对位准确, 无构型混杂——较 T13/T14 改善）；语义偏差记入待测：类目词→同义词扩展链路的意图对齐问题（"铲车"口语可指装载机, 名录落在了自卸车）——后续以"用户类目词→EL 语义解释确认"交互或更准的同义词词典校准 |
| 10 | 2026-10-15 | — | **审核包要实时存储，不要老是导出文件；注意临时文件管理，不与重要文件交叉存储** | 实现 review-serve 实时落账服务（点击即存账本）；确立目录分区规则（tmp//data-test//data/）见规则 ⑥⑦ |
| 18 | 2026-10-23 | T17 语料审核 | **审核包里大量无关内容；我们要的是设计分析文本**（如京剧脸谱式设计、江铃重卡设计描述）；把筛出的文本发到对话并算占比判断价值；问部件类型学是否已建、是否还要几轮测试；**测试内容要记录到文件里，对面试有帮助** | 段落级 A/B/C 定级 → 可用仅 **6.3%**（见 data-test/corpus/design-passages-20261023.md）；文本检索策略 v0.1 立项（docs/text-retrieval-design.md，补上了 R2 后半缺失的策略）；T17 全量入台账 §1/§2 |
| 19 | 2026-10-23 | T17 后续规划 | **先优化检索策略，准备再检索几轮；类型学是下游处理（先有语料再有分类），不是现在做** | 检索策略 v0.1 §7/§8 改为“只验证检索、不建类型学”；HANDOFF 下一步与 test-log §6.3 同步修正；类型学归分析整合模块，待检索稳定、下游启动时再做 |
| 20 | 2026-10-30 | L3 评测集 v1 审核 | 7 篇逐条裁决：01 整体描述可用（没写具体部件但语料本身符合，部件描述要参考整车描述，有效语料少要充分挖掘）；10 词汇可用但不指向车型/部位，判断准确但**考虑收录作参考——可能代表企业设计理解，分析中帮助定调**；14 构型描述很好（偏工程也行，外观分析要依工程构型决定）；15 同意 A_gen，内饰部分仅收录备用；17 同意 C（车轱辘话无有效语料）；18 **缺具体型号指向，没什么用（改判降级）**；12 未点名 | 提炼指向性标准=**对象锚定**（落到具体产品，非型号字符串匹配）；三分类口径定为 V（指向车型整体）/P（部件构型及造型，含工程构型）/G（非指向风格或部件，宏观定调参考）；L3 评测集与闸门目标同步改写 |
| 21 | 2026-10-30 | 战略讨论 + 测试指令 | **判断：网上爬到具体型号的指向性设计描述非常困难，有效语料少、通用废话多；最终要以 VLM 看图分析为主，语料爬取/历史资料/skill 都是辅助 VLM 结构化、标准化输出**。问：这部分是否以 skill 为主？现在是规则筛选阶段还是模型自主调用算法？→ 指令：用全部清单车型做大规模文本爬取-筛选测试，自己决定路由规则还是模型（模型由你扮演），结果自审后报，并写占比报告 | 分析结论：同意 VLM 为主；文本换岗为"语汇/定调/事实"三辅；skill=交付形态（schema+判据+档案+词表的内核），实战后固化；规则=两端护栏（粗筛+验收尺），判断=中间模型层，agentic 闭环 T18-blind 已验证。测试见 T18-roster（本行同批） |
| 22 | 2026-10-30 | 方向决策 | **①确定性闸门现在做（选 A）②VLM 分析线后置：当前检索模块做完并整体测试后再议 ③信源定向暂时选 B：放弃 query 级 site 定向，保留域名信任加权** | 闸门 v1 完成（`l3gate.py`：假阳性 40.4%→6.9%，召回 85.7%）；VLM 主线待整体测试后启动；`source_targeting` 开关默认关闭 |
| 23 | 2026-10-30 | 待决事项（P1–P3） | **①文本爬取启动时机：清单确认后即后台启动 vs 图片确认后 ②关联分析层级：L1–L3 默认纳入、L4 逐条确认 vs 全部逐条 ③关联 skill 形态：先文档+人工扮演 vs 等 VLM/API 就绪一起做** | 记录于 HANDOFF §3.1；我的建议默认：清单确认后启动 / L1–L3 默认 / 先文档+人工扮演；决定后写入 HANDOFF §3.1 并落地 |
| 20 | 2026-10-23 | 编排研讨 | **担心写死规则越多、长尾类目表现越差；问“放宽”是 LLM 自主还是写死；skill 覆盖不了全部工程车类型怎么办** | 定三层自由度：锁死不变量 / 内容知识数据化（来源注册表+类目档案+词表）/ 判断模型化（意图/查询/选源/段落/停止）；长尾类目不枚举，走“通用层 + 类目档案（LLM 提议、人确认）”；列出 `roster.py` 硬编码清单（40 品牌/15 车辆词/3 组同义词/URL 规则）为技术债；下一建造项=`category_profile` + `source registry` |
| 21 | 2026-10-23 | T18-budget-curve 后 | **预算曲线结论确认；决定下一步进 L3（段落级类目相关性），而不是继续加预算** | 探测预算定 **q3（≈6 篇/轮）**；生产预算从 q6 起但不做线性加篇，边际产出由“碰到高产出源”决定（离线曲线第 6 篇 1,121 字 / 第 10 篇 1,926 字，中间多篇 0）；在线 4 档被百度验证页拦，已留台账待补；**L3 为当前唯一优先项**：随车吊 1.8% vs 高空作业车 6.6% 的差异源于类目相关性，不是预算 |
| 22 | 2026-10-23 | L3 研讨 | **确定性闸门遇到“类目无直接关联但内容有用”怎么办？LLM 判定先由对话模型扮演** | **不用二值硬杀，改四级判定**：A_cat（类目相关）/A_comp（共享部件）/A_gen（通用可迁移）/C（丢弃）；三个计数器分开，指标诚实不丢可迁移内容；类目零专属时如实报 0 + 逃生口报“类目专属供给不足”；LLM judge 判定标准=四段式有没有具体证据（部件名/形态/CMF），不是关键词计数；**评测集 v1 已建**：7 篇标注，假阳性率 43% |
| 8 | 2026-10-15 | T7 | **视角识别非常差、左右不分；标注约定：以车头为前、驾驶员视角分左右** | 根因=查询词声称冒充视觉判定（与杂图同类问题）；修复：①规范 v0.2.3 写入驾驶员视角约定 ②枚举增 hero_45/side 方向未定态（机器不瞎猜，人工/VLM 定向升级）③CLIP 视觉判向对 213 张检索素材重打标（front75/side73/hero_45×33/untagged29/rear18/detail13/interior1）④禁止查询词充当视角判定 |

## 3.1 开源调研 URL 补充索引（意见 #9）

| 项目 | 地址 | 用途 |
|---|---|---|
| Chinese-CLIP | https://github.com/OFA-Sys/Chinese-CLIP | 大底座换装候选（中文跨模态, ViT-L 档） |
| EgoNet / GSNet | https://github.com/Nicholasli1995/EgoNet ｜ https://github.com/lkeab/gsnet | 学术位姿估计（重依赖, 不采用, 存档参考） |
| mizhi | https://github.com/ai-and-lab/mizhi | 轻量车辆判向（小众, 参考） |

## 4. 评估结论（意见 #5 的处置）

| 问题 | 结论 | 依据 |
|---|---|---|
| 同车型角度少 | **现在解决**（小改动）：查询模板按视角扩展（正侧/正前/尾部/内饰），配额上调；这是完备度模型（L1–L3 按视角定义）的直接输入，属核心能力不是质量打磨 | 视角缺口=缺口驱动爬取的主要缺口类型 |
| 车型数量少 | **现在解决**（轻量）：名录扩到每类目 15–20 候选，由产品负责人裁剪锁定——真实项目竞品集按类目/价位/客户选 10–15 个，扩列是 AI 的活、裁剪是人的活 | 与意见 #5 流程一致 |
| 泛化（沙漠牵引车/吊车/矿卡） | **下一轮即测**（角度/数量修正后紧接）：管线本身类目无关（词表/查询模板/门卫标签皆可配置），但只在牵引车上跑过——"类目无关"是架构承诺，需要实证；小批量（每类目 3 型号）即可暴露词表类目偏差（吊臂/支腿/货厢等，走 D11 提名池补）与门卫标签偏差 | 架构主张需早期验证，别在单类目上盖太多楼 |
| 大规模批量（500+） | **晚点**：等缺口驱动和泛化都验证后再上量——现在的量是"够测试"不是"够产品" | 避免漫灌 |

## 5. 判向探针协议对比（T12 存档, 重训时直接对表）

留一验证（82 条人工方向标注, 4 类: hero_lf46/hero_rf21/side_l8/front7, 2026-10-17）：

| 协议 | 准确率 | 结论 |
|---|---|---|
| UForm3-small 质心（v1 同款） | 35.4% | 基线复现（v1 报 36%）|
| **Chinese-CLIP B/16 质心** | **61.0%** | **定版协议（含 side 修正）** |
| B/16 镜像增广 + 对称判定 | 59.8% | 与 61.0% 同噪声级；side 类显著更好（6/8 vs 4/8）、**side_r 无中生有**，作生产判定 |
| Chinese-CLIP L/14 | 54.9% / 52.4% | 更大≠更好——瓶颈是对比特征对"左右"编码弱, 非容量 |
| kNN-1/3/5 | 52.4% / 40.2% | 劣于质心 |
| 中文文本锚点混合 | 23–40% | 反而伤害, 弃用 |
| 岭回归（含 L/14 拼接） | 63.4%（假象） | 靠吃类不平衡（hero_lf 46/46 而 hero_rf 1/21）, 弃用 |

错误结构：hero_lf↔hero_rf 互混占 17/32, 全部错例裕量 <0.05——左右是对比特征的系统性弱信号。
镜像增广原理：水平翻转的左前 45° 图物理上就是右前 45° 图 → 训练数据翻倍、hero_rf 21→67 条、side_r 由 side_l 翻转无中生有。
重训决策参考：标注 ~150 条时重跑 `probe-eval`（三后端同口径对比）；若 B/16 仍 <70% 且标注充足, 启动 M4 VLM 疑难定向评估。

### §5.1 T12 实盘结算与天花板确认（2026-10-17 复核后补记）

- **实盘准确率 54.2%（32/59, 人审为准）**——低于留一验证 59.8%（生产集含更多 side/难题图, LOO 略乐观）；
- **镜像法 side_r 实证不可靠**：10 张 side_r 建议 9 张被人工推翻（多实为左前 45°）——镜检一致性 5/8 的弱信号不足以支撑断言, "无中生有"在判定侧不成立（增广训练仍可保留, 断言不行）；
- **115 条重训留一降至 51.8%**：纠错式新增样本恰好集中在模型系统性困惑的图上（front↔hero、side↔hero 互混）, 继续堆同类标注边际收益为负；
- **结论（路线 A 收口）**：CLIP 系探针天花板 50–60%, 判向定位从"机器判+人改的独立关卡"调整为"**嵌入式元数据**"——视角标注在人本来就要看图的环节（选车/素材审核）顺手修正, 飞轮零额外成本积累; 疑难定向（如主图级精度需求）归 M4 VLM。probe-suggest 默认只出报告不落账（--apply 显式开启）; 人工下拉移除过渡态选项（规范 v0.2.4 落地）。

## 6. 文本语料评估：设计分析占比（T17 存档）

### §6.1 口径

- **A 类（可用设计分析）**：描述可见形态/CMF/姿态比例，或带设计意图；能直接支撑 FR-2.3 的部件描述或统一 schema 的“设计信息/设计意图”维度。
- **B 类（相关但偏工程/市场/内饰）**：风阻论证、开发成本、市场观察、内饰配置、人机工程——可作背景，不进入类型学正例。
- **C 类（无关）**：参数表、配置清单、油耗试驾、导购、经销商信息、图片轮播。
- 分母口径：清洗站点导航后的正文行（≥20 字）；另列“叙述性正文”口径（剔除两张参数表与一篇选车导购）。

### §6.2 数字

| 指标 | 值 |
|---|---|
| 去重文章 / 总字数 | 10 篇 / 42,743 字 |
| A 类字数 | **2,698 字（6.3%）** |
| A+B 字数 | 4,838 字（11.3%） |
| 叙述性正文中的 A 占比 | 2,698 / 21,544 = **12.5%** |
| 有 A 段文章 | 4/10 |
| A ≥500 字文章 | 3/10（08、09、10） |
| A ≥1000 字文章 | 1/10（09 浅谈中国重卡造型设计） |
| 部件覆盖 | 7/12 提及，4/12 有形态描述，5/12 零证据 |
| 类目覆盖 | 1（重卡）；吊车/装载机/矿卡 0 |

逐篇分布：官网 0/1,263、0/710；参数页 0/12,396、0/8,093；评测 67/3,019（2.2%）、0/2,915、0/5,607；行业 649/2,894（22.4%）、1,274/5,082（25.1%）、708/764（92.7%）。

### §6.3 结论

1. **查询模板是根因**：“车型名 + 试驾/评测/外观”返回的是性能、配置、内饰；设计分析只偶发出现。要拿设计文本，查询必须带设计语汇（造型/前脸/格栅/线条/家族化/CMF/演变），并扩到设计媒体、CMF 报告、设计师访谈、车展解读。
2. **筛选必须段落级**：09 篇整篇仅 25.1% 可用，05 篇仅 2.2%——篇级收/拒会双向出错。
3. **类型学不在检索阶段**：5 类部件零证据、类目只有重卡，说明“证据供给”还不足；但类型学是**下游分析整合模块**的分类方案，本轮不建。T18–T20 只验证检索策略（设计段占比、高价值命中率、信源多样性、跨类目可迁移）。
4. **可复现**：`python tmp/extract_design_passages.py` 出候选与占比；`python tmp/build_design_passages.py` 生成 `data-test/corpus/design-passages-20261023.md`。两脚本为一次性分析工具，正式版应固化为段落级分类器/评估脚本。

### §6.4 LLM 查询规划预实验（T18-pre, 2026-10-23）

**变量**：只换查询词，不换爬虫、不换配额、不加信源。基线=T17 的“车型 + 评测/外观”；实验组=设计语汇（前脸/格栅/大灯/设计语言/家族化/CMF/造型演变）。planner 由对话模型人工充当，未接 API。

| 指标 | T17 基线 | T18-pre 实验组 |
|---|---|---|
| 文章数 | 10 | 8 |
| 有 A 段文章 | 4（40%） | **8（100%）** |
| A 类字数（保守） | 2,698 | 2,891 |
| 单篇 A 字数 | 270 | 361 |
| A / 清洗后正文 | 6.3% | 2.7% |
| official 命中 | 2/2 | **0/2**（`site:`+设计词过窄） |

**结论**：
1. LLM 查询规划首先改善的是**文章级召回**——从“10 篇里 4 篇有料”变成“8 篇全有料”，这是质的差别；
2. 但**段落级产出**没有同比提升：页面清洗不足（网易页 80+ 推荐位把正文稀释到 4 万字）与 AI 生成 SEO 稿混入，让“篇篇有料”没有变成“高密度语料”；
3. 因此下一步的杠杆不在继续堆查询词，而在 **L3 段落级质检/清洗 + 来源质量评分**；
4. official 渠道不适合设计文本：厂商官网以产品参数/新闻为主，设计解读更多在行业媒体与设计媒体；
5. 正式化 L1 需要 LLM API 网关（文本模型即可，成本低于 VLM）；在网关就绪前，可继续用“对话模型出查询、脚本执行”的半自动方式做策略实验。

### §6.5 多车型放宽预实验（T18-broad, 2026-10-23）

**目的**：只改查询词不够，要看“用户输入 → 意图 → 查询 → 检索”在**不同车型/类目**上是否成立。

| 输入/类目 | 命中的东西 | 问题 |
|---|---|---|
| 沙漠牵引车（豪沃 6X6 油田） | 卡车之家图解：白色涂装适配高温、遮阳板不足、后视镜偏小、大灯铁丝防护网、粗保险杠 | 可用；说明**环境约束会直接改变设计判断** |
| 自卸车（虎 6G） | 卡车之家图解：V 字前脸、金元宝造型寓意、线条/灯组/内饰配色 | 可用；说明**工程车也有设计叙事** |
| 起重机（造型/设计语言/家族化） | 百度爱采购商品页（17 万、1.6 万字，0 设计段） | **来源污染**：B2B 采购页劫持设计查询 |
| 装载机（造型设计） | 豆丁网《立足于美学和人机工程学的装载机造型设计》 | 只有摘要预览，正文不可用；说明学术/设计源存在但需 PDF/全文渠道 |
| “翻斗车” | 商品页/短页 | **歧义**：翻斗车=自卸车；换“装载机”才命中设计文 |
| 失败 12 条 | 沙漠孤鹰 H6066、豪沃 V7-X 自卸、Paul80 沙漠卡车、解放长头越野等 | **URL 规则误拦好文章**；需按“来源+标题+正文质量”复核，而非只看 URL |

**结论**：
1. **L1 不是单纯的“查询改写”**——必须先有意图澄清（翻斗铲车→自卸车/装载机？）和信源路由（起重机去行业媒体而不是爱采购）。
2. **L3 必须加来源可信度/域名白名单**：爱采购、豆丁预览、百科、商品页降权或排除；卡车之家图解、行业媒体、学术全文升权。
3. **URL 黑名单要分级**：当前规则误杀率不低，应改为“先放行抓取、再按正文质量判定”，或对可疑 URL 走人工复核队列。
4. **跨类目的设计文本供给不均衡**：重卡/自卸/沙漠牵引车有料，起重机/装载机明显更依赖学术与设计媒体。
5. 下一轮正式 T18 应按“输入类型 × 类目 × 车型”矩阵跑，而不是按查询词跑；每个 case 记录意图、计划、命中、失败原因。

### §6.6 编排器首跑与长尾盲测（T18-blind, 2026-10-23）

本轮把“自由出口 + 运行轨迹”从设计变成可执行代码：

- `src/equiplens/runlog.py`：每次运行写 `runs/<run_id>/events.jsonl` + `summary.json`，记录阶段耗时、工具调用、LLM 调用（无 API 时 token 为估算）、决策与约束；
- `src/equiplens/strategy.py`：低信度判定与重规划 scope（允许换查询/换源/走通用层/提议档案；禁止越过 robots/配额/账本/检查点）；
- `src/equiplens/passage.py`：页面清洗、段落切分、A/B/C 初筛、来源可信度降权；
- `src/equiplens/textrun.py` + CLI `text-run`：intent → 档案 → 计划 → 执行 → 评估 → 重规划 → 报告；
- `data/source_registry.json`、`data/category_profiles.json`、`schemas/intent.schema.json`、`schemas/text-plan.schema.json`。

**运行轨迹样例（run-suicheche-blind-v2）**：总时长 36.2 秒；阶段
`validate_intent 1.3ms → plan_r1 1.4ms → execute_r1 15.7s → grade_r1 12.7ms → plan_r2 2.1ms → execute_r2 29.3s → grade_r2 32.8ms`；
token 估算输入 66 / 输出 11（人工 planner，`est=true`）；工具事件 `corpus.collect_corpus` 带 batch/quota/耗时。

| 运行 | 档案状态 | 文章 | A 字 | A 占比 | 失败 | 决策 |
|---|---|---|---|---|---|---|
| blind-v2（随车吊，真盲测） | missing | 3 | 198 | 1.8% | 35（blocked 22 / robots 7） | replan → stop |
| profile（随车吊草案档案） | draft | 6 + 4 | 0 + 562 | 0 → 2.9% | 4 + 37 | replan → stop |
| gaokong-v3（高空作业车，修正后） | missing | 5 + 4 | 947 + 1,723 | **2.9% → 6.6%** | 硬 9 / 政策跳过 29 | **replan → ok** |

**关键发现**：
1. **档案也会错**：草案档案把查询拉向“随车吊 价格/厂家”页（简书价格问答、湖北正胜/鑫力销售页），第 1 轮 A=0。说明 profile 不是免死金牌，必须用指标验收。
2. **通用层噪声大**：第 2 轮混入豆瓣书、军工/越野文；只靠“设计/造型”词无法保证类目相关。
3. **执行层补位是硬 bug**：候选被 blocked_url/robots 拦掉后不会补位，修复后单轮文章 1→6 篇。
4. **逃生口按预期工作**：低信度 → 重规划（换通用层/换源/提议档案）→ 仍低 → 停止并上报缺口，没有无限重试或越过预算。
5. **轨迹可复盘**：每次运行都有 events/summary/plan/grade，能回答“花了多久、调了什么、为什么停”。
6. **政策跳过 ≠ 抓取失败**：blocked_url/source_skipped 是主动策略，不应计入失败率；修正后高空作业车第 2 轮 A 6.6% 被正确判为 `ok`，此前因 75% “失败率”误停。
7. **重规划必须换查询**：首版宽搜轮把新查询排在旧查询后面，配额被旧查询占满，第二轮与第一轮结果完全相同；改为“宽搜轮只跑不重叠查询（工业设计/CMF/学术）”后，第二轮才真正产生不同证据。

### §6.7 预算依据与丰度（T18-budget, 2026-10-23）

**当前默认值不是“最优值”，是“探测预算”**：`max_queries=10`、`max_fetch=10`、`max_rounds=2`、每类型约 3 篇。依据：

- **时间**：单查询 SERP 约 2–3 秒，单页抓取约 0.5–3 秒；6 查询 + 6–10 篇 ≈ 30–60 秒，适合一轮人审节奏。
- **信号强度**：3 篇/类型足以判断“文章级命中率”和“A 段密度”的量级；少于 3 篇方差太大，多于 5 篇在首轮边际收益低。
- **合规与成本**：限制对百度的请求频率与抓取量；文本 LLM 尚未接入，当前成本主要是时间。

**发现两个隐藏帽**（已修）：
1. `per = min(3, max_fetch / 类型数)` —— 无论 `max_fetch` 调到 20，每类型仍是 3；高预算不生效。
2. `quota = min(per, len(queries))` —— 配额被查询条数限制，3 条查询最多 3 篇/类型，单查询多结果的丰度被浪费。

修复后：`max_fetch` 是真正上限，`per_type_quota` 可显式覆盖；离线计划测试 `max_fetch=12 → 12`、`per_type_quota=2 → 4` 通过。修复前的 20 预算运行仍只出 3+3；修复后的网络复跑遇到百度 SERP 空/验证页，0 篇——这不是预算结论，而是基础设施故障，已加 `serp_looks_blocked` 诊断，后续复跑需间隔或换 Bing。

**探测 vs 生产**：
- 探测预算（当前）：6–10 篇/轮，目标是“策略是否有效”，不是“语料是否够用”。
- 生产预算（待定）：按目标产出反推。若每台车需要 12 部件 × 1–2 段，3 台车 ≈ 36–72 段；按当前单篇 A 段 1–3 条，需 20–40 篇；建议 `max_fetch=30–60`、`per_type_quota=6–10`、`max_rounds=2–3`，并以“每多抓 1 篇新增多少 A 字”的曲线定值。

**下一步校准**：同一 intent 跑 `per_type_quota = 1 / 3 / 6 / 10` 四档，记录边际 A 字/篇、时间、硬失败率，找拐点；再按类目难度（有档案/无档案、来源丰度）设自适应预算。

### §6.8 预算-产出曲线（T18-budget-curve, 2026-10-23）

**在线尝试**：`per_type_quota=1/3/6/10` 四轮（高空作业车）全部被百度验证页拦住：SERP 6/6 blocked、0 篇、2–2.3 秒。Bing RSS 返回无关结果（“高空”被拆词），Bing HTML 无有效结果锚点——两个 Bing 兜底实测不可用。**在线曲线未完成，失败运行已入台账，不作为预算结论。**

**离线近似**（`data-test/runs/BUDGET-CURVE-20261023.md`）：用高空作业车已有成功批次按抓取顺序逐篇累加，去重后 11 篇：

| 档位 | N 篇 | 累计 A | A 占比 | A/篇 |
|---|---:|---:|---:|---:|
| q1 近似 | 2 | 252 | 3.7% | 126 |
| q3 近似 | 6 | 2,068 | 5.2% | 345 |
| q6 近似 | 12 | 样本不足 | - | - |
| q10 近似 | 20 | 样本不足 | - | - |

逐篇边际极不均匀：第 6 篇新增 1,121 字、第 10 篇新增 1,926 字，中间多篇为 0。说明**预算的边际产出主要由“是否碰到高产出源/文章”决定，不是篇数本身**；单纯加预算不加来源质量，收益不稳定。

**初步建议**：
1. 探测预算保持 **q3（≈6 篇/轮）**：足够判断策略信号，成本低。
2. 生产预算从 **q6 起**，但必须同时做来源质量与类目相关性；否则多抓的是商品页/无关文。
3. 在线曲线等 SERP 恢复后补；或接 Sogou/其他网页搜索渠道。Bing RSS/HTML 不可用已记录。
4. 预算不应“线性加篇”，应优先增加**高产出源类型**（卡车之家图解、行业原创、学术全文），而不是同一查询多抓。

### §6.9 L3 评测集 v1（T18-eval, 2026-10-23）

**目的**：在改 L3 之前先建可度量的基准——把 4 个盲测里所有 A>0 的文章逐篇用 LLM judge（对话模型）标注四级（A_cat/A_comp/A_gen/C），作为确定性闸门和 LLM 判定层的验收依据。

**标注结果**（7 篇，全部当前被关键词打分发标为 A）：

| id | 文章 | 当前 | LLM 判定 | 理由 |
|---|---|---|---|---|
| 01 | 程力随车吊——超越千万的设计 | A 99 字 | **C** | 空洞营销：无具体部件、无形态细节 |
| 10 | 中联杯设计竞赛全攻略 | A 463 字 | **C** | 错类型：讲竞赛流程，不是车辆分析 |
| 12 | 欧洲CELA 40米高空作业车 | A 252 字 | **A_cat** | 类目相关，结构/安全设计 |
| 14 | 蓝牌CELA 25米高空作业车 | A 232 字 | **A_cat** | 类目相关，双伸缩臂造型、管线内置 |
| 15 | 重卡驾驶室从模仿到自创 | A 1,121 字 | **A_gen** | 通用设计分析，可迁移但不属高空作业车 |
| 17 | 毕设设计…高空作业车建模 | A 602 字 | **C** | 错类型：毕设代做页，非实车分析 |
| 18 | 高空作业设备外观设计 | A 1,926 字 | **A_cat** | 最优：仿生造型、色彩设计、国内外对比 |

**结论**：
- **关键词打分的假阳性率 3/7 = 43%**：3 篇 C 级（空洞营销/竞赛攻略/毕设代做）被标为 A。
- **A_cat 真实产出 2,410 字**，占当前 A 总量 4,695 字的 51%；其余 49% 是 A_gen（可迁移）+ C（应丢弃）。
- 高空作业车 v3 的 6.6% A 占比中，**类目相关的只有约 4.1%**——这就是 L3 要修的。

**文件**：`data-test/evals/l3-relevance-v1.json`（含逐篇 tier/subject/anchors/reason，可复核可重跑）。

**下一步**：①确定性闸门用此评测集校准；②LLM 判定层接 API 后用同一评测集复跑，对比准确率变化。

**下一步**：L3 增加“类目相关性”维度（防止设计词对但类目跑偏）；来源注册表补设计媒体/学术全文；对 blocked_url 的好文做人工复核；高空作业车作为第二个留出类目。
