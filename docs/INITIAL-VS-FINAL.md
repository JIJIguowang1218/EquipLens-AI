# 初始 vs 最终：能不能给出一个提升数字？

更新：2026-11-12

## 结论

**能做到“受控实验的初始 vs 最终”，但不能从现有文件直接算出一个全产品统一提升数字。**

原因：早期与最终实验的 brief、plan、query、sample、交付口径不同；把 2 usable/10 queries 和 12/12 放一起会误导。

## 现在能成立的对比

### 1. task-brief：v1 格式 vs v2 方法（同一批 10 案例）

| 指标 | v1 只给格式 | v2 方法 |
|---|---:|---:|
| 自动断言 | 3/10 | **10/10** |
| 人工总体 PASS | 6 | **10** |
| 关系轴 | FAIL 5 | PASS 9 |

来源：`data-test/evals/task-brief-eval-v1b-20261111/`  
这是**同一批案例、同一模型、只差方法**，可以算初始 vs 最终。

### 2. code prefilter：同一 plan/12 槽（不是全产品 baseline）

| 指标 | 无 prefilter | 有 prefilter |
|---|---:|---:|
| 交付 | 12/12 | 12/12 |
| accepted | 236 | 224 |
| 交付构成 | 12 台 | 相同 12 台 |

结论：它不是“交付提升”，是“同交付下移除错 code accepted”。

### 3. 检索最终状态（只能作为结果，不是提升）

- `loop-p0c-20261112`：12/12，degraded 8，citation_only 1；
- `loop-generic-test`：12/12，3 generic，无删除。

这些是**最终状态**；没有同 brief/plan 的“初始状态”可直接对比。

## 不能成立的对比

- 早期 W1 smoke “2 可用/10 查询” vs 最终 12/12：
  - 查询数、brief、plan、可用定义不同；
  - 不能得出“提升 6 倍”这种结论。
- Platform 候选级 precision 94% vs 完整 loop 12/12：
  - 分母不同，不可相加。

## 想要一个可信的“初始 vs 最终”该怎么做

1. 冻结同一批 10 个 brief；
2. 固定同一 plan（或同一 planner 版本）；
3. 用两个 git commit/worktree 各跑一遍：
   - initial commit；
   - final commit；
4. 同一 12 槽、同一 gate/verifier 口径；
5. 同一人工评分表；
6. 只报同一指标：delivery、accepted precision、human pass、cost。

在这个 A/B 跑出来前，**只报受控的子实验提升，不报全产品统一提升。**
