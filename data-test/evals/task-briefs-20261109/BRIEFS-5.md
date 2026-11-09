# 检索前任务单：5 个深度案例（v0.2）

| 属性 | 内容 |
|---|---|
| 阶段 | 检索前（pre-retrieval） |
| 模块 | L1.5 任务单 |
| 测试 | 纸面测试（deep-5） |
| 日期 | 2026-11-09 |
| 标签 | `pre-retrieval`、`task-brief`、`deep-5`、`region-vs-part`、`part-location`、`base-platform` |

> 只写检索前。具体车型、库内命中、外网结果一律不出现。

## 案例 1：沙漠油田牵引车（C01）

**输入**：沙漠牵引车（前脸、登车踏步、大灯、前轮拱、防护栏、保险杠）

**假设**

| 字段 | 值 | 置信 |
|---|---|---|
| 工况 | 沙漠工况（高温/沙尘/强辐射） | 0.85 |
| 基础构型 | 6×6 重型卡车底盘/驾驶室 | 0.80 |
| 驱动/配置 | 6×6 | — |
| 版面 | 12 车 + 2 部件页 | — |

**要求**

| 粒度 | 部件/区域 | 位置 | 相关性 | 机制 | 视角 | 验收 |
|---|---|---|---|---|---|---|
| region | 前脸（整体） | — | none | — | front / hero_45 | C |
| part | 保险杠 | front_lower | strong | 沙石冲击、接近角 | front / hero_45 | A |
| part | 防护栏 | side_chassis | strong | 沙石、防撞、法规 | side / rear | B |
| part | 登车踏步 | side_lower | strong | 防滑、沙尘、离地高 | side / hero_45 | B |
| part | 大灯 | front | conditional | 沙尘、强光、灯罩防护 | front / hero_45 | A |
| part | 前轮拱 | front | conditional | 离地间隙、沙石 | side / hero_45 | A |
| part | 格栅 | front | conditional | 进气防尘 | front | A |
| part | 品牌区 | front | none | — | front | A |

**层级**：exact → environment → platform → cross（逐层耗尽才开，不预设每层数量）

**备注**：前脸是区域（整体线条/风格），大灯/保险杠同时是部件；不写具体车型。

**评审意见（2026-11-09）**

- 车辆侧护板是前后轮之间的覆盖件结构，位置要单独记。
- 前脸是覆盖件整体线条走势与风格描述，和部件的描述不是一个结构。
- 有工况的类目可以开 environment，但不能预设每层数量。

**v0.2 修订**

- 增加 location 维度
- 增加 region_requirements
- 删除每层配额

---

## 案例 2：重型吊车（C02）

**输入**：重型吊车（驾驶室后方侧护板、车辆侧护板、登车踏步、前脸）

**假设**

| 字段 | 值 | 置信 |
|---|---|---|
| 工况 | 未给（不开 environment 层） | — |
| 基础构型 | 汽车起重机/全地面起重机专用底盘 | 0.60 |
| 版面 | 12 车 + 1 部件页 | — |

**要求**

| 粒度 | 部件/区域 | 位置 | 相关性 | 机制 | 视角 | 验收 |
|---|---|---|---|---|---|---|
| region | 前脸（整体） | — | none | — | front / hero_45 | C |
| part | 车辆侧护板 | side_chassis | none | — | side | B |
| part | 驾驶室后方侧护板 | side_cab_rear | none | — | side / rear | B |
| part | 登车踏步 | side_lower | none | — | side / hero_45 | B |
| part | 格栅 | front | none | — | front | A |
| part | 大灯 | front | none | — | front / hero_45 | A |
| part | 保险杠 | front_lower | none | — | front / hero_45 | A |

**层级**：exact → platform → cross（逐层耗尽才开，不预设每层数量）

**备注**：无工况输入 → 不开 environment 层；侧护板两个位置必须拆开；词表缺 location 变体。

**评审意见（2026-11-09）**

- 驾驶室后方侧护板和车辆侧护板不是一个位置。
- 无工况的类目先按推荐来，不要硬编工况。

