# S0-01 输入识别：badcase 明细

> 上游：[`README.md`](README.md)（编号与状态规则）。
> 输入均为**测试数据**（`[test]`），只用于复现，不进入生产默认值。
> 基准来源：`tmp/s0-probe-20261115/bench-review-v3.md`（临时资产，未入库；复现需申请）。

## BC-S01-001

- **状态**：verified（生产 `taskspec.py` + 50 条全量回归）
- **现象**：“再配两台同类参考车”被记成 `quantity.backup=2`，`scope=null`。
- **触发输入（[test]）**：`这是我在展会上拍的图，型号牌上写着 X3000，帮我把这个型号找全，再配两台同类参考车`
- **期望**：先确认类目（blocking，1 个问题）；`models_provided=[X3000]`；
  `scope={mode:"mixed", adjacent:2}`；`quantity.primary=null`（X3000 的已知版本按实际检索 1..n 台）；
  `backup` 保持 null。
- **实际**：`quantity.backup=2`、`scope=null`；类目提问正确。
- **根因**：TaskSpec 没有区分“备选（同型号备用交付）”与“邻近参考（同类/跨类对比）”，
  prompt 把“同类参考”映射到了 backup。
- **下一步**：`scope` 与 `backup` 分流——“参考/同类/对比”→“scope.adjacent”；
  “备选/备用/备份”→“quantity.backup”；“再加/再补 N 台（同类）”→“delta”。
- **关联**：bench S-03；决策台账 S0-01。

## BC-S01-002

- **状态**：verified（生产 `taskspec.py` + 50 条全量回归）
- **现象**：部件词“前脸格栅”被记成 `views=["front"]`，`parts=[]`。
- **触发输入（[test]）**：`上次那批不行，换一批，重点看前脸格栅，再加两台徐工的吊车`
- **期望**：`parts=["前脸格栅"]`、`views=[]`；`intent=modify`、`delta=2`、`brands_include=["徐工"]`。
- **实际**：`views=["front"]`、`parts=[]`；其余正确。
- **根因**：视角词与部件词的判定规则不够硬，“格栅”被当成前脸视角。
- **下一步**：部件词表（保险杠/格栅/吊臂/支腿/踏步…）优先判 `parts`；
  只有“正脸/侧面/45 度/车尾/顶部”进 `views`。
- **关联**：bench S-05。

## BC-S01-003

- **状态**：verified（生产 `taskspec.py` + 50 条全量回归）
- **现象**：“沙漠车”未归一为“沙漠牵引车”。
- **触发输入（[test]）**：`沙漠车 10 个 6x6 要外国牌子的 国内外都行 别给我内饰 高清`
- **期望**：`class="沙漠牵引车"`、`class_raw="沙漠车"`、`class_aliases=["沙漠车"]`。
- **实际**：`class="沙漠车"`。
- **根因**：别名归一依赖模型自由发挥，没有最小别名规则。
- **下一步**：解析后做一次“类目规范化”：常见口语（沙漠车/随车吊/铲车/翻斗车…）
  映射到 brief 使用的标准类目；映射表放**测试/配置**而非主代码词表，或由 LLM 归一后记录 alias。
- **关联**：bench S-06。

## BC-S01-004

- **状态**：verified（生产 `taskspec.py` + 50 条全量回归）
- **现象**：“至少 3 台奔驰或沃尔沃”没有产出品牌配额。
- **触发输入（[test]）**：`必须 10 台，其中至少 3 台是奔驰或沃尔沃，其他随便`
- **期望**：`preferences.brand_quota={"brands":["奔驰","沃尔沃"],"min":3,"of":10}`；
  **自动估计，不向用户确认**；若同时缺类目，只把类目问题发出去（合并为 1 次确认）。
- **实际**：`brand_quota` 缺失、`foreign_ratio=null`；类目提问正确。
- **根因**：TaskSpec 只有 `foreign_ratio`，没有“指定品牌的最低台数”字段。
- **下一步**：新增 `brand_quota`；解析规则：`至少 N 台 + 品牌列表 + 总数` → `{brands, min:N, of:M}`；
  执行层按软配额处理（优先满足，达不到在交付里标 `brand_quota 2/3`）。
- **关联**：bench N-01；决策台账 S0-01。

## BC-S01-005

- **状态**：verified（生产 `taskspec.py` + 50 条全量回归）
- **现象**：`policy.hard/soft` 输出自由词（`domestic_only`、`electric_only`、`road_legal`、
  `constraints.exclude`、`quantity_backup`），无法被程序稳定消费。
