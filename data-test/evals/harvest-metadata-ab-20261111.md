# Harvest 元数据传递 A/B（recovery-only）

日期：2026-11-11
改动：`imagesearch.harvest_source_page()` 把页面 `<title>`/`og:title` + 图片 `alt` 拼进 `hit["title"]`；新增 `page_title/alt/source_mode=harvest`。
不变：普通搜索路径 `harvest=0` 完全不走这段；核验标准不变。

## A/B 1：generic alias query（4 个无图 target）

- 输入：run 无图 target + `plan.query` / `alias_query`；没有品牌特判。
- 结果：**15 张过门卫，old title='' 通过 0，new title 通过 0**。
- 原因：alias 把 K-65959 变成 `6x6 卡车`，召回的是东风/乌尼莫克/积木车；页面标题也不含目标。

## A/B 2：relevant query（诊断用，不是生产策略）

- 泰安：`五岳 油田牵引车`；沙漠：`沙漠运输车 6x6`
- 结果：**14 张过门卫，old 通过 0，new 通过 3**（都是页面标题含 `TAZ4413` 的图）。
- 仍有 5 张目标图 unknown：页面标题只有“重汽泰安五岳/沙漠油田理想伙伴”，不含型号；alt 为空。

## 结论

1. 元数据传递**有效但只解决“标题含型号”的子集**：0→3/14。
2. 页面 title 不够；还需要文章正文/图注/alt（或视觉复核）才能救“文章标题只有品牌”的图。
3. **normal run 不受影响**：`harvest=0` 不调用 harvest；`imagesearch 12/12`、`retrieval_engine 22/22` 通过。
4. 样本太小：3 个无图 target、1 个 target 有相关来源；不足以判断泛化。
5. 下一步应扩到 **5 个 brief / ≥20 个无图 target**，并区分：
   - query 不相关（换来源）；
   - 来源相关但 title/正文无型号（补上下文）；
   - 来源相关且 title 有型号（元数据已足够）。
