"""运行状态与检查点：原子写 state.json，追加 events.jsonl。"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


class RunStore:
    def __init__(self, run_root: str | Path, run_id: str):
        self.run_id = run_id
        self.dir = Path(run_root) / run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.dir / "state.json"
        self.events_path = self.dir / "events.jsonl"
        self.evidence_path = self.dir / "evidence.json"
        self.summary_path = self.dir / "summary.json"

    def load(self) -> dict | None:
        if not self.state_path.exists():
            return None
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save(self, state: dict) -> None:
        state["updated_at"] = now_iso()
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        # Windows：杀软/索引/OneDrive 偶尔会短暂占用目标文件，os.replace 报 WinError 5。
        # 重试几次即可；仍失败才抛出，避免把“临时占用”当成运行时错误。
        last = None
        for i in range(6):
            try:
                os.replace(tmp, self.state_path)
                return
            except PermissionError as e:  # noqa: PERF203
                last = e
                time.sleep(0.05 * (i + 1))
        if last is not None:
            raise last

    def append_event(self, event: dict) -> None:
        event = {"ts": now_iso(), **event}
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def read_events(self) -> list[dict]:
        if not self.events_path.exists():
            return []
        rows = []
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def save_evidence(self, rows: list[dict]) -> None:
        self.evidence_path.write_text(
            json.dumps({"run_id": self.run_id, "evidence": rows},
                       ensure_ascii=False, indent=2),
            encoding="utf-8")

    def save_summary(self, summary: dict) -> None:
        self.summary_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8")


def new_state(brief, *, run_id: str) -> dict[str, Any]:
    """初始状态。所有可变字段都显式列出，避免隐式默认。"""
    units = {
        u.unit_id: {
            "unit_id": u.unit_id,
            "tier": u.tier,
            "scope": u.scope,
            "parts": list(u.parts),
            "quota": u.quota,
            "budget": dict(u.budget),
            "stop": u.stop,
            "accepted_targets": [],
        }
        for u in brief.research_units
    }
    return {
        "run_id": run_id,
        "brief_id": brief.brief_id,
        "state": "BRIEF_READY",
        "finished": False,
        "round": 0,
        "tier_index": 0,
        "tier_tried": False,
        "library_done": False,
        "active_source": "",
        "active_targets": [],
        "pending_assets": [],
        "verified_assets": [],
        "verifications": {},
        "targets": {},
        "assets": {},
        "asset_meta": {},
        "final_state": "",
        "units": units,
        "decisions": [],
        "attempts": {},
        "replans": 0,
        "budget_used": {"queries": 0, "models": 0, "fetches": 0, "verifies": 0},
        "coverage": {},
        "gaps": [],
        "assumptions": list(brief.assumptions),
        "updated_at": now_iso(),
    }


def record_decision(state: dict, *, at: str, action: str, reason: str) -> None:
    state["decisions"].append({"at": at, "action": action, "reason": reason,
                               "ts": now_iso()})
