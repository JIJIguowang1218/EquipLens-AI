# P0 交付不变量 review（2026-11-12）

## 实现

1. 全局 asset 去重：已占槽 target 的 asset 不再给其他 target；
2. attempt 日志：state.attempts 记录 fetched/assets/verified/accepted/filled；
3. part_only 标记：有 scene 元数据但没有 `scene=single_vehicle` 的 target 标记；
4. code prefilter：可选，独立验证 12/12 构成不变。

## 关键 review：overview 硬规则不可用

### 尝试 A：`overview=True` 硬门槛

- 结果：`loop-p0-20261112` **10/12**（u-env 2/4）；
- 原因：`overview` 字段实际是“长边≥800”，会出现 `scene=part, overview=True`、`scene=single_vehicle, overview=False`；
- 这个字段不能代表“整车概览”，硬用会误杀。

### 尝试 B：`scene=single_vehicle` 硬门槛

- 结果：`loop-p0b-20261112` **12/12**，但 composition 变了：
  - 丢掉 rank7/8/13/14（它们只有 scene=part 的 accepted 图）；
  - 补进 rank18/20/21/23；
- 说明 gate 的 scene 对“局部图 vs 整车”并不可靠，硬门槛会改变交付构成。

### 采用：soft part_only

- `loop-p0c-20261112`：**12/12**，composition 与 baseline 一致；
- part_only 只标记 rank7/8/13/14，供人审/排序；
- 不硬拒绝，避免误杀有效图。

## 结论

- 全局去重和 attempt 日志保留；
- overview 不硬拒绝；`part_only` 是 review/排序信号；
- code prefilter 保留为可选；
- P0 可以在“软标记 + 人审”下进入第一次交付，但不能宣称 part-only 问题已解决。

## 2026-11-12 定案

- `part_only` **只作审计/排序信号**：不参与交付门槛、不拦截占槽、不再作为待拍板项；
- 之前列的“rank7/8/13/14 的图是否其实是整车”留给人审时看，不阻塞交付；
- 是否把交付资格上移到 VERIFY 属内部重构（见 `docs/fill-responsibility-audit.md`），不是前置条件。

## 待人工

- rank7/8/13/14 的 part-only 图是否其实是可用整车图；
- gate scene 是否需要后续单独校准（不要在本轮扩源里做）。


## 职责修正

`overview` 不应由 FILL 判断。FILL 的原始职责是占槽/备选/族去重；scene/overview 在 gate 里计算，但“整车交付资格”没有模块归属。当前 `part_only` 只是临时标记；长期应上移到 VERIFY/gate。详见 `docs/fill-responsibility-audit.md`。
