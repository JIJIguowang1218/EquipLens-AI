# 交付缺口与耗时审计（2026-11-13，A/B 数据）

数据：`data-test/runs/ab-negative-20261113/`（10 次 loop）+ `delivery-20261112-clean`（5 次基线）。
本文只回答两件事：**为什么缺交付**、**plan/rank/loop 时间花在哪**。

## 1. 交付缺口：不是没图，是"有图进不了正选"

| run | 候选/需池 | 发现 | 有图 | 需 N+4 | 正选 | 备选 | 剩余有图 | 正选可补 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| c1 with | 27/23 | 25 | 16 | 14 | 10/10 | 4 | 2 | 0 |
| c1 without | 17/23 | 17 | 11 | 14 | **9/10** | 2 | 0 | **1** |
| c1 baseline | 17/23 | 17 | 11 | 14 | **9/10** | 2 | 0 | **1** |
| c2 with | 16/23 | 16 | 10 | 14 | **8/10** | 2 | 0 | **2** |
| c2 without | 17/23 | 17 | 14 | 14 | **9/10** | 4 | 1 | **1** |
| c2 baseline | 16/23 | 16 | 12 | 14 | 10/10 | 2 | 0 | 0 |
| c3 with | 30/23 | 17 | 15 | 14 | 10/10 | 4 | 1 | 0 |
| c3 without | 25/23 | 20 | 15 | 14 | 10/10 | 4 | 1 | 0 |
| c3 baseline | 27/23 | 20 | 17 | 14 | 10/10 | 4 | 3 | 0 |
| c4 with | 23/16 | 14 | 13 | 10 | 6/6 | 4 | 3 | 0 |
| c4 without | 24/16 | 14 | 10 | 10 | 6/6 | 4 | 0 | 0 |
| c4 baseline | 24/16 | 12 | 10 | 10 | 6/6 | 4 | 0 | 0 |
| c5 with | 36/29 | 19 | 19 | 18 | 14/14 | 4 | 1 | 0 |
| c5 without | 31/29 | 23 | 22 | 18 | 14/14 | 4 | 4 | 0 |
| c5 baseline | 36/29 | 28 | 23 | 18 | 14/14 | 4 | 5 | 0 |

"正选可补" = `min(有图, N) - 正选`。**4 个缺口 run 全部满足 `有图 ≥ N`，
即正选缺口没有一次是因为"图不够"，全部是分配问题。**

### 1.1 直接证据：c2 without

- 有图 **14** 台 = N+4（10+4）刚好够；
- 实际交付 **9 正 + 4 备**，还剩 **1 台有图未用**；
- 10 台正选本可以占满，且备选 4 台也够——**只靠重新分配，不需要多抓一张图**。

### 1.2 根因：unit 配额在发现时冻结，正选填槽不能再平衡

`web._partition_plan()` 按 unit 配额把 plan 切成两段：

- `u-exact` 配额 7（10 槽时 `round(10×2/3)=7`）；
- `u-env` 配额 3。

每个 target 在 `EXTERNAL_DISCOVER` 时被写死 `unit_ids=[当前有缺口的 unit]`
（`engine._add_targets`），之后 `_fill_pass` 只认这个 unit、且不超过它的 quota：

```python
for uid in target.get("unit_ids") or [target.get("unit_id")]:
    if len(unit["accepted_targets"]) >= quota:   # 配额满了就跳过
        continue
```

结果：`u-exact` 7/7 满了以后，它名下多出来的有图车（c2 with 的 XCMG、G 系列）
**不能再填 `u-env` 空着的 2 个槽**，只能在提交阶段被当成备选。

c2 with 的 2 台"备选"就是这 2 台：
`u-exact 7/7 + u-env 1/3`，有图 10 台，交付 8 正 + 2 备。
**正选空 2 个、备选却有人，正是这个原因。**

### 1.3 降级递补执行了，但被配额锁死

- `DEGRADE` 分支确实调用了 `_degraded_fill()`（engine L467），
  c2 with / c1 without 的 decisions 里有 `all_tiers_exhausted`，说明走到了兜底；
