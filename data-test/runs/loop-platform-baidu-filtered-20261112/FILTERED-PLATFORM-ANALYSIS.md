# Baidu + relevance 预筛后：完整 loop 对照

修复：`search_platforms` 在下载前复用 `_relevant(query,title,model)`；平台路径不再直接 union 原始通道结果。

| 指标 | 360 基线 | 360+Baidu（未预筛） | 360+Baidu（预筛） |
|---|---:|---:|---:|
| 交付 | 12/12 | 12/12 | 12/12 |
| fetch 行 | 324 | 608 | 288 |
| gate pass | 264 | 452 | 228 |
| verifications | 256 | 392 | 220 |
| accepted | 236 | 100 | 216 |
| unknown | 20 | 284 | **0** |
| degraded | 8 | 12 | 8 |
| citation_only | 1 | 2 | 0 |
| bonus | 18 | 38 | 6 |

## 效果

预筛把 unknown 从 284 降到 0，accepted rate 回到 98.2%（216/220），
下载量也降了（608→288）。**修复本身是对的。**

## 但交付构成仍不理想

预筛后交付：

- 3, 5, 7, 8, 13, 14, 18, 19, 9, 10, 11, 12
- **丢失 HF8066（rank6）和 TAZ4922（rank1）**；
- 补进 rank18 沙豹、rank19 EQ2220AX。

其中：

- TAZ 在 360 基线里是“TAZ4413 错图”假阳性，预筛拒掉是对的；
- HF8066 是真实目标，但在预筛后的平台结果里没有 assets，最终丢失。

## 结论

1. **平台路径绕过 `_relevant` 是明确 bug，已修**；
2. 修复后 unknown 清零、候选量下降，说明正常预筛必须保留；
3. 但预筛后 Baidu 仍没有让交付更好，反而丢失 HF8066；
4. 说明“平台扩源”在**强目标/稀有型号**上没有增量，还会改变 composition；
5. 不接入 Platform；normal 默认 360 不变。

## 待验证

- 标题 code 与目标 code 明确不一致时，是否可在**下载前**拒绝；
  - 在未预筛 Baidu run 上，12 个 gate-pass 唯一图会被拒，其中 2 张是 accepted 的 TAZ4413 错图；
  - 没有观察到“目标 code 被误拒”的 accepted 样本，但样本小；
  - 需作为独立 prefilter 验证，不能和平台扩源混在一起。
