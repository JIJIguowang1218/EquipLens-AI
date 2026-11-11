# 多图/多源身份证据：评估（2026-11-12）

## 观察

用户核对时：

- 目标没有具体车型（generic）；
- 标题有具体车型；
- 品牌一致；
- 多张图肉眼看起来是同一辆车；

会显著提高“这组图属于目标”的信心。

## 是否有帮助

有，但它是**簇级证据**，不是单图标题证据。

当前 `RuleVerifier` 是逐图看 title：
- 不会利用“多张图是同一辆”；
- 不会利用“多个独立来源”；
- 对 generic target 的“具体车型标题”可能判 unknown；
- 对 specific target 的“同品牌不同型号”又可能误收。

## 建议的条件（先评估，不上线）

1. 目标身份分级：
   - target 有 code/series：必须命中同一 code/series；同品牌不同 code 不能仅凭视觉升级；
   - target 是 generic：允许“具体车型代表”，但只能到 `probable/representative`，不能 confirmed。
2. 标题必须：
   - 有具体车型/车系；
   - 品牌、车身、构型与 target 不矛盾；
   - 不是多车型对比/封面文章。
3. 簇级支持：
   - ≥2 个独立来源（不同 registrable domain，且不是同一篇文章转载）；
   - 图片 hash/视觉相似度高，确认是同一辆车；
   - 同页多图不算独立证据。
4. 输出：
   - `identity_tier = confirmed | representative | probable | unknown`
   - `source_count`、`visual_cluster_size`、`conflicts`
   - 只作为排序/人审提示，不直接放宽 accepted。

## 反例

- `HOWO TAZ4922` target，标题 `TAZ4413`：同品牌、同系列，但用户判“不是” → 同品牌不能替代具体 code。
- `Zetros 4051` target，标题 `Zetros 3351`：用户判“是目标车” → 变体容忍取决于设计意图，不能一概而论。
- 标题同时有 `Zetros/Arocs`，图是 Arocs：多车型文章，不能按标题目标词升级。

## 结论

- 观察有价值，适合做**簇级 confidence / representative 证据**；
- 不适合做“标题具体 + 品牌一致 → 直接 accepted”的规则；
- 先在现有 100+44+33 标注上做离线簇分析，验证“多源 + 视觉一致”是否真的提高 human target rate；
- 通过后再考虑接入；完整 loop 对照暂缓。
