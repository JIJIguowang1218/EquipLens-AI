# 正式链路状态机（STAGES）

> 作用：回答“**现在真实跑的是哪一版代码**”，而不是仓库里存在哪些版本。
> 机器可读： [`docs/stages.json`](stages.json)；检查：`PYTHONPATH=src python scripts/check_stages.py`。
> 规则：`active` = 真实业务使用；`silent` = 保留但默认不可达（不告警、不写日志）；`planned` = 已设计未实现。
> 任何机制替换都必须同时更新本文件、`stages.json`、`CODE-INDEX.md`、`DATA-CHANGELOG.md`。

## 1. 总表（2026-11-15）

| 阶段 | 状态 | 当前版本 | 正式入口 | 静默下线 |
|---|---|---|---|---|
| **S0 用户输入识别 / 任务单** | active | **taskspec-v0.4** | `taskspec_llm.parse` → `taskspec.normalize/validate` → `briefing.apply_taskspec`；CLI `build_brief.py` 默认走此路径 | `briefing.generate_brief(use_taskspec=False)`（库默认，兼容/评估）；`build_brief.py --legacy-brief` |
| **S1 第一段检索** | active | p8-idmatch | `planning.build_query_plan`、`scripts/plan_candidates.py`、`scripts/rank_plan.py`（intent N+4） | — |
| **S2 第二段检索** | active | p8-idmatch | `retrieval_engine/web.py`、`gate.py`、`identity.py` | — |
| **S3 交付验收** | active | manifest-v1 | `scripts/build_delivery_manifest.py` | — |
| **S4 Loop / 反馈 / 记忆** | planned | session-v0 | 未实现 | — |
| **S5 产品/工程** | n/a | — | 不驱动代码 | — |

## 2. S0 正式链路

```
用户文本
  → taskspec_llm.parse（LLM，v0.4 prompt）
  → taskspec.normalize（固定枚举/软硬分流/配额/去重/提问策略）
  → taskspec.validate（结构校验）
  → briefing.apply_taskspec（class/env/config/台数覆盖 + 挂载 taskspec）
  → brief.json（s0.mechanism="taskspec", version="v0.4"）
```

旧机制（**静默**，默认不可达）：

- `briefing.generate_brief` 的库默认仍是 `use_taskspec=False`（为了不破坏评估脚本/历史调用）；
- CLI 只有显式 `--legacy-brief` 才会回退到“一次 LLM 直接出 brief”的旧路径；
- 两条路径都不打印弃用警告（按“下线静默”要求），但 `meta.s0.mechanism` 会记录实际走的哪条。

## 3. 如何检查

```bash
PYTHONPATH=src python scripts/check_stages.py
```

检查内容：
1. 每个 `active` 阶段的入口文件/符号存在；
2. 每个 `legacy` 条目必须标 `silent` 且符号存在；
3. active 阶段不能没有入口。

如果检查失败，说明状态机文件与代码不一致——**先修状态机，再跑业务**。

## 4. 变更流程

1. 新机制先落 `stages.json`（`active`），旧机制移到 `legacy` 并标 `silent`；
2. 更新 `CODE-INDEX.md` 的“正式/legacy”标注；
3. 在 `DATA-CHANGELOG.md` 记录替换原因、影响面、回滚方式；
4. 跑 `check_stages.py` + 相关单测；
5. 禁止“代码里已经切了但状态机没改”，也禁止“状态机改了但入口没接”。

## 5. 已知缺口

- `briefing.generate_brief` 的库默认仍是旧路径（CLI 已是新路径）；是否把库默认也切成 `use_taskspec=True`，等 S0-05 session 接口稳定后再定；
- S4（Loop/反馈）仍是 planned，`stages.json` 里没有入口，属预期；
- S0 的 prompt 在 `taskspec_llm.py`，若未来改 prompt 版本，必须同步 `stages.json` 的 `version` 和 `brief.s0.version`。
