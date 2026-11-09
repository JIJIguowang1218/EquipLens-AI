# 检索前任务单：20 个扩展案例（v0.2，广度测试）

| 属性 | 内容 |
|---|---|
| 阶段 | 检索前（pre-retrieval） |
| 模块 | L1.5 任务单 |
| 测试 | 纸面测试（breadth-20） |
| 日期 | 2026-11-09 |
| 标签 | `pre-retrieval`、`task-brief`、`breadth-20`、`stability` |

> 只写检索前。具体车型、库内命中、外网结果一律不出现；具体车型留给“检索中”。

## 稳定性矩阵

| ID | 类目 | 工况 | 基础构型 | environment 层 | 区域要求 | 新部件 |
|---|---|---|---|---|---|---|
| C01 | 沙漠油田牵引车 | 沙漠工况（高温/沙尘/强辐射） | 6×6 重型卡车底盘/驾驶室 | 开 | 前脸（整体） | — |
| C02 | 重型吊车 | — | 汽车起重机/全地面起重机专用底盘 | — | 前脸（整体） | — |
| C03 | 矿用翻斗卡车 | 矿山工况（粉尘/重载/坡道） | 矿用自卸底盘 | 开 | — | — |
| C04 | 随车起重运输车 | — | 载货车底盘 + 吊机 | — | — | — |
| C05 | 重型长途牵引车 | — | 重型长途牵引车/重卡 | — | 前脸（整体） | — |
| C06 | 寒区矿山自卸车 | 寒区矿山（低温/冰雪/粉尘） | 矿用自卸底盘 | 开 | 前脸（整体） | 货厢 |
| C07 | 高原混凝土搅拌车 | 高原（低氧/低温/强紫外） | 重卡底盘 | — | 前脸（整体） | 搅拌罐 |
| C08 | 港口集装箱牵引车 | 港口（盐雾/潮湿） | 4×2/6×4 牵引车 | 开 | 前脸（整体） | 挡泥板 |
| C09 | 隧道施工装载机 | 隧道（粉尘/低净空） | 轮式装载机 | 开 | — | 铲斗、动臂、驾驶室、发动机罩 |
| C10 | 市政洒水车 | 城市道路 | 重卡底盘 | — | 前脸（整体） | 罐体 |
| C11 | 全地面起重机 | 通用 | 专用起重机底盘 | — | 前脸（整体） | 驾驶室、支腿、配重 |
| C12 | 履带起重机 | 通用 | 履带底盘 | — | — | 驾驶室、吊臂、履带架、配重 |
| C13 | 矿用宽体自卸车 | 矿山（粉尘/重载/坡道） | 宽体矿卡 | 开 | 前脸（整体） | 货厢 |
| C14 | 井下铲运机 | 井下（低净空/粉尘） | 地下 LHD | 开 | — | 铲斗、动臂、驾驶室、轮胎防护 |
| C15 | 林业抓木机 | 林区（坡地/枝桠） | 轮式/履带底盘 + 抓具 | 开 | — | 抓具、动臂、驾驶室、防护网 |
| C16 | 除雪车 | 雪/寒（低温/冰雪） | 重卡底盘 | 开 | 前脸（整体） | 除雪铲 |
| C17 | 机场除冰车 | 寒/机场（低温/除冰液） | 专用底盘 | 开 | 前脸（整体） | 驾驶室、除冰臂 |
| C18 | 油田修井机 | 油田（油污/风沙） | 重卡/专用底盘 | — | 前脸（整体） | 修井架 |
| C19 | 沙漠越野运输车 | 沙漠（高温/沙尘/强辐射） | 6×6/8×8 越野卡车 | 开 | 前脸（整体） | — |
| C20 | 压缩式垃圾车 | 城市道路 | 重卡底盘 | — | 前脸（整体） | 压缩箱 |

## 案例

### C01 沙漠油田牵引车

- 工况：沙漠工况（高温/沙尘/强辐射）
- 基础构型：6×6 重型卡车底盘/驾驶室（6×6）
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,strong)；防护栏(part,side_chassis,strong)；登车踏步(part,side_lower,strong)；大灯(part,front,conditional)；前轮拱(part,front,conditional)；格栅(part,front,conditional)；品牌区(part,front,none)
- 层级：exact → environment → platform → cross
- 备注：前脸是区域（整体线条/风格），大灯/保险杠同时是部件；不写具体车型。

