# plan 并发 A 测试（2026-11-13）

同一份 brief，`plan_candidates.py --concurrency 1` vs `4`，只跑 plan 阶段。

- `SUMMARY.md/json`：5 case 的耗时、候选数、token、单次 chat ms；
- `<case>/{serial,concurrent}/`：`plan.json`、`plan.log`、`api_log.jsonl`（含每次调用 ms）；
- 结论：串行合计 518.3 s → 并发 155.3 s（3.34×）；候选 132 vs 125（噪声内）。
- 生产默认仍是 `--concurrency 1`；本目录只作实验证据。
