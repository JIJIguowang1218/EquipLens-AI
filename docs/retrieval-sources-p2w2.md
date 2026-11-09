# 源路由与健康（P2-W2，2026-11-09）

| 属性 | 内容 |
|---|---|
| 阶段 | **检索中**（`EXTERNAL_DISCOVER` 前后的源选择） |
| 模块 | `src/equiplens/retrieval_engine/sources.py` |
| 状态 | P2-W2 骨架完成：健康度、熔断、24h 缓存、SearXNG/Tavily 适配器、路由 |
| 测试 | `tests/test_retrieval_sources.py` **5/5** |
| 未做 | 真实 SearXNG/Tavily 联调（缺实例/API key）；E5 源对照未跑 |

---

## 1. 源的分层

```
SourceRouter
  ├─ 360（直连图源，current primary）
  ├─ SearXNG（聚合器，自托管；可再扇出 Bing/Google 等）
  └─ Tavily（付费搜索 API；图片能力需实测）
```

三者都是 `(query, limit, model) -> (hits, status)` 的适配器；路由只负责顺序、健康、缓存，不替源做判断。

## 2. 健康度 / 熔断 / 缓存

| 机制 | 行为 |
|---|---|
| **健康度** | 每个源记录 `calls / ok / empty / blocked / consecutive_failures / last_status` |
| **熔断** | 连续 2 次 `blocked`/`error` → `open_until = now + 300s`；期间跳过该源 |
| **缓存** | 同一 `query/limit/model` 24h 内复用；命中直接返回，不再打源 |
| **顺序** | 360 → SearXNG → Tavily；第一个非空即停；被拦/空结果换下一个 |
| **诊断** | 每次返回 `[{channel, status, returned}]`，记录 `circuit_open/cached` |

状态文件默认在 `data-test/runs/<run_id>/source_health.json` 和 `source_cache.json`，不污染正式库。

## 3. 适配器

### SearXNG

- 需要自托管实例，并开启 `format=json` 与 `categories=images`；
- 适配器请求 `{base}/search?q=...&format=json&categories=images`；
- 解析 `results[].img_src / thumbnail_src / width / height`；
- 图片覆盖取决于实例启用了哪些引擎，中文工程车覆盖**未实测**。

### Tavily

- 需要 API key；
- 请求 `/search`，`include_images=true`；
- 解析 `images`（字符串或 `{url,title}`）；
- 图片能力与中文覆盖**未实测**，代码按防御式解析写，后续按真实响应调整。

## 4. 跑法

```bash
# 360 + 本地 SearXNG
PYTHONPATH=src python -m equiplens retrieval-run \
  --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
  --web-only --models "豪沃6X6,德龙X3000" \
  --searxng http://127.0.0.1:8080 \
  --run-root data-test/runs --run-id web-searxng

# 360 + Tavily
PYTHONPATH=src python -m equiplens retrieval-run \
  --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
  --web-only --models "豪沃6X6,德龙X3000" \
  --tavily-key "$TAVILY_API_KEY" \
  --run-root data-test/runs --run-id web-tavily
```

## 5. E5 源对照（待跑）

| 项 | 内容 |
|---|---|
| 样本 | 20 条中文工程车查询（5 车型 × 4 视角/部件） |
| 源 | 360 / SearXNG / Tavily / Bing / 官网（可选） |
| 指标 | blocked 率、下载成功、门卫通过、长边≥1200、人工可用、耗时、成本 |
| 决策 | 主源、备源、熔断阈值、缓存 TTL |

**现在不能跑 E5 的原因**：没有 SearXNG 实例和 Tavily key；代码只做了适配器骨架与离线测试。

## 6. 已知限制

1. 360 仍是唯一实测可用的源；W1-HD 只有 3 张人工可用（全 C7H）。
2. SearXNG/Tavily 未联调；解析字段可能需按真实响应调整。
3. 门卫仍会误判多车拼图；需要补“多车/拼图”检测。
4. 下载回退（原图失败→缩略图）还没接进 `_download_and_gate`。
5. 健康度/熔断只按源，不按域名/查询类型细分。
