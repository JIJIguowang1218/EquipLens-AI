# 分析模块（L5）实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把"图片 → 结构化分析"的契约落成可跑的模块：单台车出 region + 5 部件 + 三词，多视角补证，校验通过后渲染成可审阅的 HTML。

**Architecture:** `analysis.py` 只管"契约与调用"（prompt 组装、provider、校验、多视角合并），不碰数据库与渲染；`scripts/analyze_batch.py` 负责选车取图与落盘；`scripts/build_analysis_review.py` 负责渲染。provider 三态（api/mock/manual）同契约，测试只用 mock。

**Tech Stack:** Python 3.11 标准库（urllib/json），无新增依赖；数据资产 `data/part_taxonomy.json`、`data/style_vocabulary.json`。

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `src/equiplens/analysis.py` | 核心：prompt 组装、API provider、校验、多视角合并 |
| `tests/test_analysis.py` | 离线测试：校验规则、合并规则、三词去重 |
| `scripts/analyze_batch.py` | 选车、取图、逐台调用、落 `analysis.json` |
| `scripts/build_analysis_review.py` | 落 HTML 审阅页（图 + 文本） |

---

### Task 1: 校验器（validate_analysis）

**Files:**
- Create: `src/equiplens/analysis.py`
- Test: `tests/test_analysis.py`

- [ ] **Step 1: 写失败测试**

```python
from equiplens.analysis import validate_analysis

VOCAB = {"stability": ["稳重"], "tough": ["硬朗"], "modern": ["整面化"]}
TAX = {"grille": ["冲孔网板格栅"], "bumper": ["整体式保险杠"]}

def test_tags_must_be_three_distinct_clusters():
    data = {"unit": {"kind": "region", "style_tags": [
        {"tag": "稳重", "cluster": "stability", "evidence": "x"},
        {"tag": "稳重", "cluster": "stability", "evidence": "y"},
        {"tag": "硬朗", "cluster": "tough", "evidence": "z"}]}, "parts": []}
    errs = validate_analysis(data, used=[], vocab=VOCAB, tax=TAX, required_slots=[])
    assert any("同簇" in e for e in errs)

def test_not_visible_cannot_carry_description():
    data = {"unit": {"kind": "region", "style_tags": []},
            "parts": [{"slot": "grille", "visible": "not_visible",
                       "term": "冲孔网板格栅", "form": "有描述"}]}
    errs = validate_analysis(data, used=[], vocab=VOCAB, tax=TAX, required_slots=["grille"])
    assert any("not_visible" in e for e in errs)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `PYTHONPATH=src python tests/test_analysis.py`
Expected: ImportError / NameError

- [ ] **Step 3: 最小实现**

实现 `validate_analysis(data, used, vocab, tax, required_slots)`，检查：三词数量=3、簇互异、词在簇内、evidence 非空、不与 used 冲突；`visible=not_visible` 时 term/form/cmf/intent 全空；term ∈ tax[slot]；必需槽齐全；句长 ≤40。

- [ ] **Step 4: 跑测试确认通过**

Run: `PYTHONPATH=src python tests/test_analysis.py`
Expected: `analysis: N/N 通过`

- [ ] **Step 5: 提交**

```bash
git add src/equiplens/analysis.py tests/test_analysis.py
git commit -m "feat(analysis): 契约校验器——三词/可见性/构型名词表"
```

---

### Task 2: 多视角合并（merge_views）

**Files:**
- Modify: `src/equiplens/analysis.py`
- Test: `tests/test_analysis.py`

- [ ] **Step 1: 写失败测试**

```python
from equiplens.analysis import merge_views

def test_second_view_fills_invisible_part():
    primary = {"unit": {"kind": "region"}, "parts": [
        {"slot": "step", "visible": "not_visible", "term": None, "form": None}]}
    secondary = {"parts": [
        {"slot": "step", "visible": "full", "term": "两级固定踏板", "form": "两级，层间可见"}]}
    merged = merge_views(primary, secondary, view_tag="side")
    step = [p for p in merged["parts"] if p["slot"] == "step"][0]
    assert step["visible"] == "full" and step["source_view"] == "side"
