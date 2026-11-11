# v1 检索收敛与下一步架构决策（2026-11-12）

## 结论

- **停止继续做 query/source/platform 扩源策略**；检索模块进入 v1 收敛。
- 先补 3 个交付不变量，再向用户做第一次图片交付 + 反馈。
- LangGraph 不在现在全量迁移；先做 **feedback/session 子图 spike**，核心检索保持确定性。

## 为什么不再扩源

- Class vs alias precision 不显著（p≈0.726）；
- C holdout 0/6；
- Platform union 丢 HF8066，预筛后仍丢；
- 360+Baidu 定向补位 0 accepted（query/来源没命中）；
- 360che/lmjx 初测反爬/超时；
- 继续投入的边际收益低，误杀/复杂度风险高。

## v1 交付前必须补的 3 个不变量

1. **全局去重**：URL/sha1/车型身份；同一图不能重复占槽；
2. **整车槽资格**：至少一张 `scene=single_vehicle` 的 overview；part-only 只做部件证据，不单独占槽；
3. **preferred attempt 日志**：每个 primary/preferred target 是否 fetch/verify/accept，失败原因可见；不先做复杂预留槽。

可选低风险：code prefilter（已独立验证：12/12 构成不变，accepted 236→224，无 target 丢失）。

## 第一次用户交付

可以做，但定位为 **beta/有人审**：

- 检索 12 主 + 2 备；
- 人工快速确认目标/非目标；
- 用户看到图后给反馈；
- 反馈进入 session，不直接改检索核心。

## 反馈 → 分析

- 先做 **feedback router + 短期 session state**：
  - 反馈意图：换车/换品牌/保留/排除/部件看不清/重来；
  - 路由到节点：retrieve/fill/analysis；
  - 不跨项目长期记忆。
- 分析模块已有结构化输出；先接检索结果，不做大规模重构。

## LangGraph 怎么进

- **不建议现在全量迁移**；
- 先开 `spike/langgraph-feedback` 分支，只包：
  - session state；
  - feedback intent router；
  - checkpoint/interrupt；
- 核心 gate/verify/fill 仍用现有代码；
- 用同一输入并行跑 legacy/spike，比较反馈路由、状态恢复、成本；
- 通过后再考虑核心迁移。

## 顺序

1. 冻结扩源；
2. 交付不变量 + 回归；
3. 第一次用户交付（人审）；
4. feedback router/session；
5. LangGraph feedback spike；
6. 反馈稳定后，再决定是否迁核心。
