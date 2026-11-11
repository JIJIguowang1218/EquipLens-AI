# Platform 完整 loop：为什么 Baidu 后交付构成变差

## 1. 数据

同一 M1 brief / plan-ranked / 12 槽，只切平台。

| 指标 | 360 | 360+Baidu |
|---|---:|---:|
| fetch 行 | 324 | 608 |
| 下载成功 | 284 | 508 |
| gate pass | 264 | 452 |
| 唯一 sha1 | 69 | 111 |
| verifications | 256 | 392 |
| accepted verifications | 236 | 100 |
| **verification accepted rate** | **92.2%** | **25.5%** |
| unknown | 20 | 284 |
| degraded | 8 | 12 |
| citation_only | 1 | 2 |
| 交付 | 12/12 | 12/12 |

## 2. 交付构成

360 交付（intent rank）：

1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14  
包含 HF8066（rank6）、豪沃6×6（rank14）。

Baidu 交付：

1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12, 13  
新增 rank2 泰安五岳、rank4 沙漠越野；  
**丢掉 rank6 HF8066 和 rank14 豪沃6×6。**

所以 12/12 没变，但构成变了：不是单纯“变差”，而是**原本的强 primary 被换掉**。  
如果只看槽位数，会误以为平台无影响；实际 composition 已变化。

## 3. 为什么 unknown 从 20 涨到 284

- Baidu 返回了大量**标题与目标车型不符**的图。
- gate 只判断“像不像卡车/能不能用”，不判断“是不是这台车”；
- verifier 只看标题，遇到错误/泛化标题就 unknown。

典型 HF8066：

| 平台 | 标题 |
|---|---|
| 360 | `连接总重230吨 2018IAA最大卡车比利时莫尔HF8066正式发布` |
| Baidu | `东风4x4驱动越野轻型货车...`、`六驱沙漠旅游观光车...`、`东风六驱6x6大马力沙漠车观光车...` |

Baidu 的 HF 图全是**错误车型/旅游观光车**，verifier 判 `wrong_config`/`unknown`；HF 因此没有 accepted，不能占槽。

## 4. 是策略问题还是平台问题？

**两者都有，主因是平台结果相关性差，策略放大了它。**

### 平台问题

- Baidu 对具体车型 query 返回大量泛化/错误车型；
- gate pass 452 张里只有 100 张 verifier accepted（25.5%）；
- 这些图标题不是目标，不能靠“更多图”解决。

### 策略问题

- `_search_360_baidu` 把 Baidu 结果**全量 union**，没有相关性过滤、没有按 target 配额；
- 候选量翻倍后，verification/占槽被大量 unknown 图片占用；
- 没有“preferred target 验证/占槽保护”；
- HF 的 assets 存在但全部 unknown，最终没有兜底/重试。

所以不是“Baidu 精度差”这么简单，而是：

> **平台返回低相关结果 + 策略无选择地接收 + 没有 preferred 保护 = 交付构成被低质候选改写。**

## 5. 如果以后重开 Platform

不要直接 union。至少需要：

1. 平台结果先做 target/标题相关性预筛；
2. 每个 target 限制平台候选数；
3. preferred target 先验证、先占槽；
4. 平台只作为补充，不覆盖 360 的强候选。

但当前结论仍是：**Platform 不接入；先保护 preferred，再谈扩源。**
