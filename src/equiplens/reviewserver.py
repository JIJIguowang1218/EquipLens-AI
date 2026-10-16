"""审核包实时存储服务（localhost，仅本机可访问）。

产品负责人要求（2026-10-15，意见 #10）：审核操作实时落账，不再手动导出文件。
机制: python -m equiplens review-serve <批次> → 浏览器 http://127.0.0.1:8765
每张卡片的 接受/驳回/改视角 点击即 POST → 当场走 review/workflow 落账（可撤销）。
页面内嵌缩略图自包含；数据只写本地 SQLite，无外部暴露。
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import db, review, workflow


def serve(conn, data_dir: Path, batch_id: str, port: int = 8765) -> None:
    html_text, stats = review.render_review_html(conn, data_dir, batch_id)
    print(f"批次 {batch_id}: {stats['assets']} 个素材 / {stats['groups']} 组")
    print(f"实时审核地址: http://127.0.0.1:{port}  （每点即存, 关闭浏览器即结束）")

    def _post_conn():
        """每请求独立连接（ThreadingHTTPServer 跨线程, SQLite 连接不可共用）。"""
        c = db.connect(data_dir / "equiplens.db")
        db.init_db(c)
        return c

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str = "application/json"):
            self.send_response(code)
            self.send_header("Content-Type", ctype + "; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == "/":
                self._send(200, html_text.encode("utf-8"), "text/html")
            else:
                self._send(404, b'{"ok": false, "error": "not found"}')

        def do_POST(self):
            c = _post_conn()
            try:
                n = int(self.headers.get("Content-Length", 0))
                body = json.loads((self.rfile.read(n) or b"{}").decode("utf-8"))
                if self.path == "/decision":
                    summary = review.apply_review(
                        c, {"batch_id": batch_id, "decisions": [body]}, data_dir)
                    self._send(200, json.dumps({"ok": True, "summary": summary},
                                               ensure_ascii=False).encode())
                elif self.path == "/view":
                    workflow.set_view(c, body["asset_id"], body["view"])
                    self._send(200, b'{"ok": true}')
                else:
                    self._send(404, b'{"ok": false, "error": "not found"}')
            except Exception as e:  # noqa: BLE001
                self._send(400, json.dumps({"ok": False, "error": str(e)},
                                           ensure_ascii=False).encode())
            finally:
                c.close()

        def log_message(self, *args):  # 静默访问日志
            pass

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