```

- [ ] **Step 2: 跑测试确认失败** → `expected: NameError`

- [ ] **Step 3: 实现**

按可见性排序 `full > partial > not_visible` 覆盖；被覆盖的部件写 `source_view`；主视角 region 不动。

- [ ] **Step 4: 跑测试确认通过**

- [ ] **Step 5: 提交**

```bash
git commit -am "feat(analysis): 多视角补证合并"
```

---

### Task 3: 三词跨车去重（TagLedger）

**Files:**
- Modify: `src/equiplens/analysis.py`
- Test: `tests/test_analysis.py`

- [ ] **Step 1: 写失败测试**

```python
from equiplens.analysis import TagLedger

def test_ledger_avoids_reuse_until_exhausted():
    led = TagLedger({"stability": ["稳重", "沉稳"], "tough": ["硬朗"]})
    a = led.take(["稳重", "硬朗"])
    assert a == ["稳重", "硬朗"]
    assert "稳重" in led.used and "硬朗" in led.used
```

- [ ] **Step 2–5:** 失败 → 实现（记录 used、给 prompt 提供"已用词"、报告级均衡 `max-min<=1` 检查）→ 通过 → 提交。

---

### Task 4: API provider + prompt 组装

**Files:**
- Modify: `src/equiplens/analysis.py`

- [ ] **Step 1: 实现 `build_prompt(vehicle, taxonomy, vocab, slots, used_tags)`**
  只注入本次要分析的槽位词条；带六条文风规则；要求只输出 JSON。
- [ ] **Step 2: 实现 `ApiProvider.call(image_path, prompt)`**
  从 `.env` 读 `LLM_BASE_URL/LLM_API_KEY/LLM_VISION_MODEL`；`reasoning_effort=low`；`max_tokens=12000`；`urllib` 调用；抽取 JSON。
- [ ] **Step 3: 实现 `analyze(provider, vehicle, image, slots, used_tags)`**
  prompt → call → validate → 失败带原因重试一次 → 仍失败标 `needs_review`。
- [ ] **Step 4: 提交**

```bash
git commit -am "feat(analysis): API provider 与 prompt 组装"
```

---

### Task 5: 批处理脚本 + 审阅页

**Files:**
- Create: `scripts/analyze_batch.py`
- Create: `scripts/build_analysis_review.py`

- [ ] **Step 1: `analyze_batch.py`**
  输入：`--vehicles JH6,银河,...`；查库取每台车最大 `hero_lf/hero_rf` 为主图，`side_l/side` 为副图；逐台跑；`not_visible/partial` 的槽用副图补跑一次并合并；写 `out/<vehicle>.json`；打印每个槽的可见性与来源视角。
- [ ] **Step 2: `build_analysis_review.py`**
  读 JSON + 图，渲染单文件 HTML：每车一卡（主图 + 三词 + 前脸分析 + 部件表 + 裁图位）；补证部件标"来源：侧视"。
- [ ] **Step 3: 跑 10 台车**

Run: `PYTHONPATH=src python scripts/analyze_batch.py --vehicles <10 台> --out data-test/analysis-20261031`
Expected: 10 份 JSON，`adhoc_rate=0`，跨车无重词。

- [ ] **Step 4: 生成审阅页并人工看**

Run: `PYTHONPATH=src python scripts/build_analysis_review.py --dir data-test/analysis-20261031`
Expected: `review.html`，每车一卡。

- [ ] **Step 5: 提交**

```bash
git commit -am "feat(analysis): 批处理与审阅页——10 台车验证"
```

---

## 验收

- 单测全绿（离线，不调 API）
- 10 台车 JSON 全部通过 `validate_analysis`
- 三词跨车零复用
- 每个 `not_visible` 槽有补证记录或明确缺口
- 审阅页可打开、图与文对应
