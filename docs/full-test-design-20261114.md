# 完整测试设计（6+4，2026-11-14，未执行）

> 目的：验证**泛化**（未见类目）与**稳定**（同 brief 重复），而不是再调机制。
> 规模说明：6+4 仍然是“同一大类（工程/商用车）下的 10 个类目”，
> 只能证明**类目级泛化**，不能证明跨域泛化（如乘用车、农机之外的品类）。

## 1. 样本结构（6 已知 + 4 未见）

### 6 个已知类目（已有冻结 brief，可直接复用）

| # | 类目 | brief 来源 | 槽位 | 历史基线 | 备注 |
|---|---|---|---:|---|---|
| S1 | 沙漠牵引车 | `delivery-20261113-regress/c1-desert-tractor` | 10 | 10/10 + 1/4 | 紧供、波动大 |
| S2 | 港口正面吊 | 同上 `c2-reach-stacker` | 10 | 10/10 + 3/4 | 拉丁型号多 |
| S3 | 轮式拖拉机 | 同上 `c3-tractor` | 10 | 10/10 + 4/4 | 品牌多、型号杂 |
| S4 | 电动叉车 | 同上 `c4-forklift` | 6 | 6/6 + 4/4 | 非卡车类目 |
| S5 | 单钢轮压路机 | 同上 `c5-roller` | 14 | 14/14 + 4/4 | 槽位多、耗时最长 |
| S6 | 混凝土搅拌车 | `source-expansion-briefs-20261111/mixer` | 待确认 | 未跑 loop | 与 S1–S5 不同车身 |

### 4 个未见类目（holdout，已生成并冻结，2026-11-14）

生成方式：`scripts/build_brief.py`（API 生成，未手写）；位置 `data-test/evals/fulltest-20261114/`；
清单 `MANIFEST.json`（含每份 sha256）。

| # | 目录 | class（生成结果） | 槽位 | 部件数 | custom 部件 |
|---|---|---|---:|---:|---:|
| H1 | `h1-fire` | 水罐/泡沫消防车（罐式，含泵房与器材箱上装） | 8（5+3） | 6 | 3 |
| H2 | `h2-wrecker` | 清障车（拖吊/平板） | 6（4+2） | 7 | 4 |
| H3 | `h3-sweeper` | 扫路车（道路清扫车） | 6（4+2） | 5 | 3（可读：`custom_brush_guard` 等） |
| H4 | `h4-crane-truck` | 随车起重运输车（随车吊 / 二类底盘改装） | 8（5+3） | 7 | 4 |

**Brief 质量备注**：
- H1/H2/H4 的 custom 部件带语义名（如 `custom_pump_room_side_panel`），可读；
- H3 已于 11-14 重新生成：词表外部件改为**可读 key**（`custom_brush_guard`、
  `custom_hopper_side_panel`、`custom_suction_nozzle`），不再出现不透明 hash；
  brief 内容随之更新（manifest 已重算 sha256）。

> 注意：`aerial`（高空作业车）和 `mining-dump`（矿用自卸）在早期探针里出现过，
> **不算未见**；若要扩到 12 个类目，可把它们作为“半 holdout”。

## 2. 重复与对照

| 维度 | 设计 |
|---|---|
| 重复 | 每个 brief **3 次**（10×3 = 30 次 loop） |
| 配置 | 固定 `--concurrency 4`、`--download-workers 4`、rank=LLM、`extract-mode=model`、`glean=0` |
| 输入 | brief 冻结；plan 每次重跑（不冻结），因为要测“端到端稳定”而不是“同 plan 复跑” |
| 对照 | 同一 brief 的 3 次重复内部比较；不跨 brief 比绝对值 |

## 3. 指标（全部可自动化）

| 层 | 指标 |
|---|---|
| plan | 候选数、pool_ok、code/generic/slot/key 覆盖、去重重复组 |
| loop | 主交付/备选、degraded 占比、no_hits 率、`query_tiers` 分布（含 `search_key` 触发率） |
| 成本/时延 | peak/off-peak 成本、elapsed、FETCH 占比 |
| 稳定性 | 同一 brief 3 次的极差与变异系数（CV） |
| 人工（可选） | 每类抽 5 张图做“错图率”（F7 分类） |

