# W1-HD 批次（web-smoke-hd-20261109）

| 属性 | 内容 |
|---|---|
| 阶段/模块 | 检索中 / web-smoke |
| 测试 | W1-HD |
| 日期 | 2026-11-09 |
| 源 | 360 |
| 策略 | 原查询 + 高清 + 大图（`search_images_hd(..., hd=True)`） |
| 样本 | 10 查询 × 8 候选 |
| 结果 | 73 候选 / 35 门卫 / 自动 4 / 人工 3 |

## 看什么

- `report.md`：汇总与明细；
- `report.json`：机器可读；
- `review.html`：35 张门卫通过图；
- `all-downloads.html`：**51 张下载成功图**（含门卫未通过），带 PASS/FAIL 标记；
- `all-downloads/`：全部下载成功图；
- `MANUAL-REVIEW.md`：人工复核（4 张自动可用里 1 张是拼图，真正 3 张全是 C7H）；
- `images/`：只存门卫通过图。

## 说明

与 `web-smoke-20261109`（基础阶梯）对照：HD 阶梯人工可用 1→3，但仍远低于 W1 验收（≥10）。
