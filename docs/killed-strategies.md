# 已毙 / 已收口策略登记（不许再提）

更新：2026-11-12  
用途：新会话、评审、封装前先看这里。**这些策略不再讨论、不排期、不"顺手补上"**；  
再提时必须按 §4 的重新开启条件走，否则一律回复"已毙，见本文件"。

> 与 `docs/CURRENT-ARCHITECTURE.md` §4 的关系：那里写"生产/实验/已收口"的总表，这里写**每条的判决、理由、证据**。  
> 判决只有三种：**毙**（不做）、**收口**（做了但停）、**归档**（代码/字段保留，不再读取）。

## 1. 判决表

| # | 策略 | 判决 | 日期 | 理由 / 证据 | 现在谁负责 |
|---|---|---|---|---|---|
| K1 | **三证②：部件-可见性（检索时计算）** | **归档·不许再提** | 2026-11-12 | 产品负责人决定：可见性判断挪到后面的**人机交互**（用户看图判断），检索侧不再算、不用它占槽/排序 | 后续人机交互阶段 |
| K2 | **三证③：改装 / 原厂状态** | **毙** | 2026-11-12 | 分类错误率高、边际效益低，不采纳；`Verification.origin` 恒 `unknown`，只作历史字段兼容 | 不做 |
| K3 | `part_views.json` 静态表（部件→视角） | 毙 | 2026-11-11 | 视角由用户看图判断，模型不因视角等待或过滤 | 人机交互 |
| K4 | `part_axes.json` 静态关系轴表 | 改为 brief 输出 | 2026-11-11 | 关系轴（exact/environment/platform/cross）由 `task-brief@v2` 按对象输出，不建静态表 | `skills/task-brief/` |
| K5 | 硬性"整车槽必须有 overview" / 硬性 part-only 拒绝 | 弃 | 2026-11-12 | `loop-p0` 10/12；`loop-p0b` 12/12 但交付构成被改变（丢 rank7/8/13/14）。现为 `part_only` 软标记 + 人审 | FILL 打标，人审 |
| K6 | body / tonnage 硬 guard | 弃 | 2026-11-12 | 激进版 precision 75% 但误杀 8 张目标图；保守版 68.2%；不采纳 | 不做 |
| K7 | Platform union / 百度默认启用 | 弃 | 2026-11-12 | 完整 loop 丢 HF8066、unknown 20→284；仅保留 `--platform-extra baidu` 实验开关 | 实验开关 |
| K8 | harvest 标题元数据进生产 | 否定 | 2026-11-11 | 控制变量后只取 harvest 图 21 张，A/B/C 均 0 通过；收益来自 base 标题。代码已回退，`--harvest` 仅 opt-in | 不接 |
| K9 | 多车型标题专用规则 | 弃 | 2026-11-12 | 全实验只 1 例，规则成本 > 收益 | 不做 |
| K10 | Query / Source / Platform 扩源（class query、alias 阶梯、专门来源直采） | 收口 | 2026-11-12 | class vs alias p≈0.726 不显著；C holdout 0/6；360che 反爬、lmjx 超时 | 冻结，见 `v1-retrieval-convergence-decision.md` |
| K11 | 默认加进口查询 | 不默认 | 2026-11-10 | E15：加 `进口 {class} {conf} 车型` 后外国候选 16–20%，未超过 A 组 18–24%，且偶发丢 KAMAZ/TB800 | 由 brief 明确目标市场 |
| K12 | 硬编码 18 品牌名单的 `discover` fallback | 废弃 | 2026-11-11 | 静默国产-only，污染"360 有没有外国车"的结论；文件保留但无调用点，CLI 已拦截 | `plan_candidates.py` |
| K13 | 用 fixture / 预制 brief / `plan.json` 当生产输入 | 禁止 | 2026-11-09 | 违反"不许假信息"；brief 必须 API 生成，fixture 必须标注 | 封装检查 |
| K14 | `data/retrieval_strategies.json` + `--strategy` | 删除 | 2026-11-12 | 加载后从不读取（`self.strategy` 只存不用），属死配置；已删文件与 CLI 参数 | 无 |

## 2. 已归档字段（保留兼容，不再读取/计算）

| 字段 | 位置 | 现状 |
|---|---|---|
| `Verification.visibility` | `retrieval_engine/contracts.py` | 恒 `"unknown"`；旧实现用"有宽高"冒充 `full`，已去掉 |
| `Verification.origin` | 同上 | 恒 `"unknown"`（K2） |
| `Brief.stop_rules` / `Brief.negative` / `Brief.strategy_ref` | `contracts.py` | **只解析不消费**（2026-11-12 确认）。schema 里保留以免旧 brief 校验失败；新 brief 不要再指望它们生效 |
| unit 级 `budget` / `stop`（"2 台占满即停"） | brief `research_units[*]` | 同上，不消费 |
| `.env` 的 `LLM_MONTHLY_BUDGET_CNY` / `LLM_MAX_IMAGES_PER_CALL` | `~/.equiplens` 外的仓库 `.env` | 代码从不读取，已从 `.env` 删除 |

## 3. 常见"又来一遍"的问法 → 标准回答

| 问法 | 回答 |
|---|---|
| "要不要把部件可见性加回来，好判断能不能裁？" | K1 已归档：可见性由人机交互判断，检索侧不做 |
| "能不能判断这张图是原厂还是改装？" | K2 已毙：错误率高、收益低；`origin` 恒 unknown |
| "为什么不做多平台/百度联合检索？" | K7：完整 loop 丢 HF8066、unknown 暴增；只留实验开关 |
| "用 strategy 配置驱动查询阶梯是不是更灵活？" | K14：已删。查询阶梯是 `imagesearch.query_variants` 的硬编码行为，改行为改代码 + 测试 |
| "brief 里的 stop_rules/negative 为什么没生效？" | §2：已归档、不消费。停止条件由代码实现（tier 耗尽 / 槽位满 / 预算帽） |
| "能不能按品牌白名单先发现候选？" | K12：已废弃，会造成静默国产-only 偏置 |

## 4. 重新开启的唯一入口

1. 只允许**一个变量**、预注册（目标层 / 样本 / 指标 / 停止阈值先写下来）；
2. 样本：8–10 brief、150–250 图、≥2 holdout；
3. 指标：accepted precision、target recovery、overview 率、成本；
4. 先定阈值，不通过就停；**不叠加** guard/query 规则；
5. 通过后回写本文件与本表（把判决从"毙"改成"采纳"）。否则视为违反流程。