- 但 `_fill_pass(allow_degraded=True)` 仍然按 `unit_ids` + `quota` 填，
  `u-env` 的 2 个空槽拿不到 `u-exact` 名下的图，**补 0 台**；
- c2 without 补了 1 台（XCMG 45t），仍差 1 台，同样因为剩下的图都在满额的 `u-exact` 名下。

所以不是"降级机制没加载"，是**它被单元边界限制，实际无效**。

### 1.4 验收是不是太严？不是

对 3 个缺口 run 的"未进正选但有图"车型做核验统计：

| run | 剩余有图 | 其中有 accepted 核验（probable/confirmed） |
|---|---:|---:|
| c2 with | 2 | **2**（XCMG、G 系列都是 probable） |
| c1 without | 2 | 1（371HP 是 probable；TX 是 unknown） |
| c2 without | 5 | **5** |

c2 with 的 2 台质量完全够正常占槽（accepted=probable），却因为 unit 满了进不去。
`RuleVerifier` 不是这里的卡点；门卫 gate_pass 也有 145–240 张。

### 1.5 与历史对比

- 这不是今天新出现的 bug：baseline c1（`delivery-20261112-clean`）同样是
  **9/10、有图 11、u-env 2/3**，同样有 1 个正选槽被锁死；
- baseline c2 是 10/10（`u-env` 3/3 恰好都有图），今天 c2 with 的 `u-env` 只有 1 台有图，
  于是同样的锁死放大成 2 个缺口；
- 12 槽历史 run（`loop-p0c`、`verify-backup2`）两个 unit 都是 8/8 + 4/4，没暴露；
- 所以是**长期存在的隐性缺陷 + 本轮 env 分区取图波动**，不是链路整体退化；
  但 c2 with 的 8/10 确实是这一批里最差的一次。

### 1.6 另一个独立缺口：备选不够是"池子太小"

c1 without（17 候选）、c2 with（16 候选）都低于需池 23（1.6×(10+4)），
有图 11/10 < 14，因此备选只能 2/4。这是上游 plan 的候选池不足（波动），
和正选分配是两件事：**正选能补满，备选补不满**。

## 2. 耗时：loop 是爬虫，不是一次 API 调用

### 2.1 实测（10 次 A/B，driver 墙钟）

| 阶段 | 中位数 | 范围 | 占中位总时长 |
|---|---:|---:|---:|
| plan | 101 s | 74–161 s | 21% |
| rank | 43 s | 26–65 s | 9% |
| loop | 345 s | 216–635 s | 70% |
| 合计 | **490 s** | — | 100% |

### 2.2 plan（不是 loop 的一部分）

独立进程 `scripts/plan_candidates.py`，上游阶段。每次：

1. `build_query_plan` 生成 6 条查询（base/model/env/english/unit×2）；
2. 每条：`POST /v1/tools/search`（实测 0.8–1.0 s，20 条结果）；
3. 每条：`POST /v1/chat/completions` 做抽取——prompt 约 **4.9k tokens**，
   输出 **2.0–3.3k tokens**（c1 without 单次输出 3.3k）；
4. 6–8 条串行，合计 **15k–27k 输出 tokens**，90–160 s；
5. 池不足再 topup 2 条（+2 search +2 chat）。

耗时几乎全是"生成抽取 JSON"的 token 时间，不是网络慢。

### 2.3 rank

一次 chat 调用：把 16–36 个候选（model/reason/来源）塞进 prompt，输出带
band/reason/role 的排序 JSON。26–65 s，同样是输出 token 时间。
**rank 的 usage 目前没记入 api_log**，成本口径缺这一块。

### 2.4 loop

| 状态 | 中位数 | 说明 |
|---|---:|---|
| FETCH | 270 s | 逐台下载 250–492 张图 + 两段式 ONNX 门卫；实测约 1 s/张（网络为主，门卫推理 23–37 ms/张，模型加载约 2 s） |
| EXTERNAL_DISCOVER | 71 s | 车型图搜（每台最多 3 档 query × 6 条）+ 每候选 1–2 次 citation Fetch（约 1 s/次） |
| VERIFY / FILL / GAP_CHECK | < 1 s | 规则核验和状态机本身很快 |

