# 生产级评估与监控方案调研（工程车图片检索）

**日期** 2026-11-14 ｜ **范围** 仅网络检索 ｜ **核实方式**：下列链接均于当日实测 HTTP 200；`api.github.com`、`raw.githubusercontent.com` 在本环境被阻断，故以 GitHub 仓库页与 PyPI 页为准，打不开的标"未验证"。

**我们的缺口**：两段式管道（查询→抽车型→按车型抓图+规则核验）已有冻结计划快照、per-case 指标、2000 次配对 bootstrap；缺的是 ①冻结集治理 ②三层指标统一口径 ③持续监控与合入门槛。下面每条都按"能不能直接抄"来评判。

## 一、8 个方案（按可落地性排序）

### 1. promptfoo ｜ [github](https://github.com/promptfoo/promptfoo) ｜ [CI/CD 文档](https://www.promptfoo.dev/docs/integrations/ci-cd/)
- **解决**：把评估变成可进 CI 的断言集合 + 质量门，一次跑出 JSON / JUnit / HTML 三种产物。
- **最小落地**：`npx promptfoo@latest eval -c promptfoo.yaml -o results.json -o results.junit.xml`，CI 里 `jq '.results.stats.failures'` 判退出码。
- **可借鉴**：结果 JSON 的 `results.stats.{successes,failures}` 字段名、`--fail-on-error`、`--tag ci.run-id=… --tag git.sha=…` 三条溯源标签——我们 `summary.json` 照抄字段名，gate 十行写完。
- **成本 低**（Node ≥22，无服务端）｜**局限**：断言面向文本/LLM-judge，不认"图片规则核验"；栈里多一个 Node 运行时。

### 2. DeepEval ｜ [github](https://github.com/confident-ai/deepeval) ｜ [docs](https://deepeval.com/docs/getting-started)
- **解决**：评估写成 pytest 用例，指标自带 threshold，失败即测试失败，天然接 CI。
- **最小落地**：`pip install -U deepeval`（当前 4.3.4），一个 `test_eval.py` 里 `assert_test(case, [metric])`，`deepeval test run`。
- **可借鉴**："一 case 一测试函数 + 指标自带阈值"的结构——我们让每个冻结 case 成 pytest 参数，`pytest -k extraction` 可单跑一层。
- **成本 低**（pip + pytest）｜**局限**：LLM-judge 指标要 API key 且花钱；非 LLM 指标偏少；云端 Confident AI 是商业服务。

### 3. RAGAS ｜ [github](https://github.com/vibrantlabsai/ragas)（原 explodinggradients 已重定向到此）｜ [docs](https://docs.ragas.io/)
- **解决**：把"检索质量"与"生成质量"拆成两组指标（context precision/recall、faithfulness 等），反对单一总分。
- **最小落地**：`pip install ragas`（0.4.3 / 2026-01-13），用 `ragas.metrics.collections` 的指标对已有 JSON 打分。
- **可借鉴**：指标分层 + 每个分数必须带 reason——我们三层指标各配"失败原因"字段，禁止加权合成一个数。
- **成本 中**（judge 调用费）｜**局限**：0.2→0.4 有破坏性 API 变更，必须锁版本；面向"有 context/answer"的 RAG，与图片检索只部分同构。

### 4. Arize Phoenix ｜ [github](https://github.com/Arize-ai/phoenix) ｜ docs（跳转 arize.com，本环境未打开 → **未验证**）
- **解决**：自托管观测台，trace + dataset + experiment，能对比两版逐条结果。
- **最小落地**：`pip install arize-phoenix && phoenix serve`，用 OTEL 把"抽车型 / 抓图 / 规则核验"报成三段 span。
- **可借鉴**：dataset→experiment→逐条 diff 的组织方式，正好治我们"交付层失败无法回放"。
- **成本 中**（一个常驻服务 + 埋点改造）｜**局限**：许可非 Apache/MIT（Elastic License 2.0，**未逐字核实**，商用前确认）；埋点改造量 > 收益，除非确实要 UI。

### 5. Label Studio ｜ [github](https://github.com/HumanSignal/label-studio) ｜ [labelstud.io](https://labelstud.io/)
- **解决**：图像分类 + 检索相关性标注 + 人工复核，官方已把"AI Evaluation / RAG & Retrieval QA"做成一等模板。
- **最小落地**：`pip install -U label-studio && label-studio`，用 Image Classification 模板建项目，通过 predictions API 预标注。
- **可借鉴**：预标注 + 人工只改错；导出 JSON 的 `annotations[].result` 结构直接当我们的 gold 格式。
- **成本 低**（软件）但人力才是大头｜**局限**：社区版/企业版功能有差；自建要管账号与图片存储。

### 6. Argilla ｜ [github](https://github.com/argilla-io/argilla) ｜ [docs](https://docs.argilla.io/)
- **解决**："record + suggestion + response" 式团队标注，适合把线上 bad case 沉淀成金标。
- **最小落地**：`pip install argilla`，HF Space 模板一键起服务，`dataset.records.log(records=…)` 灌数据。
- **可借鉴**：suggestion（机器判断）与 response（人工结论）分列存储——我们直接量化"规则核验 vs 人工"的差异率。
- **成本 中**（要 server）｜**局限**：2.8.0 发布于 2025-03-10，之后无新版；图像标注不如 Label Studio 成熟。