**v0.2 修订**

- 同名部件按 location 拆分
- 无工况时不强开 environment 层

---

## 案例 3：矿用翻斗卡车（C03）

**输入**：矿用翻斗卡车（登车踏步、大灯、后视镜）

**假设**

| 字段 | 值 | 置信 |
|---|---|---|
| 工况 | 矿山工况（粉尘/重载/坡道） | 0.75 |
| 基础构型 | 矿用自卸底盘 | 0.65 |
| 版面 | 12 车 + 1 部件页 | — |

**要求**

| 粒度 | 部件/区域 | 位置 | 相关性 | 机制 | 视角 | 验收 |
|---|---|---|---|---|---|---|
| part | 登车踏步 | side_lower | strong | 粉尘、防滑、离地高 | side / hero_45 | B |
| part | 大灯 | front | conditional | 粉尘、飞石、灯罩防护 | front / hero_45 | A |
| part | 后视镜 | side_upper | conditional | 粉尘、振动、宽体 | front / side | B |

**层级**：exact → environment → platform → cross（逐层耗尽才开，不预设每层数量）

**备注**：矿用自卸 vs 刚性矿卡有歧义，默认自卸并写 assumption；后视镜属于 side region。

**评审意见（2026-11-09）**

- 矿用自卸和刚性矿卡的区分很好。

**v0.2 修订**

- 保留歧义 assumption，不加追问

---

## 案例 4：随车起重运输车（C04）

**输入**：随车吊车（侧护板、前轮拱、登车踏步）

**假设**

| 字段 | 值 | 置信 |
|---|---|---|
| 工况 | 未给（不开 environment 层） | — |
| 基础构型 | 载货车底盘 + 吊机 | 0.60 |
| 版面 | 12 车 + 1 部件页 | — |

**要求**

| 粒度 | 部件/区域 | 位置 | 相关性 | 机制 | 视角 | 验收 |
|---|---|---|---|---|---|---|
| part | 侧护板 | side_chassis | none | — | side | B |
| part | 前轮拱 | front | none | — | side / hero_45 | A |
| part | 登车踏步 | side_lower | none | — | side / hero_45 | B |

**层级**：exact → platform → cross（逐层耗尽才开，不预设每层数量）

**备注**：随车吊 vs 汽车吊有歧义；无工况；基础构型是“普通卡车 + 吊机”，踏步/驾驶室按卡车看。

**评审意见（2026-11-09）**

- 随车吊是普通卡车搭载吊机，踏步和驾驶室造型与专用吊车很不一样。

**v0.2 修订**

- 增加 base_platform

---

## 案例 5：重型长途牵引车（C05）

**输入**：重型长途卡车（前脸、保险杠、大灯、登车踏步、前轮拱）

**假设**

| 字段 | 值 | 置信 |
|---|---|---|
| 工况 | 未给（不开 environment 层） | — |
| 基础构型 | 重型长途牵引车/重卡 | 0.80 |
| 驱动/配置 | 6×4 | — |
| 版面 | 12 车 + 2 部件页 | — |

**要求**

| 粒度 | 部件/区域 | 位置 | 相关性 | 机制 | 视角 | 验收 |
|---|---|---|---|---|---|---|
| region | 前脸（整体） | — | none | — | front / hero_45 | C |
| part | 保险杠 | front_lower | none | — | front / hero_45 | A |
| part | 大灯 | front | none | — | front / hero_45 | A |
| part | 登车踏步 | side_lower | none | — | side / hero_45 | B |
| part | 前轮拱 | front | none | — | side / hero_45 | A |

**层级**：exact → platform → cross（逐层耗尽才开，不预设每层数量）

**备注**：“长途”是使用场景，不是环境特化 → 不开 environment 层；前脸为区域。

**评审意见（2026-11-09）**

- 基础构型会影响踏步/驾驶室的判断。

**v0.2 修订**

- 增加 base_platform
- 无工况不开 environment

---
