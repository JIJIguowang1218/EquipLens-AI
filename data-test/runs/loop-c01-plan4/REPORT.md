# C01 在线规划 + 补位 + 重规划 · 12 槽交付（2026-11-10）

## 输入

- 任务单：`brief-m1-desert.json`
- 部件：**前脸（区域）、防护栏、大灯、前轮拱、登车踏步**（区域不参与验收）
- 车槽：12（exact 8 + environment 4）

## 本轮修掉的 loop 设计问题

上一轮只交付 8/12，根因不是“没图”，是 loop 有三个缺陷：

| # | 问题 | 修法 |
|---|---|---|
| 1 | `GAP_CHECK` 在一次发现后就 `DEGRADE`，**没有把候选池排空** | 池里还有候选 → `refill` 继续发现（同层可多次） |
| 2 | 池子空了就降级，**不会重新规划** | 池空且槽未满 → `replan`（LLM + 搜索，最多 2 次） |
| 3 | 规划给的是长名字，**直接被当查询词**，搜不到 | 归一化 `normalize_query`：去括号 → 取型号代码/车系 → 加 6x6 |

另外：`replan` 原先在 `has_more` 之前触发（一开局就白调一次），已调整为先补位、再重规划。

## 日志（本轮新增）

| 文件 | 内容 |
|---|---|
| `api_log.jsonl` | **每次 DeepSeek Search/Fetch/Chat 调用**：接口、状态、耗时、是否计费、成本 |
| `replan_log.jsonl` | 重规划：失败车型、缺口、新增候选数 |
| `citation_log.jsonl` | 引用核验：URL、状态、字符数、命中 token、耗时 |
| `events.jsonl` / `state.json` / `summary.json` | 状态流转与决策（含 `refill` / `replan` / `no_evidence`） |
| `fetch_log.jsonl` | 每张图的抓取与门卫结果（含未通过） |

本轮 API 成本：**35 次调用，$0.02325**（Search $0.00075/次成功；Chat 仅记 token）。

## 结果

| 指标 | 值 |
|---|---:|
| 候选池 | 15 + 重规划 4 + 4 = 23 |
| **车槽** | **12 / 12，DONE** |
| 唯一图 | 47 |
| 过两段式门卫（v4） | 42 |
| 标准 ≥800 | 9 |
| 高清 ≥1200 | 5 |
| 下载失败行 | 20 |
| 引用核验 | 25 次，19 次命中 |
| 预算 | 23 queries / 160 fetches |

### 轨迹

```
LIBRARY_SEARCH(0)
→ GAP_CHECK refill（池中仍有 15）
→ EXTERNAL_DISCOVER(exact 12) → FETCH/VERIFY/FILL → GAP_CHECK refill（7/12）
→ EXTERNAL_DISCOVER(exact 3) → … 7/12
→ GAP_CHECK replan（缺口 5，重规划 4）
→ EXTERNAL_DISCOVER(4) → … 
→ GAP_CHECK replan（缺口 2，重规划 4）
→ EXTERNAL_DISCOVER(no_targets) → DEGRADE(environment)
→ EXTERNAL_DISCOVER(environment 4) → GAP_CHECK done（12/12）
```

## 仍然存在的问题

1. 42 张过门卫里只有 **9 张 ≥800**：沙漠车型的图多来自经销商/资讯页；
2. environment 层只收 2 台（全局已满就停）；
3. 身份/上装校验仍缺（“沙漠车”类结果可能混入不同上装）；
4. 重规划有成本（本轮 $0.023），大规模跑要做预算上限。

## 产物

`audit.html`（47 张图审核）、`fetch_log.jsonl`、`citation_log.jsonl`、`api_log.jsonl`、`replan_log.jsonl`、`evidence.db`、`images/`。
