# 填槽修复验证（2026-11-13）

用修复后的引擎、**复用原 plan** 复跑 c2 两臂，不重新抓图、不改 plan。

- `c2-with/`：修复前 8 正 + 2 备 → 修复后 **10 正 + 0 备**；
- `c2-without/`：修复前 9 正 + 4 备 → 修复后 **10 正 + 4 备（满）**；
- 每臂含 `brief.json`、`plan-ranked.json`、`run/`（state/DELIVERY/audit/fetch_log）。