### 7. ir_measures ｜ [github](https://github.com/terrierteam/ir_measures) ｜ [pypi](https://pypi.org/project/ir-measures/)
- **解决**：统一 qrels/run 接口算 nDCG/AP/RR/P@k，同时给 aggregate 与 per-query 两种口径。
- **最小落地**：`pip install ir-measures`（0.4.3 / 2025-11-25），`calc_aggregate([nDCG@10, R@20], qrels, run)`。
- **可借鉴**：qrels/run 数据形态 + `iter_calc` 的 per-query 输出——我们 per-case 指标按 per-query 语义落表，指标名统一到 nDCG@10 / R@20。
- **成本 低**｜**局限**：前提是有金标 qrels；不含显著性检验（bootstrap 自己写，我们已有）。注：PyPI `pytrec-eval` 最后发布 2020-09-07，维护版在 [terrierteam/pytrec_eval](https://github.com/terrierteam/pytrec_eval)。

### 8. Evidently ｜ [github](https://github.com/evidentlyai/evidently)
- **解决**：参考窗口 vs 当前窗口的统计漂移检测，出 HTML 报告，并以 "tests" 形式给 pass/fail。
- **最小落地**：`pip install evidently`，把两次 eval 的 per-case 表当两份 DataFrame 喂进去出 Report。
- **可借鉴**："dataset summary + 逐列统计检验 + pass/fail" 三段式结构，直接当我们周报模板。
- **成本 低**｜**局限**：面向表格/文本特征，图片质量与规则命中率需自定义列映射；报告要人看，不自动归因。

## 二、哪些"框架重"、哪些"几十行能抄"

| 方案 | 为什么现在不选 |
| --- | --- |
| [Braintrust](https://www.braintrust.dev/docs) | SaaS，席位/用量计费；价值在"全链路 tracing + 在线评分"。我们是规则+抓图管道，LLM 调用不密集，接入成本远大于收益。 |
| [LangSmith](https://docs.langchain.com/) | 同上（文档已迁至 docs.langchain.com）；self-host 版要 K8s 运维。 |
| [TruLens](https://github.com/truera/trulens) | OTEL-native、Snowflake 维护（2.16.0 / 2026-10-19），但主题是 RAG 三元组 + 7 个 agent evaluator，PyPI 标 3-Alpha。只借"可解释反馈函数"理念。 |
| [OpenAI Evals](https://github.com/openai/evals) | 围绕 benchmark registry 与 OpenAI 模型组织，自定义"图片检索"指标要写大量胶水；价值是评测规范而非运行时。 |
| [Doccano](https://github.com/doccano/doccano) | 最后可用版 1.8.4（2023-07-20）；2026-01-11 的 1.8.5 已被 yank，单维护者。新项目别选。 |
| [BEIR](https://github.com/beir-cellar/beir) | 是"跨数据集零样本 benchmark"的方法论与数据，不是评估运行时；只借"留出整个车型族做泛化测试"的思路。 |

**几十行就能抄的 5 处**（不引入依赖也成立）：
1. **promptfoo 的质量门**：读 `results.json` 的 `stats` → 与阈值比 → `exit 1`（约 10 行）。
2. **DeepEval 的 pytest 化**：一 case 一 test 函数 + metric 阈值，断言失败即 CI 红（约 30 行）。
3. **ir_measures 的语义**：qrels/run 两表 + per-query 输出，指标名对齐 `nDCG@10`/`R@20`（约 20 行，不装包）。
4. **分层配对 bootstrap**：现有 2000 次重采样改成按 `layer_tags` 分层，报 Δ 的 95% CI 与 P(Δ>0)（约 40 行）。
5. **Evidently 的漂移报告三段式**：reference/current + 逐指标检验 + pass/fail（约 50 行，不装包）。

## 三、给我们设计的 5 步最小评估流水线

**Step 1 · 冻结集先行**：产出 `eval/cases/v1.jsonl`（字段 `case_id / query / expected_models / expected_images / layer_tags[extraction|retrieval|delivery] / source / difficulty`）与 `eval/manifest.json`（N、分层计数、文件 sha256、冻结时间、标注人）。铁律：v1 只增不删，改动一律升版本号，所有指标必须携带 `dataset_version`——这是"改动可归因"的唯一前提。

**Step 2 · 三层分开算，落成一张 per-case 宽表**：抽取层 `nDCG@10`（对 expected_models）；召回层 `R@20`（对 expected_images）+ 规则核验 precision（每周人工抽检 50 张）；交付层 `hit@3`、空结果率、误报率。输出 `eval/out/{run_id}/cases.parquet`，一行一 case，**不合成加权总分**，任何总分都会掩盖层的退化。

**Step 3 · 分层配对 bootstrap**：现有脚本改三处——①按 `layer_tags` 分层重采样（交付层样本少也能得稳 CI）②同时报主指标 Δ、95% CI、P(Δ>0) ③给出分层 Δ。合入门槛：主指标 CI 下界 > -0.01，且无任一层 Δ < -0.03。

**Step 4 · CI gate**：新增 `scripts/eval_gate.py`，读 `summary.json`，三个硬指标（抽取 nDCG@10 / 召回 R@20 / 交付 hit@3）低于阈值或 ΔCI 越界即 `exit 1`；同时输出 `results.junit.xml` 让 CI 原生展示，并把 `git.sha`、`run_id`、`dataset_version` 打进 summary。只在 `eval/`、prompt、抓图规则目录变更时触发。

**Step 5 · 周度漂移 + 回流**：参考窗口=冻结集基线，当前窗口=近 7 天线上抽样 200 条（其中 50 条人工标注）；连续指标用 KS、比例指标用 PSI，叠加分层 Δ。任一指标 >2σ 或某层掉 5pp → 告警，并把告警样本带 `predictions` 预标注导入 Label Studio；人工复核后升为 v1.1。`scripts/drift_report.py` 每周一 09:00 跑。
