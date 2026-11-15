# S0-05 Session / Router：badcase 与测试记录

> 测试资产（临时，未入库）：`tmp/s0-05/`
> - `corpus.json`：28 条调参集（合成，覆盖 F1–F9 与破坏性）；
> - `holdout.json`：14 条**未参与调参**的 holdout（合成，测泛化）；
> - 规则版 `session.classify_text` vs LLM 版探针（`router_llm_probe.py`）。
> 状态：M2 单测完成；M3 router 仍在选型，**未接入正式链路**。

## 结果总览

| 方法 | 调参集 28 | holdout hard | holdout targets | holdout 全对 |
|---|---|---|---|---|
| 规则版（调参后） | 28/28 | 11/14 | 7/14 | **7/14** |
| LLM（deepseek-flash，无 session context） | — | **13/14** | 9/14 | **9/14** |

**结论**：规则版在调参集上 100%，但 holdout 只有 7/14 —— 典型的过拟合/同义词脆弱；
LLM 的 hard 判定明显更稳（13/14），但 target 粒度仍会错（“同款更多图”被判成加车型）。
**单靠任一方法都不够**，M3 采用“LLM 提议 + 规则守卫 + 歧义提问”。

## BC-S05-001

- **状态**：open（M3 部分验证：dev30 规则 15/30，LLM+context 30/30；待新 holdout）
- **现象**：规则版对同义改写不敏感，holdout 7/14。
- **触发输入（[test]）**：`全要正面`（规则找不到“正脸”）、`同款再来三张`、`补两台这个型号`、
  `把重汽加进来`、`数量加到 14 台`。
- **期望**：分别识别为 views / fill.quota / fill.quota / plan.add_targets / plan.quantity。
- **根因**：规则依赖关键词；同义词/口语句式覆盖不了。
- **下一步**：LLM 提议 + 规则把同义映射到 target；规则只做守卫，不再单独决策。

## BC-S05-002

- **状态**：open（dev30 已通过，待新 holdout 确认）
- **现象**：LLM 把“同款更多图”判成 `plan.add_targets`，而不是 `fill.quota`。
- **触发输入（[test]）**：`同款再来三张`、`补两台这个型号`。
- **期望**：`fill.quota`（同一 target/model 加图）。
- **根因**：没有 session context（当前 target/model 不明），LLM 只能猜“加车型”。
- **下一步**：router 输入带 `current_targets/models` 摘要；“同款/这个型号”优先映射到 fill.quota。

## BC-S05-003

- **状态**：by-design（2026-11-15 拍板）
- **现象**：“第三张图错了，是公路版”是纠错，不是删除。
- **规则**：默认 **soft 纠错**——旧图标 `superseded`，补新图；
  只有用户明确“删掉/换掉”才走交付编辑；**交付前不物理删除**，用户可找回。
- **确认**：目标明确（如“第 3 张”“某个型号码”）→ **不弹确认**，直接降级+补；
  目标不明确（“删掉一张”“换掉那个”）→ 先问 1 个问题。
- **关联**：bench H-07；测试 `test_clear_destructive_no_confirm` / `test_ambiguous_destructive_asks`。

## BC-S05-004

- **状态**：by-design（2026-11-15 拍板）
- **规则**：`只要/仅限 + 环境/类目` → **hard scope**（任务定义变化）；
  `不要/排除 + 品牌/挂车/内饰` → **约束是 hard，打断是 soft**。
- **为什么“不要”是 soft 打断**：
  1. **约束强度（enforce）**：它是硬约束，必须排除，不能进候选/交付——`plan.negative` +
     FILL 过滤 + 下一轮负词，三处都生效；
  2. **打断类型（interrupt）**：它不是任务定义变化，不需要取消在途请求、重排配额；在下一个
     checkpoint 应用即可，避免浪费已抓图；
  3. 只有“改变范围/数量/构型”才 hard 打断，因为旧计划/配额作废。
- **两个轴**（以后一律分开说）：

| 说法 | 约束强度 | 打断类型 | 例子 |
|---|---|---|---|
| 要正脸 | soft | soft | 视角 |
| 不要挂车/北奔 | **hard**（必须排除） | **soft**（checkpoint 过滤） | 排除项 |
| 只要沙漠版 | **hard** | **hard**（重排） | 范围/类目 |
| 数量改 12 | **hard** | **hard** | 交付定义 |
| 删掉第 2 张 | hard（该资产不再交付） | soft（降级，不删除） | 交付编辑 |

- **关联**：bench H-08；测试 `test_negative_is_hard_constraint_soft_interrupt`。

## BC-S05-005

- **状态**：by-design（2026-11-15 拍板）
- **规则**：含“全部/全都/整批”+“换/重来”→ **hard + confirm**，先问 1 个问题
  （整批重来 / 只换范围），不自动 reset。
- **原因**：重大调整不可逆感强；即使底层只标 superseded，也应让用户确认意图。

## 参数设置与理由（本轮）

| 参数 | 取值 | 理由 |
|---|---|---|
| `max_rounds` | **5** | 典型会话 2–4 轮（改进 → 纠错 → 补充）；5 轮覆盖“加图 + 换 brand + 纠错 + 范围 + 收尾”；>5 状态陈旧、成本线性涨 |
| `delta_query_ratio` | **0.25** | 一轮 query 约 50 条；25% = ~12 条，够补 1 个品牌/2 个 target；超过应视为新任务 |
| `delta_fetch_ratio` | **0.20** | 抓取比查询更贵；20% 防止“多轮少量修改”反复抓全量 |
| 提问上限 | **1 条/轮** | 只对 destructive/歧义；避免打断疲劳 |
| 持久化 | **JSON** | 先跑通状态机；稳定后再评估 SQLite |
| 打断默认 | **soft**；仅范围/数量/构型/重置为 hard | 交付编辑目标明确时 soft（降级不删）；排除项约束 hard、打断 soft；soft 在 checkpoint 生效，不浪费已抓图 |

## 决策建议（M3 前）

1. 纠错类（BC-S05-003）默认 soft，只有“删/换已交付”才 hard+确认；
2. “只要/仅限 + 环境/类目”按 hard scope；纯“不要 + 品牌/挂件”按 soft negative；
3. “全部/整批 + 换/重来”先问 1 个问题，不自动 reset；
4. LLM router 必须带 `current_targets/models` 摘要，否则分不清“同款加图”与“加车型”；
5. 破坏性操作 100% 确认，LLM 与规则不一致时**以更保守的为准**。


## BC-S05-006

- **状态**：open（M4 前处理）
- **现象**：holdout H-14 “这个不够，再补”被判成 `plan.quantity`（hard），
  期望 `fill.quota`（soft，给现有型号加图）。
- **触发输入（[test]）**：`这个不够，再补`（context：X3000 已有 6 台）。
- **根因**：句子没有“台/数量”，但“再补”在规则上容易落到数量变更；
  与“同款再来三张”只差一个明确的“张/型号”。
- **建议**：无“台/数量”且 context 有 target → `fill.quota`；
  只有“台数/数量/总量 + 改/加到”才 `plan.quantity`。
- **纪律**：holdout 只跑一次，不据此调 prompt；下一轮在新 dev 集上修，再用**新** holdout 验收。
