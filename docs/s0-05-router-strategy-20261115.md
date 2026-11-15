# S0-05 Router 策略：同义改写脆弱怎么解

> 背景：规则版 router 在调参集 28/28，但未见 holdout 仅 7/14；LLM 无 context 时 holdout 9/14，
> hard 判定 13/14，target 粒度仍错。见 [`badcases/S0-05-session.md`](badcases/S0-05-session.md) BC-S05-001/002。
> 结论：**不靠“加同义词/加关键词”解决**；用语义 router + 动作 schema + 会话上下文 + 规则守卫 + 歧义提问。

## 1. 根因拆解（不是“词不够多”）

| 根因 | 表现 | 例子 |
|---|---|---|
| 词法规则只认显式词 | 换个说法就漏 | “全要正面”没有“正脸”；“同款再来三张”没有“再加” |
| 缺会话上下文 | 分不清“同款加图”与“加车型” | “补两台这个型号” |
| 动作边界模糊 | target 粒度错 | `fill.quota`（同型号加图） vs `plan.add_targets`（加新车型） |
| 硬/软混在一起 | 把约束当打断 | “不要挂车”被当成 hard 重启 |
| 安全策略缺失 | 删除/替换误判 | “全都换成进口的”差点 reset |

## 2. 策略：四层，不写领域同义词表

### 2.1 第一层：LLM 语义提议（主）

- 输入 = 用户原话 + **context digest**；
- 输出 JSON：`{hard, targets[], destructive, confirm, enforce, confidence, evidence}`；
- `targets` 只能取**动作 schema**（不是品牌/车型表）：
  `fetch.filters.views / fetch.filters.quality / fetch.parts / fill.quota /
   plan.add_targets / plan.negative / verify.blacklist / fill.replace /
   scope.ratio / plan.quantity / plan.configuration / session.reset /
   delivered.remove / delivered.replace / session.pause / session.resume`
- 每个 target 给一句**语义定义**（见 §3），让模型按“要做什么”而不是“出现哪个词”判断；
- 要求 `evidence` 引用原话片段，便于审计。

### 2.2 第二层：context digest（解决“同款/这个/那个”）

```json
{
  "class": "沙漠牵引车",
  "targets": [{"model": "X3000", "count": 4}, {"model": "Zetros", "count": 2}],
  "delivered": {"count": 10, "last_round": 2},
  "last_patches": [{"target": "fetch.filters.views", "value": ["front"]}],
  "preferences": {"views": ["front"]}
}
```

规则：
- “同款/这个型号/再来几张” + 已有 target → `fill.quota`；
- “再加两个品牌/把重汽加进来” → `plan.add_targets`；
- “第 N 张/那张” → 定位到 delivered 资产，再判 remove/replace；
- 无 context 且指代不清 → **不猜**，问 1 个问题。

### 2.3 第三层：规则守卫（确定性，保证安全）

| 守卫 | 动作 |
|---|---|
| target 不在白名单 | 丢弃；若为空 → 提问 |
| `scope.ratio / plan.quantity / plan.configuration / session.reset` | 强制 `hard=True, enforce=hard` |
| `plan.negative` | 强制 `enforce=hard`，`hard=False`（约束硬、打断软） |
| `delivered.remove/replace` | 文本有“第 N 张/型号”等明确目标 → `confirm=False`；否则 `confirm=True` |
| 文本含“删/换/重来”但 LLM 说 soft | 升级为 destructive 检查；无法确认目标 → 提问 |
| LLM 与规则不一致 | **取更保守**（hard/confirm 优先） |
| 多 target >3 或 confidence <0.65 | 先问 1 个问题，不执行 |

### 2.4 第四层：歧义提问（最多 1 个）

- 只问“二选一/三选一”，带默认；
- 例：“你是想给现有 X3000 再加图（fill.quota），还是新增车型（plan.add_targets）？”
- 回答后走同一 patch 管线；不回答不阻塞，可按默认/放弃本轮。

## 3. 动作语义（给模型的定义，不是实体表）

