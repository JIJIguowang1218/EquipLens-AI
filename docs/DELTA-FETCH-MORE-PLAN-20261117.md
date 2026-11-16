# Delta 换图开发步骤（待指令执行）

> 状态：**未开始**；等产品负责人完成架构讨论并下指令后，按本文件执行。
> 当前已有：`SessionRunner.delta_edit(seq, replace|remove)`；replace 无新图时保留旧图；
> remove 先删再补；live 实测 `added=0, old_active=true`。缺的是“有界 fetch-more”新图源。

## 0. 前置事实

- `world.fetch(target, part)` 对同一 target 重复调用返回同一批资产；delta reopen 后没有新图。
- 预算：全局 `world.query_count`；delta 目前只限 `max_steps=60`，没有查询/时间上限。
- 交付原则：**最终交付优先**；replace 没新图不缩水；remove 明确删除，补不到要报缺口。

## 1. 步骤

### Step 1：有界 fetch-more（0.5–1 天）

1. `WebWorld.fetch_more(target, part, *, exclude_keys, round_idx)`：
   - 只针对**同一 target**，不换品牌/车型；
   - round 1：在现有查询上加质量/来源变体（如“高清/大图/实拍”），复用 `_search` + 下载/门卫；
   - round 2：翻页或同源变体（若源支持）；
   - 排除 `exclude_keys`（url/sha/asset_id），返回新资产。
2. 预算：每次 delta 最多 **2 轮 × 3 查询，60s**；`world.query_count` 增量超限即停；
   不改变 target/plan/交付主配额。
3. `FakeWorld.fetch_more`：返回 `exclude_keys` 之外的新资产，供单测。
4. `RetrievalEngine.reopen(..., more=True)`：`_state_fetch` 优先调用 `fetch_more`。

### Step 2：接进 delta_edit（0.5 天）

- replace：先 fetch-more → 新图 verified → 加入交付 → 再降级旧图；无新图 → **旧图保持 active**，消息说明。
- remove：先降级旧图 → fetch-more 补 → 有新增则减 `pending_replenish`；无新增保留并报“缺 1 张”。
- 去重：`asset_id`/`url`/`sha1`；同一 seq 重复编辑幂等。
- 预算/时间/轮次记录到返回值和 session 事件；不无限重试。

### Step 3：测试（0.5 天）

**单测（FakeWorld）**
- 有新图：replace active 数不变，旧图 superseded，新图 active；
- 无新图：replace 旧图 active，不 superseded；
- remove 无新图：active -1，`pending_replenish=1`；
- 预算超限：停止，不超 6 查询/60s；
- 重复编辑同一 seq：不重复交付。

**live 3 case（独立 session）**
1. `h2e` replace seq1（当前源大概率无新图）：期望 `added=0, old_active=true`，active 不缩水；
2. `c1e` remove seq1：期望 active -1，`pending_replenish=1`，消息明确；
3. 任一 case 若 fetch-more 拿到新图：期望 active 不变、旧图 superseded、重复 0、查询增量 ≤6。

命令模板：
```bash
# replace
HF_HUB_OFFLINE=1 PYTHONPATH=src python scripts/run_session.py \
  --brief data-test/briefs/m43e/h2e.json --plan data-test/plans/m43e/h2e.json \
  --session data-test/sessions/l2e-h2e.json --run-id l2e-h2e \
  --router rules --no-citation --delta replace --seq 1

# remove
HF_HUB_OFFLINE=1 PYTHONPATH=src python scripts/run_session.py \
  --brief data-test/briefs/m43e/c1e.json --plan data-test/plans/m43e/c1e.json \
  --session data-test/sessions/l2e-c1e.json --run-id l2e-c1e \
  --router rules --no-citation --delta remove --seq 1
```
结果落 `data-test/evals/delta-20261117-*.json`（active before/after、superseded、added、queries、秒、message）。

### Step 4：收敛（0.5 天）

- 若 3 case 通过（含“无新图保留旧图/报缺口”）：S4 可收敛；delta 成熟度标
  **生产可用（best-effort，不保证换到）**，不是“生产生效”。
- 若 fetch-more 能稳定拿到新图：可标“生产生效（受预算限制）”。
- 更新：`stages.json` S4 capabilities、`STAGES.md`、`CODE-INDEX`、`DATA-CHANGELOG`、
  `BACKLOG`（BL-027/028）、badcase BC-S4-017。
- 跑：`check_stages.py`、`check_machine.py`、`run_ledger.py --check`。
- 完成时明确告知：**“S4 收敛，可进架构讨论/分析模块。”**

## 2. 边界与失败处理

- **不新增第三方源**（豆包/Bing 等）——那是 BL-007，另立项；
- **不换 target** 来“凑”新图；
- 无新图是合法结果：replace 保留旧图并说明；remove 报缺口；
- 预算超限直接停，不重试到无限；
- 不改主交付配额/主 target。

## 3. 预计

- 总计 **1–2 天**；live 3 case 约 30–60 分钟；
- 若 Step 1 在现有源上仍拿不到新图：按“best-effort + 明确说明”收敛，不阻塞分析模块。
