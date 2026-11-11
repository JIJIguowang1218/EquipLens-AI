# LangGraph 迁移评估与分支计划

状态：**暂不迁移，先做扩源/恢复；记录为后续候选架构。**
更新时间：2026-11-11

## 结论

- 当前自研状态机行为稳定，gate/verify/quota/provenance 都有测试；不立即全量重写。
- 若做 LangGraph，优先用它承载 **session / checkpoint / feedback router / recovery**，
  核心 gate/verify/fill 仍作为确定性节点或函数保留。
- 迁移方式：**strangler（先包一层，再逐步替换）**，不做一次性重写。

## Git 分支策略

`main` 保持可交付；迁移在独立分支开发，按阶段合并：

| 分支 | 用途 | 生命周期 |
|---|---|---|
| `spike/langgraph-orchestration` | 验证 LangGraph 能否包住现有 loop；可丢弃 | 1 次 spike |
| `feat/langgraph-session` | session/checkpoint/feedback router 的生产候选 | 中期 |
| `feat/langgraph-recovery` | 恢复状态机迁移 | 视 spike 结果 |
| `main` | 稳定版本；只接受通过回归的合并 | 长期 |

规则：

1. 从 `main` 切分支，不直接改 `main`；
2. 每个 PR 只做一个节点/子图，保持可回滚；
3. 用 feature flag：`ORCHESTRATOR=legacy|langgraph`，默认 legacy；
4. 同一输入并行跑 legacy/langgraph，比较：
   - 10 案例 brief 自动断言 + 人工 PASS/FAIL；
   - 12 槽交付、HF8066/primary 命中、gate/verify 通过；
   - 成本、耗时、状态/证据可追溯；
5. 合并门槛：行为等价或更优、无 gate 语义变化、可回滚；否则保留分支，不合并。

注意：分支能隔离代码，但不能避免长期分叉；迁移应小步合并，避免 6 个月长分支。

## 迁移范围（如果启动）

1. **只包一层**：现有 loop 作为一个 `legacy_loop` 节点/子图，行为不变；
2. **session/checkpoint**：保存 brief、候选、图片、核验、用户反馈、pin/exclude；
3. **feedback router**：intent + 对象 + 目标节点，使用 `Command`/条件边；
4. **recovery controller**：只允许固定动作（换 query/源、补 backup、pin、stop）；
5. 核心 gate/verify/fill 不改成 LLM 决策。

## 触发条件

- 扩源/换源测试完成，失败原因和恢复收益明确；
- 要接用户反馈/多轮对话（需要 checkpoint/interrupt）；
- 现有状态机难以表达回退/重入，而不是仅仅“想用框架”。

## 风险

- 框架版本/调试成本；
- 状态 schema 迁移导致旧 run 不可读；
- 两套编排并存期间行为不一致；
- 为了“规范”迁移，收益不足。
