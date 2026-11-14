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
| `data/legacy/category_profiles.json` | `4f1e79a33578` | 类目档案（旧 textrun） | 旧 `text-run` 链路**仍默认加载**（`textrun.load_profiles()` 无门控）；主链 loop 不读。见下方「已知偏差」 |
| `data/legacy/brand_aliases.json` | `a3bb257a8117` | 中外品牌别名 | 默认空；仅 `EQUIPLENS_ENABLE_LEGACY_BRANDS=1` 时加载 |

### 3.1 已知偏差（2026-11-14 复核，尚未修）

- **`category_profiles.json` 没有真正静默**：`textrun.load_profiles(path=None)` 会回落
  `DEFAULT_PROFILES` 并加载该表；`text-run` 命令因此**默认带上类目档案**（歧义判定/查询词汇）。
  它与 §1.1「不得默认加载」冲突，但属于 13 个旧链路测试（`tests/test_textrun.py`
  `test_profile_resolution_and_ambiguity` 直接断言默认档案存在）的既有行为，
  改动需连测试一起改，故**先记录、不改**。主链（`retrieval_engine`）不 import `textrun`，
  近期的 P0–P4 实验不受影响。
- **`data/style_vocabulary.json` 未纳入清单**：`analysis.load_vocab()` 默认加载它，
  用于校验分析输出里的风格词。它是**描述性语汇**（不是品牌/车型/部件枚举），
  按 §2.1 视为"通用语言学"边界情形，**是否要迁入 `data/legacy/` 待拍板**。
- **旧链路模块仍在 `src/` 内自带词表**：`l3gate.py`（`PARTS` 56 / `FORMS` / `OPTION_WORDS`）、
  `passage.py`（`STRONG`/`WEAK`/`NEGATIVE`）、`audit.py`（`STRONG_WORDS`）、
  `roster.py`（`BRANDS` 50+ / `VEHICLE_WORDS`）、`corpus.py`（`SOURCE_TYPES`）。
  它们**不在主链 import 图内**（主链只 import `imagesearch`、`gate`），
  按 §1 的字面"不得包含"属于违规；按"主链不可达"属可接受。**当前取舍：保留，靠守卫锁住可达性**（§6），
  若要彻底清理需单独排期。

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
- 上述文件仍存在于 `data/legacy/`（防止误删导致 legacy 脚本静默失效）；
- **主链 `src/equiplens/retrieval_engine/**` 不得 import 旧链路模块**
  （`textrun`/`l3gate`/`passage`/`audit`/`roster`/`corpus`/`domainbench`/`strategy`）——
  这条锁住"旧词表不会顺着 import 图回流主链"。

**未覆盖（已知缺口，见 §3.1）**：`textrun.load_profiles()` 与 `analysis.load_vocab()` 的
默认加载；守卫只做静态字符串/import 检查，不追踪运行时路径。
