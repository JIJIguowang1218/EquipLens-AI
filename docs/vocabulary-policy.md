# 词表与枚举清单政策（2026-11-14）

> 背景：项目多次因“用词表认世界”吃亏（部件 hash、品牌误判、类目降权误伤）。
> 本文件是硬规则，新机制评审时逐条对照。

## 1. 硬规则

1. **主体代码（`src/equiplens/`）不得包含或默认加载领域实体枚举**：
   品牌、类目、部件、车型、来源白名单都不行；
2. **高风险表一律静默**：放在 `data/legacy/`，默认不加载；需要时用**显式开关**（环境变量/参数），
   且只能被 legacy 脚本或对照实验使用；
3. 判定逻辑必须能回答：“**没有这张表，这条规则还成立吗？**” 不成立就不许进主链；
4. 新机制必须写清：依赖什么信号、这个信号是否枚举、失败时是“放行/丢弃/降权”哪一种。

## 2. 允许的例外（不是领域枚举）

| 类型 | 例子 | 约束 |
|---|---|---|
| 通用语言学停用词 | `NON_VEHICLE`、`VEHICLE_WORDS`、`GENERIC` | ≤30 条；只做“是否像车”的粗筛，不决定身份 |
| 模型提示标签 | gate 的 keep/drop/scene/view 文本 | 是 CLIP 的提示词，不是用户实体表 |
| 输出结构常量 | 视角枚举、分析字段、part key 的写法规则 | 是 schema，不是实体清单 |
| 运维配置 | `data/source_registry.json` | 只用于来源健康/统计，**不参与交付准入**（已与 loop 解耦） |

## 3. 已静默的 legacy 文件（保留，不加载）

| 文件 | sha256（前 12） | 原用途 | 现状 |
|---|---|---|---|
| `data/legacy/part_taxonomy.json` | `0b4a521be011` | 部件键/区域/术语 | `briefing`/`analysis` 不再读取；仅 `make_ui_fixtures` 显式引用 |
| `data/legacy/category_profiles.json` | `4f1e79a33578` | 类目档案（旧 textrun） | 旧链路默认路径；正常 loop 不读 |
| `data/legacy/brand_aliases.json` | `a3bb257a8117` | 中外品牌别名 | 默认空；仅 `EQUIPLENS_ENABLE_LEGACY_BRANDS=1` 时加载 |

> 注意：这些文件**没有删除**，只是静默；删除需单独评审（见 §5）。

## 4. 当前主链依赖（对照用）

- 部件：`briefing` 只按“写法”生成 key（ascii snake 保留，其余 `custom_<slug>`），**不查表**；
- 品牌：`_brand_group` 只认“车名开头词/括号外子串”，不查表；品牌表默认空；
- 类目：不做类目词穷举；wide 抽取的离类问题靠“来源证据”而非词表（A1 已否决自动降权）；
- 身份：型号码/拉丁 token/中文片段三类证据；品牌命中只是加分。

## 5. 变更流程（删除/恢复表）

1. 先写影响面：哪些模块 import、哪些测试依赖、哪些历史 run 回放需要；
2. 先静默（本文件 §3），跑一轮回归（单测 + 冻结 plan 的 c1/c2）；
3. 确认无回归后再删除；删除必须在 `DATA-CHANGELOG` 记录 sha256 与替代方案；
4. 禁止“为了方便”把表加回主链；确需恢复，走 §1.2 的显式开关。

## 6. 自动守卫

`tests/test_no_legacy_tables.py` 会检查：
- `briefing.py` / `analysis.py` 不再出现 `part_taxonomy`；
- `imagesearch.BRAND_GROUPS` 默认为空（未设置 legacy 环境变量时）；
- 上述文件仍存在于 `data/legacy/`（防止误删导致 legacy 脚本静默失效）。
