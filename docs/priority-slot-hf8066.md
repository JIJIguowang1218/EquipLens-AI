# 优先级占槽与 HF8066 丢失（2026-11-12）

## 现象

- 360 baseline：HF8066（intent rank 6，primary）有 assets、verifier accepted、占槽；
- Baidu 未预筛：HF8066 有 assets，但 verifications 全是 wrong_config/unknown，未占槽；
- Baidu 预筛后：HF8066 **没有 fetch_log 行、没有 assets**，未进入证据链，未占槽。

## 当前机制

1. `WebWorld._plan_targets` 按 `pinned > primary > backup > intent_rank` 排序，按 unit quota 取批；
2. `_state_fetch` 对 active targets 抓图，再把 asset 写入 `state.assets`；
3. `_state_verify` 按 asset×part 核验；
4. `_state_fill` 按 `pinned > role > intent_rank` 遍历，**但只接受已有 accepted 证据的 target**；
5. 配额满即停，剩余 target 即使优先级高也不再补抓/补验。

## 结论

- priority 只保证**尝试顺序**，不保证**预留槽/补抓/补验**；
- 高优先级 target 一旦没有 accepted 证据，就会被后面的 accepted target 顶掉；
- 预筛后 HF 甚至连 fetch 行都没有，说明它没有进入抓取/验证，不是被“坏图挤掉”，而是**证据链没覆盖到**；
- 未预筛时是另一种情况：HF assets 存在，但标题全错，verifier 拒绝，仍被顶掉。

## 需要补的机制（不在本轮实现）

- 高优先级 target 的 fetch/verify **attempt 日志**：确认是否真的被抓过；
- preferred target **保留槽位或补抓/补验**，而不是只排序；
- 不能靠“更多平台/更多图”解决；先保证 priority target 有证据。

## 风险

- 预留槽位会降低其他 target 的覆盖率；
- 补抓/补验会增加成本；
- 必须先测，不直接改 normal。
