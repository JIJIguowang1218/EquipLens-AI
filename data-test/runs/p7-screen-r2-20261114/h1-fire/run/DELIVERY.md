# 交付清单：run

> 任务单：`auto-20261114-024559` · 主 8 台 + 备选 4 台 · 状态 DONE
> 交付 8/8 · degraded 8 · citation_only 4 · 备选 4 台

## 一、用户交付物

| # | 车型 | 优先级 | 名次 | 图 | 标记 |
|---:|---|---|---:|---:|---|
| 1 | PM75多功能水罐泡沫消防车 | primary | 1 | 30 | degraded/citation_only |
| 2 | CSC5160GXFSG/PM70/E6 水罐/泡沫消防车 | primary | 2 | 30 | degraded/citation_only |
| 3 | 3500升4*2泡沫水罐消防车 | primary | 3 | 18 | degraded |
| 4 | 中联重科 ZLJ5160GXFPM40 泡沫水罐消防车 | primary | 4 | 30 | degraded |
| 5 | 福田瑞沃水罐泡沫消防车（CLW5160GXFSG60） | primary | 5 | 30 | degraded/citation_only |
| 6 | QHV5170GXFPM60/M6 泡沫消防车 | primary | 6 | 24 | degraded/citation_only |
| 7 | 斯堪尼亚P310城市主战消防车 | primary | 7 | 36 | degraded |
| 8 | 五十铃GIGA 8立方米水泡沫消防车 | primary | 8 | 36 | degraded |

**备选（随包）**：

- 1. 东风大多利卡 4吨水罐泡沫消防车（role=backup，rank=9，24 图）
- 2. 中国重汽 HOWO 泡沫消防车 SGX5191GXFPM80（role=backup，rank=10，24 图）
- 3. 梅赛德斯-奔驰 Atego 1330 4×2 压缩空气泡沫消防车（role=backup，rank=11，6 图）
- 4. 东风 4×2 消防车（SLS5160，6000L 罐）（role=backup，rank=12，18 图）

## 二、内部监控（不对用户）

- 下载：hits 444 / downloaded 372 / failed 72 / blocked 0 / gate_pass 342
- 缺图归因：not_delivered 5
- 总耗时：133447 ms

| 节点 | 耗时(ms) |
|---|---:|
| BRIEF_READY | 0 |
| LIBRARY_SEARCH | 0 |
| FETCH | 0 |
| VERIFY | 0 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 2287 |
| FETCH | 47733 |
| VERIFY | 5 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 0 |
| DEGRADE | 0 |
| EXTERNAL_DISCOVER | 3934 |
| FETCH | 18906 |
| VERIFY | 3 |
| FILL | 0 |
| GAP_CHECK | 0 |
| EXTERNAL_DISCOVER | 11486 |
| FETCH | 49088 |
| VERIFY | 4 |
| GAP_CHECK | 0 |
| DONE | 0 |
| WRITEBACK | 1 |

**API 成本（同一份用量，两种时段口径）**

| 口径 | chat | Search/Fetch | 合计 |
|---|---:|---:|---:|
| 全高峰 | ¥0.2894 | ¥0.14 | **¥0.4294** |
| 全空闲 | ¥0.1447 | ¥0.14 | **¥0.2847** |

用量：输入 31552 tokens（按未命中计，偏保守）/ 输出 28293 / Search 6 次 / Fetch 22 次

## 三、可复用中间产物（给其它环节）

- 任务单：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\h1-fire\brief.json`（分析模块输入）
- 优先级先验：`C:\Users\86136\Desktop\EquipLens-AI\data-test\runs\p7-screen-r2-20261114\h1-fire\plan-ranked.json`
- 审核页：``
- 证据库：``
- 部件图：按 part 分组见 `user_delivery.*.images`（分析/知识库候选）
