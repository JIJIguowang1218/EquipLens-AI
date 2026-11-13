# 交付清单：run

> 任务单：`auto-20261114-024559` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 7 · citation_only 3 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | 东风大多利卡 4吨水罐泡沫消防车（CLW5090GXFP40） | primary | 1 | 12 | degraded/citation_only |
| 2 | 沈阳捷通 PM75 多功能水罐泡沫消防车 | primary | 2 | 36 | degraded |
| 3 | 斯堪尼亚 P310 城市主战消防车 | primary | 3 | 24 | — |
| 4 | 中国重汽 HOWO 泡沫消防车（SGX5191GXFPM80） | primary | 4 | 18 | degraded/citation_only |
| 5 | 五十铃 GIGA 8立方米水泡沫消防车 | primary | 5 | 36 | degraded |
| 6 | CSC5160GXFSG/PM70/E6 水罐/泡沫消防车 | primary | 6 | 30 | degraded/citation_only |
| 7 | 梅赛德斯-奔驰 Atego 1330 4×2 压缩空气泡沫消防车 | primary | 7 | 6 | degraded |
| 8 | 瑞沃 CLW5160GXFSG60 水罐泡沫消防车 | primary | 8 | 6 | degraded |

**备选（随包）**：

- 1. 中联重科 ZLJ5160GXFPM40 泡沫水罐消防车（role=backup，rank=9，30 图）
- 2. 五十铃 4吨水罐/泡沫消防车（QL1110ANKAY）（role=backup，rank=11，30 图）
- 3. TGM18.290B6 QHV5170GXFPM60/M6 泡沫消防车（role=backup，rank=10，6 图）
- 4. FAW 4×2 水罐泡沫消防车（role=backup，rank=12，36 图）

## 二、内部监控（不对用户）

- 下载：hits 408 / downloaded 330 / failed 78 / blocked 0 / gate_pass 300
- 缺图归因：not_delivered 5
- 总耗时：131991 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 9575 |
| FETCH | 46740 |
| VERIFY | 4 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 1533 |
| FETCH | 21517 |
| VERIFY | 1 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2696 |
| FETCH | 49921 |
| VERIFY | 3 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2899 | ¥0.15 | **¥0.4399** |
| 全空闲 | ¥0.1449 | ¥0.15 | **¥0.2949** |

用量：输入 31532 tokens（按未命中计，偏保守）/ 输出 28350 / Search 6 次 / Fetch 24 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\h1-fire\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r3-20261114\h1-fire\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
