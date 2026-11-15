# -*- coding: utf-8 -*-
"""S0-05 Session 状态机（无网络）。

职责：跨 run 的会话状态、软/硬打断、patch 队列、checkpoint 应用、交付去重、
轮次上限与持久化。**不包含检索策略**；引擎仍是内层 Job 状态机。
"""
from __future__ import annotations

import copy
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class SessionState(str, Enum):
    IDLE = "IDLE"
    ANALYZING = "ANALYZING"
    CLARIFYING = "CLARIFYING"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


ALLOWED_TARGETS = {
    "fetch.filters.views", "fetch.filters.quality", "fetch.parts",
    "plan.add_targets", "plan.negative", "fill.quota",
    "verify.blacklist", "fill.replace", "scope.ratio",
    "plan.quantity", "plan.configuration", "session.reset",
    "delivered.remove", "delivered.replace",
    "session.pause", "session.resume",
}
HARD_TARGETS = {"scope.ratio", "plan.quantity", "plan.configuration", "session.reset",
                "delivered.remove", "delivered.replace", "session.pause"}
DESTRUCTIVE_TARGETS = {"delivered.remove", "delivered.replace", "session.reset"}
DEFAULT_MAX_ROUNDS = 5
DELTA_QUERY_RATIO = 0.25
DELTA_FETCH_RATIO = 0.20


@dataclass
class Patch:
    target: str
    op: str = "set"
    value: object = None
    confidence: float = 0.9
    destructive: bool = False
    enforce: str = "soft"
    source_msg_id: str = ""
    note: str = ""
    patch_id: str = field(default_factory=lambda: "p-" + uuid.uuid4().hex[:8])
    base_version: int = 1

    def as_dict(self) -> dict:
        return {
            "patch_id": self.patch_id, "base_version": self.base_version,
            "target": self.target, "op": self.op, "value": self.value,
            "confidence": self.confidence, "destructive": self.destructive,
            "enforce": self.enforce,
            "source_msg_id": self.source_msg_id, "note": self.note,
        }


