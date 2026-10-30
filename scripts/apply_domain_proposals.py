# -*- coding: utf-8 -*-
"""把 domain-bench 的 proposals.json 应用到 data/source_registry.json（带审计输出）。

用法: python tmp/apply_domain_proposals.py data-test/evals/domain-bench-20261030/proposals.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
reg_path = ROOT / "data" / "source_registry.json"
props = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
reg = json.loads(reg_path.read_text(encoding="utf-8"))
known = {s["domain"]: s for s in reg.get("sources", [])}
changes = []

for p in props.get("promote", []):
    if p["domain"] in known:
        known[p["domain"]]["trust"] = "high"
        changes.append(f"promote {p['domain']} → high")
for p in props.get("demote", []):
    if p["domain"] in known:
        known[p["domain"]]["trust"] = "low"
        changes.append(f"demote {p['domain']} → low")
for p in props.get("add", []):
    if p["domain"] not in known:
        reg.setdefault("sources", []).append({
            "domain": p["domain"], "type": "unknown",
            "trust": p["trust"], "design_yield": p["design_yield"],
            "notes": p.get("notes", "domain-bench 发现")})
        changes.append(f"add {p['domain']} ({p['trust']})")

reg["updated_at"] = "2026-10-30"
reg_path.write_text(json.dumps(reg, ensure_ascii=False, indent=1),
                    encoding="utf-8")
print("变更:", changes or "无")
