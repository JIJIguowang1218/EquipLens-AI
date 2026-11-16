# Badcase 登记册（测试异常与边界）

> 目的：测试中发现的异常/边界，全部编号登记，后续修复、复测、索引都按编号走；
> 避免“聊过就忘”“同一个坑反复踩”。规则与 `docs/external/doubao-consult-decisions.md`
> 的决策台账配套：**决策台账管“外部意见采纳与否”，本册管“实现/行为缺陷”**。

## 1. 编号与状态

- 编号：`BC-<模块>-<三位序号>`，例如 `BC-S01-001`（S01 = S0-01 输入识别）。
  编号一经分配**永不复用**，即使判为 by-design 也保留。
- 状态：
  | 状态 | 含义 |
  |---|---|
  | `open` | 已确认是缺陷/待定，未处理 |
  | `proto-fixed` | 临时原型已修并定向回归，尚未进生产 |
  | `fixed` | 已改（附 commit / 文件） |
  | `verified` | 改后复测通过（附复测记录） |
  | `by-design` | 复测后确认当前行为正确，不是缺陷（保留记录防止反复提） |
  | `product-decision` | 需要产品拍板，暂不实现 |
- 每条必须包含：**触发输入（测试数据，标注 `[test]`）**、期望、实际、根因、下一步。
- 测试输入只用于复现；**不得**写入生产默认值、配置或词表。

## 2. 索引

| ID | 模块 | 一句话 | 状态 |
|---|---|---|---|
| [BC-S01-001](S0-01-input.md#bc-s01-001) | S0-01 | “同类参考”被记成 `backup`，应进 `scope.adjacent` | verified |
| [BC-S01-002](S0-01-input.md#bc-s01-002) | S0-01 | 部件词“前脸格栅”被记成 `views=front` | verified |
| [BC-S01-003](S0-01-input.md#bc-s01-003) | S0-01 | “沙漠车”未归一为“沙漠牵引车” | verified |
| [BC-S01-004](S0-01-input.md#bc-s01-004) | S0-01 | 品牌配额（至少 3 台奔驰/沃尔沃）未自动估计 | verified |
| [BC-S01-005](S0-01-input.md#bc-s01-005) | S0-01 | `policy.hard/soft` 输出自由词，未用固定枚举 | verified |
| [BC-S01-006](S0-01-input.md#bc-s01-006) | S0-01 | “同类参考”与“加同型号”语义歧义 | by-design |
| [BC-S01-007](S0-01-input.md#bc-s01-007) | S0-01 | 缺类目时提问 1 次（正确行为） | by-design |
| [BC-S01-008](S0-01-input.md#bc-s01-008) | S0-01 | 未指定替换型号时自动另选（正确行为） | by-design |
| [BC-S01-009](S0-01-input.md#bc-s01-009) | S0-01 | 文本“(图)”无真图时要求补图（正确行为） | by-design |
| [BC-S01-010](S0-01-input.md#bc-s01-010) | S0-01 | class 混入 environment（v0.2 已修） | verified |
| [BC-S01-013](S0-01-input.md#bc-s01-013) | S0-01 | 文本“(图)”无真图却产出 `models_provided` | verified |
| [BC-S01-011](S0-01-input.md#bc-s01-011) | S0-01 | modify 被当新任务数量（v0.2 已修） | verified |
| [BC-S01-012](S0-01-input.md#bc-s01-012) | S0-01 | 软/硬偏好不分（v0.2 已修） | verified |
| [BC-S1-001](S1-planning.md#bc-s1-001) | S1 | 清障车 plan 池 8<16，备选 2/4 | open |
| [BC-S4-001](S4-router.md#bc-s4-001) | S4 | 显式总数被降级为增量 | open |
| [BC-S4-002](S4-router.md#bc-s4-002) | S4 | 质量诉求被标成排除项（标注口径） | by-design |
| [BC-S4-003](S4-router.md#bc-s4-003) | S4 | 部件请求漏识别 | open |
| [BC-S4-004](S4-router.md#bc-s4-004) | S4 | 多意图漏项 | open |
| [BC-S4-005](S4-router.md#bc-s4-005) | S4 | 破坏性 hard/soft 口径 | product-decision |
| [BC-S4-006](S4-router.md#bc-s4-006) | S4 | 缺能力/可行性层，越界请求被硬映射 | open |
| [BC-S4-007](S4-router.md#bc-s4-007) | S4 | 缺阶段维度，跨阶段误读 | open |
| [BC-S4-008](S4-router.md#bc-s4-008) | S4 | 数量语义未建模（总量/每款/同车/条件扩张） | open |
| [BC-S4-009](S4-router.md#bc-s4-009) | S4 | 复合意图只出一个 target | fixed |
| [BC-S4-010](S4-router.md#bc-s4-010) | S4 | 构型替换+补型号未拆全（#17） | open |
| [BC-S01-014](S0-01-input.md#bc-s01-014) | S0-01 | 用户排除项被 negative 前 4 条截断 | fixed |
| [BC-S05-001](S0-05-session.md#bc-s05-001) | S0-05 | 规则 router 对同义改写脆弱（holdout 7/14） | open |
| [BC-S05-002](S0-05-session.md#bc-s05-002) | S0-05 | LLM 把“同款更多图”判成加车型 | open |
| [BC-S05-003](S0-05-session.md#bc-s05-003) | S0-05 | “第三张图错了”纠错 vs 替换的 hard/soft | by-design |
| [BC-S05-004](S0-05-session.md#bc-s05-004) | S0-05 | “只要沙漠版”范围 vs 排除（两轴） | by-design |
| [BC-S05-005](S0-05-session.md#bc-s05-005) | S0-05 | “全都换成进口的”reset vs scope | by-design |
| [BC-S05-006](S0-05-session.md#bc-s05-006) | S0-05 | “这个不够，再补”数量 vs 同款加图 | open |
| [BC-S05-008](S0-05-session.md#bc-s05-008) | S0-05 | 删除/纠错后“第 N 张”的编号口径 | by-design |

## 3. 流程

1. 测试/用户反馈 → 先查本册是否已有；没有就新建编号；
2. 写清最小复现输入（`[test]` 标注）与期望；
3. 修复后改 `fixed` 并写 commit；复测通过改 `verified`；
4. 若复测证明行为正确 → `by-design`，并在文末“已确认行为”留一句，防止再提；
5. 需要产品决定的 → `product-decision`，挂到决策台账对应条目。

## 4. 已确认行为（不要重复提）

- 缺类目时必须提 1 个澄清问题（blocking），不是“猜一个类目硬跑”；
- 未指定替换型号的“换一个”由系统从同类中自动另选，**不需要**用户确认；
  只有“删除/替换**已交付**内容”才需要确认（破坏性、不可逆）；
- 文本里只有“(图)”但没真图时，必须要求补图/补型号，不得假装有图。
