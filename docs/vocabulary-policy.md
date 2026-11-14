# 词表与枚举清单政策（2026-11-14，删除版）

> 背景：项目多次因“用词表认世界”吃亏（部件 hash、品牌误判、类目降权误伤）。
> 本文件是硬规则，新机制评审时逐条对照。

## 1. 硬规则

1. **主体代码（`src/equiplens/`）不得包含、索引或默认加载领域实体枚举**：
   品牌、类目、部件、车型、来源白名单都不行；也不得保留指向旧词表文件的路径常量；
2. **高风险表不得入库**：需要做考古/对照时，放在仓库外（或实验机本地），
   用**显式参数**传入，且只能被 legacy 脚本使用；不得写成默认路径；
3. 判定逻辑必须能回答：“**没有这张表，这条规则还成立吗？**” 不成立就不许进主链；
4. 新机制必须写清：依赖什么信号、这个信号是否枚举、失败时是“放行/丢弃/降权”哪一种。

## 2. 允许的例外（不是领域枚举）

| 类型 | 例子 | 约束 |
|---|---|---|
| 通用语言学停用词 | `NON_VEHICLE`、`VEHICLE_WORDS`、`GENERIC` | ≤30 条；只做“是否像车”的粗筛，不决定身份 |
| 模型提示标签 | gate 的 keep/drop/scene/view 文本 | 是 CLIP 的提示词，不是用户实体表 |
| 输出结构常量 | 视角枚举、分析字段、part key 的写法规则 | 是 schema，不是实体清单 |
| 运维配置 | `data/source_registry.json` | 只用于来源健康/统计，**不参与交付准入**（已与 loop 解耦） |
| **大类排除词** | `briefing.DEFAULT_NEGATIVE`（客车/SUV/房车/内饰/广告） | 是“不要什么大类”的粗筛，**不是穷举实体表**；只进 negative，不决定身份；产品负责人 2026-11-14 明确认可 |

## 3. 已删除的 legacy 词表（2026-11-14，用户批准）

| 文件（已不存在） | sha256（删除前） | 原用途 | 删除后 |
|---|---|---|---|
| `part_taxonomy.json` | `0b4a521be011…` | 部件键/区域/术语穷举 | key 只按写法生成（ascii snake 保留，其余 `custom_<slug>`）；`analysis.load_taxonomy()` 返回 `{}`；`make_ui_fixtures` 归档并显式退出 |
| `category_profiles.json` | `4f1e79a33578…` | 类目档案（别名/代表车型/部件词） | `textrun.load_profiles()` 默认返回空；只有显式 `--profiles <path>` 才读外部文件；缺档案走通用层 |
| `brand_aliases.json` | `a3bb257a8117…` | 中外品牌别名 | `imagesearch.BRAND_GROUPS = ()`；无 `EQUIPLENS_ENABLE_LEGACY_BRANDS` 开关；品牌只靠“车名开头词/括号外子串”结构性判断 |

> 删除记录见 `docs/DATA-CHANGELOG.md` §26（含 sha256、被删除的代码路径、回归结果）。

## 3.1 残留偏差（已知，按优先级）

- **`data/style_vocabulary.json` 未纳管**：`analysis.load_vocab()` 默认加载它，
  用于校验分析输出里的风格词。它是**描述性语汇**（不是品牌/车型/部件枚举），
  按 §2 视为边界情形；是否也要删除/外置，**待拍板**（主链 loop 不读）。
- **旧链路模块仍自带词表**：`l3gate.py`（`PARTS` / `FORMS` / `OPTION_WORDS`）、
  `passage.py`（`STRONG`/`WEAK`/`NEGATIVE`）、`audit.py`（`STRONG_WORDS`）、
  `roster.py`（`BRANDS` / `VEHICLE_WORDS`）、`corpus.py`（`SOURCE_TYPES`）。
  它们**不在主链 import 图内**（主链只 import `imagesearch`、`gate`），
  按 §1 字面“不得包含”仍属违规；**当前取舍：保留，靠守卫锁住可达性**（§6），
  彻底清理需单独排期（旧链路一旦整体下线，应随之下线）。

## 4. 当前主链依赖（对照用）

- 部件：`briefing` 只按“写法”生成 key（ascii snake 保留，其余 `custom_<slug>`），**不查表**；
- 品牌：`_brand_group` 只认“车名开头词/括号外子串”，不查表；`BRAND_GROUPS` 恒为空；
- 类目：不做类目词穷举；wide 抽取的离类问题靠“来源证据”而非词表（A1 已否决自动降权）；
- 身份：型号码/拉丁 token/中文片段三类证据；品牌命中只是加分；
- 负词：`DEFAULT_NEGATIVE` 是**大类排除**（§2 例外），不穷举具体车型/品牌。

## 5. 变更流程（新增/恢复表）

1. 先写影响面：哪些模块 import、哪些测试依赖、哪些历史 run 回放需要；
2. **默认路径不得指向表**；需要时只接受显式参数；
3. 恢复任何词表都要在 `DATA-CHANGELOG` 记录原因与影响面，并更新 §3；
4. 禁止“为了方便”把表加回主链或改回默认加载。

## 6. 自动守卫

`tests/test_no_legacy_tables.py`（4 条，2026-11-14 强化）检查：

- **`src/` 全量扫描**：不得出现 `part_taxonomy` / `category_profiles` / `brand_aliases` /
  `ENABLE_LEGACY` / `data/legacy` 任何字样；
- **三张表必须不存在**（防止恢复）；
- `imagesearch.BRAND_GROUPS == ()`；
- **主链 `retrieval_engine/**` 不得 import 旧链路模块**
  （`textrun`/`l3gate`/`passage`/`audit`/`roster`/`corpus`/`domainbench`/`strategy`）。

**未覆盖**：`analysis.load_vocab()` 的默认加载（§3.1）与旧链路模块自带的词表；
守卫只做静态字符串/import 检查，不追踪运行时路径。
