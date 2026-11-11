# Harvest 元数据传递：控制变量测试（结论：不采纳）

日期：2026-11-11
状态：**实验否定，代码已回退；normal/harvest 路径都不改。**

## 为什么要重做

第一次 A/B 把 `search_images_hd(..., harvest=2)` 的**base 搜索结果**和 **harvest 来源页图**混在一起：
base 结果本来就有标题，所以“0→3”是 base 的标题带来的，不是 harvest 元数据。
必须只比较 `channel == "page"` 的 harvest 图。

## 干净 A/B（只取 harvest 图）

查询沿用上一轮测试输入（不是生产策略）：

- `五岳 油田牵引车`
- `沙漠运输车 6x6`
- `K-65959 6x6`
- `6x6 沙漠卡车`

结果：

| 组 | 过门卫 harvest 图 | 核验通过 |
|---|---:|---:|
| A 旧 `title=""` | 21 | 0 |
| B 页面 title + alt | 21 | 0 |
| C 页面 title + alt + meta description | 21 | 0 |

同一批 21 张图，B/C 仍然 0：页面标题是“唯一参展石油装备展的底盘企业 重汽泰安五岳有何亮点”“JEEP 牧马人”“兰博基尼”等，不含目标型号；description 也没有救回来。

同时，base 搜索结果有 16 张过门卫，其中 3 张带 `TAZ4413` 标题并被核验通过——**收益来自搜索标题，不是 harvest 元数据**。

## 结论

1. **不需要加图注/正文上下文**：至少在这批样本里，title/alt/description 都没有带来增量。
2. 页面 title 不是身份证据；真正的问题是 **harvest 来源与目标不相关**，不是“title 字段没传”。
3. 代码已回退到原 harvest 行为；normal/harvest 均不改。
4. 样本仍小（2 个 brief 家族、4 个无图 target），但方向明确：先修 **query/来源相关性**，不是继续堆元数据。
5. 34 张人工核对图的结论不变：核验 precision 高、recall 低；但“漏掉的目标图”主要来自 base 搜索标题，不是 harvest。
