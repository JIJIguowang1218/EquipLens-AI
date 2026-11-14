# 完整测试报告（P0–P4，2026-11-14）

> 执行：自动化脚本（`scripts/run_fulltest.py`、`scripts/eval_fulltest*.py`），无人值守。
> 固定配置：`plan --concurrency 4`、`--download-workers 4`、rank=LLM、`extract-mode=model`、
> `glean=0`、topup 默认 2；每次 run 的 `summary.config` 已记录。
> 预算充足，未改生产默认（唯一代码改动是 opt-in 的 `--topup` 上限从 2 放宽到 4，默认不变）。

## P0 冒烟：品牌表静默后（冻结 plan，c1/c2）

**目的**：确认 `BRAND_GROUPS` 移出主代码、默认空表后没有回归。

**方法**：复用 `delivery-20261113-regress` 的 brief + plan-ranked，只改代码；各跑 1 次 loop。

**结果**：

| case | 静默前（p2） | 静默后（p6） | 差异 |
|---|---|---|---|
| c1 | 10/10 + 1/4，degraded 9，hits 315 | 10/10 + 1/4，degraded 9，hits 305 | 持平 |
| c2 | 10/10 + 3/4，degraded 6，hits 470 | 10/10 + **4/4**，degraded 6，hits 495 | 备选 +1 |

**结论**：**通过**，无回归；c2 备选 +1。`query_tiers` 记录正常。

## P1 冒烟：新 brief（洒水车）

**目的**：确认去表化后新类目可生成、可校验、可进 plan，且部件 key 可读。

**方法**：`build_brief.py` 生成洒水车（4×2，6 台，5 部件），检查 prompt/schema/契约/plan。

**结果**：
- prompt 无 `reference_parts`、含 `no_vocabulary_note`；
- 部件 key：`custom_front_bumper`、`custom_tank_side_panel`、`custom_pump_room_side_door`、
  `custom_boarding_step`、`custom_wheel_arch`（可读，无 hash）；
- `validate_brief_json == []`、schema 通过、`Brief.from_dict` 正常；
- plan：30 候选、`pool_ok=true`（required 16）。

**结论**：**通过**。

## P2 十类目筛查（10×1）

**目的**：类目级泛化体检 + 失败归因。

**方法**：6 已知（c1–c5 + s6 搅拌车）+ 4 holdout（消防/清障/扫路/随车吊），各 1 次完整链路。

**结果**（`data-test/runs/p7-screen-20261114/`）：