- **触发输入（[test]）**：`8 台，必须都是国产` / `10 台，只要电动车` / `10 台，不要带挂车…`
- **期望**：固定枚举：
  `quantity` / `class` / `brands_include` / `brands_exclude` / `models_pinned` /
  `constraints.exclude` / `configuration` / `environment`；
  未支持的（国产/电动/能上路）进 `unknowns`，不要进 policy。
- **实际**：自由词混入。
- **根因**：prompt 只给了示例，没有给“允许值枚举”。
- **下一步**：TaskSpec schema 固定 enum；解析后做一次校验，非法值降级到 `unknowns`。
- **关联**：bench N-07/N-22。

## BC-S01-006

- **状态**：by-design（2026-11-15 拍板）
- **现象**：“再找 2 台同类参考”里“同类”到底指同型号还是邻近类目，无法判定。
- **触发输入（[test]）**：`再找 2 台同类的参考`
- **两种读法**：① 同型号/同车系再加 2 台（`delta=2`）；② 邻近类目参考 2 台（`scope.adjacent=2`）。
- **规则（已拍板）**：有 session context 时按“上一批同类”→ `scope.adjacent`；
  无 context 且明确说“加”才 `delta`；两者都不明确 → 1 个 blocking 问题
  （选项：同型号再加 / 邻近类目参考）。v0.4 回归 R-08/R-09 已验证两条分支。
- **关联**：bench N-28。

## BC-S01-013

- **状态**：verified（生产 `taskspec.py`）
- **现象**：文本只有“(图)”没有真图时，仍产出 `models_provided=[{"image":true}]`（无 model）。
- **触发输入（[test]）**：`分析一下这个车型（图）`
- **期望**：不编造 `models_provided`；缺类目/缺图 → 1 个 blocking 问题。
- **实际**：产出了空 model 的 provided 条目。
- **修复**：`taskspec.normalize()` 过滤 `model` 为空的 provided 条目；单测
  `test_provided_without_model_dropped`。
- **关联**：bench N-16。

## BC-S01-007（by-design）

- **状态**：by-design
- **现象**：输入没有类目时，parser 提 1 个问题（blocking）。
- **结论**：**正确**。缺类目无法规划；提问 1 次优于猜一个类目硬跑。
- **触发**：`必须 10 台…` / `推荐 8 台，看着办` 等 22 条基准输入。

## BC-S01-008（by-design）

- **状态**：by-design
- **现象**：“不要这个型号，换一个”被系统自动从同类另选，未二次确认。
- **结论**：**正确**（产品负责人 2026-11-15 确认）。用户未指定替换型号时，系统应自行从同类中另选；
  只有“删除/替换**已交付**内容”才需要确认（破坏性、不可逆）。
- **关联**：bench N-29。

## BC-S01-009（by-design）

- **状态**：by-design
- **现象**：文本只有“(图)”但没真图时，parser 要求补图/补型号。
- **结论**：**正确**，不得假装有图。
- **关联**：bench N-16/N-17。

## BC-S01-010（verified）

- **状态**：verified（v0.2）
- **现象**：class 混入 environment（“电动叉车（仓储物流工况）”）。
- **修复**：TaskSpec 拆 `environment`/`configuration`；v0.2 复测 10/10 历史输入拆出 environment。
- **输入（[test]）**：历史 10 条原始任务单。

## BC-S01-011（verified）

- **状态**：verified（v0.2）
- **现象**：modify“再加两台”被当新任务 `primary=2`。
- **修复**：`quantity.delta`；S-05 复测 `delta=2`、`primary=null`。

## BC-S01-012（verified）

- **状态**：verified（v0.2）
- **现象**：“最好有齐格勒/卢森堡亚”被当硬性 `brands_include`。
- **修复**：`preferences.soft_brands`；S-10 复测 soft，include 为空。

## 附：与决策台账的关系

- 本册只记“实现/行为”问题；外部意见的采纳与否在
  [`docs/external/doubao-consult-decisions.md`](../external/doubao-consult-decisions.md)。
- 修复顺序建议：BC-S01-001（scope/backup）→ 004（brand_quota）→ 005（enum）→ 002/003；
  006 已拍板；007–009 不再改动。
- **v0.4 定向回归**：10 条新输入（未复用旧 50 条）10/10 通过；
- **生产化 + 全量回归**：`src/equiplens/taskspec.py`（19 条单测）+ 50 条全量回归 50/50；
  001–005 升为 `verified`，013 新增并修复。
