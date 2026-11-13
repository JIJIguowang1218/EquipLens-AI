# rank 必要性评估（2026-11-13，暂停待验证）

> 状态：**已记录，暂停深挖**。不删代码，不切默认；等有"相关性"指标后再评估。

## 1. 它最初解决什么

E19/T47（2026-11-11）：当时占槽 = 规划顺序 + citation + 配额，导致"强关联车型有 confirmed 图却不占槽"
（HF8066 排在发现顺序后面）。于是引入"只看文本、看图之前"的意向排序，决定 **先抓谁 / 先给谁**
（N primary + 4 backup），不是质量闸门。

## 2. 机制

一次 LLM 调用（`scripts/rank_plan.py`），输入只有文本：`model`、`identity_kind`、
`reason` 前 160 字、前 3 条 `source_queries` + brief 的 `request`；输出
`intent_rank / role / band / reason`。之后 `WebWorld` 按 `pinned > primary > backup > intent_rank`
排抓取顺序，FILL 按同样顺序遍历，但**只接受已有 accepted 证据的车型**。

## 3. 证据

| 证据 | 数值 |
|---|---|
| ab-rank 两 case（`ab-rank-20261113`） | LLM vs 确定性：交付/备选/degraded **完全一致**；top10 Jaccard 0.25 / 0.54 |
| 组合回归递补率（`delivery-20261113-regress`） | 48 台交付里 **19 台（40%）来自 primary 之外**，11 台跨 unit 借位 |
| rank 与"有没有图"的关系（1112 条 target 记录） | primary 有图 79.7% vs 非 primary 73.2%；但 **rank 1–5 有图率仅 69.0%，rank 5–9 反而 83.2%** |
| 文本输入区分度（23 份 11-13 plan，515 候选） | generic 49%、`source_count` 中位数 **1**、reason 中位 63 字 |
| 成本 | LLM rank 20–50 s/case（5 case 合计 180–213 s）；确定性 0.2 s/case |

## 4. 判断

1. rank 目前只是"尝试顺序先验"，交付由证据准入决定 → 在供给不足时几乎被完全吞掉；
2. 文本侧信息**不足以判断真实相关性**：一半候选是泛称、多数只有 1 个来源、reason 由同一批
   snippet 生成（循环证据）；
3. 现有指标只测"交付数量/身份强度"，**没有测"交付车型是否切题"**，所以 rank 的价值既没被证实、
   也没被证伪。

## 5. 待验证（重启条件）

- 指标：人工评交付清单的"相关性"（1–5 分或切题/不切题），而非只数交付台数；
- 样本：n≥5 brief，双盲（LLM rank vs 确定性）；
- 若相关性无差异 → 默认确定性（0 成本），LLM rank 仅保留为可选；
- 若相关性有差异 → 再讨论让 rank 影响"补抓优先级/展示顺序"，而不是假设它能决定交付。

## 6. 明确不做的

- 不删 `rank_plan.py`、不改默认（本轮只记录）；
- 不因为"文本排序看起来合理"就追加规则。
