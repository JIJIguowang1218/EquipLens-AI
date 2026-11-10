# 检索前任务单：纸面测试（2026-11-09）

| 属性 | 内容 |
|---|---|
| **阶段** | 检索前（pre-retrieval） |
| **模块** | L1.5 任务单（task brief） |
| **测试类型** | 纸面测试（paper test）：不联网、不查库、不写代码 |
| **版本** | v0.2（含 2026-11-09 产品负责人评审修订） |
| **标签** | `pre-retrieval`、`task-brief`、`paper-test`、`region-vs-part`、`part-location`、`base-platform` |
| **输入** | 5 个真实输入（深度）+ 20 个扩展类目（广度） |
| **产出** | `BRIEFS-5.md` / `BRIEFS-5.json`；`CASES-20.md` / `CASES-20.json` |
| **不包含** | 具体车型、库内命中、外网结果、覆盖率——这些属于**检索中** |
| **判定** | 只判“任务单是否可指导检索”，不判“检索结果好不好” |

## 1. 文件

| 文件 | 内容 | 读法 |
|---|---|---|
| `BRIEFS-5.md` | 5 个深度案例：假设、区域/部件要求、层级、评审意见 | 评审用 |
| `BRIEFS-5.json` | 同上，结构化，便于后续脚本消费 | 机器读 |
| `CASES-20.md` | 20 个扩展案例：类目、工况、基础构型、部件、层级、备注 | 稳定性抽查 |
| `CASES-20.json` | 同上，结构化 | 机器读 |
| `README.md` | 本文件：口径、标签、评审 rubric、发现 | 入口 |

## 2. 这一版改了什么（v0.1 → v0.2）

| # | 评审意见（2026-11-09） | 改动 |
|---|---|---|
| 1 | “车辆侧护板是前后轮之间的覆盖件结构；驾驶室后方侧护板是另一个位置” | 任务单增加 **`location`** 维度（`side_chassis` / `side_cab_rear` / `front_lower` …），同一 `part` 可按位置拆成多个要求 |
| 2 | “前脸是覆盖件的整体线条走势和风格描述，和部件描述不是一个结构” | 任务单增加 **`region_requirements`**（`gesture` / `character_lines` / `proportion` / `cmf` / `judgement` / `style_tags`），与 `part_requirements` 分开 |
| 3 | “无环境的先按推荐来” | 无工况输入时不强开 `environment` 层；`design_relevance` 全 `none` 时只走 exact → platform → cross |
| 4 | “类目歧义目前不明显” | 保留“默认解释 + 写 assumption”，不加追问；歧义只在备注里标注 |
| 5 | “任务单要不要给基础构型？沙漠牵引车本质是卡车头；随车吊是卡车+吊机” | 任务单增加 **`base_platform`**（+ 可选 `configuration`），`platform` / `cross` 层按基础构型收窄 |
| 6 | “配额不能预先分配层级数量” | **删除每层配额**；只保留版面容量（12 车 / 5–6 单元）与成本护栏；层级按“耗尽才开”降级 |

## 3. 稳定性 rubric（评审时逐条打勾）

| # | 检查 | 期望 |
|---|---|---|
| R1 | 每个案例是否给出 `base_platform`？ | 100% |
| R2 | “前脸/侧面/后围”是否落在 `region`，而不是 `part`？ | 100% |
| R3 | 同名不同位置的部件（如侧护板）是否拆成不同 `location`？ | 至少 C02 拆开 |
| R4 | 无工况输入的案例是否**没有** `environment` 层？ | 100% |
| R5 | 有工况但设计无关的案例（如高原搅拌车）是否也没有 `environment` 层？ | 是 |
| R6 | 是否出现具体车型？ | 0（除非用户点名） |
| R7 | 是否出现“每层找 N 台”的预设配额？ | 0 |
| R8 | 新部件是否标了 `taxonomy: new` 并给出建议族/视角？ | 100% |
| R9 | 区域要求是否要求“整体可见”，而不是局部特写？ | 100% |
| R10 | 层级是否按 exact → environment → platform → cross，且“耗尽才开”？ | 100% |

## 4. 本轮已暴露的设计问题（待下一轮处理）

1. **位置维度**：`location` 目前是自由文本，应该收敛成受控词表（front_lower / front_upper / side_chassis / side_cab_rear / side_lower / rear_body / roof / underbody）。
2. **词表缺口**：`side_guard` 没有位置变体；`cargo_body`、`tank`、`boom`、`outrigger`、`bucket`、`cab`、`plow`、`grapple`、`pump_boom`、`compactor_body` 等部件不在 [`data/part_taxonomy.json`](../../../data/part_taxonomy.json) 里，本测试一律标 `taxonomy: new`。
3. **区域与部件的关系**：前脸区域包含 grille/headlamp/bumper/brand_zone；用户单列大灯/保险杠时，既要区域要求，也要部件要求，不能互相替代。
4. **基础构型**：`base_platform` 目前靠推理，应写进 `data/category_profiles.json`（每个类目加 `base_platform` + `configuration`），否则每次都要现推。
5. **无工况类目**：exact → platform → cross 的顺序成立，但 `cross` 的“同基础构型”约束还没写成数据。

## 5. 与测试台账的关系

- 本轮已在 [`docs/test-log.md`](../../../docs/test-log.md) §1 追加 `T19-pre-brief`；
- 本目录只放**检索前**任务单，不放命中单/证据单；命中单在后续 `T19-retrieval-*` 轮次另建目录；
- 所有文件只读，不接生产库；样本输入来自产品负责人 2026-11-09 提供的 5 条 + 本项目扩展的 15 条。

## 6. 2026-11-11 起：brief 必须 API 生成

此前 `brief-m1-desert.json` / `brief-m1b-global.json` 是**人工根据口述写的**，用于 T31–T41 的下游测试；这导致 brief 生成环节从未被测试。现在改为：

```bash
PYTHONPATH=src python scripts/build_brief.py   --input "沙漠牵引车（前脸、登车踏步、大灯、前轮拱、防护栏、保险杠）；沙漠/油田工况；6×6；12 台"   --class "沙漠牵引车" --slots 12 --out data-test/briefs/brief-c01-auto.json
```

- 提示/规则：`skills/task-brief/SKILL.md`（`task-brief@v1`）；
- 校验：`validate_brief` + `schemas/task-brief-v3.schema.json`；
- 产物带 `brief.json.meta.json`（raw_input / model / skill_version / attempts / llm_payload）；
- 本目录的 `brief-m1-*.json` 标为 **legacy 手工输入**，只用于复现历史 run，不再作为新实验输入。