| case | 组 | 交付 | 备选 | degraded | no_hits | 候选/池 | 成本¥ | 耗时s |
|---|---|---|---:|---:|---:|---:|---:|---:|
| c1 | 已知 | 10/10 | 4/4 | 9 | 0 | 21/ok | 0.456 | 148 |
| c2 | 已知 | 10/10 | 4/4 | 7 | 1 | 25/ok | 0.486 | 392 |
| c3 | 已知 | 10/10 | 4/4 | 4 | 0 | 26/ok | 0.459 | 252 |
| c4 | 已知 | 6/6 | 4/4 | 5 | 1 | 25/ok | 0.424 | 249 |
| c5 | 已知 | 14/14 | 4/4 | 5 | 0 | 36/ok | 0.509 | 392 |
| s6 | 已知 | 12/12 | 4/4 | **10** | 0 | 16/**short** | 0.527 | 209 |
| h1 | holdout | 8/8 | 4/4 | 7 | 0 | 20/ok | 0.437 | 143 |
| h2 | holdout | 6/6 | 4/4 | 5 | 0 | 29/ok | 0.516 | 187 |
| h3 | holdout | 6/6 | 4/4 | 4 | 0 | 22/ok | 0.349 | 99 |
| h4 | holdout | 8/8 | **2/4** | 5 | 0 | **12/short** | 0.518 | 144 |

**汇总**：已知 62/62、holdout 28/28；no_hits 2；成本 ¥1.82；loop 572 s。
**Go = true**（holdout/known 交付率 = 1.0，no_hits 0 vs 2）。

**问题记录**：h4 与 s6 候选池不足（12/20、16/26）→ 备选/degraded 受影响；未按单类目改机制。

## P3 重复测试（10 类目 × 3 次）

**目的**：同 brief 重复，检验交付/备选/身份的稳定性，并做 known vs holdout 对照。

**方法**：同一套 10 个 brief 跑 3 个完整 suite（r1/r2/r3），每 suite 重新 plan（不冻结），
指标取 3 次均值/极差/CV；判定阈值预先写死：
交付极差 ≤1/6、备选极差 ≤1、degraded 占比 CV ≤0.25、每类 3 次齐全。

**结果**（`data-test/runs/p7-screen-r2/r3-20261114/`，汇总 `data-test/evals/fulltest-repeats.json`）：

| case | 组 | 交付率均值 | 极差 | 备选均值(±) | degraded 均值 | CV | no_hits 均值 |
|---|---|---:|---:|---:|---:|---:|---:|
| c1 | 已知 | 1.000 | 0 | 4.00 (0) | 0.867 | 0.054 | 0 |
| c2 | 已知 | 1.000 | 0 | 4.00 (0) | 0.600 | 0.136 | 0.33 |
| c3 | 已知 | 1.000 | 0 | 4.00 (0) | 0.467 | 0.101 | 0 |
| c4 | 已知 | 1.000 | 0 | 4.00 (0) | 0.944 | 0.083 | 0.33 |
| c5 | 已知 | 1.000 | 0 | 4.00 (0) | 0.238 | **0.374** | 0 |
| s6 | 已知 | 1.000 | 0 | 3.67 (±1) | 0.861 | 0.046 | 0 |
| h1 | holdout | 1.000 | 0 | 4.00 (0) | 0.917 | 0.064 | 0 |
| h2 | holdout | 1.000 | 0 | 4.00 (0) | 0.889 | 0.089 | 0.33 |
| h3 | holdout | 1.000 | 0 | 4.00 (0) | 0.611 | 0.129 | 0 |
| h4 | holdout | 1.000 | 0 | 3.00 (**±2**) | 0.667 | 0.088 | 0 |

**汇总**：
- 已知：交付 1.000、备选 3.94、degraded 0.663、no_hits 0.11；
- holdout：交付 1.000、备选 3.75、degraded 0.771、no_hits 0.08；
- 成本约 ¥4.6/suite、loop 约 2200 s/suite（3 suite 合计 ≈¥14、1.8 h）。

**判定**：
- 交付：**通过**（10 类目 ×3 全部 100%，极差 0）；
- 备选：**未通过**（h4 极差 2 > 1；s6 极差 1）；
- 身份：**未通过**（c5 degraded CV 0.374 > 0.25，但绝对值仅 2–5/14 台，均值低导致 CV 放大）；
- 总体 `go_stability=false`（预注册阈值，如实记录）。

**归因**：
- h4/s6 的波动来自**候选池数量波动**（h4: 12/20/15；s6: 16/21/15），不是交付逻辑；
- c5 的 CV 是**身份判定分配**（哪几台拿到 confirmed），绝对差异小；
- 无崩溃、无字段缺失、无 no_hits 异常。

## 调整-验证：topup 上限 2→4（opt-in）

**目的**：验证“候选池不足时多补 2 条通用查询”能否稳住 h4/s6 的备选。

**方法**：`top_up_queries` 增加通用后缀（图集/参数/评测），`--topup 4` 才生效（默认仍 2）；
对 h4、s6 各跑 2 次（新 plan），对比 3 次基线。

**结果**：

| case | 基线（topup 2）候选/备选 | topup 4 候选/备选 |
|---|---|---|
| h4 | 12→2/4、20→4/4、15→3/4 | 21→**4/4**、17→3/4 |
| s6 | 16→4/4、21→4/4、15→3/4 | 20→**4/4**、30→**4/4** |

**结论**：**部分有效**——候选池整体上移、s6 两次都满备选，h4 从 2/3 提升到 3/4；
但**没有消除波动**（抽取/搜索仍随机）。因此：
- 默认保持 topup=2（不改变生产行为）；
- 对“紧供类目”可显式 `--topup 4` 作为缓解，不按类目写死。

## P4 守卫与回归

- `tests/test_no_legacy_tables.py` 3/3、`briefing 5/5`、`planning 16/16`、
  `retrieval_engine 47/47`、`imagesearch 16/16`、`ledger 8/8`、`pricing 4/4`、`manifest 3/3`；
- 词表静默后主链无遗留引用；`summary.config` 在 30 个 run 中全部存在。

## 总体结论

1. **交付能力**：10 个类目（含 4 个未见类目）×3 次，**全部满额交付**，交付稳定性极强；
   no_hits 极低（均值 <0.4/类目），说明“判死点修复 + 候选抽取”在跨类目上成立。
2. **泛化**：holdout 与已知类目的交付率相同（1.0 vs 1.0），
   但这是**同域类目级泛化**（工程/商用车），不能外推到乘用车/农机等域。
3. **质量口径**：degraded 占比偏高（已知 0.66、holdout 0.77），即多数交付是弱身份图；
   交付“够数”不等于“身份都强”，这是当前最大质量短板。
4. **稳定性**：交付稳定；**备选与 degraded 占比不稳定**，根因是候选池波动与身份分配，
   不是代码回归；预注册阈值如实未通过。
5. **机制价值**：search_key、槽位、去表化、并发默认在生产路径上均无回归；
   `query_tiers` 显示 search_key 在 30 次运行中**未触发**（0 次），符合“末档兜底”定位。
6. **下一步优先级**（按证据）：
   - 候选池供给（topup 4 可选、或 wide 抽取+护栏）→ 直接影响备选稳定性；
   - degraded 政策（B1 已有告警，需定“可接受占比”或人工复核）；
   - 不建议再加新的检索规则，直到这两项有结论。

## 复现

```bash
PYTHONPATH=src python scripts/run_fulltest.py \
  --cases data-test/evals/fulltest-20261114/CASES.json \
  --root data-test/runs/p7-screen-20261114 --repeat 1
PYTHONPATH=src python scripts/eval_fulltest_repeats.py \
  --roots data-test/runs/p7-screen-20261114,data-test/runs/p7-screen-r2-20261114,data-test/runs/p7-screen-r3-20261114
```

## 代码版本与严谨性（2026-11-14 复核）

**问题背景**：词表静默的代码改动曾因 `git add` 中止而未真正入库（`d6f60c8` 只含文件移动），
后来由 `d0a4cec` 补提交。需要回答：测试跑的是哪一版代码？

**核对**：
- 源码 mtime：`briefing.py` 03:07、`imagesearch.py` 03:08、`analysis.py` 03:08、`web.py` 03:09；
- 首次运行：P0 03:17；P2 03:26–04:19；P3 04:19–06:10；
- `git diff d0a4cec HEAD -- src scripts tests` = 空 → **测试时的代码内容 == `d0a4cec` 的内容**；
- `plan_candidates.py` 的 topup4 改动发生在 06:03（P3 尾声），且默认仍是 2，
  P2/P3 未使用 `--topup 4`；P8 诊断才使用；
- 安全脱敏只改了两份证据里的 URL 字符串，不改指标。

**判定**：
- **结论有效**：执行用的是工作树中已改好的代码，不是旧的已提交版本；
- **可复现性在 `388171a` 窗口内受损**：该提交不含代码改动，检出它会得到旧代码；
  `d0a4cec` 起恢复一致；
- **加固**：本次新增 `summary.config.code_version`（git short sha），
  今后每个 run 自带代码版本；`retrieval_engine 47/47`。
