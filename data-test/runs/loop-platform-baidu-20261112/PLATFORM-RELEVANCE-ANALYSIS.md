# Baidu 平台结果为什么泛化/错误：相关性预筛被绕过了

## 正常路径

```text
search result（带 title）
  → _relevant(query,title,model) 预筛
  → 下载
  → gate（图能不能用）
  → verifier（是不是目标）
  → fill
```

正常 `search_images_hd` → `search_images_ex` 会调用 `_relevant`，不相关标题的图**不会下载**。

## Platform 实验路径

`WebWorld._search_360_baidu()` 直接调用 `_search_360` / `_search_baidu`，
再把结果 union 返回；**没有经过 `_relevant`**。

所以这次是：

```text
search → 全量 union → 下载 → gate → verifier
```

不是“先爬再筛”的正常流程，而是“平台实验路径漏了预筛”。

## 离线核算

对两个 run 的 gate-pass 唯一图，按 target query 重新跑 `_relevant`：

| run | 唯一 gate-pass | 通过 `_relevant` | 被过滤 |
|---|---:|---:|---:|
| 360 | 64 | 64 | 0（0%） |
| 360+Baidu | 98 | 18 | **80（81.6%）** |

也就是说：

- 360 的图基本都能过相关性护栏；
- Baidu 的图 **81.6% 在下载前就应该被过滤**；
- 当前 unknown 284 张里，很大一部分是“本该不下载”的低相关图。

## 这是百度的问题还是我们的问题？

两边都有：

1. **百度本身对具体车型 query 会返回泛化结果**（轻卡、观光车、其他品牌）；
2. **我们的 Platform 实验路径绕过了已有的 `_relevant` 预筛**，把低相关结果全量下载了；
3. gate 只判断“图能不能用”，不判断“是不是目标”；
4. verifier 只看 title，错误标题自然 unknown。

所以主因不是“百度精度差到不可用”，而是：

> **平台路径没有复用正常的 title 相关性预筛，导致低相关结果进入下载/验证。**

## 优化空间

1. **立即**：`_search_360_baidu` 返回前按 `_relevant(query,title,model)` 过滤；
2. 记录平台层 `filtered_by_relevance` 数量；
3. 可选：平台候选按 target 配额，避免淹没 360；
4. 不建议直接做 strict code/body 硬过滤（会误杀；TAZ4413 vs TAZ4922 已经证明）。

## 注意

`_relevant` 是**召回优先的宽松护栏**，不是精确身份：
- 同品牌不同型号仍可能通过；
- 多车型文章仍可能通过；
- 所以它只能减少“明显不相关”的下载，不能替代 verifier。

## 结论

- 这次 Platform 结果不能直接归因于百度；
- 先修“平台路径漏预筛”，再重跑同一 loop；
- 如果修完后 Baidu 仍带来大量错误，再讨论平台本身质量。
