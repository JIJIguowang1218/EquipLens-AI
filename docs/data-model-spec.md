# 数据模型规范：单车素材管理（v0.1）

| 文档属性 | 内容 |
|---|---|
| 文档版本 | v0.1（按 2026-10-10 讨论定稿，待产品负责人逐字段复核） |
| 范围 | **单车素材管理**：一辆车的图片、来源、事实、描述、确认记录的存储形式与从属关系。项目级管理与数据飞轮为后续范围 |
| 部署前提 | 单机本地：SQLite（结构化数据）+ 文件系统（图片）。不引入数据库服务 |
| 关联文档 | docs/HANDOFF.md；docs/architecture-discussion.md（§2 统一 schema、§4 沉淀路线）；docs/PRD.md（附录 B 词表、NFR-6/7） |
| 配套产物 | schemas/equip-data.schema.json（机读校验）；db/schema.sql（建表）；src/equiplens/（数据访问层）；tests/test_data_layer.py（第一档测试） |

---

## 1. 决策记录（本轮讨论锁定项）

| # | 决策 | 状态 |
|---|---|---|
| D1 | 四层单车树：Vehicle / Facts / Descriptions / Asset 树；**原图不可变，只从原图裁**（不从裁图再裁），裁图记 bbox | 已确认 |
| D2 | 外源特写不"拒收"，按证据分级延迟归号；库中只存**证据类型+绑定状态**，T1–T4 档位为展示层派生概念 | 已确认（技术路径暂定） |
| D3 | 完备度 L0–L3 分级；**缺失是一等状态**；完备度为派生查询，不存储 | 已确认 |
| D4 | 描述三轴：节点（整体/部位）× 类型（结构事实/设计特征/设计意图）× 范围（品牌家族/本型号） | 已确认 |
| D5 | 同图多源合并：一个 Asset 挂 N 条来源；授权挂在来源上 | 已确认 |
| D6 | 批量确认：确认记录含机器原值/操作ID/方式，**只增不改**；仅高置信结构标签可批量 | 已确认 |
| D7 | 视角单枚举（朝向并入）；新增 `ortho_sheet`（三视图图版）与 `interior`/`scene`（范围外·归档）取值 | 已确认 |
| D8 | 工作区/正式库**逻辑分离**：同库，机器字段可覆盖，确认记录只增不改，"正式"=按状态过滤的视图 | 已确认 |
| D9 | 冗余收窄 S1–S5：分析实体并入描述档案；完备度/T档/槽位状态不存储；朝向并入枚举；两库物理分离降级为逻辑分离 | 已确认 |

**设计律（三条不变量，全库强制）：**

1. **可推导状态不存储**：完备度、T 档、槽位状态一律查询即得，库中只存实体、原始素材、机器标注原值、确认记录、证据；
2. **确认记录只增不改**：`confirm_log` 表禁止 UPDATE/DELETE（触发器强制）；机器字段允许覆盖，机器原值保留在确认记录中，撤销=恢复机器原值；
3. **原图不可变**：`source_image` 类素材文件一经写入不可覆盖；派生裁图必须记录 `parent_asset_id + crop_bbox`。

## 2. 实体与从属关系

```
Vehicle（车型实体，对应名录一个型号）
├─ hero_asset_id ──────────┐（主图指针，逻辑指向某 Asset）
├─ Facts 事实档案（1:N）     │
├─ Descriptions 描述档案(1:N)│
└─ Asset 素材树             │
   ├─ SourceImage 原图 ◄────┘
   │   └─ Crop 裁图（parent_asset_id + crop_bbox）
   └─ Source 来源记录（1:N，同图多源，授权挂在来源上）
ConfirmLog 确认记录（跨实体，只增不改）
Vocab 词表（附录 B 部位词表，可扩展）
```

- **Vehicle 与 Asset 分离**：车型实体先于素材存在（来自名录），素材通过"对号"挂到车上。对号 = Asset 上的 `binding_status + binding_evidence`；
- **Facts 与身份字段分工**（落表细化）：品牌/型号/类别/年款是车辆身份，直接做 Vehicle 列（可查询、可唯一约束）；吨位/功率等**参数类事实**进 Facts 表（键值式 + 来源）。分界规则：带数字单位的参数来自文档 → Facts；图上观察到的形态陈述 → Descriptions；
- **Descriptions 即分析输出**（S1 收窄）：MVP 单车层面不设独立"分析结果"实体，三轴描述档案就是分析整合模块的落库产物。

## 3. 表定义

主键统一为 UUID（TEXT）；时间统一 ISO8601 文本。`R`=必填，`O`=可空。

### 3.1 vehicles 车型实体

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | TEXT | PK | UUID |
| brand | TEXT | R | 品牌 |
| model_name | TEXT | R | 型号 |
| category | TEXT | O | 设备类别（重卡/装载机/起重机/矿卡…，受控词表待项目期定稿） |
| generation | TEXT | O | 世代/年款（来源名录或用户；空不算错） |
| list_status | TEXT | R | `candidate` 名录候选 / `locked` 闭集锁定 |
| hero_asset_id | TEXT | O | 主图指针；**逻辑引用不设外键**（避免建表循环），由访问层 `set_hero()` 校验 |
| project_id | TEXT | O | 预留，项目实体随项目模块定稿 |
| created_at | TEXT | R | |

