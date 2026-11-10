# API 生成的任务单

本目录只放 `scripts/build_brief.py` 从 DeepSeek Chat 生成的任务单：

- `brief-*.json`：通过 `validate_brief` + `schemas/task-brief-v3.schema.json`；
- `brief-*.json.meta.json`：`raw_input / model / skill_version / attempts / usage / llm_payload`。

`brief-c01-auto.json` 与 `brief-c01-auto-r2.json` 是同一输入的两次生成（稳定性对照）：
parts / regions / 8+4 单元一致，个别 `views` 有差异（如 bumper 多了 `side`/`detail`）。

手工 brief 在 `data-test/evals/task-briefs-20261109/`，已标 legacy，不要用于新实验。
