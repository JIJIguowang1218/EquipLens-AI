# 检索中 P1 夹具（2026-11-09）

| 属性 | 内容 |
|---|---|
| 阶段 | 检索中（P1） |
| 用途 | 给状态机/检查点/降级/缺口做离线演示与回归 |
| 标签 | `retrieval`、`p1`、`fixtures`、`offline` |
| 不联网 | 是 |
| 不写正式库 | 是 |

## 文件

| 文件 | 内容 |
|---|---|
| `brief-desert.json` | 沙漠牵引车任务单：2 个 research unit（exact / environment） |
| `world-desert.json` | 假世界：库内 1 台（step 被拒）、外检 exact 2 台、environment 1 台 |

## 演示逻辑

```
LIBRARY_SEARCH:
  lib-1：保险杠通过，踏步被拒（wrong_identity）
GAP_CHECK → EXTERNAL_DISCOVER(exact):
  ext-1 / ext-2：保险杠 + 踏步都通过 → u-exact 2/2
GAP_CHECK → DEGRADE(environment):
  ext-3：防护栏 + 踏步通过 → u-env 1/1
DONE
```

## 跑法

```bash
PYTHONPATH=src python -m equiplens.retrieval_engine \
  --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
  --fixtures data-test/retrieval-fixtures-20261109/world-desert.json \
  --run-root data-test/runs --run-id p1-demo
```

产物：`data-test/runs/p1-demo/{state.json,events.jsonl,evidence.json,summary.json}`。

## 说明

- `world-desert.json` 的 `verify` 是人工写的验收结果，不代表真实模型；
- 真实库/真实通道接入后，用同样结构替换 `FakeWorld` 即可；
- 夹具只用于 P1，不进入正式数据。
