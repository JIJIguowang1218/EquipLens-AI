# -*- coding: utf-8 -*-
"""L1 Session runner：入口 / 持久化 / 驱动引擎 / 边界应用 patch。

设计边界（2026-11-16）：
- Session 只管跨轮状态（patch/deliver/events），不复制引擎状态；
- 引擎仍是确定性 Job；runner 在状态边界把 pending patch 交给 `engine.apply_patches`；
- 持久化两份：引擎 state（RunStore 已有）+ session JSON（本模块）。
- 这是**原型入口**，不是生产 CLI；S4 仍 planned。
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from .retrieval_engine import RetrievalEngine
from .retrieval_engine.contracts import Brief
from .session import Session


class SessionRunner:
    def __init__(self, brief: dict, world: Any, *, run_root: str | Path = "data-test/runs",
                 run_id: str | None = None, session_id: str | None = None,
                 store_path: str | Path | None = None, max_steps: int = 240):
        self.brief_dict = brief
        self.world = world
        self.run_root = str(run_root)
        self.run_id = run_id or f"sess-{time.strftime('%Y%m%d-%H%M%S')}"
        self.session_id = session_id or self.run_id
        self.engine = RetrievalEngine(Brief.from_dict(brief), world,
                                      run_root=self.run_root, run_id=self.run_id,
                                      max_steps=max_steps)
        self.state = self.engine._load_or_init()
        self.session = Session(brief, session_id=self.session_id)
        self.store_path = Path(store_path) if store_path else \
            Path("data/sessions") / f"{self.session_id}.json"
        self.steps = 0
        self.applied = 0

    # ---------------- 持久化 ----------------
    def save(self) -> Path:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "run_root": self.run_root,
            "brief": self.brief_dict,
            "session": self.session.to_dict(),
            "steps": self.steps,
            "applied": self.applied,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.store_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
        return self.store_path

    @classmethod
    def load(cls, path: str | Path, world: Any) -> "SessionRunner":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        runner = cls(payload["brief"], world,
                     run_root=payload.get("run_root") or "data-test/runs",
                     run_id=payload.get("run_id"),
                     session_id=payload.get("session_id"),
                     store_path=path)
        runner.session = Session.from_dict(payload.get("session") or {})
        runner.steps = int(payload.get("steps") or 0)
        runner.applied = int(payload.get("applied") or 0)
        return runner

    # ---------------- 交互 ----------------
    def send(self, text: str, *, msg_id: str = "", result: dict | None = None) -> dict:
        res = self.session.interrupt(text, msg_id=msg_id, result=result)
        self.save()
        return res

    def confirm(self, accept: bool = True) -> dict:
        res = self.session.confirm(accept)
        self.save()
        return res

    def status(self) -> dict:
        return {"session": self.session.status(),
                "engine_state": self.state.get("state"),
                "finished": bool(self.state.get("finished")),
                "steps": self.steps, "applied": self.applied,
                "pending": len(self.session.pending)}

    # ---------------- 驱动 ----------------
    def _apply_at_boundary(self) -> dict | None:
        """在 FETCH 边界把 pending patch 交给引擎（M4.3 语义）。"""
        if self.state.get("state") != "FETCH" or not self.session.pending:
            return None
        patches = [p.as_dict() for p in self.session.pending]
        out = self.engine.apply_patches(self.state, patches)
        self.session.apply_pending()
        self.applied += len(out.get("applied") or [])
        return out

    def step(self) -> dict:
        self._apply_at_boundary()
        self.state = self.engine.step(self.state)
        self.steps += 1
        if not self.state.get("finished"):
            self.session.last_checkpoint = self.state.get("state") or ""
        self.save()
        return self.status()

    def run(self, max_steps: int | None = None) -> dict:
        limit = max_steps or self.engine.max_steps
        while not self.state.get("finished") and self.steps < limit:
            self.step()
        if self.state.get("finished") and not self.session.delivered:
            assets = self._delivered_assets()
            if assets:
                self.session.deliver(assets)
        if self.state.get("finished"):
            summary = self.engine._summary(self.state)
            self.engine.store.save_summary(summary)
        self.save()
        return self.summary()

    def _delivered_assets(self) -> list[dict]:
        meta_all = self.state.get("asset_meta") or {}
        out: list[dict] = []
        for _uid, unit in (self.state.get("units") or {}).items():
            for tid in unit.get("accepted_targets") or []:
                for _part, ids in ((self.state.get("assets") or {}).get(tid) or {}).items():
                    for aid in ids or []:
                        meta = meta_all.get(aid) or {}
                        if not meta:
                            continue
                        out.append({"asset_id": aid, "url": meta.get("url") or "",
                                    "model": meta.get("model") or "",
                                    "target": tid})
        return out

    def summary(self) -> dict:
        delivery = (self.engine._summary(self.state).get("delivery") or {})
        return {"session_id": self.session_id, "run_id": self.run_id,
                "engine_state": self.state.get("state"),
                "delivered": delivery.get("delivered"),
                "required": delivery.get("required"),
                "missing": delivery.get("missing"),
                "degraded": delivery.get("degraded"),
                "session": self.session.status(),
                "steps": self.steps, "applied": self.applied,
                "store_path": str(self.store_path)}
