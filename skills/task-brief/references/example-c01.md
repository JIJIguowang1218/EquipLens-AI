# 示例（仅示意，不是模板）

> 这是 2026-11-11 用 C01 输入跑出的一个**正例**，用来说明“分析字段长什么样”。
> **不要照抄车型、部件、理由或数量**；新输入必须重新分析。
> 完整 brief 的格式以 `schemas/task-brief-v3.schema.json` 为准。

```json
{
  "request": {
    "class": "沙漠牵引车",
    "environment": "沙漠/油田工况",
    "base_platform": "6×6 重型卡车底盘",
    "configuration": "6×6",
    "design_questions": ["前脸在沙尘环境下的防护与家族化", "踏步的防滑与离地"]
  },
  "regions": [
    {"region": "front_face", "label": "前脸",
     "views": ["front", "hero_45"],
     "design_axes": ["form_gesture", "proportion", "cmf"]}
  ],
  "parts": [
    {"part": "step", "label": "登车踏步", "kind": "part",
     "location": "side_lower", "part_family": "frame_profile",
     "taxonomy_status": "known", "relation_axis": "environment",
     "design_axes": ["structure", "function_ergonomics", "environment_protection"],
     "views": ["side", "hero_45"], "design_relevance": "strong", "accept": "B",
     "mechanism": ["防滑", "沙尘", "离地高"],
     "why": "沙漠工况下踏步要防沙积、防滑，且离地高度影响登车"},
    {"part": "custom_9d3f2a7c", "label": "涉水喉", "kind": "function",
     "location": "side_cab_rear", "part_family": "function_attachment",
     "taxonomy_status": "new", "relation_axis": "environment",
     "design_axes": ["form_gesture", "function_ergonomics"],
     "views": ["side", "hero_45"], "design_relevance": "conditional", "accept": "B",
     "mechanism": ["进气", "涉水"],
     "why": "用户点名，词表没有；按功能/位置/形态描述，保证可检索"}
  ],
  "assumptions": [
    {"field": "environment", "value": "沙漠/油田工况", "why": "用户原话", "confidence": 0.9}
  ],
  "negative": ["客车", "SUV", "房车", "多车拼图", "内饰", "模型"]
}
```