### 2.5 为什么比 DeepSeek 网页对话慢

网页/对话式是一次模型调用 + 内置检索片段，几秒到几十秒；我们是一条流水线：

- plan 本身就是 **6–8 次完整 LLM 调用**（为了"每条候选必须来自该查询的结果"的出处约束，
  不能合成一次大抽取）；
- rank 再来 **1 次完整 LLM 调用**；
- loop 要**真实下载几百张图**、逐张过本地 ONNX 门卫，还要逐候选 Fetch 引用页；
- 全部串行，没有并发；为反爬还有 0.3–1.0 s sleep。

所以不是"DeepSeek API 慢"，是**我们做了网页对话不会做的事**：
多轮抽取 + 出处核验 + 几百张图的下载与本地视觉门卫。

### 2.6 与历史耗时对比

baseline clean：plan 74–167 s、rank 28–52 s、loop 176–502 s。
本轮：plan 74–161 s、rank 26–65 s、loop 216–635 s。
**没有系统性变慢**；loop 波动主要来自下载量（c5 492 张 vs baseline 714 张，
但网络单张更慢：0.62 s → 1.07 s）。

### 2.7 可优化项（按收益）

1. **plan 查询并发**：6–8 条互不依赖，并发后 90–160 s → 约 25–40 s；需控 API 并发。
2. **rank 合并或并行**：与 plan 的最后一次抽取合并，或接受确定性排序，省 26–65 s。
3. **下载并发**：按 host 限流（2–4 并发）可把 FETCH 270 s 压到 100–150 s；
   风险是 360/百度反爬。
4. **监控补齐**：plan 的 api_log 只有 tokens 没有 ms；rank 既无 ms 也无 usage；
   建议两条都记 `ms`/`usage`，并把 plan/rank 墙钟写进 suite JSON。

## 3. 结论与建议修复

**卡点排序**：

1. **正选填槽机制（P0，确定性 bug）**：unit 配额 + 发现时冻结的 `unit_ids`，
   让有图车进不了正选；降级兜底也被同一把锁挡住。这是"正选空、备选有"的直接原因。
2. **plan 候选池波动（P1）**：c1 without 17、c2 with 16 < 需池 23，导致备选不够；
   不是门卫/核验问题。
3. **验收（不是卡点）**：剩余有图车大多有 accepted probable/confirmed。
4. **耗时（体验问题，非缺陷）**：loop 是下载/门卫密集型；plan/rank 是多次 LLM 生成。

**建议修复（不改数据、不加 API 成本）**：

- `_fill_pass(allow_degraded=True)` 忽略 `unit_ids` 与 unit quota，按全局优先级
  把有图车填满 N；先试"有 accepted 图"的，再试任意图；
- 正常 FILL 也允许"本 unit 满时借其它 unit 的空槽"（quality-first），
  避免把 quality-ok 的车留到 degraded；
- 提交阶段强制"正选优先"：`delivered < N` 时，不得把有图车算进备选；
  备选只能取正选填满后的剩余；
- 加不变量测试：给定有图数 ≥ N、unit 配额不均，`delivered` 必须等于 N，
  且 `backup` 只能来自剩余。

按今天的数据预估修复效果（不重新抓图）：

| run | 现在 | 修复后 |
|---|---|---|
| c2 with | 8 正 + 2 备 | **10 正 + 0 备** |
| c1 without | 9 正 + 2 备 | **10 正 + 1 备** |
| c2 without | 9 正 + 4 备 | **10 正 + 4 备（满交付）** |
| c1 baseline | 9 正 + 2 备 | **10 正 + 1 备** |

备选仍会 short 的 run 是"有图 < 14"的 c1 without / c2 with，这属于池子不足，
要靠 plan 扩容/重试解决，不是填槽能补的。
