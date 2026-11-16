# -*- coding: utf-8 -*-
"""L1 Session 入口（原型 CLI）：新建 / 追加消息 / 确认 / 跑完 / 查看 / 续跑。

用法（离线，夹具）:
  PYTHONPATH=src python scripts/run_session.py --brief data-test/retrieval-fixtures-20261109/brief-desert.json \
      --fixtures data-test/retrieval-fixtures-20261109/world-desert.json \
      --session data-test/sessions/demo.json --run-id demo-1 \
      --message "都要侧面" --run

用法（live，brief+plan）:
  PYTHONPATH=src python scripts/run_session.py --brief data-test/briefs/m43/c1-desert.json \
      --plan data-test/plans/m43-c1-desert.json \
      --session data-test/sessions/c1.json --run-id m43-sess-l1 --message "都要正脸" --run

注意：这是**原型入口**，不进生产链路；S4 仍 planned。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from equiplens.retrieval_engine.adapters import FakeWorld  # noqa: E402
from equiplens.retrieval_engine.web import WebWorld  # noqa: E402
from equiplens.session_runner import SessionRunner  # noqa: E402

KEY_FILE = Path.home() / ".equiplens" / "deepseek.env"


def load_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    if KEY_FILE.exists():
        for line in KEY_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("no DEEPSEEK_API_KEY（--router llm 需要 key）")


def build_router(kind: str):
    if kind != "llm":
        return None
    from equiplens.session_router import make_router
    return make_router(load_key())


def build_world(args, brief_doc: dict):
    if args.fixtures:
        return FakeWorld.from_file(args.fixtures)
    plan = None
    plan_meta: dict = {}
    if args.plan:
        doc = json.loads(Path(args.plan).read_text(encoding="utf-8"))
        plan = doc.get("candidates") or []
        plan_meta = {"concurrency": doc.get("concurrency"),
                     "rank_method": (doc.get("ranking") or {}).get("method"),
                     "created_at": doc.get("created_at")}
    parts = {}
    from equiplens.retrieval_engine.contracts import PartRequirement
    for p in brief_doc.get("part_requirements") or []:
        req = PartRequirement.from_dict(p)
        parts[req.part] = req
    run_dir = Path(args.run_root) / args.run_id
    return WebWorld(None, parts, image_dir=run_dir / "images", plan=plan,
                    citation_check=not args.no_citation, plan_meta=plan_meta,
                    pins=[], download_workers=args.download_workers,
                    brief={"request": brief_doc.get("request") or {}})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", default="", help="新建会话时必填；续跑可省略（从会话文件读）")
    ap.add_argument("--plan", default="")
    ap.add_argument("--fixtures", default="", help="离线夹具世界")
    ap.add_argument("--session", required=True, help="会话 JSON 路径")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--run-root", default="data-test/runs")
    ap.add_argument("--message", action="append", default=[], help="可重复：逐条追加用户消息")
    ap.add_argument("--confirm", action="store_true")
    ap.add_argument("--reject", action="store_true")
    ap.add_argument("--run", action="store_true", help="驱动引擎直到结束")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--download-workers", type=int, default=4)
    ap.add_argument("--no-citation", action="store_true")
    ap.add_argument("--router", choices=["rules", "llm"], default="rules",
                    help="rules=规则版（默认）；llm=LLM 提议+守卫")
    ap.add_argument("--script", default="", help="JSONL 动作脚本：message/confirm/run/run_to_end")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    router = build_router(args.router)
    session_path = Path(args.session)
    if session_path.exists():
        brief_doc = json.loads(Path(args.brief).read_text(encoding="utf-8")) if args.brief else \
            json.loads(session_path.read_text(encoding="utf-8")).get("brief") or {}
        world = build_world(args, brief_doc)
        runner = SessionRunner.load(session_path, world, router=router)
    else:
        if not args.brief:
            ap.error("新建会话需要 --brief")
        brief_doc = json.loads(Path(args.brief).read_text(encoding="utf-8"))
        world = build_world(args, brief_doc)
        runner = SessionRunner(brief_doc, world, run_root=args.run_root,
                               run_id=args.run_id or None,
                               store_path=session_path, router=router,
                               router_name=args.router)

    run_id = runner.run_id if not args.run_id else args.run_id
    out = {"run_id": run_id, "session": runner.session_id, "turns": []}
    for msg in args.message:
        res = runner.send(msg)
        out["turns"].append({"msg": msg, "clarify": bool(res.get("clarify")),
                             "question": res.get("question"), "hard": bool(res.get("hard")),
                             "targets": [p.get("target") for p in res.get("patches") or []]})
    actions = []
    if args.script:
        actions = [json.loads(line) for line in
                   Path(args.script).read_text(encoding="utf-8").splitlines() if line.strip()]
    if actions:
        for act in actions:
            if "message" in act:
                res = runner.send(str(act["message"]))
                out["turns"].append({"msg": act["message"], "clarify": bool(res.get("clarify")),
                                     "question": res.get("question"),
                                     "hard": bool(res.get("hard")),
                                     "targets": [p.get("target") for p in res.get("patches") or []]})
            elif "confirm" in act:
                out["confirm"] = runner.confirm(bool(act["confirm"]))
            elif "run_until" in act:
                runner.run_until(str(act["run_until"]),
                                 require_targets=bool(act.get("require_targets")))
            elif act.get("run_to_end"):
                out["summary"] = runner.run(max_steps=args.max_steps)
            elif "run" in act:
                n = 10 if act["run"] is True else int(act["run"])
                for _ in range(max(1, n)):
                    if runner.state.get("finished"):
                        break
                    runner.step()
        if "summary" not in out and args.run:
            out["summary"] = runner.run(max_steps=args.max_steps)
        if "summary" not in out:
            out["status"] = runner.status()
    else:
        if args.confirm:
            out["confirm"] = runner.confirm(True)
        if args.reject:
            out["confirm"] = runner.confirm(False)
        if args.run:
            out["summary"] = runner.run(max_steps=args.max_steps)
        else:
            out["status"] = runner.status()
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"session: {runner.session_id}  engine: {runner.state.get('state')}  "
              f"steps: {runner.steps}  applied: {runner.applied}")
        for t in out["turns"]:
            line = f"  msg: {t['msg']} -> {t['targets']}"
            if t["clarify"]:
                line += f"  [clarify] {t['question']}"
            print(line)
        if "summary" in out:
            s = out["summary"]
            print(f"  delivery: {s['delivered']}/{s['required']}  missing={s['missing']}  "
                  f"degraded={s['degraded']}  session_state={s['session']['state']}")
        print(f"  store: {runner.store_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
