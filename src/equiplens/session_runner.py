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
                 store_path: str | Path | None = None, max_steps: int = 240,
                 router=None, router_name: str = "rules"):
        self.brief_dict = brief
        self.world = world
        self.run_root = str(run_root)
        self.run_id = run_id or f"sess-{time.strftime('%Y%m%d-%H%M%S')}"
        self.session_id = session_id or self.run_id
        self.engine = RetrievalEngine(Brief.from_dict(brief), world,
                                      run_root=self.run_root, run_id=self.run_id,
                                      max_steps=max_steps)
        self.state = self.engine._load_or_init()
        self.router_name = router_name
        self.router = router
        self.session = Session(brief, session_id=self.session_id, router=router)
        self.store_path = Path(store_path) if store_path else \
            Path("data-test/sessions") / f"{self.session_id}.json"
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
            "created_from_text": getattr(self, "created_from_text", ""),
            "router_name": self.router_name,
            "session": self.session.to_dict(),
            "steps": self.steps,
            "applied": self.applied,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.store_path.write_text(json.dumps(payload, ensure_ascii=False, indent=1),
                                   encoding="utf-8")
        return self.store_path

    @classmethod
    def load(cls, path: str | Path, world: Any, router=None) -> "SessionRunner":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        runner = cls(payload["brief"], world,
                     run_root=payload.get("run_root") or "data-test/runs",
                     run_id=payload.get("run_id"),
                     session_id=payload.get("session_id"),
                     store_path=path, router=router,
                     router_name=payload.get("router_name") or "rules")
        runner.session = Session.from_dict(payload.get("session") or {})
        runner.session.router = router
        runner.created_from_text = payload.get("created_from_text") or ""
        runner.steps = int(payload.get("steps") or 0)
        runner.applied = int(payload.get("applied") or 0)
        return runner

    @classmethod
    def create_from_text(cls, text: str, api_key: str, *, run_root: str | Path = "data-test/runs",
                         run_id: str | None = None, session_id: str | None = None,
                         store_path: str | Path | None = None, router=None,
                         build_world=None, chat_fn=None,
                         session_context: dict | None = None,
                         brief_kwargs: dict | None = None) -> "SessionRunner":
        """M6 首轮建单：第一句走 S0 正式链路生成 brief，**不经过 router/patch**。"""
        from .briefing import generate_brief
        out = generate_brief(text, api_key, use_taskspec=True,
                             session_context=session_context, chat_fn=chat_fn,
                             **(brief_kwargs or {}))
        brief = out["brief"]
        world = build_world(brief) if build_world else None
        runner = cls(brief, world, run_root=run_root, run_id=run_id,
                     session_id=session_id, store_path=store_path, router=router,
                     router_name="llm" if router else "rules")
        runner.created_from_text = text
        runner.save()
        return runner

    # ---------------- 交互 ----------------
    def _stage(self) -> str:
        st = self.state or {}
        if st.get("finished") or st.get("state") in ("DELIVERED", "DONE"):
            return "delivered"
        if st.get("state") in ("BRIEF_READY", ""):
            return "pre_run"
        return "running"

    def send(self, text: str, *, msg_id: str = "", result: dict | None = None) -> dict:
        # 同一轮里连着说两句时，先把上一条的 pending 在边界落掉，
        # 否则 interrupt 会覆盖 pending（2026-11-16 实测 applied=0）。
        if self.session.pending and self.state.get("state") == "FETCH":
            self._apply_at_boundary()
        if (self.session.pending and (self.state.get("finished")
                                      or self.state.get("state") in ("DELIVERED", "DONE"))):
            self.session.apply_pending()
        res = self.session.interrupt(text, msg_id=msg_id, result=result, stage=self._stage())
        if (not res.get("clarify") and self.session.pending
                and (self.state.get("finished")
                     or self.state.get("state") in ("DELIVERED", "DONE"))):
            # 交付后没有 FETCH 边界，会话类 patch 直接落地
            self.session.apply_pending()
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
        ENGINE_TARGETS = {"fetch.filters.views", "fetch.parts", "fetch.filters.quality",
                          "plan.negative", "plan.add_targets", "fill.quota",
                          "plan.quantity_per_model"}
        engine_p = [p for p in self.session.pending if p.target in ENGINE_TARGETS]
        session_p = [p for p in self.session.pending if p.target not in ENGINE_TARGETS]
        out = {"applied": [], "added_targets": [], "negative": []}
        if engine_p:
            out = self.engine.apply_patches(self.state, [p.as_dict() for p in engine_p])
            # 只有真落地了才清引擎类 pending：首轮空 FETCH（无 target）不能吞 patch
            if out.get("applied"):
                self.session.apply_pending(engine_p)
                self.applied += len(out.get("applied") or [])
        if session_p:
            self.session.apply_pending(session_p)
        return out

    def step(self) -> dict:
        self._apply_at_boundary()
        self.state = self.engine.step(self.state)
        self.steps += 1
        if not self.state.get("finished"):
            self.session.last_checkpoint = self.state.get("state") or ""
        self.save()
        return self.status()

    def run_until(self, state_name: str, max_steps: int = 80,
                  require_targets: bool = False) -> dict:
        """推进引擎直到到达某个状态（默认要求有 target 的 FETCH），用于多轮模拟。"""
        for _ in range(max(1, max_steps)):
            st = self.state
            if st.get("finished"):
                break
            if st.get("state") == state_name and (not require_targets or st.get("active_targets")):
                if self.session.pending and st.get("state") == "FETCH":
                    self._apply_at_boundary()
                break
            self.step()
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
        report = any(p.get("target") == "delivery.report" for p in self.session.patches)
        delivery_pref = (self.session.preferences or {}).get("delivery") or {}
        return {"session_id": self.session_id, "run_id": self.run_id,
                "report_requested": report,
                "delivery_format": delivery_pref.get("format"),
                "pending_replenish": (self.session.preferences or {}).get("pending_replenish") or 0,
                "gated_actions": sum(1 for e in self.session.events
                                     if e.get("kind") == "gated_action"),
                "engine_state": self.state.get("state"),
                "delivered": delivery.get("delivered"),
                "required": delivery.get("required"),
                "missing": delivery.get("missing"),
                "degraded": delivery.get("degraded"),
                "session": self.session.status(),
                "steps": self.steps, "applied": self.applied,
                "store_path": str(self.store_path)}