## 4. 判定规则（先写死）

- 每个指标按 brief 内 3 次求均值，跨 10 个 brief 做配对 bootstrap（2000 次）95% CI；
- **CI 跨 0 → 无结论**；CI 全正/全负 → 有方向；
- 泛化门槛：4 个 holdout 的交付率均值 ≥ 5 个已知类目的 80%，且 no_hits 率不高于已知类目的 1.5 倍；
- 稳定门槛：同一 brief 3 次的主交付极差 ≤ 1 台、degraded 占比 CV ≤ 0.25。

## 5. 规模与成本（诚实评估）

| 方案 | loop 次数 | 预计耗时 | 预计成本 |
|---|---:|---|---:|
| 10 brief × 1 次（筛查） | 10 | ~1–1.5 h | ¥4–6 |
| **10 brief × 3 次（正式）** | **30** | **~3–4 h** | **¥12–18** |
| 12 brief × 3 次（含半 holdout） | 36 | ~4–5 h | ¥15–22 |

规模确实不大：10 个类目只能做**类目级**结论；若要“跨域泛化”，需要另加 4–6 个非工程车类目
（不在本轮范围）。建议先跑 10×1 筛查，若 holdout 明显掉点，再对掉点类目补到 3 次。

## 6. 执行前置条件（未满足前不跑）

1. 生成 4 个 holdout brief（API，不允许手写），并冻结到 `data-test/evals/fulltest-20261114/`；
2. 确认 S6（mixer）的槽位与基线；
3. 固定代码版本（当前 HEAD）与配置，记录到每个 run 的 `summary.config`；
4. 先跑 **c1/c2 两个冻结 plan 的 loop 冒烟**（品牌表静默后是否掉点），再跑 1 个新 brief 验证
   brief/part key 可读；都通过后才批量。

## 7. 筛查（10×1）的目的、风险与应对

**目的（4 个，不含“证明质量”）**：
1. **泛化体检**：4 个未见类目能否端到端跑通（brief→plan→loop→交付），不崩溃、有 summary；
2. **失败归因**：把失败分到 候选池不足 / no_hits / 门卫或核验拒绝 / 填槽或配额 / brief 本身 五类，
   决定是否值得投入 10×3；
3. **脚手架自检**：`summary.config`、`query_tiers`、台账、DELIVERY 字段在 10 个类目上是否都正常；
4. **成本/时延标定**：为正式测试定预算与时间。

**风险与应对**：
| 风险 | 表现 | 应对 |
|---|---|---|
| brief 质量 | parts/槽位不合理、custom hash | 筛查前人工看 5 分钟；不合格就用 API 重新生成（不手改） |
| 类目模糊 | 消防车混乘用车、清障车多形态 | 在 brief 里写清场景/部件；接受模糊，不在筛查中调机制 |
| 供给稀缺 | 冷门类目候选少、no_hits 高 | 看 pool_ok/no_hits，区分“数据问题”与“代码问题”，不为单类目改机制 |
| holdout 污染 | 部件/品牌在旧实验中见过 | 只能声称“类目级 holdout”，不声称跨域 |
| 单次波动 | 同 brief 候选 9–27 | 筛查只做 triage；正式测试才 3 次重复 |
| 配置漂移 | 并发/rank 不同 | 固定 HEAD，跑前跑后 `check_env` + 单测，记录 `summary.config` |
| API/网络失败 | 429、超时 | 并发 4、失败 run 单独重跑，不混入统计 |
| 图片缺失 | images 被 gitignore | 只读 state/summary/DELIVERY.json 判定 |

**Go/No-Go（筛查后）**：
- 10 个 brief 均有 summary（允许 FAILED/short，但不能崩溃）；
- holdout 主交付均值 ≥ 已知均值 80%；
- no_hits 率 ≤ 已知的 1.5 倍；
- 成本 <¥8、耗时 <2h；
- 任一“崩溃/字段缺失” → 先修脚手架，再谈正式测试。

**掉点时的归因顺序**：pool（候选够不够）→ no_hits（搜不到）→ gate/verify（拒绝）→ fill（配额/借位）→ brief。
