# -*- coding: utf-8 -*-
"""裁框数据接收服务：编辑器点「这张好了」直接 POST 到这里落盘。

用法:
  PYTHONPATH=src python scripts/box_server.py --out data-test/edit-batch --port 8766
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def valid(item: dict) -> bool:
    parts = item.get("parts")
    if not isinstance(parts, list) or not parts:
        return False
    for p in parts:
        b = p.get("bbox")
        if not (isinstance(b, list) and len(b) == 4):
            return False
        if not all(isinstance(x, (int, float)) and 0 <= x <= 1000 for x in b):
            return False
    return True


def make_handler(outdir: Path):
    class Handler(BaseHTTPRequestHandler):
        def _cors(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

        def _json(self, code: int, obj: dict):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors()
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):  # noqa: N802
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self):  # noqa: N802
            if self.path.startswith("/health"):
                self._json(200, {"ok": True, "out": str(outdir)})
            else:
                self._json(404, {"ok": False})

        def do_POST(self):  # noqa: N802
            if not self.path.startswith("/save"):
                self._json(404, {"ok": False})
                return
            n = int(self.headers.get("Content-Length") or 0)
            try:
                item = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception as e:  # noqa: BLE001
                self._json(400, {"ok": False, "error": f"bad json: {e}"})
                return
            if item.get("kind") == "layout":
                if not item.get("slug") or not isinstance(item.get("blocks"), list):
                    self._json(400, {"ok": False, "error": "bad layout"})
                    return
                ldir = ROOT / "data-test" / "layouts"
                ldir.mkdir(parents=True, exist_ok=True)
                target = ldir / f"{item['slug']}.json"
                target.write_text(json.dumps(item, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
                print(f"[layout] {target.name} blocks={len(item['blocks'])}")
                self._json(200, {"ok": True, "file": target.name})
                return
            if not item.get("slug") or not valid(item):
                self._json(400, {"ok": False, "error": "invalid payload"})
                return
            outdir.mkdir(parents=True, exist_ok=True)
            if item.get("kind") == "layout":
                ldir = ROOT / "data-test" / "layouts"
                ldir.mkdir(parents=True, exist_ok=True)
                target = ldir / f"{item['slug']}.json"
                target.write_text(json.dumps(item, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
                print(f"[layout] {target.name}  blocks={len(item.get('blocks', []))}")
                self._json(200, {"ok": True, "file": target.name})
                return
            target = outdir / f"{item['slug']}-boxes.json"
            target.write_text(json.dumps(item, ensure_ascii=False, indent=2),
                              encoding="utf-8")
            print(f"[saved] {target.name}  parts={len(item['parts'])}")
            self._json(200, {"ok": True, "file": target.name})

        def log_message(self, *a):  # 静音
            return

    return Handler


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data-test/edit-batch")
    ap.add_argument("--port", type=int, default=8766)
    args = ap.parse_args()
    outdir = ROOT / args.out
    srv = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(outdir))
    print(f"裁框接收服务: http://127.0.0.1:{args.port}/save  →  {outdir}")
    print("（保持本窗口运行，编辑器里每点一次「这张好了」都会落盘）")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n停止")
    return 0


if __name__ == "__main__":
    sys.exit(main())