| target | 定义 | 典型说法 |
|---|---|---|
| `fetch.filters.views` | 换/加拍摄角度 | 正脸、侧面、45 度、车尾 |
| `fetch.filters.quality` | 清晰度/水印/分辨率 | 高清、别带水印 |
| `fetch.parts` | 指定部件细节 | 前脸格栅、保险杠、吊臂 |
| `fill.quota` | **现有型号**加图/加数量 | 同款再来三张、补两台这个型号 |
| `plan.add_targets` | 增加**新品牌/新车型** | 把重汽加进来、再找陕汽 |
| `plan.negative` | 排除品牌/挂车/内饰 | 不要挂车、去掉北奔 |
| `verify.blacklist` | 单张图/单个资产判错 | 第 3 张不是沙漠版 |
| `fill.replace` | 用新图替换错误图 | 换一张对的 |
| `scope.ratio` | 改精确/邻近比例或范围 | 只要精确、多来点邻近 |
| `plan.quantity` | 改总量 | 数量改成 12 台、加到 14 |
| `plan.configuration` | 改驱动/构型 | 6×6 换 8×8 |
| `session.reset` | 整批重来 | 全部重来、重新选 |
| `delivered.remove/replace` | 删/换**已交付**资产 | 删掉第 2 张、第 1 张换掉 |

## 4. 模型与成本

- 主用 `deepseek-flash`（一次 ~¥0.001）；
- `confidence < 0.6` 或规则冲突 → 允许**一次**升级到更强模型（如 `v4-pro`），仍不确定则提问；
- 不把“更大模型”当主解：target 错误主要来自缺上下文，不是参数不够。

## 5. 评估：按“改写类型”分层，而不是一个总分

新 holdout（**不复用已看过的 14 条**）建议 30 条，分层：

| 层 | 数量 | 例子 |
|---|---|---|
| A 同义改写 | 10 | 全要正面 / 同款再来三张 / 补两台 |
| B 指代/省略 | 8 | 这个 / 那个 / 再加点 / 换掉它 |
| C 多意图 | 4 | 要正脸，再加两台，别要北影 |
| D 删除/替换（明确 vs 模糊） | 4 | 删掉第 2 张 / 删掉一张 |
| E 范围/数量/构型 | 4 | 只要沙漠版 / 数量改 12 / 6×6 换 8×8 |

指标（安全优先）：
- destructive 精确率/召回率 **100%**（不允许误删/误 reset）；
- hard 判定 ≥90%；
- target exact ≥80%（分层看 A/B 最弱）；
- 误提问率 ≤10%（不该问的别问）；
- 延迟/成本在预算内。

对比 4 个变体：规则版、LLM 无 context、LLM+context、LLM+context+守卫。
**新一轮 holdout 只用于最终验收，不参与调参**；调参用 dev 集，避免再次“28/28 过拟合”。

## 6. 失败处理与学习

- 每次错路由 → 登记 `BC-S05-xxx`，标注层/根因；
- 修正方式：**改 prompt 的动作定义 + 加 few-shot 例子**，不加关键词表；
- few-shot 例子来自真实错误（如“补两台这个型号”→fill.quota），只作为语义示例，不作为实体表；
- 每轮调参后必须在**新** holdout 上复测；同一 holdout 只看一次。

## 7. 接下来做什么（M3.1–M3.5）

| 步骤 | 内容 | 产出 |
|---|---|---|
| M3.1 | `session_router.py`：LLM 提议 + 守卫 + context digest | 可单测（fake LLM） |
| M3.2 | 动作 schema + prompt（含 6–8 个 few-shot） | prompt 版本 v1 |
| M3.3 | dev 集 30 条（临时）+ 4 变体对比 | 错误分层表 |
| M3.4 | 新 holdout 20–30 条，只跑一次 | 验收报告 |
| M3.5 | 接入 `Session.interrupt`，替换规则版默认；规则版保留兜底 | 状态机 + 单测 |

验收门槛：destructive 100%、hard ≥90%、target ≥80%、误提问 ≤10%；达不到就继续 prompt 迭代，不放宽安全门槛。

## 8. 不做什么

- 不写“同义词→target”的领域词表（政策禁止，且解决不了指代/多意图）；
- 不让规则单独决定删除/替换；
- 不在同一个 holdout 上反复调参；
- 不把“更大模型”当唯一方案。
