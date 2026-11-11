# 当前整体技术框架（单一事实源）

更新：2026-11-12  
用途：任何打包/封装/新会话先读这里，避免把旧策略、fixture、预置假数据带进产品。

## 1. 当前产品阶段

**检索模块 v1 收敛中；第一次用户交付准备阶段。**

- 正常检索：360 主通道，12 槽，意图排序，gate v4，RuleVerifier，fill，audit；
- 已停止继续扩源（Query/Source/Platform 实验收口）；
- 第一次交付定位 **beta + 人审**，不是无人值守生产；
- 下一步：feedback router/session → LangGraph feedback spike。

## 2. 生产路径（normal）

```text
task-brief@v2 (API)
  → plan_candidates (Search + LLM 抽取 + provenance)
  → rank_plan (intent 12 primary + 2 backup)
  → retrieval loop:
       LIBRARY_SEARCH → EXTERNAL_DISCOVER(360)
       → FETCH → VERIFY(gate v4 + RuleVerifier)
       → FILL → GAP_CHECK → DONE/FAILED
  → fetch_audit.html / state / evidence
  → analysis (vision, separate module)
```

关键文件：

| 环节 | 文件 |
|---|---|
| brief | `skills/task-brief/SKILL.md`、`src/equiplens/briefing.py`、`scripts/build_brief.py` |
| plan | `src/equiplens/planning.py`、`scripts/plan_candidates.py` |
| intent rank | `scripts/rank_plan.py` |
| loop | `src/equiplens/retrieval_engine/{engine,web,contracts,state}.py` |
| gate | `src/equiplens/gate.py` |
| verifier | `src/equiplens/retrieval_engine/web.py`（`RuleVerifier`） |
| audit | `scripts/render_fetch_audit.py` |
| analysis | `src/equiplens/analysis.py`、`docs/superpowers/specs/2026-10-31-analysis-schema-design.md` |
| eval | `data-test/evals/`、`scripts/eval_task_brief.py` |

## 3. P0 交付不变量（2026-11-12）

已实现：

- 全局 asset 去重：已占槽 target 用过的 asset 不再给其他 target 占槽；
- 每个 target 的 fetch/verify/filled attempt 写入 `state.attempts`；
- `part_only` 标记：有 scene 元数据、但没有 `scene=single_vehicle` 的 target 标记 `part_only=True`；
- code prefilter（可选，`--code-prefilter`）：code target 且 title code 明确不一致时下载前拒绝。

**未采用**：

- 硬性“part-only 不得占槽”：实测会把 12/12 降到 10/12，且改变 composition；当前只打标，供人审/后续排序。
- Platform union / Baidu 默认启用：完整 loop 对照失败（丢 HF8066、unknown 暴增）。
- body/tonnage 硬 guard：误杀目标。
- harvest 元数据：控制变量后无收益，代码已回退。

## 4. 生产 / 实验 / 已收口

### 生产默认

- 360 平台；
- gate v4 + RuleVerifier；
- intent rank；
- 12 槽；
- code prefilter 默认 **关闭**（实验通过但未默认）。

### 实验（不默认）

- `--platform-extra baidu`：仅实验/降级候选；
- `--code-prefilter`：低风险 prefilter，待产品决定；
- `--require-overview` 不存在；part_only 只标记。

### 已收口

- Query/Source/Platform 扩源；
- harvest title 元数据；
- body/tonnage guard；
- 多车型标题专用规则；
- specialized source 直接 harvest（360che 反爬、lmjx 超时）。

详见 `docs/recovery-strategy-closeout.md`、`docs/v1-retrieval-convergence-decision.md`。

## 5. 数据与“不许假信息”规则

- 所有 brief 必须由 API 生成，不允许手工代写；
- eval 输出与 run 数据必须来自实际执行；fixture 必须标注 `fixture`；
- 打包时禁止用 `data-test/evals/*` 的预制 brief 当真实用户输入；
- 禁止把 `plan.json`、fixture、mock 图片当生产数据；
- `data-test/runs/INDEX.md` 是 run 台账；`docs/EXPERIMENTS-INDEX.md` 是实验索引；
- 若某策略已收口，不得在打包时恢复默认。

## 6. 当前未决

1. `part_only` 是否最终允许占槽：需要人审/产品决定；
2. code prefilter 是否默认：已独立验证不影响 12/12，待产品决定；
3. 360 单点 fallback：Baidu 仅作降级，未实现 health/circuit；
4. 第一次用户交付的反馈 router/session；
5. LangGraph 迁移：只做 feedback spike，不做核心重写。

## 7. 当前状态快照（2026-11-12）

- 最新完整 normal run：`loop-p0c-20261112`，12/12，degraded 8，citation_only 1；
- P0 硬 overview 试验：`loop-p0-20261112` 10/12（已放弃硬规则）；
- 平台对照：`loop-platform-{360,baidu,baidu-filtered}-20261112`，Platform 不接入；
- code prefilter 独立对照：`loop-code-prefilter-20261112`，12/12 构成不变。