def classify_text(text: str) -> dict:
    """规则版 router 基线（M2 用；M3 会加 LLM，规则保留做校验/兜底）。"""
    t = (text or "").strip()
    low = t.lower()
    out = {"intent": "modify", "hard": False, "targets": [], "destructive": False,
           "confirm": False, "confidence": 0.8, "reason": "", "asset_index": None}
    import re as _re0
    _m = _re0.search(r"第\s*([一二三四五六七八九十\d]+)\s*张", t)
    if _m:
        _v = _m.group(1)
        _cn = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6,
               "七": 7, "八": 8, "九": 9, "十": 10}
        out["asset_index"] = int(_v) if _v.isdigit() else _cn.get(_v[0])

    def add(target, reason):
        if target not in out["targets"]:
            out["targets"].append(target)
        out["reason"] = reason

    import re as _re
    if any(k in low for k in ("重新来", "全部重来", "重做一遍", "全部重做",
                              "全都不要", "全部不要", "重新选", "全部重选")):
        out.update(hard=True, destructive=True, confirm=True, enforce="hard")
        add("session.reset", "重大调整，先确认")
        return out
    if "品牌" in t and ("不要" in t or "换成" in t):
        out["enforce"] = "hard"
        add("plan.negative", "排除旧品牌")
        add("plan.add_targets", "补入新品牌")
        return out
    if ("数量" in t or "台数" in t) and any(k in t for k in ("改成", "改为", "调到", "加到")):
        out.update(hard=True, enforce="hard")
        add("plan.quantity", "修改总量，需重排交付")
        return out
    if any(k in t for k in ("6×6", "6x6", "8×8", "8x8", "4×2", "4x2")) and any(k in t for k in ("换", "改")):
        out.update(hard=True, enforce="hard")
        add("plan.configuration", "修改驱动构型，需重排候选")
        return out
    clear_target = bool(_re.search(r"第\s*[一二三四五六七八九十\d]+\s*张", t)) or bool(_re.search(r"[A-Za-z]{2,}\d{2,}", t))
    image_ctx = clear_target or any(k in t for k in ("张", "图", "照片"))
    destructive_verb = any(k in low for k in ("删", "去掉", "换掉", "换成"))
    if destructive_verb and image_ctx and clear_target:
        out.update(hard=False, destructive=True, confirm=False, enforce="hard")
        if "删" in low or "去掉" in low:
            add("delivered.remove", "目标明确：降级旧图，不删除")
        else:
            add("delivered.replace", "目标明确：降级旧图并补新图")
        return out
    if destructive_verb and image_ctx:
        out.update(hard=False, destructive=True, confirm=True, enforce="hard")
        add("delivered.remove", "未指明哪张/哪个型号，先确认")
        return out
    if ("数量" in t or "台数" in t) and any(k in t for k in ("改成", "改为", "调到")):
        out.update(hard=True, enforce="hard")
        add("plan.quantity", "修改总量，需重排交付")
        return out
    if any(k in t for k in ("6×6", "6x6", "8×8", "8x8", "4×2", "4x2")) and any(k in t for k in ("换", "改")):
        out.update(hard=True, enforce="hard")
        add("plan.configuration", "修改驱动构型，需重排候选")
        return out
    if any(k in low for k in ("改成", "改做", "换类目", "换个类目", "只要精确",
                              "不要邻近", "比例改", "邻近改")):
        out.update(hard=True, confirm=False, enforce="hard")
        add("scope.ratio", "范围/类目切换，需重启受影响节点")
        return out
    if any(k in low for k in ("先停", "暂停", "等一下", "停一下")):
        out.update(hard=True)
        add("session.pause", "暂停当前 run")
        return out
    if any(k in low for k in ("继续", "恢复", "接着跑")):
        add("session.resume", "恢复")
        return out

    parts = ("格栅", "保险杠", "大灯", "吊臂", "支腿", "踏步", "后视镜",
             "罐体", "料斗", "机罩", "配重", "护栏", "前脸格栅")
    if any(p in t for p in parts):
        add("fetch.parts", "部件细节")
        return out
    if any(k in t for k in ("正脸", "前脸", "侧面", "45", "车尾", "顶部", "角度")):
        add("fetch.filters.views", "视角要求")
        return out
    if any(k in t for k in ("高清", "清晰", "水印", "分辨率")):
        add("fetch.filters.quality", "质量要求")
        return out
    if any(k in t for k in ("再加", "再补", "多找", "多来", "多给")):
        if any(k in t for k in ("品牌", "奔驰", "沃尔沃", "陕汽", "徐工", "三一", "中联")):
            add("plan.add_targets", "增加品牌/车型")
        else:
            add("fill.quota", "增加数量")
        return out
    if any(k in t for k in ("不要", "排除", "去掉", "别给")):
        out["enforce"] = "hard"
        add("plan.negative", "排除是硬约束；检索侧 soft 打断，FILL 过滤 + 负词")
        return out
    if any(k in t for k in ("不对", "不是", "错了", "搞错")):
        out["enforce"] = "hard"
        add("verify.blacklist", "纠正错误款型")
        add("fill.replace", "替换错误图")
        return out
    if any(k in t for k in ("再找", "加两个", "加两台", "加点")):
        add("plan.add_targets", "扩充候选")
        return out

    out.update(intent="question", confidence=0.4, reason="无法判定，需澄清")
    return out


