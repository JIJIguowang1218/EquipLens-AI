# 死图床监测（只统计，不参与生产）

> 生成：2026-11-12T16:14:37 · 扫描 32 个 run / 10910 行 fetch_log · 失败 1770 行

用途：长期积累 403/DNS 的分布，供以后决定是否做持久化黑名单或换源。
生产侧仍只在单轮 run 内临时拉黑（`imagesearch.DomainHealth`），**不读本表**。

| # | host | 失败次数 | 分类 | 涉及 run | 首次 | 最近 |
|---|---|---:|---|---:|---|---|
| 1 | `img.jdzj.com` | 496 | http_403 472 / blocked 24 | 21 | 2026-11-10 | 2026-11-12 |
| 2 | `img2.fr-trading.com` | 372 | dns 372 | 29 | 2026-11-10 | 2026-11-12 |
| 3 | `img6.baixing.net` | 90 | http_403 90 | 2 |  |  |
| 4 | `img.chinacar.com.cn` | 76 | timeout 76 | 3 |  |  |
| 5 | `www.chinatruck.org` | 76 | redirect 68 / http_404 8 | 18 | 2026-11-11 | 2026-11-12 |
| 6 | `img24070801.mjqishi.com` | 72 | dns 72 | 18 | 2026-11-11 | 2026-11-12 |
| 7 | `uwui8.unshoist.com` | 72 | dns 72 | 18 | 2026-11-11 | 2026-11-12 |
| 8 | `img1.fr-trading.com` | 60 | dns 60 | 15 | 2026-11-12 | 2026-11-12 |
| 9 | `static.cnmasike.com` | 60 | http_403 60 | 3 | 2026-11-10 | 2026-11-10 |
| 10 | `www.86huoche.com` | 38 | http_404 30 / other 8 | 3 | 2026-11-12 | 2026-11-12 |
| 11 | `oss.huangye88.net` | 36 | http_403 36 | 9 | 2026-11-12 | 2026-11-12 |
| 12 | `img005.hc360.cn` | 30 | http_404 30 | 2 |  |  |
| 13 | `img3.fengj.com` | 30 | http_403 30 | 2 |  |  |
| 14 | `img6.go007.com` | 30 | http_404 30 | 2 |  |  |
| 15 | `www.360trucks.cn` | 23 | http_404 23 | 4 |  |  |
| 16 | `04.imgmini.eastday.com` | 15 | dns 15 | 2 |  |  |
| 17 | `img001.hc360.cn` | 15 | http_404 15 | 2 |  |  |
| 18 | `img003.hc360.cn` | 15 | http_404 15 | 2 |  |  |
| 19 | `img2.baixing.net` | 15 | dns 15 | 2 |  |  |
| 20 | `img3.makepolo.net` | 15 | dns 15 | 2 |  |  |
| 21 | `img4.baixing.net` | 15 | http_403 15 | 2 |  |  |
| 22 | `pics4.baidu.com` | 15 | http_403 15 | 2 |  |  |
| 23 | `pics6.baidu.com` | 15 | http_403 15 | 2 |  |  |
| 24 | `pics7.baidu.com` | 15 | http_403 15 | 2 |  |  |
| 25 | `himg.china.cn` | 8 | dns 8 | 1 | 2026-11-12 | 2026-11-12 |
| 26 | `www.dfyyc.com` | 8 | http_404 8 | 2 | 2026-11-10 | 2026-11-10 |
| 27 | `www.zhka.com` | 8 | connection 8 | 1 | 2026-11-12 | 2026-11-12 |
| 28 | `10.eewimg.cn` | 4 | http_403 4 | 1 |  |  |
| 29 | `biz72img-1253219747.image.myqcloud.com` | 4 | http_403 4 | 1 |  |  |
| 30 | `datasheet.eeworld.com.cn` | 4 | http_403 4 | 1 |  |  |

## 说明

- `blocked` = 单轮内已被拉黑后跳过的行（不是新失败）；
- `dns` 多为已死域名；`http_403` 多为防盗链/反爬；
- 同一 host 跨 run 反复出现，才值得考虑持久化或换源。
