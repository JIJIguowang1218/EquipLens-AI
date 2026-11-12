# 交付测试汇总（5 个输入）

> 每个 case 独立目录；brief/plan/rank/loop 全部走 API 与规则代码，无手工字段。

## 1. 交付结果

| 输入 | 类目 | 槽位 | 候选 | 需池 | 发现 | 有图 | 交付 | 备选 | degraded | citation | 池告警 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| c1-desert-tractor | 沙漠牵引车 | 10 | 14 | 23 | 14 | 9 | 8/10 | 1/4 | 4 | 0 | **WARN** |
| c2-reach-stacker | 港口集装箱正面吊（reach stacker，集装箱堆高机） | 10 | 23 | 23 | 20 | 19 | 10/10 | 4/4 | 4 | 1 | — |
| c3-tractor | 大马力轮式拖拉机 | 10 | 27 | 23 | 17 | 15 | 10/10 | 4/4 | 3 | 1 | — |
| c4-forklift | 电动叉车（四轮平衡重式，仓储物流用） | 6 | 23 | 16 | 16 | 10 | 6/6 | 4/4 | 4 | 3 | — |
| c5-roller | 单钢轮振动压路机 | 14 | 36 | 29 | 28 | 24 | 14/14 | 4/4 | 1 | 1 | — |

## 2. 成本（同一份用量，峰/谷两口径，单位 ¥）

| 输入 | chat tokens in/out | Search/Fetch | 全高峰 | 全空闲 |
|---|---|---:|---:|---:|
| c1-desert-tractor | 40555 / 25755 | 8 / 28 | ¥0.4672 | ¥0.3236 |
| c2-reach-stacker | 40100 / 20981 | 8 / 36 | ¥0.468 | ¥0.344 |
| c3-tractor | 30366 / 20873 | 6 / 34 | ¥0.4277 | ¥0.3139 |
| c4-forklift | 30361 / 17889 | 6 / 30 | ¥0.3838 | ¥0.2819 |
| c5-roller | 41563 / 16171 | 8 / 54 | ¥0.5225 | ¥0.4162 |

## 3. 耗时（秒；节点明细见各 case 的 DELIVERY.md）

| 输入 | 总耗时 | 主要节点 (state=ms) |
|---|---:|---|
| c1-desert-tractor | 236.6 | FETCH=147441 · EXTERNAL_DISCOVER=89154 · WRITEBACK=12 · VERIFY=2 |
| c2-reach-stacker | 291.8 | FETCH=211550 · EXTERNAL_DISCOVER=80190 · WRITEBACK=11 · VERIFY=3 |
| c3-tractor | 335.6 | FETCH=284223 · EXTERNAL_DISCOVER=51377 · WRITEBACK=11 · VERIFY=3 |
| c4-forklift | 226.9 | FETCH=217432 · EXTERNAL_DISCOVER=9411 · WRITEBACK=18 · VERIFY=1 |
| c5-roller | 574.1 | FETCH=465789 · EXTERNAL_DISCOVER=108318 · WRITEBACK=12 · VERIFY=7 |

## 4. 缺图归因

- c1-desert-tractor: all_download_failed 2 / no_hits 3 / not_delivered 1
- c2-reach-stacker: no_hits 1 / not_delivered 9
- c3-tractor: all_download_failed 1 / gate_or_verify_rejected 1 / not_delivered 5
- c4-forklift: all_download_failed 1 / gate_or_verify_rejected 4 / no_hits 1 / not_delivered 4
- c5-roller: all_download_failed 1 / gate_or_verify_rejected 2 / no_hits 1 / not_delivered 10

## 5. 下载质量

| 输入 | hits | downloaded | failed | blocked | gate_pass |
|---|---:|---:|---:|---:|---:|
| c1-desert-tractor | 235 | 180 | 41 | 0 | 175 |
| c2-reach-stacker | 460 | 435 | 25 | 0 | 360 |
| c3-tractor | 415 | 335 | 80 | 0 | 260 |
| c4-forklift | 355 | 295 | 60 | 0 | 165 |
| c5-roller | 917 | 756 | 155 | 0 | 616 |
