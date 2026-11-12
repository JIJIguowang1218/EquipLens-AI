# 交付测试汇总（5 个输入）

> 每个 case 独立目录；brief/plan/rank/loop 全部走 API 与规则代码，无手工字段。

## 1. 交付结果

| 输入 | 类目 | 槽位 | 候选 | 需池 | 发现 | 有图 | 交付 | 备选 | degraded | citation | 池告警 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| c1-desert-tractor | 沙漠牵引车 | 10 | 12 | 23 | 12 | 10 | 9/10 | 1/4 | 6 | 1 | **WARN** |
| c2-reach-stacker | 港口集装箱正面吊（reach stacker，集装箱正面吊运机） | 10 | 8 | 23 | 8 | 7 | 7/10 | 0/4 | 4 | 0 | **WARN** |
| c3-tractor | 大马力轮式拖拉机（200–300 hp 级农用轮式拖拉机） | 10 | 11 | 23 | 11 | 9 | 8/10 | 1/4 | 2 | 1 | **WARN** |
| c4-forklift | 电动叉车（四轮平衡重式，仓储物流用） | 6 | 12 | 16 | 12 | 8 | 6/6 | 2/4 | 4 | 3 | **WARN** |
| c5-roller | 单钢轮振动压路机 | 14 | 30 | 29 | 19 | 18 | 14/14 | 4/4 | 3 | 2 | — |

## 2. 成本（同一份用量，峰/谷两口径，单位 ¥）

| 输入 | chat tokens in/out | Search/Fetch | 全高峰 | 全空闲 |
|---|---|---:|---:|---:|
| c1-desert-tractor | 28066 / 21119 | 6 / 22 | ¥0.3651 | ¥0.2525 |
| c2-reach-stacker | 20731 / 5143 | 6 / 10 | ¥0.1626 | ¥0.1213 |
| c3-tractor | 33579 / 12749 | 6 / 20 | ¥0.2992 | ¥0.2146 |
| c4-forklift | 32136 / 7482 | 6 / 22 | ¥0.2641 | ¥0.2021 |
| c5-roller | 29883 / 27225 | 6 / 40 | ¥0.5076 | ¥0.3688 |

## 3. 耗时（秒；节点明细见各 case 的 DELIVERY.md）

| 输入 | 总耗时 | 主要节点 (state=ms) |
|---|---:|---|
| c1-desert-tractor | 216.7 | FETCH=173083 · EXTERNAL_DISCOVER=43594 · WRITEBACK=8 · VERIFY=2 |
| c2-reach-stacker | 184.5 | FETCH=159206 · EXTERNAL_DISCOVER=25263 · WRITEBACK=10 · VERIFY=1 |
| c3-tractor | 209.5 | FETCH=167489 · EXTERNAL_DISCOVER=41979 · WRITEBACK=10 · VERIFY=1 |
| c4-forklift | 201.1 | FETCH=151687 · EXTERNAL_DISCOVER=49432 · WRITEBACK=16 · BRIEF_READY=0 |
| c5-roller | 472.3 | FETCH=353158 · EXTERNAL_DISCOVER=119081 · WRITEBACK=14 · VERIFY=4 |

## 4. 缺图归因

- c1-desert-tractor: no_hits 2 / not_delivered 1
- c2-reach-stacker: gate_or_verify_rejected 1
- c3-tractor: gate_or_verify_rejected 2 / not_delivered 1
- c4-forklift: all_download_failed 1 / gate_or_verify_rejected 3 / not_delivered 2
- c5-roller: gate_or_verify_rejected 1 / not_delivered 4

## 5. 下载质量

| 输入 | hits | downloaded | failed | blocked | gate_pass |
|---|---:|---:|---:|---:|---:|
| c1-desert-tractor | 300 | 265 | 35 | 0 | 240 |
| c2-reach-stacker | 180 | 140 | 40 | 0 | 125 |
| c3-tractor | 215 | 200 | 15 | 0 | 150 |
| c4-forklift | 315 | 250 | 65 | 0 | 130 |
| c5-roller | 714 | 588 | 119 | 7 | 420 |
