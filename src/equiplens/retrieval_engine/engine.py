"""检索中状态机（P1）：库内优先 → 外检 → 核验 → 填槽 → 降级/停止。

P1 只依赖适配器协议与夹具；不联网、不碰数据库。
状态与事件落盘见 state.py；契约见 contracts.py。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import Asset, Brief, ResearchUnit, Target, Verification
from .state import RunStore, new_state, record_decision


class RetrievalEngine:
    def __init__(self, brief: Brief, world: Any, *, run_root: str | Path,
                 run_id: str, strategy: dict | None = None,
                 evidence_writer=None, max_steps: int = 200):
        self.brief = brief
        self.world = world
        self.store = RunStore(run_root, run_id)
        self.run_id = run_id
        self.strategy = strategy or {}
        self.evidence_writer = evidence_writer
        self.max_steps = max_steps
        self.handlers = {
            "BRIEF_READY": self._state_brief_ready,
            "LIBRARY_SEARCH": self._state_library_search,
            "FETCH": self._state_fetch,
            "VERIFY": self._state_verify,
            "FILL": self._state_fill,
            "GAP_CHECK": self._state_gap_check,
            "EXTERNAL_DISCOVER": self._state_external_discover,
            "DEGRADE": self._state_degrade,
            "DONE": self._state_done,
            "FAILED": self._state_failed,
            "WRITEBACK": self._state_writeback,
        }

    # ---------------------------------------------------------------- public
    def run(self) -> dict:
        state = self.store.load()
        if state is None:
            state = new_state(self.brief, run_id=self.run_id)
            self.store.save(state)
            self.store.append_event({
                "run_id": self.run_id, "from": "", "to": "BRIEF_READY",
                "action": "start"})

        if state.get("finished"):
            return self._summary(state)

        steps = 0
        while not state.get("finished") and steps < self.max_steps:
            before = state["state"]
            handler = self.handlers.get(before)
            if handler is None:
                raise RuntimeError(f"未知状态: {before}")
            handler(state)
            if state["state"] != before:
                self.store.append_event({
                    "run_id": self.run_id, "from": before,
                    "to": state["state"], "action": "transition"})
            self.store.save(state)
            steps += 1

        if not state.get("finished"):
            state["final_state"] = "FAILED"
            state["state"] = "WRITEBACK"
            record_decision(state, at="engine", action="abort",
                            reason=f"max_steps {self.max_steps} exceeded")
            self.store.save(state)

        summary = self._summary(state)
        self.store.save_summary(summary)
        return summary

    # ---------------------------------------------------------------- helpers
    def _unit(self, state: dict, unit_id: str) -> dict:
        return state["units"][unit_id]

    def _unit_obj(self, unit: dict) -> ResearchUnit:
        return ResearchUnit(
            unit_id=unit["unit_id"], tier=unit["tier"], scope=unit["scope"],
            parts=tuple(unit["parts"]), quota=int(unit["quota"]),
            budget=dict(unit.get("budget") or {}), stop=unit.get("stop", ""))

    def _target_obj(self, t: dict) -> Target:
        return Target(target_id=t["target_id"], model=t["model"],
                      source=t["source"], tier=t["tier"],
                      parts=tuple(t["parts"]), unit_id=t.get("unit_id", ""))

    def _add_targets(self, state: dict, targets: list[Target]) -> None:
        for t in targets:
            if not t.unit_id:
                continue
            rec = t.to_dict()
            prev = state["targets"].get(t.target_id)
            if prev is None:
                rec["unit_ids"] = [t.unit_id]
                state["targets"][t.target_id] = rec
                continue
            # 同一个车型可能被不同层级重复发现：不能覆盖，否则后一层会把前面
            # 已积累的证据“抢走”（M1 实测：exact 0/2，证据全被 environment 接管）。
            units = set(prev.get("unit_ids") or [prev.get("unit_id")])
            units.add(t.unit_id)
            prev["unit_ids"] = sorted(u for u in units if u)
            prev["unit_id"] = prev.get("unit_id") or t.unit_id
            prev["parts"] = sorted(set(prev.get("parts") or [])
                                   | set(rec.get("parts") or []))
            prev["identity_kind"] = prev.get("identity_kind") or rec.get("identity_kind")
            for k in ("intent_rank", "intent_band", "intent_reason", "role", "pinned"):
                if rec.get(k) and not prev.get(k):
                    prev[k] = rec[k]

    def _coverage(self, state: dict) -> dict:
        cov = {}
        for unit_id, unit in state["units"].items():
            accepted = len(unit.get("accepted_targets") or [])
            cov[unit_id] = {
                "quota": int(unit["quota"]),
                "accepted": accepted,
                "filled": accepted >= int(unit["quota"]),
            }
        state["coverage"] = cov
        return cov

    def _global_accepted(self, state: dict) -> int:
        ids: set[str] = set()
        for unit in state["units"].values():
            ids.update(unit.get("accepted_targets") or [])
        return len(ids)

    def _slot_target(self) -> int:
        if self.brief.vehicle_slots > 0:
            return self.brief.vehicle_slots
        return sum(int(u.quota) for u in self.brief.research_units)

    def _gaps(self, state: dict) -> list[str]:
        cov = self._coverage(state)
        return [uid for uid, c in cov.items() if not c["filled"]]

    def _budget_cap(self, key: str) -> int | None:
        value = self.brief.budget.get(key)
        return int(value) if value is not None else None

    # ---------------------------------------------------------------- states
    def _state_brief_ready(self, state: dict) -> None:
        state["state"] = "LIBRARY_SEARCH"

    def _state_library_search(self, state: dict) -> None:
        if not state.get("library_done"):
            targets: list[Target] = []
            for unit_id, unit in state["units"].items():
                got = self.world.library_targets(self._unit_obj(unit))
                for t in got:
                    t.unit_id = unit_id
                targets.extend(got)
            self._add_targets(state, targets)
            state["active_source"] = "library"
            state["active_targets"] = [t.target_id for t in targets]
            state["library_done"] = True
            record_decision(state, at="LIBRARY_SEARCH", action="library_scanned",
                            reason=f"库内候选 {len(targets)} 个")
        else:
            state["active_source"] = "library"
            state["active_targets"] = [tid for tid, t in state["targets"].items()
                                       if t.get("source") == "library"]
        state["state"] = "FETCH"

    def _state_fetch(self, state: dict) -> None:
        # 去重键 = (asset, part)：一张整车图可以同时是 bumper / step / side_guard 的证据；
        # 旧实现按 asset_id 全局去重，导致后面的部件永远拿不到资产（M1 loop 实测 0/2）。
        seen = set(state.get("verified_assets") or [])
        seen.update(f"{a['asset_id']}:{a['part']}"
                    for a in state.get("pending_assets") or [])
        for tid in state.get("active_targets") or []:
            target = state["targets"].get(tid)
            if not target:
                continue
            target_obj = self._target_obj(target)
            att = state.setdefault("attempts", {}).setdefault(tid, {})
            att["fetched"] = True
            att.setdefault("assets", 0)
            for part in target_obj.parts:
                for asset in self.world.fetch(target_obj, part):
                    key = f"{asset.asset_id}:{part}"
                    if key in seen:
                        continue
                    seen.add(key)
                    state["pending_assets"].append(asset.to_dict())
                    state.setdefault("asset_meta", {})[asset.asset_id] = asset.to_dict()
                    state.setdefault("assets", {}).setdefault(tid, {}) \
                        .setdefault(part, []).append(asset.asset_id)
                    state["budget_used"]["fetches"] = \
                        int(state["budget_used"].get("fetches", 0)) + 1
        state["state"] = "VERIFY"

    def _state_verify(self, state: dict) -> None:
        verified = set(state.get("verified_assets") or [])
        remaining = [a for a in state.get("pending_assets") or []
                     if f"{a['asset_id']}:{a['part']}" not in verified]
        for row in remaining:
            # 必须带上 title/model：否则 RuleVerifier 的型号/构型校验会被静默跳过
            asset = Asset(asset_id=row["asset_id"], target_id=row["target_id"],
                          part=row["part"], view=row.get("view", ""),
                          width=int(row.get("width") or 0),
                          height=int(row.get("height") or 0),
                          url=row.get("url", ""),
                          title=row.get("title", ""),
                          model=row.get("model", ""))
            v = self.world.verify(asset, asset.part)
            key = f"{asset.asset_id}:{asset.part}"
            state["verifications"][key] = v.to_dict()
            state["verified_assets"].append(key)
            att = state.setdefault("attempts", {}).setdefault(asset.target_id, {})
            att["verified"] = int(att.get("verified", 0)) + 1
            if v.accepted:
                att["accepted"] = int(att.get("accepted", 0)) + 1
            state["budget_used"]["verifies"] = \
                int(state["budget_used"].get("verifies", 0)) + 1
        state["pending_assets"] = []
        state["state"] = "FILL"

    def _state_fill(self, state: dict) -> None:
        for unit in state["units"].values():
            unit["accepted_targets"] = []
        role_rank = {"primary": 0, "backup": 1}
        ordered = sorted(
            enumerate(state["targets"].items()),
            key=lambda kv: (0 if kv[1][1].get("pinned") else 1,
                            role_rank.get(str(kv[1][1].get("role") or ""), 2),
                            int(kv[1][1].get("intent_rank") or 10 ** 9),
                            kv[0]))
        used_assets: set[str] = set()
        for _idx, (tid, target) in ordered:
            for uid in target.get("unit_ids") or [target.get("unit_id")]:
                unit = state["units"].get(uid)
                if not unit:
                    continue
                # 每台车至少 1 张通过核验的图；且不能和已占槽 target 复用同一 asset。
                acc_assets = [
                    aid for part in unit["parts"]
                    for aid in state.get("assets", {}).get(tid, {}).get(part, [])
                    if state["verifications"].get(f"{aid}:{part}", {}).get("accepted")
                    and aid not in used_assets
                ]
                ok = bool(acc_assets)
                # 引用页已证实该车型：有图即可占槽（整车型号证据在 target 上）
                if not ok and target.get("citation_ok"):
                    ok = any(
                        aid not in used_assets
                        for part in unit["parts"]
                        for aid in state.get("assets", {}).get(tid, {}).get(part, []))
                # P0：有 scene 元数据时，整车槽必须有 overview；part-only 不单独占槽。
                if ok:
                    meta = state.get("asset_meta") or {}
                    known = [aid for aid in acc_assets if aid in meta]
                    has_scene_meta = any(bool(meta[aid].get("scene")) for aid in known)
                    if has_scene_meta and not any(
                            meta[aid].get("scene") == "single_vehicle" for aid in known):
                        # P0 评审：hard reject 会改变 composition；默认只标记，供人工/排序
                        target["part_only"] = True

                quota = int(unit.get("quota") or 0) or 10 ** 9
                if self._global_accepted(state) >= self._slot_target():
                    break
                if (ok and tid not in unit["accepted_targets"]
                        and len(unit["accepted_targets"]) < quota):
                    unit["accepted_targets"].append(tid)
                    used_assets.update(acc_assets)
                    state.setdefault("attempts", {}).setdefault(tid, {})["filled"] = True
        state["state"] = "GAP_CHECK"

    def _state_gap_check(self, state: dict) -> None:
        gaps = self._gaps(state)
        if self._global_accepted(state) >= self._slot_target():
            record_decision(state, at="GAP_CHECK", action="done",
                            reason=f"全局槽位 {self._global_accepted(state)}/"
                                   f"{self._slot_target()} 已满")
            state["gaps"] = []   # 全局满了就不报单元缺口（单元配额只是建议）
            state["state"] = "DONE"
            return
        # 候选池还有货：先补位（同层可多次发现）
        more = getattr(self.world, "has_more", None)
        if callable(more) and more():
            record_decision(state, at="GAP_CHECK", action="refill",
                            reason=f"槽位 {self._global_accepted(state)}/"
                                   f"{self._slot_target()}，池中仍有候选")
            state["state"] = "EXTERNAL_DISCOVER"
            return
        # 池子空了且槽位未满：尝试重规划（只对“规划池模式”的世界生效），最多 2 次
        can = getattr(self.world, "can_replan", None)
        replan = getattr(self.world, "replan", None)
        if (callable(can) and can() and callable(replan)
                and int(state.get("replans", 0)) < 4):
            failed = [tid for tid, t in state["targets"].items()
                      if not any(state.get("assets", {}).get(tid, {}).values())]
            need = self._slot_target() - self._global_accepted(state)
            try:
                got = replan(failed, need)
            except Exception:  # noqa: BLE001
                got = 0
            if got:
                state["replans"] = int(state.get("replans", 0)) + 1
                record_decision(state, at="GAP_CHECK", action="replan",
                                reason=f"缺口 {need}，重规划 {got} 个候选")
                state["state"] = "EXTERNAL_DISCOVER"
                return
        # 候选池还有货：继续补位（同层可以多次发现，不能一次没满就降级）
        more = getattr(self.world, "has_more", None)
        if callable(more) and more():
            record_decision(state, at="GAP_CHECK", action="refill",
                            reason=f"槽位 {self._global_accepted(state)}/"
                                   f"{self._slot_target()}，池中仍有候选")
            state["state"] = "EXTERNAL_DISCOVER"
            return
        if not state.get("tier_tried"):
            state["state"] = "EXTERNAL_DISCOVER"
            return
        state["state"] = "DEGRADE"

    def _state_external_discover(self, state: dict) -> None:
        cap = self._budget_cap("max_queries")
        if cap is not None and int(state["budget_used"].get("queries", 0)) >= cap:
            record_decision(state, at="EXTERNAL_DISCOVER", action="budget_exhausted",
                            reason=f"queries {state['budget_used']['queries']} >= {cap}")
            state["state"] = "FAILED"
            return
        gaps = self._gaps(state)
        current_tier = self._tier_name(state)
        gaps = [uid for uid in gaps
                if state["units"][uid].get("tier") == current_tier]
        targets: list[Target] = []
        for unit_id in gaps:
            unit = state["units"][unit_id]
            got = self.world.external_targets(self._unit_obj(unit))
            for t in got:
                t.unit_id = unit_id
            targets.extend(got)
        if not targets:
            record_decision(state, at="EXTERNAL_DISCOVER", action="no_targets",
                            reason="当前层级没有候选")
            state["state"] = "DEGRADE"
            return
        self._add_targets(state, targets)
        state["active_source"] = f"external:{self._tier_name(state)}"
        state["active_targets"] = [t.target_id for t in targets]
        state["tier_tried"] = True
        state["budget_used"]["queries"] = \
            int(state["budget_used"].get("queries", 0)) + len(targets)
        state["budget_used"]["models"] = \
            int(state["budget_used"].get("models", 0)) + len(targets)
        record_decision(state, at="EXTERNAL_DISCOVER", action="discover",
                        reason=f"层级 {self._tier_name(state)} 候选 {len(targets)} 个")
        state["state"] = "FETCH"

    def _tier_name(self, state: dict) -> str:
        idx = int(state.get("tier_index", 0))
        tiers = self.brief.tiers or ["exact"]
        return tiers[idx] if idx < len(tiers) else "exhausted"

    def _state_degrade(self, state: dict) -> None:
        current = self._tier_name(state)
        state["tier_index"] = int(state.get("tier_index", 0)) + 1
        if state["tier_index"] < len(self.brief.tiers or []):
            state["tier_tried"] = False
            record_decision(state, at="DEGRADE", action="open_next_tier",
                            reason=f"{current} 耗尽，开 {self._tier_name(state)}")
            state["state"] = "EXTERNAL_DISCOVER"
        else:
            record_decision(state, at="DEGRADE", action="all_tiers_exhausted",
                            reason="所有层级耗尽，报缺口")
            state["state"] = "FAILED"

    def _state_done(self, state: dict) -> None:
        state["final_state"] = "DONE"
        state["state"] = "WRITEBACK"

    def _state_failed(self, state: dict) -> None:
        state["final_state"] = "FAILED"
        state["state"] = "WRITEBACK"

    def _state_writeback(self, state: dict) -> None:
        rows = []
        for unit_id, unit in state["units"].items():
            for tid in unit.get("accepted_targets") or []:
                target = state["targets"].get(tid, {})
                for part in unit["parts"]:
                    ids = state.get("assets", {}).get(tid, {}).get(part, [])
                    for aid in ids:
                        v = state["verifications"].get(f"{aid}:{part}")
                        if v and v.get("accepted"):
                            meta = state.get("asset_meta", {}).get(aid, {})
                            rows.append({
                                "unit_id": unit_id,
                                "target_id": tid,
                                "model": target.get("model", ""),
                                "part": part,
                                "asset_id": aid,
                                "view": meta.get("view", ""),
                                "width": meta.get("width", 0),
                                "height": meta.get("height", 0),
                                "source_url": meta.get("url", ""),
                                "channel": meta.get("channel", ""),
                                **v,
                            })
                            break
        self.store.save_evidence(rows)
        if self.evidence_writer is not None:
            self.evidence_writer(rows)
        state["state"] = state.get("final_state") or "DONE"
        state["finished"] = True

    # ---------------------------------------------------------------- summary
    def _delivery(self, state: dict) -> dict:
        """交付守卫：要求 N 槽就必须有 N 个车型，不足要显式报 short + 缺口。

        `degraded` = 已交付但没有任何一张图达到 confirmed 身份的车型数
        （靠 probable/unknown + 引用页兜底进来的，必须让调用方看见）。
        """
        target = self._slot_target()
        accepted = self._global_accepted(state)
        verifs = state.get("verifications") or {}
        by_target = state.get("assets") or {}
        accepted_ids = {tid for u in state["units"].values()
                        for tid in (u.get("accepted_targets") or [])}
        degraded = 0
        degraded_targets: list[str] = []
        citation_only: list[str] = []
        for tid, parts in by_target.items():
            if tid not in accepted_ids:
                continue   # 抓过图但没占槽的车型不算进交付质量
            ids = {a for items in (parts or {}).values() for a in (items or [])}
            idents = {v.get("identity") for k, v in verifs.items()
                      if k.split(":")[0] in ids and v.get("accepted")}
            if ids and not idents:
                citation_only.append(tid)   # 一张核验通过的图都没有，只靠引用页
            if ids and "confirmed" not in idents:
                degraded += 1
                degraded_targets.append(tid)
        missing = max(0, target - accepted)
        bonus_models = sorted(tid for tid, parts in by_target.items()
                              if tid not in accepted_ids
                              and any((v or []) for v in (parts or {}).values()))
        bonus_images = sum(len({a for v in (by_target[m] or {}).values() for a in (v or [])})
                           for m in bonus_models)
        return {
            "required": target,
            "delivered": accepted,
            "missing": missing,
            "degraded": degraded,
            "degraded_targets": degraded_targets,
            "citation_only": len(citation_only),
            "citation_only_targets": citation_only,
            "bonus": {"models": len(bonus_models), "images": bonus_images},
            "status": "complete" if accepted >= target else "short",
        }

    def _summary(self, state: dict) -> dict:
        cov = self._coverage(state)
        accepted = self._global_accepted(state)
        target = self._slot_target()
        # 全局槽位满了就不报单元缺口（单元配额是建议，不是硬性）
        gaps = ([] if accepted >= target
                else [uid for uid, c in cov.items() if not c["filled"]])
        return {
            "run_id": self.run_id,
            "brief_id": self.brief.brief_id,
            "state": state.get("final_state") or state["state"],
            "slots": {"target": target, "accepted": accepted,
                      "filled": accepted >= target},
            "delivery": self._delivery(state),
            "coverage": cov,
            "gaps": gaps,
            "accepted_targets": {
                uid: list(u.get("accepted_targets") or [])
                for uid, u in state["units"].items()
            },
            "budget_used": dict(state.get("budget_used") or {}),
            "decisions": list(state.get("decisions") or []),
            "state_path": str(self.store.state_path),
            "events_path": str(self.store.events_path),
            "evidence_path": str(self.store.evidence_path),
        }
