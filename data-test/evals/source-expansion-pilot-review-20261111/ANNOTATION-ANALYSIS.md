# 扩源 pilot 100 图：标注与重复/门卫分析

来源：`annotations.json`（2026-11-11）

## 1. 标注总体

原始 100 行：

| 判断 | 行数 |
|---|---:|
| 是目标车 | 53 |
| 不是 | 24 |
| 不确定 | 22 |
| 空白 | 1 |

按 URL 去重后 81 张：

| 判断 | 唯一图 |
|---|---:|
| 是目标车 | 46 |
| 不是 | 17 |
| 不确定 | 21 |
| 空白 | 1 |

有 4 组同一 URL 被标了不同结果，集中在 C-aerial 的 AP28CA 两个变体：
同一张解放/乌拉尔图，在一个 target 下标“不是”，另一个标“不确定/是”。这说明重复图会污染标注。

## 2. 重复图：19 组、19 张冗余

- 100 行 → 81 个唯一 URL；
- 19 个 URL 出现 2 次，共多出 19 行；
- 重复原因：
  1. **同一 URL 被多个 target 的搜索结果返回**，probe 按 target 逐条存，没有全局 URL 去重；
  2. plan 里有同款变体（`GKS28J` / `GKS28`、两个 `AP28CA...`），alias query 相同，结果自然重复；
  3. 来源页 harvest 同一页图被多个候选抽取；
  4. 核对页按行渲染，没有按 URL 去重。

## 3. 门卫为什么没拦住

抽了 8 张“不是/局部/游戏”图重新过门卫：

| 图 | 用户判断 | gate | scene | keep label |
|---|---|---|---|---|
| v14 | 局部图 | pass | part | close-up truck part |
| v15 | 局部图 | pass | part | close-up truck part |
| v16 | 局部图 | pass | part | close-up truck part |
| v23 | 无主体 | pass | part | close-up truck part |
| v28 | 游戏画面 | pass | part | close-up truck part |
| v47 | 装载机 | pass | part | construction machinery |
| v49 | 游戏画面 | pass | part | close-up truck part |
| v57 | 铲车 | pass | part | construction machinery |

门卫 v4 的职责是“图能不能用”，不是“是不是目标车”；`scene=part` 本来就允许通过，供部件分析用。问题在**交付策略**：
- `_state_fill` 只要任一部件有 accepted 图就占整车槽；
- 所以局部图/零件图/游戏图可能占槽；
- 不是门卫漏拦，是“part 图可以占整车槽”的规则不对。

## 4. 核验口径：precision 高、recall 低

9 张被 verifier accepted 的图，用户全部标为“是目标车”（9/9）。  
但 46 张唯一目标图里只 accepted 9 张，recall 低；大量目标图因标题空/泛被判 unknown。

所以：
- **不能靠门卫筛目标**；
- 需要“整车交付资格”：至少一张 `scene=single_vehicle` 的图，part 图只做部件证据；
- accepted 的 9 张精度看起来不错，但样本小，仍需扩大。

## 5. 下一步

1. 修重复：probe/审核/交付按 URL/sha1 全局去重；plan 先按车型身份合并变体。
2. 修占槽：整车槽要求 overview/`scene=single_vehicle`；part 图只进部件证据，不单独占槽。
3. 不调门卫 v4；门卫继续做图像可用性，交付资格单独做。
4. 重新跑同一批 24 个失败 target，先看去重/占槽策略，再看扩源收益。
5. 人工复核仍有必要，但下一版审核页按 URL 去重、隐藏 identity。
