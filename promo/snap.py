import sys, threading, functools, http.server, socketserver, pathlib
from playwright.sync_api import sync_playwright

scene, times, out = sys.argv[1], [float(x) for x in sys.argv[2].split(",")], pathlib.Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
cname = {"02": "retrieval", "03": "association"}[scene[:2]]
ROOT = pathlib.Path(".").resolve()


class H(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = path.split("?")[0]
        if p.startswith("/compositions/assets/"):
            p = p[len("/compositions"):]
        return str(ROOT / p.lstrip("/"))

    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(H, directory=str(ROOT)))
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

with sync_playwright() as p:
    b = p.chromium.launch(args=['--disable-gpu','--no-sandbox'])
    pg = b.new_page(viewport={"width": 1920, "height": 1080})
    pg.add_init_script("window.__timelines = window.__timelines || {};")
    pg.goto(f"http://127.0.0.1:{port}/compositions/{scene}.html")
    pg.wait_for_timeout(900)
    for t in times:
        pg.evaluate(f'window.__timelines["{cname}"].seek({t})')
        pg.wait_for_timeout(220)
        pg.screenshot(path=str(out / f"{scene}-{t:05.1f}.png"))
    b.close()
srv.shutdown()
print("ok")
