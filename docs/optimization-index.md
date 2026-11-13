# 优化轮次索引（2026-11-13 起）

按时间顺序记录每一轮“提了什么机制、试了什么、结论是什么”。原始数据在 `data-test/`，
实验索引在 `EXPERIMENTS-INDEX.md`，待办在 `backlog-mechanisms-20261114.md`。

| 日期 | 轮次文档 | 主题 | 结论摘要 |
|---|---|---|---|
| 11-13 | `query-optimization-20261113.md` | 判死点、宽抽取 | c1 8/10→10/10（品牌误判修复）；wide 抽取涨候选但离类 |
| 11-13 | `query-kill-chain-20261113.md` | 判死链复盘 | 9 个判死点；去表化修法；离线回放 0 回归 |
| 11-13 | `optimization-round-20261114.md` | A4/B1/A1 | 长查询无需再优；tier 规则落地；来源降权否决 |
| 11-14 | `optimization-round2-20261114.md` | A3/C1/D1 | 英文仅条件可用；标题一致性循环论证；rank 重定义 |
| 11-14 | `a3-ladder-design-20261114.md` | 英文条件档设计 | 品牌识别 33%/43%，只做“有证据 token”的条件档 |
| 11-14 | `optimization-round3-20261114.md` | search_key + 调研 | 条件兜底 3/3 救回；3 份行业调研 |
| 11-14 | `optimization-round4-20261114.md` | Gleaning / 归一化去重 | Gleaning 0 增益否决；归一化 0.9% 重复 |
| 11-14 | `optimization-round5-20261114.md` | 结构化槽位 + 冻结评估 | 见本轮 |

## 文件约定

- 每轮一份 `optimization-roundN-YYYYMMDD.md`；设计类放 `a3-*`/`query-*`；
- 实验数据：`data-test/runs/<topic>-YYYYMMDD/`；评测 JSON：`data-test/evals/`；
- 调研报告：`docs/research/`，索引 `docs/research/README.md`；
- 机制状态只维护在 `backlog-mechanisms-20261114.md`（单一事实源）。
