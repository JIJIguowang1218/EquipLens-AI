# 域名基准运行手册（domain-bench runbook）

适用：`domain-bench` 的复跑与判读。目的：让 `data/source_registry.json` 的信任等级
保持"有证据、可复现"，不靠记忆和印象。

## 1. 什么时候跑

| 触发 | 时机 | 说明 |
|---|---|---|
| 时间触发 | 每 30 天（开发期可每 2–4 周） | 源会改版/加反爬/停更，信任会腐烂 |
| 事件触发 | 某批 SERP 拦截率 >50%；或连续两批 A 产出为 0；或新域名刚入库 | 立刻复跑，判断是通道问题还是源问题 |
| 版本触发 | 查询模板、筛选规则、来源注册表改动后 | 作为回归基线，确认改动没有破坏产出 |

**当前阶段（开发期）**：手动执行，不需要调度器。
**正式运行期**：由调度器按上表周期执行，人工只看报告与告警。

## 2. 怎么跑

```bash
# 基础（每域 2 页，适合日常）
PYTHONPATH=src python -m equiplens domain-bench scripts/domain-bench-queries.json \
  --data-dir data-test --out data-test/evals/domain-bench-YYYYMMDD

# 复测确认（每域 5 页、换一组查询，用于晋升/降级前）
PYTHONPATH=src python -m equiplens domain-bench scripts/domain-bench-queries-r2.json \
  --data-dir data-test --out data-test/evals/domain-bench-YYYYMMDD-r2 \
  --per-domain 5 --max-anchors 10

# 只重建建议/报告（不重爬，规则改动后用）
PYTHONPATH=src python -m equiplens domain-bench \
  --from-leaderboard data-test/evals/domain-bench-YYYYMMDD/leaderboard.json
```

查询集建议：至少覆盖 4 个类目 × 2 条（车型/部件/定调各一条），两组查询不要重复，
避免同一批页面反复计分。

## 3. 怎么判读

1. **先看通道**：报告首行 `SERP 被拦并退 Bing：N 查询`。若被拦比例高，
   本次结果只能作参考，换时段或换通道重跑；Bing 样本不参与信任分级。
2. **再看样本量**：单页样本（尤其是 4–5K 字的小页）不晋升、不降级，
   只进"保持/观察"。
3. **门槛**（与 `build_proposals` 一致）：
   - 新增：≥2 页成功、正文 ≥5,000 字、有百度通道样本；
   - 晋升：建议等级 high 且现注册表低于 high；
   - 降级：建议等级 none、≥3 页成功、正文 ≥15,000 字、≥2 页百度样本；
   - 其余：保持/观察。
4. **人工复核**：晋升/新增前必须抽查 1–2 篇，确认是真实设计文本（不是转载错的
   车型/参数页）；转载站标注"需核原创性"。

## 4. 结果记到哪

| 产物 | 位置 |
|---|---|
| 报告/排行榜/建议 | `data-test/evals/domain-bench-YYYYMMDD[-rN]/{report.md,leaderboard.json,proposals.json}` |
| 两轮对比 | `data-test/evals/domain-bench-compare-YYYYMMDD.md` |
| 台账 | `docs/test-log.md` 新增 `T18-domainbench-rN` 行（根因/修正/结论） |
| 注册表 | `data/source_registry.json`，note 里写证据（页数/字数/千字产出/复测结果） |

## 5. 已知坑

- **百度 SERP 会间歇性被拦**：同一查询不同时刻结果不同；被拦时先重试一次，仍拦则退 Bing 并在报告标明。
- **子域不是同源**：`mp.weixin.qq.com ≠ qq.com`、`news.qq.com ≠ qq.com`，匹配只做"去 www 同域"。
- **单页高产出是方差**：tcv360/sohu 曾出现 1 页 163–228/千字，样本不足不入库。
- **A 档产出 ≠ 全部价值**：163 等门户 A 产出低，但可能产出 G 档（宏观定调）文本；降级要谨慎，保留 medium 观察。
- **robots 与频率**：遵守 `webchannel.robots_allows` 与 1.2s 间隔，不因基准测试绕规矩。
- **复测必须用新 run_id**：runner 的断点续跑会按 unit 状态复用旧批次，复用 run_id 会拿到旧数据（T18-roster2 踩过）。
- **site: 定向查询不可用**：百度对 site: 查询拦截率极高；Bing RSS 只回栏目页。`source_targeting=site`
  仅作实验开关，默认关闭；替代方向是"品牌名查询"（如"卡车之家 重卡 造型 设计"），需百度恢复后验证。

## 6. 通道降级链（2026-10-30 结论）

- runner 默认链：`auto`（百度，被拦退 Bing）→ **延迟 4s 重试百度** → `bing`。
  依据：百度是间歇性拦截，延迟重试常能恢复；Bing 兜底结果偏官网/商品页、质量差，放最后。
- **已验证不采用**：搜狗（结果被站内提示链接污染，真实结果不可靠）、360che 站内搜索
  （JS 渲染，抓不到结果）、Bing HTML（历史记录不可用）。再遇到新通道候选，先用
  `scripts/` 或 `tmp/` 脚本验证可解析性再接入。
- 若某查询在 auto 阶段被拦并已退 Bing，runner 的下一级（延迟百度）会用新会话重试，
  成功则整批改用新结果，`events.jsonl` 会记录 attempts/channel。
