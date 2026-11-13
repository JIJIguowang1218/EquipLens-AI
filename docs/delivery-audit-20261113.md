# 交付缺口审计：unit 配额锁死（2026-11-13）

> 结论先行：本批 4 个"正选缺 1–2 台"的 run，**全部满足"有图 ≥ 输入槽位"**，
> 缺的不是图，是**有图车被 unit 配额挡在正选之外**。
> 详细数据见 `data-test/runs/ab-negative-20261113/AUDIT-DELIVERY-TIMING.md`。

## 1. 现象

| run | 输入 | 有图 | 正选 | 备选 | 剩余有图 |
|---|---:|---:|---:|---:|---:|
| c2 with | 10 | 10 | 8 | 2 | 0 |
| c1 without | 10 | 11 | 9 | 2 | 0 |
| c2 without | 10 | 14 | 9 | 4 | 1 |
| c1 baseline | 10 | 11 | 9 | 2 | 0 |

c2 without 是最直接的证据：**有图 14 = 10 正 + 4 备刚好够，实际却 9 正 + 4 备，还剩 1 台有图未用**。

## 2. 根因

1. `WebWorld._partition_plan()` 按 unit 配额切 plan：10 槽 → `u-exact` 7 + `u-env` 3；
2. 候选在 `EXTERNAL_DISCOVER` 时被写死 `unit_ids=[当时有缺口的 unit]`；
3. `engine._fill_pass()` 只按 `unit_ids` 找 unit，且严格 `len(accepted) >= quota` 就跳过；
4. `DEGRADE` 的 `_degraded_fill()` 仍然走同一逻辑，所以"降级兜底"补 0 台。

于是 `u-exact` 满了以后，它名下多出来的有图车只能进"备选"，`u-env` 的空槽一直空着。

## 3. 验收不是卡点

c2 with 的 2 台剩余有图车（XCMG、G 系列）都有 `accepted=probable` 的核验，
质量足够正常占槽；问题纯粹是分配。

## 4. 修复方向（正选优先、跨 unit 借位）

- `_fill_pass`：先尝试候选自己的 unit；本 unit 满/无可用图时，**允许借其它 unit 的空槽**；
- `DEGRADE` 的兜底填充**忽略 unit 边界与配额**，按全局优先级把 N 填满；
- 提交阶段：`delivered < N` 时，有图车不得先算作备选；备选只取正选填满后的剩余；
- 不变量测试：给定有图数 ≥ N、unit 配额不均，`delivered` 必须等于 N。

用现有 state 离线模拟修复后：

| run | 现在 | 修复后 |
|---|---|---|
| c2 with | 8 + 2 | **10 + 0** |
| c1 without | 9 + 2 | **10 + 1** |
| c2 without | 9 + 4 | **10 + 4（满）** |
| c1 baseline | 9 + 2 | **10 + 1** |

备选仍 short 的只有"有图 < 14"的 c1 without / c2 with，属于 plan 候选池不足，不是填槽能补的。

## 5. 与历史的关系

不是本轮新引入：baseline c1 同样 9/10、11 张图、`u-env 2/3`。
12 槽历史 run（`loop-p0c`、`verify-backup2`）两个 unit 都是 8/8 + 4/4，所以没暴露。
属于长期隐性缺陷，被本轮 `u-env` 只出 1 台有图放大成 8/10。