UNIQUE(brand, model_name, generation)。

### 3.2 assets 素材

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | TEXT | PK | UUID |
| vehicle_id | TEXT | O | FK→vehicles；与 binding_status 联动（见下） |
| binding_status | TEXT | R | `unbound` 待归号池 / `provisional` 疑似待确认 / `confirmed` 已对号 |
| binding_evidence | TEXT | R | `none` / `self_derived` 内生裁图自证 / `region_match` 区域匹配 / `co_occurrence_labeled` 同源+型号标注 / `co_occurrence_only` 同源共现 / `human` 人工判定 |
| kind | TEXT | R | `source_image` / `crop` |
| parent_asset_id | TEXT | O | FK→assets；**crop 必填，原图必须为空** |
| crop_bbox | TEXT | O | JSON `{"x":..,"y":..,"w":..,"h":..}`；同上联动 |
| file_path | TEXT | R | 相对 data/ 的路径（见 §5） |
| view_angle | TEXT | R | 视角枚举（§4.1，11 值） |
| asset_nature | TEXT | R | 素材性质枚举（§4.2） |
| part_id | TEXT | O | FK→vocab；仅裁图/特写挂部位，原图=整车不挂 |
| width/height | INTEGER | O | 像素 |
| quality_flags | TEXT | O | JSON 数组，取值见 §4.3 |
| hash_sha256 | TEXT | R | 文件哈希，判重与完整性 |
| phash | TEXT | O | 感知哈希，近似判重/区域匹配（P1.5 启用） |
| confirm_status | TEXT | R | `machine_tagged` / `confirmed` / `rejected` |
| notes | TEXT | O | |
| created_at / updated_at | TEXT | R | |

表级 CHECK（不变量的强制执行点）：
- `(kind='crop') = (parent_asset_id IS NOT NULL AND crop_bbox IS NOT NULL)`；
- `(vehicle_id IS NULL) = (binding_status='unbound')`；
- `binding_status='unbound' ⇔ binding_evidence='none'`；
- 原图不允许有 parent（并入第一条）。

### 3.3 sources 来源记录

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id | TEXT | PK | |
| asset_id | TEXT | R | FK→assets，级联删除 |
| url | TEXT | O | 网络/系统来源；自摄可空 |
| platform | TEXT | O | 官网/经销商/新闻/甲方邮件/展会… |
| retrieved_at | TEXT | O | |
| license | TEXT | R | 授权枚举（§4.4），**挂在来源上**（D5） |
| is_primary | INTEGER | R | 0/1，展示取主来源 |
| note | TEXT | O | |

### 3.4 facts 参数事实

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id / vehicle_id | | R | FK→vehicles |
| field_key | TEXT | R | 参数键，起步清单见 §4.5，可扩展 |
| value | TEXT | R | 值 |
| unit | TEXT | O | 单位 |
| source_id | TEXT | O | FK→sources（参数出处） |
| confirm_status | TEXT | R | 同 §3.2 |
| created_at / updated_at | TEXT | R | |

### 3.5 descriptions 描述档案（= 分析输出，三轴 D4）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id / vehicle_id | | R | FK→vehicles |
| node_type | TEXT | R | `whole` 整体 / `part` 部位 |
| part_id | TEXT | O | FK→vocab；**node_type='part' 时必填，'whole' 时必须为空**（CHECK） |
| axis_type | TEXT | R | `structure` 结构事实 / `design_feature` 设计特征 / `intent` 设计意图 |
| scope | TEXT | R | `family` 品牌家族 / `model` 本型号 |
| body | TEXT | R | 描述正文（一句一事） |
| evidence_asset_ids | TEXT | R | JSON 数组，**≥1 条**：支撑本描述的素材（NFR-6 文字溯源） |
| source_ids | TEXT | O | JSON 数组，引用的文档来源 |
| confirm_status | TEXT | R | 同 §3.2 |
| version | INTEGER | R | 默认 1，飞轮期启用 |
| created_at / updated_at | TEXT | R | |

### 3.6 confirm_log 确认记录（只增不改）

| 字段 | 类型 | 约束 | 说明 |
|---|---|---|---|
| id / op_id | TEXT | R | op_id：同一次批量操作共用 |
| object_type | TEXT | R | vehicle/asset/source/fact/description |
| object_id | TEXT | R | |
| field | TEXT | R | 被确认/修改的字段名 |
| machine_value | TEXT | R | 机器原值（JSON 文本），**撤销依据** |
| confirmed_value | TEXT | R | 确认后的值（JSON 文本） |
| method | TEXT | R | `single` / `batch` / `auto`（T1 自证批量抽查路径） |
| confirmed_at / confirmed_by | TEXT | R | confirmed_by 默认 `user` |

触发器强制：UPDATE/DELETE 一律 ABORT。确认动作由访问层 `confirm()` 完成：写一条日志 + 更新目标字段；`undo()` 恢复 machine_value。