class Session:
    def __init__(self, brief: dict, *, session_id: str = "", max_rounds: int = DEFAULT_MAX_ROUNDS,
                 router=None):
        self.session_id = session_id or "s-" + uuid.uuid4().hex[:8]
        self.router = router  # callable(text, context) -> result dict；None 时用规则版
        self.brief = copy.deepcopy(brief or {})
        self.max_rounds = max_rounds
        self.state = SessionState.PLANNING
        self.version = 1
        self.brief_versions = [{"v": 1, "hash": str(abs(hash(json.dumps(self.brief, sort_keys=True, ensure_ascii=False))))}]
        self.pending: list[Patch] = []
        self.patches: list[dict] = []
        self.events: list[dict] = []
        self.delivered: list[dict] = []
        self.blacklist: list[dict] = []
        self.preferences: dict = {}
        self.rounds = 0
        self.last_checkpoint = "PLANNING"
        self._seen_msgs: set[str] = set()
        self._event("created")

    # ---------- 基础 ----------
    def _event(self, kind: str, **kw) -> None:
        self.events.append({"at": round(time.time(), 3), "kind": kind, **kw})

    def context(self) -> dict:
        req = (self.brief or {}).get("request") or {}
        return {"class": req.get("class") or "",
                "targets": (self.brief or {}).get("targets") or [],
                "delivered": {"count": len(self.delivered), "last_round": self.version,
                              "assets": [{"index": i + 1, "asset_id": d.get("asset_id") or d.get("sha1"),
                                          "model": d.get("model"), "status": d.get("status")}
                                         for i, d in enumerate(self.delivered[:20])]},
                "last_patches": self.patches[-3:],
                "preferences": self.preferences}

    def status(self) -> dict:
        return {"session_id": self.session_id, "state": self.state.value,
                "version": self.version, "rounds": self.rounds,
                "pending": [p.as_dict() for p in self.pending],
                "delivered": len(self.delivered), "last_checkpoint": self.last_checkpoint}

    def _bump(self) -> None:
        self.version += 1
        self.rounds += 1
        self.brief_versions.append({"v": self.version,
                                    "hash": str(abs(hash(json.dumps(self.brief, sort_keys=True, ensure_ascii=False))))})

    # ---------- 输入 ----------
    def interrupt(self, text: str, *, msg_id: str = "", result: dict | None = None) -> dict:
        msg_id = msg_id or "m-" + uuid.uuid4().hex[:8]
        if msg_id in self._seen_msgs:
            return {"ok": True, "duplicate": True, "status": self.status()}
        self._seen_msgs.add(msg_id)
        if self.rounds >= self.max_rounds:
            self._event("rejected_max_rounds", msg_id=msg_id)
            return {"ok": False, "error": "max_rounds", "status": self.status()}
        res = result
        if res is None:
            if self.router:
                try:
                    res = self.router(text, self.context())
                except Exception:  # noqa: BLE001
                    res = classify_text(text)
            else:
                res = classify_text(text)
        self._event("user_msg", msg_id=msg_id, text=text[:120], result=res)
        if not res.get("targets"):
            self.state = SessionState.CLARIFYING
            return {"ok": True, "intent": res.get("intent"), "clarify": True,
                    "question": "你想改哪一部分？（视角/数量/品牌/删除/范围）", "status": self.status()}
        patches = [Patch(target=t, value={"text": text, "asset_index": res.get("asset_index")},
                         confidence=res.get("confidence", 0.8),
                         destructive=bool(res.get("destructive")),
                         enforce=res.get("enforce", "soft"),
                         source_msg_id=msg_id, note=res.get("reason", ""), base_version=self.version)
                   for t in res["targets"]]
        for p in patches:
            if p.target not in ALLOWED_TARGETS:
                return {"ok": False, "error": f"bad_target:{p.target}", "status": self.status()}
        self.pending = patches
        if res.get("destructive") and res.get("confirm"):
            self.state = SessionState.CLARIFYING
            return {"ok": True, "clarify": True, "patches": [p.as_dict() for p in patches],
                    "question": "这会删除/替换已交付内容，确认执行吗？", "status": self.status()}
        if res.get("hard"):
            self.state = SessionState.PAUSED
            return {"ok": True, "hard": True, "patches": [p.as_dict() for p in patches],
                    "status": self.status()}
        if self.state in (SessionState.PLANNING, SessionState.IDLE):
            self.state = SessionState.RUNNING
        return {"ok": True, "hard": False, "patches": [p.as_dict() for p in patches],
                "status": self.status()}

    def confirm(self, accept: bool = True) -> dict:
        if self.state != SessionState.CLARIFYING or not self.pending:
            return {"ok": False, "error": "nothing_to_confirm", "status": self.status()}
        if not accept:
            self.pending = []
            self.state = SessionState.PLANNING
            self._event("confirm_rejected")
            return {"ok": True, "accepted": False, "status": self.status()}
        self.apply_pending()
        self._event("confirm_accepted")
        return {"ok": True, "accepted": True, "status": self.status()}

    # ---------- 执行 ----------
    def start(self) -> None:
        self.state = SessionState.RUNNING
        self._event("run_started")

    def checkpoint(self, job_state: str = "FETCH") -> dict:
        self.last_checkpoint = job_state
        self.state = SessionState.RUNNING
        self._event("checkpoint", job_state=job_state)
        if self.pending:
            self.apply_pending()
        return self.status()

    def apply_pending(self) -> None:
        active_snapshot = [d for d in self.delivered if d.get("status") == "active"]
        for p in self.pending:
            self.patches.append(p.as_dict())
            self.brief.setdefault("session_patches", []).append(p.as_dict())
            idx = (p.value or {}).get("asset_index") if isinstance(p.value, dict) else None
            if p.target == "session.reset":
                for d in self.delivered:
                    if d.get("status") == "active":
                        d["status"] = "superseded"
                        d["superseded_by"] = p.patch_id
            elif p.target in ("delivered.remove", "delivered.replace",
                              "verify.blacklist", "fill.replace"):
                # 只降级目标资产；不物理删除
                hit = None
                if idx and 0 < idx <= len(active_snapshot):
                    hit = active_snapshot[idx - 1]
                if hit is not None:
                    hit["status"] = "superseded"
                    hit["superseded_by"] = p.patch_id
                if p.target == "verify.blacklist":
                    self.blacklist.append({"patch_id": p.patch_id, "value": p.value,
                                           "asset": (hit or {}).get("asset_id") or (hit or {}).get("sha1")})
        self.pending = []
        self._bump()
        self.state = SessionState.PLANNING

    def resume(self) -> dict:
        if self.state not in (SessionState.PAUSED, SessionState.PLANNING):
            return {"ok": False, "error": f"cannot_resume:{self.state.value}"}
        self.apply_pending()
        self.state = SessionState.RUNNING
        self._event("resumed")
        return {"ok": True, "status": self.status()}

    def pause(self) -> dict:
        self.state = SessionState.PAUSED
        self._event("paused")
        return {"ok": True, "status": self.status()}

    # ---------- 交付 ----------
    @staticmethod
    def asset_key(asset: dict) -> str:
        return "|".join(str(asset.get(k) or "") for k in ("url", "sha1", "model", "target"))

    def deliver(self, assets: list[dict]) -> dict:
        added, skipped = [], []
        for a in assets or []:
            key = self.asset_key(a)
            if any(self.asset_key(d) == key and d.get("status") == "active" for d in self.delivered):
                skipped.append(key)
                continue
            item = dict(a, status="active", round=self.version)
            self.delivered.append(item)
            added.append(key)
        self.state = SessionState.DELIVERED
        self._event("delivered", added=len(added), skipped=len(skipped))
        return {"ok": True, "added": added, "skipped": skipped, "status": self.status()}

    # ---------- 持久化 ----------
    def to_dict(self) -> dict:
        return {"session_id": self.session_id, "state": self.state.value, "version": self.version,
                "brief": self.brief, "brief_versions": self.brief_versions,
                "patches": self.patches, "events": self.events, "delivered": self.delivered,
                "blacklist": self.blacklist, "preferences": self.preferences,
                "rounds": self.rounds, "max_rounds": self.max_rounds,
                "last_checkpoint": self.last_checkpoint}

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        s = cls(data.get("brief") or {}, session_id=data.get("session_id") or "",
                max_rounds=data.get("max_rounds") or DEFAULT_MAX_ROUNDS)
        s.state = SessionState(data.get("state", "PLANNING"))
        s.version = data.get("version", 1)
        s.brief_versions = data.get("brief_versions") or []
        s.patches = data.get("patches") or []
        s.events = data.get("events") or []
        s.delivered = data.get("delivered") or []
        s.blacklist = data.get("blacklist") or []
        s.preferences = data.get("preferences") or {}
        s.rounds = data.get("rounds", 0)
        s.last_checkpoint = data.get("last_checkpoint", "PLANNING")
        return s
