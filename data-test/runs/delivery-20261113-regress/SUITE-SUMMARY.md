# 交付测试汇总（5 个输入）

> 每个 case 独立目录；brief/plan/rank/loop 全部走 API 与规则代码，无手工字段。

## 1. 交付结果

| 输入 | 类目 | 槽位 | 候选 | 需池 | 发现 | 有图 | 交付 | 备选 | degraded | citation | 池告警 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| c1-desert-tractor | 沙漠牵引车 | 10 | 12 | 23 | 12 | 8 | 8/10 | 0/4 | 7 | 1 | **WARN** |
| c2-reach-stacker | 港口集装箱正面吊（reach stacker） | 10 | 21 | 23 | 21 | 13 | 10/10 | 3/4 | 7 | 1 | **WARN** |
| c3-tractor | 大马力轮式拖拉机 | 10 | 26 | 23 | 21 | 17 | 10/10 | 4/4 | 4 | 0 | — |
| c4-forklift | 电动叉车（四轮平衡重式） | 6 | 22 | 16 | 16 | 10 | 6/6 | 4/4 | 3 | 2 | — |
| c5-roller | 单钢轮振动压路机 | 14 | 35 | 29 | 27 | 25 | 14/14 | 4/4 | 2 | 2 | — |

## 2. 成本（同一份用量，峰/谷两口径，单位 ¥）

| 输入 | chat tokens in/out | Search/Fetch | 全高峰 | 全空闲 |
|---|---|---:|---:|---:|
| c1-desert-tractor | 39443 / 26322 | 8 / 24 | ¥0.4495 | ¥0.3047 |
| c2-reach-stacker | 38684 / 17406 | 8 / 34 | ¥0.4266 | ¥0.3183 |
| c3-tractor | 29771 / 18446 | 6 / 30 | ¥0.3871 | ¥0.2836 |
| c4-forklift | 30061 / 18537 | 6 / 30 | ¥0.3884 | ¥0.2842 |
| c5-roller | 29762 / 14013 | 6 / 48 | ¥0.4416 | ¥0.3558 |

## 3. 耗时（秒；节点明细见各 case 的 DELIVERY.md）

| 输入 | 总耗时 | 主要节点 (state=ms) |
|---|---:|---|
| c1-desert-tractor | 205.4 | FETCH=159392 · EXTERNAL_DISCOVER=46040 · VERIFY=8 · WRITEBACK=5 |
| c2-reach-stacker | 613.7 | FETCH=478789 · EXTERNAL_DISCOVER=134898 · VERIFY=6 · WRITEBACK=6 |
| c3-tractor | 586.3 | FETCH=453664 · EXTERNAL_DISCOVER=132596 · VERIFY=9 · WRITEBACK=6 |
| c4-forklift | 378.7 | FETCH=210668 · EXTERNAL_DISCOVER=168015 · WRITEBACK=6 · VERIFY=3 |
| c5-roller | 753.1 | FETCH=650616 · EXTERNAL_DISCOVER=102413 · VERIFY=17 · WRITEBACK=6 |

## 4. 缺图归因

- c1-desert-tractor: all_download_failed 1 / no_hits 3
- c2-reach-stacker: all_download_failed 1 / gate_or_verify_rejected 4 / no_hits 3 / not_delivered 3
- c3-tractor: gate_or_verify_rejected 3 / no_hits 1 / not_delivered 7
- c4-forklift: all_download_failed 1 / gate_or_verify_rejected 2 / no_hits 3 / not_delivered 4
- c5-roller: gate_or_verify_rejected 2 / not_delivered 11

## 5. 下载质量

| 输入 | hits | downloaded | failed | blocked | gate_pass |
|---|---:|---:|---:|---:|---:|
| c1-desert-tractor | 200 | 195 | 5 | 0 | 190 |
| c2-reach-stacker | 420 | 335 | 63 | 0 | 215 |
| c3-tractor | 525 | 440 | 85 | 0 | 355 |
| c4-forklift | 295 | 230 | 65 | 0 | 145 |
| c5-roller | 894 | 768 | 120 | 6 | 582 |