### C02 重型吊车

- 工况：未给
- 基础构型：汽车起重机/全地面起重机专用底盘
- 部件：前脸（整体）(region,none)；车辆侧护板(part,side_chassis,none)；驾驶室后方侧护板(part,side_cab_rear,none)；登车踏步(part,side_lower,none)；格栅(part,front,none)；大灯(part,front,none)；保险杠(part,front_lower,none)
- 层级：exact → platform → cross
- 备注：无工况输入 → 不开 environment 层；侧护板两个位置必须拆开；词表缺 location 变体。

### C03 矿用翻斗卡车

- 工况：矿山工况（粉尘/重载/坡道）
- 基础构型：矿用自卸底盘
- 部件：登车踏步(part,side_lower,strong)；大灯(part,front,conditional)；后视镜(part,side_upper,conditional)
- 层级：exact → environment → platform → cross
- 备注：矿用自卸 vs 刚性矿卡有歧义，默认自卸并写 assumption；后视镜属于 side region。

### C04 随车起重运输车

- 工况：未给
- 基础构型：载货车底盘 + 吊机
- 部件：侧护板(part,side_chassis,none)；前轮拱(part,front,none)；登车踏步(part,side_lower,none)
- 层级：exact → platform → cross
- 备注：随车吊 vs 汽车吊有歧义；无工况；基础构型是“普通卡车 + 吊机”，踏步/驾驶室按卡车看。

### C05 重型长途牵引车

- 工况：未给
- 基础构型：重型长途牵引车/重卡（6×4）
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,none)；大灯(part,front,none)；登车踏步(part,side_lower,none)；前轮拱(part,front,none)
- 层级：exact → platform → cross
- 备注：“长途”是使用场景，不是环境特化 → 不开 environment 层；前脸为区域。

### C06 寒区矿山自卸车

- 工况：寒区矿山（低温/冰雪/粉尘）
- 基础构型：矿用自卸底盘
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,strong)；登车踏步(part,side_lower,strong)；大灯(part,front,conditional)；后视镜(part,side_upper,conditional)；货厢(part,rear_body,strong,new)；侧护板(part,side_chassis,conditional)
- 层级：exact → environment → platform
- 备注：寒区工况对货厢/踏步/保险杠有设计驱动；货厢为 taxonomy 新部件。

### C07 高原混凝土搅拌车

- 工况：高原（低氧/低温/强紫外）
- 基础构型：重卡底盘
- 部件：前脸（整体）(region,none)；登车踏步(part,side_lower,none)；搅拌罐(part,rear_body,none,new)；侧护板(part,side_chassis,none)；保险杠(part,front_lower,none)
- 层级：exact → platform
- 备注：工况存在但不驱动这些外观件 → 不开 environment 层；这是“有环境但无关”的对照。

### C08 港口集装箱牵引车

- 工况：港口（盐雾/潮湿）
- 基础构型：4×2/6×4 牵引车
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,conditional)；登车踏步(part,side_lower,conditional)；后视镜(part,side_upper,none)；挡泥板(part,side_lower,conditional,new)
- 层级：exact → environment → platform
- 备注：盐雾对保险杠/踏步/挡泥板有防腐驱动；挡泥板为 taxonomy 新部件。

### C09 隧道施工装载机

- 工况：隧道（粉尘/低净空）
- 基础构型：轮式装载机
- 部件：铲斗(part,front_lower,strong,new)；动臂(part,front_upper,strong,new)；驾驶室(part,front_upper,conditional,new)；发动机罩(part,rear_upper,conditional,new)；登车踏步(part,side_lower,none)
- 层级：exact → environment → platform
- 备注：隧道工况驱动铲斗/动臂/驾驶室防护；多个新部件。

### C10 市政洒水车

- 工况：城市道路
- 基础构型：重卡底盘
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,none)；罐体(part,rear_body,none,new)；侧护板(part,side_chassis,none)；登车踏步(part,side_lower,none)
- 层级：exact → platform
- 备注：城市不是外观设计约束 → 不开 environment 层；罐体为 taxonomy 新部件。

### C11 全地面起重机

