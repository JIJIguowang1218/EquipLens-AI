# 交付测试汇总（5 个输入）

> 每个 case 独立目录；brief/plan/rank/loop 全部走 API 与规则代码，无手工字段。

## 1. 交付结果

| 输入 | 类目 | 槽位 | 候选 | 需池 | 发现 | 有图 | 交付 | 备选 | degraded | citation | 池告警 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| c1-desert-tractor | 沙漠牵引车（重型牵引车，油田/沙漠运输用途，小批量 10 台） | 10 | 13 | 23 | 13 | 8 | 7/10 | 1/4 | 6 | 0 | **WARN** |
| c2-reach-stacker | 港口集装箱正面吊（reach stacker） | 10 | 16 | 23 | 16 | 11 | 10/10 | 1/4 | 4 | 1 | **WARN** |
| c3-tractor | 大马力轮式拖拉机（200–300 hp 级，4×4 轮式，非铰接） | 10 | 17 | 23 | 17 | 16 | 10/10 | 4/4 | 3 | 3 | **WARN** |
| c4-forklift | 电动叉车 | 6 | 24 | 16 | 16 | 11 | 6/6 | 4/4 | 4 | 1 | — |
| c5-roller | 单钢轮振动压路机 | 14 | 36 | 29 | 23 | 23 | 14/14 | 4/4 | 5 | 4 | — |

## 2. 成本（同一份用量，峰/谷两口径，单位 ¥）

| 输入 | chat tokens in/out | Search/Fetch | 全高峰 | 全空闲 |
|---|---|---:|---:|---:|
| c1-desert-tractor | 30317 / 25623 | 6 / 18 | ¥0.3856 | ¥0.2528 |
| c2-reach-stacker | 28111 / 15982 | 6 / 28 | ¥0.3541 | ¥0.262 |
| c3-tractor | 30316 / 18579 | 6 / 32 | ¥0.3993 | ¥0.2946 |
| c4-forklift | 30482 / 11298 | 6 / 24 | ¥0.3013 | ¥0.2257 |
| c5-roller | 30611 / 22191 | 6 / 44 | ¥0.4887 | ¥0.3694 |

## 3. 耗时（秒；节点明细见各 case 的 DELIVERY.md）

| 输入 | 总耗时 | 主要节点 (state=ms) |
|---|---:|---|
| c1-desert-tractor | 164.6 | FETCH=148185 · EXTERNAL_DISCOVER=16432 · WRITEBACK=10 · VERIFY=2 |
| c2-reach-stacker | 389.5 | FETCH=290624 · EXTERNAL_DISCOVER=98872 · WRITEBACK=11 · VERIFY=1 |
| c3-tractor | 327.8 | FETCH=262725 · EXTERNAL_DISCOVER=65046 · WRITEBACK=10 · VERIFY=4 |
| c4-forklift | 262.0 | FETCH=193980 · EXTERNAL_DISCOVER=67975 · WRITEBACK=14 · BRIEF_READY=0 |
| c5-roller | 503.7 | FETCH=419996 · EXTERNAL_DISCOVER=83644 · VERIFY=10 · WRITEBACK=10 |

## 4. 缺图归因

- c1-desert-tractor: all_download_failed 1 / no_hits 4 / not_delivered 1
- c2-reach-stacker: gate_or_verify_rejected 3 / no_hits 2 / not_delivered 1
- c3-tractor: gate_or_verify_rejected 1 / not_delivered 6
- c4-forklift: gate_or_verify_rejected 3 / no_hits 2 / not_delivered 5
- c5-roller: not_delivered 9

## 5. 下载质量

| 输入 | hits | downloaded | failed | blocked | gate_pass |
|---|---:|---:|---:|---:|---:|
| c1-desert-tractor | 225 | 195 | 23 | 0 | 190 |
| c2-reach-stacker | 325 | 275 | 50 | 0 | 215 |
| c3-tractor | 450 | 375 | 75 | 0 | 305 |
| c4-forklift | 335 | 270 | 55 | 10 | 150 |
| c5-roller | 750 | 636 | 114 | 0 | 462 |
