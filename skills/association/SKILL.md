---
name: association-roster-planning
description: 把「车型类别（+具体车型）＋ 要分析的部件」翻译成页数预算内的检索清单，并保证每条目标都有可核对的来源（URL）。当用户要分析某类工程车、需要先决定查哪些车、排几页、哪些作备选时使用。本 skill 只管"产物规范与证据"，不规定判断方法；清单必须过 association-list schema 与 check_list 校验。
---

# 关联清单：产物规范与证据（v1.0-downgraded）

**本 skill 不做判断。** 判断（选哪些车、按什么轴、什么层级）由模型自由完成；
这里只规定三件事：**产物结构（schema）、来源证据（E3）、可交付性（校验）**。

> 2026-10-31 降级：原"六条判断纪律"实测未带来判断增益（三轮 A/B 打平），已移入
> `references/judging-rules.md` 作为**可选 checklist**，不再是硬规则。背景见
> `docs/association-skill-archive.md`。

## 输入

- `intent`：类目、车型（可选）、要分析的部件；
- 页数预算：默认 `{total:20, fixed_pages:5, vehicle_slots:12, part_page_slots:2}`；
- 证据索引：`data-test/evals/evidence-index-*.json`（`evidence_check.py --lookup` 可查）。

## 输出（必须）

一个过 `schemas/association-list.schema.json` 的 JSON；关键约束：

| 约束 | 说明 |
|---|---|
| `targets[].evidence` | 每条占槽目标必须带 `{url,title,grade,source}`；`grade` E1/E2/E3 |
| `recommended` | 必须 **E3**（标题含型号的详情页/专文），否则降 `provisional` |
| `provisional` | 至少 E1（SERP 命中），并写 `verify_by`（转正动作，**warning 级**） |
| 12 台 | 必须交满 `requested` 台带车型名的目标；弱关联可，但要标 `relevance_strength=weak` |
| `slots` | `recommended`/`provisional` 才可占槽；备选不占槽 |
| `next_action` | 无车型名的"方向"放这里，不占槽 |
| `run_meta` | 建议写 `model_id`/`prompt_version`/`evidence_index_version`/`run_at`（缺失仅告警） |

## 流程（四步，判断自定）

1. **读输入**：类目档案（`data/category_profiles.json`）、名录（`data-test/roster-*.json`）、证据索引；
2. **出清单**：12 台目标 + 备选；每台查 `evidence_check.py --lookup` 拿 URL，查不到就不进推荐位；
3. **校验**：`python scripts/check_list.py <list.json>`，必须 `ok:true`；
4. **报缺口**：凑不满写 `coverage.gap_kind` 与 `next_action`，不编造。

## 硬约束（校验会拦）

- 推荐位没有 E3 证据 → 拦；
- 交不满 `requested` 台 → 拦；
- 备选占槽、槽位重复、页数超限 → 拦；
- 阻断式确认（scope=all）生效仍占槽 → 拦。

## 可选：判断 checklist

`references/judging-rules.md` 保留六条经验（环境轴优先、结构不存在排除、口语类目落参数、
低置信先确认、理由写"能提供什么证据"、宁可确认也不猜）。它们是**参考**，不是门槛；
不用它们也能过校验。

## 脚本

| 脚本 | 用途 |
|---|---|
| `scripts/check_list.py` | schema + 槽位/12 台/证据/页数校验（交付前必跑） |
| `scripts/evidence_check.py` | 建索引 / 查型号证据 / 校验证据链 |
| `scripts/slots.py` | 页槽算术（去重、族上限、缓冲）——**不做语义判断** |
| `scripts/inventory.py` | 库内主图盘点（只读） |
