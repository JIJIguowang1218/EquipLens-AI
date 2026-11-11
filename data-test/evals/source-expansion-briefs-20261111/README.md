# 扩源实验用新 brief（2026-11-11）

## 选取逻辑

为扩源 A/B 新增 3 个**不同品类**，避免继续在 M1 沙漠牵引车上调参：

| ID | 品类 | 角色 | 关键部件/区域 |
|---|---|---|---|
| A | 矿用宽体自卸车 | 开发 | 货箱前/侧板、轮胎挡泥板、登车踏步；前脸/侧面 region |
| B | 12 方混凝土搅拌车 | 开发 | 搅拌罐、进出料斗、侧防护、尾部操作台；前脸/侧面/后围 region |
| C | 28 米级折叠臂高空作业车 | **holdout** | 臂架/折叠关节、工作斗、支腿、侧防护；前脸 region |

选取条件：

1. 与 M1/M1B 不同品类（自卸/搅拌/高空），不是同一 brief 换皮；
2. prompt 不含具体品牌/车型；
3. 每份 4 个部件 + 至少 1 个 region，便于 query 变体；
4. C 只做留出验证，不参与策略选择；
5. 生成方式：`scripts/build_brief.py --prompt-mode v2`（task-brief@v2），不是手写。

## 生成结果

- A 4 部件：`custom_cargo_front_plate` / `custom_cargo_side_plate` /
  `custom_tire_mudguard` / `step`；前脸、侧面由 region 覆盖。
- B 4 部件：`custom_mixer_drum` / `custom_charging_discharge_hopper` /
  `side_guard` / `custom_rear_operating_platform`。
- C 4 部件：`custom_boom_folding_joint` / `custom_work_basket` /
  `custom_outriggers` / `side_guard`。

## 注意

- A 的“前脸/驾驶室侧围”落在 region，不是独立 part；如果实验要求部件级 query，
  需要先决定是否补成 part。
- C 是 holdout；不能拿 C 的结果回去改 query 策略。
- 三份都需人工先审：品类/基型/构型、region、关系轴/设计轴是否合理。
