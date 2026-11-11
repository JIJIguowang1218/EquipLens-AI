# 失败原因 / 初始阶梯统计

> 旧 run 的 fetch_log 没有 `tries`，只能统计失败原因；新 run 才有阶梯次数。

## loop-intent-test3-20261111

- fetch 328 / ok 288 / 过门卫 264 / 唯一图 70
- 目标 20 / 交付 12 / 无图目标 4 / citation_false 1
- 下载失败原因：[('connection', 20), ('http_403', 16), ('redirect_loop', 4)]
- 门卫拒绝：[('a grid or collage made of several different truck photos', 12), ('a photo of a row or lineup of many parked trucks', 4), ('', 4), ('a photo of a passenger bus or coach', 4)]
- 核验 unknown/缺陷：24 / []
- 阶梯：未采集（旧日志无 tries）

- 无图目标示例：泰安五岳油田专用全驱牵引车（豪沃驾驶室）、沙漠越野重型牵引车（康明斯 + 艾里逊沙漠运输底盘）、K-65959（6×6，GVW 35000 kg）、6×6 全驱沙漠车
## loop-generic-test-20261111

- fetch 392 / ok 340 / 过门卫 316 / 唯一图 82
- 目标 24 / 交付 12 / 无图目标 5 / citation_false 4
- 下载失败原因：[('http_403', 28), ('connection', 20), ('redirect_loop', 4)]
- 门卫拒绝：[('a grid or collage made of several different truck photos', 12), ('a photo of a row or lineup of many parked trucks', 4), ('', 4), ('a photo of a passenger bus or coach', 4)]
- 核验 unknown/缺陷：24 / []
- 阶梯：未采集（旧日志无 tries）

- 无图目标示例：沙漠越野重型牵引车（康明斯 + 艾里逊沙漠运输底盘）、6×6 全驱沙漠车、泰安五岳油田专用全驱牵引车（豪沃驾驶室）、K-65959（6×6，GVW 35000 kg）、6×6 越野牵引头（460马力）
## loop-m1b-global-v2

- fetch 372 / ok 316 / 过门卫 308 / 唯一图 77
- 目标 23 / 交付 12 / 无图目标 2 / citation_false 6
- 下载失败原因：[('http_403', 48), ('connection', 4), ('http_404', 4)]
- 门卫拒绝：[('a grid or collage made of several different truck photos', 4), ('a photo of the interior cabin of a truck, seats and dashboard', 4)]
- 核验 unknown/缺陷：56 / [('wrong_config', 4)]
- 阶梯：未采集（旧日志无 tries）

- 无图目标示例：6×6 全驱沙漠车（可改装油田专用车）、HF8066 6×6 重型越野牵引/运输底盘
## loop-c01-plan9

- fetch 176 / ok 152 / 过门卫 136 / 唯一图 36
- 目标 24 / 交付 12 / 无图目标 12 / citation_false 8
- 下载失败原因：[('connection', 12), ('http_404', 8), ('http_403', 4)]
- 门卫拒绝：[('a grid or collage made of several different truck photos', 16)]
- 核验 unknown/缺陷：20 / []
- 阶梯：未采集（旧日志无 tries）

- 无图目标示例：EQ2250AX（六驱沙漠越野卡车）、6×6全驱沙漠车（可改装油田专用车）、Zetros 4051 AS（6×6沙漠牵引车）、Arocs 6×6 / 8×8 全驱牵引车、HF8066（6×6重型沙漠运输车）

## 失败 URL 重放（12 条 sample，2026-11-11）

从 `loop-intent-test3` 的失败行里取前 12 条，用当前下载阶梯重新下载：

- 下载成功：**0/12**；过门卫：0/12；
- `tries=2`（DNS 解析失败/403 直接放弃）；
- 失败集中在 `uwui8.unshoist.com`（DNS）、`img2.fr-trading.com`（DNS）、`img.jdzj.com`（403）。

**结论**：同一 URL 重试没有收益；恢复必须换**源页/图床/查询**，而不是在下载阶梯里多试几次。