- 工况：通用
- 基础构型：专用起重机底盘
- 部件：前脸（整体）(region,none)；驾驶室(part,front_upper,none,new)；支腿(part,side_lower,none,new)；登车踏步(part,side_lower,none)；配重(part,rear_body,none,new)
- 层级：exact → platform
- 备注：无工况；专用底盘，踏步/驾驶室不能按普通卡车判。

### C12 履带起重机

- 工况：通用
- 基础构型：履带底盘
- 部件：驾驶室(part,front_upper,none,new)；吊臂(part,front_upper,none,new)；履带架(part,side_lower,none,new)；登车踏步(part,side_lower,none)；配重(part,rear_body,none,new)
- 层级：exact → platform
- 备注：无工况；履带底盘与轮式底盘不可互借。

### C13 矿用宽体自卸车

- 工况：矿山（粉尘/重载/坡道）
- 基础构型：宽体矿卡
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,strong)；登车踏步(part,side_lower,strong)；大灯(part,front,conditional)；货厢(part,rear_body,strong,new)；侧护板(part,side_chassis,conditional)
- 层级：exact → environment → platform
- 备注：矿山工况驱动保险杠/踏步/货厢；货厢为新部件。

### C14 井下铲运机

- 工况：井下（低净空/粉尘）
- 基础构型：地下 LHD
- 部件：铲斗(part,front_lower,strong,new)；动臂(part,front_upper,strong,new)；驾驶室(part,front_upper,conditional,new)；登车踏步(part,side_lower,none)；轮胎防护(part,side_lower,conditional,new)
- 层级：exact → environment → platform
- 备注：井下工况驱动铲斗/动臂/驾驶室；轮胎防护为新部件。

### C15 林业抓木机

- 工况：林区（坡地/枝桠）
- 基础构型：轮式/履带底盘 + 抓具
- 部件：抓具(part,front_upper,strong,new)；动臂(part,front_upper,strong,new)；驾驶室(part,front_upper,conditional,new)；登车踏步(part,side_lower,none)；防护网(part,front_upper,conditional,new)
- 层级：exact → environment → platform
- 备注：林区工况驱动抓具/防护网；多个新部件。

### C16 除雪车

- 工况：雪/寒（低温/冰雪）
- 基础构型：重卡底盘
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,conditional)；除雪铲(part,front_lower,strong,new)；登车踏步(part,side_lower,conditional)；大灯(part,front,conditional)
- 层级：exact → environment → platform
- 备注：雪/寒工况驱动除雪铲/踏步/保险杠；除雪铲为新部件。

### C17 机场除冰车

- 工况：寒/机场（低温/除冰液）
- 基础构型：专用底盘
- 部件：前脸（整体）(region,none)；驾驶室(part,front_upper,conditional,new)；除冰臂(part,front_upper,strong,new)；登车踏步(part,side_lower,conditional)；大灯(part,front,conditional)
- 层级：exact → environment → platform
- 备注：寒/机场工况驱动除冰臂/驾驶室；除冰臂为新部件。

### C18 油田修井机

- 工况：油田（油污/风沙）
- 基础构型：重卡/专用底盘
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,none)；修井架(part,rear_body,conditional,new)；登车踏步(part,side_lower,none)；侧护板(part,side_chassis,none)
- 层级：exact → platform
- 备注：油田工况对修井架有防腐/防风影响，但对外观覆盖件弱 → 不开 environment 层；修井架为新部件。

### C19 沙漠越野运输车

- 工况：沙漠（高温/沙尘/强辐射）
- 基础构型：6×6/8×8 越野卡车（6×6/8×8）
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,strong)；登车踏步(part,side_lower,strong)；前轮拱(part,front,strong)；侧护板(part,side_chassis,strong)；大灯(part,front,conditional)
- 层级：exact → environment → platform
- 备注：沙漠工况驱动保险杠/踏步/轮拱/侧护板；与 C01 同类但用途不同。

### C20 压缩式垃圾车

- 工况：城市道路
- 基础构型：重卡底盘
- 部件：前脸（整体）(region,none)；保险杠(part,front_lower,none)；压缩箱(part,rear_body,none,new)；登车踏步(part,side_lower,none)；侧护板(part,side_chassis,none)
- 层级：exact → platform
- 备注：城市不是外观设计约束；压缩箱为新部件。
