"""运行日志：按真实 AI 产品的运行轨迹记录时间、token 估算、工具调用与阶段。

设计原则:
- 每次运行一个 run_id 目录: <data_dir>/runs/<run_id>/
- events.jsonl 追加式事件流（run_start/stage_*/tool_call/llm_call/decision/run_end）
- summary.json 结束时汇总（时长/阶段/工具/指标/产物）
- 无 LLM API 时，token 用启发式估算并显式标注 est=True；接入网关后传实际 usage 即可替换。
"""

from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


def _now() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def estimate_tokens(text: str) -> int:
    """粗略 token 估算：CJK 约 1 字/token，ASCII 约 4 字符/token。仅供记账参考。"""
    if not text:
        return 0
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return max(1, cjk + (len(text) - cjk) // 4)


class RunLog:
    def __init__(self, root: Path, run_id: str | None = None,
                 meta: dict | None = None):
        self.run_id = run_id or (
            f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}")
        self.dir = Path(root) / "runs" / self.run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.events_path = self.dir / "events.jsonl"
        self.started_at = _now()
        self._t0 = time.perf_counter()
        self.meta = meta or {}
        self.stages: list[dict] = []
        self.tools: list[dict] = []
        self.decisions: list[dict] = []
        self.llm_calls: list[dict] = []
        self._write("run_start", meta=self.meta)

    def _write(self, event: str, **fields) -> None:
        rec = {"ts": _now(), "event": event, **fields}
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def event(self, event: str, **fields) -> None:
        self._write(event, **fields)

    @contextmanager
    def stage(self, name: str, **fields):
        t0 = time.perf_counter()
        self._write("stage_start", stage=name, **fields)
        try:
            yield
        except Exception as e:  # noqa: BLE001
            dur = (time.perf_counter() - t0) * 1000
            err = f"{type(e).__name__}: {e}"
            self.stages.append({"stage": name, "duration_ms": round(dur, 1),
                                "status": "error", "error": err, **fields})
            self._write("stage_end", stage=name, duration_ms=round(dur, 1),
                        status="error", error=err, **fields)
            raise
        else:
            dur = (time.perf_counter() - t0) * 1000
            self.stages.append({"stage": name, "duration_ms": round(dur, 1),
                                "status": "ok", **fields})
            self._write("stage_end", stage=name, duration_ms=round(dur, 1),
                        status="ok", **fields)

    def tool(self, name: str, args: dict | None = None, result: dict | None = None,
             duration_ms: float | None = None, status: str = "ok") -> None:
        rec = {"name": name, "args": args or {}, "result": result or {},
               "duration_ms": None if duration_ms is None else round(duration_ms, 1),
               "status": status}
        self.tools.append(rec)
        self._write("tool_call", **rec)

    def llm(self, model: str, prompt_version: str, input_text: str = "",
            output_text: str = "", input_tokens: int | None = None,
            output_tokens: int | None = None, **fields) -> None:
        it = input_tokens if input_tokens is not None else estimate_tokens(input_text)
        ot = output_tokens if output_tokens is not None else estimate_tokens(output_text)
        rec = {"model": model, "prompt_version": prompt_version,
               "input_tokens_est": it, "output_tokens_est": ot, "est": True,
               **fields}
        self.llm_calls.append(rec)
        self._write("llm_call", **rec)

    def decision(self, action: str, reason: str, **fields) -> None:
        rec = {"action": action, "reason": reason, **fields}
        self.decisions.append(rec)
        self._write("decision", **rec)

    def finish(self, summary: dict | None = None, metrics: dict | None = None) -> dict:
        dur = (time.perf_counter() - self._t0) * 1000
        out = {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "ended_at": _now(),
            "duration_ms": round(dur, 1),
            "meta": self.meta,
            "stages": self.stages,
            "tools": self.tools,
            "llm_calls": self.llm_calls,
            "decisions": self.decisions,
            "summary": summary or {},
            "metrics": metrics or {},
            "token_estimate": {
                "input": sum(c["input_tokens_est"] for c in self.llm_calls),
                "output": sum(c["output_tokens_est"] for c in self.llm_calls),
                "note": "启发式估算，非 API usage",
            },
            "events": str(self.events_path),
        }
        (self.dir / "summary.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        self._write("run_end", duration_ms=round(dur, 1), summary=out["summary"],
                    metrics=out["metrics"])
        return out
