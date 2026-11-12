# 交付测试汇总（5 个输入）

> 每个 case 独立目录；brief/plan/rank/loop 全部走 API 与规则代码，无手工字段。

## 1. 交付结果

| 输入 | 类目 | 槽位 | 候选 | 需池 | 发现 | 有图 | 交付 | 备选 | degraded | citation | 池告警 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| c1-desert-tractor | 沙漠牵引车 | 10 | 17 | 23 | 17 | 11 | 9/10 | 2/4 | 8 | 2 | **WARN** |
| c2-reach-stacker | 港口集装箱正面吊（reach stacker） | 10 | 16 | 23 | 16 | 12 | 10/10 | 2/4 | 6 | 0 | **WARN** |
| c3-tractor | 大马力轮式拖拉机 | 10 | 27 | 23 | 20 | 17 | 10/10 | 4/4 | 1 | 1 | — |
| c4-forklift | 电动叉车（四轮平衡重式） | 6 | 24 | 16 | 12 | 10 | 6/6 | 4/4 | 4 | 2 | — |
| c5-roller | 单钢轮振动压路机 | 14 | 36 | 29 | 28 | 23 | 14/14 | 4/4 | 2 | 0 | — |

## 2. 成本（同一份用量，峰/谷两口径，单位 ¥）

| 输入 | chat tokens in/out | Search/Fetch | 全高峰 | 全空闲 |
|---|---|---:|---:|---:|
| c1-desert-tractor | 39291 / 25725 | 8 / 28 | ¥0.4644 | ¥0.3222 |
| c2-reach-stacker | 38902 / 19927 | 8 / 30 | ¥0.4272 | ¥0.3086 |
| c3-tractor | 29687 / 14363 | 6 / 40 | ¥0.4043 | ¥0.3171 |
| c4-forklift | 30840 / 12366 | 6 / 24 | ¥0.3106 | ¥0.2303 |
| c5-roller | 29349 / 14826 | 6 / 50 | ¥0.4573 | ¥0.3687 |

## 3. 耗时（秒；节点明细见各 case 的 DELIVERY.md）

| 输入 | 总耗时 | 主要节点 (state=ms) |
|---|---:|---|
| c1-desert-tractor | 304.0 | FETCH=266666 · EXTERNAL_DISCOVER=37271 · WRITEBACK=9 · VERIFY=7 |
| c2-reach-stacker | 315.2 | FETCH=215118 · EXTERNAL_DISCOVER=100021 · WRITEBACK=9 · VERIFY=3 |
| c3-tractor | 501.9 | FETCH=411554 · EXTERNAL_DISCOVER=90297 · WRITEBACK=14 · VERIFY=1 |
| c4-forklift | 176.5 | FETCH=113143 · EXTERNAL_DISCOVER=63306 · WRITEBACK=10 · BRIEF_READY=0 |
| c5-roller | 441.7 | FETCH=331382 · EXTERNAL_DISCOVER=110247 · WRITEBACK=22 · VERIFY=7 |

## 4. 缺图归因

- c1-desert-tractor: no_hits 6 / not_delivered 2
- c2-reach-stacker: all_download_failed 1 / gate_or_verify_rejected 2 / no_hits 1 / not_delivered 2
- c3-tractor: all_download_failed 1 / gate_or_verify_rejected 2 / not_delivered 7
- c4-forklift: gate_or_verify_rejected 1 / no_hits 1 / not_delivered 4
- c5-roller: all_download_failed 1 / gate_or_verify_rejected 3 / no_hits 1 / not_delivered 9

## 5. 下载质量

| 输入 | hits | downloaded | failed | blocked | gate_pass |
|---|---:|---:|---:|---:|---:|
| c1-desert-tractor | 270 | 245 | 25 | 0 | 240 |
| c2-reach-stacker | 380 | 300 | 58 | 0 | 235 |
| c3-tractor | 465 | 370 | 95 | 0 | 280 |
| c4-forklift | 255 | 230 | 25 | 0 | 170 |
| c5-roller | 852 | 714 | 138 | 0 | 510 |
