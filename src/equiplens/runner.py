"""批次执行 loop：重试策略 + 降级链 + 断点续跑。

机制借鉴（不引入框架运行时）：
- Temporal：Activity 重试策略语义（有限尝试/退避）、幂等与断点续跑、事件记录；
- Crawlee：重试耗尽后的兜底（failed_request_handler）、可重试/不可重试错误区分；
- LangGraph：条件边式的降级分支（通道链，每级成功即停）；
- OpenAI Agents SDK：有界循环（max_attempts）与护栏（LOCKED 约束不在此模块内）。

设计约束：
- 本模块只做"控制面"，不碰 robots/配额/账本/schema 等不变量（它们在 corpus/webchannel）；
- collect 与 grade 以可调用对象注入，便于离线测试与替换；
- 单元状态落盘为 JSON（原子写），重启可续跑；已达标单元直接跳过。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

# 这些状态不是"重试能解决"的（Crawlee no_retry 语义）
NON_RETRYABLE_STATUSES = ("robots_denied", "too_short", "source_skipped",
                          "blocked_url")


@dataclass
class RetryPolicy:
    max_attempts: int = 2
    initial_ms: int = 1500
    backoff: float = 2.0

    def delay_ms(self, attempt: int) -> int:
        """第 attempt 次尝试前的等待（1 起）。"""
        return int(self.initial_ms * (self.backoff ** max(0, attempt - 1)))


@dataclass
class Contract:
    """单元验收契约：不达标即进入降级/重试。"""
    min_saved: int = 2
    min_candidates: int = 1
    max_failure_ratio: float = 0.8


@dataclass
class Unit:
    unit_id: str
    plan: dict
    contract: Contract = field(default_factory=Contract)
    channels: list[dict] = field(default_factory=lambda: [
        {"serp_channel": "auto"}, {"serp_channel": "bing"}])


@dataclass
class UnitResult:
    unit_id: str
    status: str  # ok | degraded | failed
    attempts: int
    channel: str
    batch_id: str
    saved: int
    candidates: int
    blockers: list[str] = field(default_factory=list)
    report: dict | None = None


class UnitStateStore:
    """单元状态：state_root/<unit_id>.json，原子写。"""

    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, unit_id: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in unit_id)
        return self.root / f"{safe}.json"

    def load(self, unit_id: str) -> dict | None:
        p = self._path(unit_id)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def save(self, unit_id: str, state: dict) -> None:
        p = self._path(unit_id)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                       encoding="utf-8")
        tmp.replace(p)


def _saved(report: dict) -> int:
    return sum(1 for r in report.get("index", []) if r.get("status") == "saved")


def _hard_failed(report: dict) -> int:
    return sum(1 for r in report.get("index", [])
               if str(r.get("status", "")).startswith(
                   ("fetch_error", "fetch_failed", "robots_denied", "too_short")))


def _candidates(grade: dict | None) -> int:
    if not grade:
        return 0
    return sum(int(d.get("a_count", 0)) for d in grade.get("docs", []))


def evaluate(report: dict, grade: dict | None, contract: Contract) -> tuple[bool, list[str]]:
    """契约判定：返回 (是否达标, 阻塞原因列表)。"""
    saved, failed = _saved(report), _hard_failed(report)
    cand = _candidates(grade)
    blockers: list[str] = []
    if saved < contract.min_saved:
        blockers.append(f"low_yield: saved {saved} < {contract.min_saved}")
    if cand < contract.min_candidates:
        blockers.append(f"no_candidates: A 段 {cand} < {contract.min_candidates}")
    ratio = failed / (failed + saved) if (failed + saved) else 0.0
    if ratio > contract.max_failure_ratio:
        blockers.append(f"high_failure: {ratio:.0%} > {contract.max_failure_ratio:.0%}")
    return not blockers, blockers


def run_unit(unit: Unit, *, collect, grade, data_dir: Path | str,
             state_root: Path | str | None = None,
             policy: RetryPolicy | None = None, sleep=time.sleep) -> UnitResult:
    """执行一个单元：契约 → 重试（同通道）→ 降级（换通道）→ 有限停止。

    collect(plan) -> report{outdir, index, batch_id, summary}
    grade(outdir)  -> {docs:[{a_count}], metrics:{...}}
    """
    policy = policy or RetryPolicy()
    data_dir = Path(data_dir)
    store = UnitStateStore(state_root) if state_root else None

    # 断点续跑：已达标且批次目录存在 → 直接复用
    if store:
        st = store.load(unit.unit_id)
        if st and st.get("status") == "ok":
            bdir = Path(st.get("outdir") or (data_dir / "corpus" /
                                             str(st.get("batch_id", ""))))
            if (bdir / "index.json").exists():
                return UnitResult(
                    unit_id=unit.unit_id, status="ok", attempts=st["attempts"],
                    channel=st.get("channel", ""), batch_id=st.get("batch_id", ""),
                    saved=st.get("saved", 0), candidates=st.get("candidates", 0),
                    report={"batch_id": st.get("batch_id"),
                            "outdir": str(bdir), "index": []})

    attempts = 0
    best: tuple[int, dict, dict | None] = (-1, {}, None)
    blockers: list[str] = []
    for attempt in range(1, policy.max_attempts + 1):
        for ch in unit.channels:
            attempts += 1
            if attempts > 1:
                sleep(policy.delay_ms(attempt) / 1000.0)
            plan = {**unit.plan, **ch}
            try:
                report = collect(plan)
            except Exception as e:  # noqa: BLE001
                blockers = [f"collect_error: {type(e).__name__}"]
                continue
            g = None
            try:
                g = grade(report.get("outdir"))
            except Exception:  # noqa: BLE001
                g = None
            ok, why = evaluate(report, g, unit.contract)
            saved = _saved(report)
            if saved > best[0]:
                best = (saved, report, g)
            if store:
                store.save(unit.unit_id, {
                    "unit_id": unit.unit_id, "status": "ok" if ok else "degraded",
                    "attempts": attempts, "channel": ch.get("serp_channel", ""),
                    "batch_id": report.get("batch_id", ""),
                    "outdir": report.get("outdir", ""),
                    "saved": saved,
                    "candidates": _candidates(g), "blockers": why,
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                })
            if ok:
                return UnitResult(unit.unit_id, "ok", attempts,
                                  ch.get("serp_channel", ""),
                                  report.get("batch_id", ""), saved,
                                  _candidates(g), [], report)
            blockers = why
    _, best_rep, best_g = best
    status = "degraded" if best_rep and _saved(best_rep) > 0 else "failed"
    return UnitResult(unit.unit_id, status, attempts, "", 
                      best_rep.get("batch_id", ""), _saved(best_rep),
                      _candidates(best_g), blockers, best_rep or None)