### 3.7 vocab 词表（辅助配置表）

| 字段 | 说明 |
|---|---|
| id | 部位 slug（bumper/headlamp/grille/step/fender/mirror/sunvisor/skirt/fluid_window/width_pole/brand_zone/paint/other） |
| type | 仅 `part`（后续可扩） |
| term | 中文词（附录 B v0 全量预填） |
| status | `active` / `retired`（词表可退役不可删） |

## 4. 枚举取值表

### 4.1 view_angle 视角（单枚举，D7）

| 值 | 中文 | 说明 |
|---|---|---|
| hero_lf / hero_rf | 左前/右前 3/4 主视角 | 主视角图；特征线页（FR-3）必须 hero_lf/hero_rf |
| front / rear | 正前 / 正后 | |
| side_l / side_r | 左侧 / 右侧 | |
| ortho_sheet | 三视图图版 | **v0.1 补记**：宣传册单图含多个正交视，经裁图拆分为 front/side/rear |
| detail | 局部特写 | 外源特写与内生裁图均用此值，性质由 kind 区分 |
| interior | 内饰 | **范围外·归档**：只路由不分析；P2 情绪版意象图候选 |
| scene | 场景图 | 同上，另可作封面/主视觉候选 |
| nameplate | 铭牌/Logo 特写 | 闭集对号最强证据 |

### 4.2 asset_nature 素材性质
`render` 官方渲染（比例可能失真，不可当实拍用） / `official_photo` 官方宣传照 / `real_photo` 实拍 / `report_screenshot` 旧报告截图

### 4.3 quality_flags 质量标记
`blur` 模糊 / `overexposed` 过曝 / `occluded` 遮挡 / `cluttered` 背景杂乱 / `watermarked` 有水印（水印大图排版不可用，确认时人工把关）

### 4.4 license 授权（挂来源，D5）
`client_provided` 甲方授权 / `self_captured` 自摄 / `web_official` 网络-官方渠道 / `web_third_party` 网络-第三方（待确认）。报告只允许引用授权通过的来源。

### 4.5 facts.field_key 起步清单
`curb_weight` 整备质量 / `engine_power` 额定功率 / `cab_type` 驾驶室形式 / `axle_config` 驱动形式 / `overall_dimensions` 外廓尺寸 / `payload` 载重或吨位级——可扩展，不入枚举强约束。

## 5. 文件目录约定

```
data/
├── equiplens.db                     # SQLite
└── assets/<vehicle_id>/
    ├── originals/<asset_id>.<ext>   # 原图，写入后不可覆盖
    └── crops/<asset_id>.<ext>       # 裁图，由访问层从原图派生
```

- file_path 存相对 data/ 的 POSIX 风格路径，跨目录迁移不碎；
- 原图不可变由访问层 `save_original()` 强制：目标文件已存在即拒绝；
- 镜像翻转等修图只发生在排版渲染阶段，永不改原图文件。

## 6. 派生状态定义（只查不存，D3/D9）

| 派生量 | 规则 |
|---|---|
| **L0** | 无 confirmed 主视角（hero_lf/hero_rf）或正侧（side_l/side_r）素材 |
| **L1** | 有 confirmed hero（任一）**或** confirmed 正侧（任一） |
| **L2** | L1 且 有 confirmed front/rear 且 confirmed 带部位裁图 ≥2（其中 ≥1 属前脸组：bumper/headlamp/grille） |
| **L3** | L2 且 front、rear、side、interior 齐 且 confirmed 裁图 ≥4 |
| 完备度计算基数 | `binding_status='confirmed' AND confirm_status='confirmed'` 的素材；provisional/unbound 不计 |
| 槽位状态 | 有·已确认 / 有·待确认 / 缺失——按部位查询 confirmed/provisional 裁图得出 |
| 待归号池 | `binding_status='unbound'` 的素材集合（即 PRD FR-1.1"待确认"分组） |

## 7. MVP 激活范围

- binding_evidence 当前仅激活 `self_derived`（内生裁图）与 `human`（人工对号）；`region_match`、`co_occurrence_*` 随 P1.5 联网检索启用——枚举现在收全，避免将来改约束；
- 批量确认（method=batch）当前仅用于视角/质量/对号等高置信结构标签；描述永远逐条；
- word 词表扩展入口：vocab 表 `status` 字段，退役不删除。

## 8. 测试分层与状态

| 层 | 内容 | 依赖 | 状态 |
|---|---|---|---|
| 第一档 | schema 合法性（含负例）、不变量（触发器/CHECK/访问层）、往返一致、派生查询正确性 | 全合成数据，零模型调用 | **本次执行，见测试报告** |
| 第二档 | 拟真校验：真实图片 + 人工标注标准答案 | 产品负责人提供 3–5 张图 + 标注（约 0.5–1 小时） | 待素材 |

## 9. 修订记录

| 版本 | 修改 |
|---|---|
| v0.1 | 初版：按 2026-10-10 讨论定稿六表+vocab、三不变量、派生规则；补记 ortho_sheet 枚举值（宣传册三视图图版经裁图拆分） |
