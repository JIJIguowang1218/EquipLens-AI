from playwright.sync_api import sync_playwright
from pathlib import Path
p = Path("docs/ui-mock/screens.html").resolve().as_uri()
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width":1440,"height":900}, device_scale_factor=2)
    pg.goto(p)
    pg.wait_for_timeout(600)
    for sid in ("s0","s1","s1r"):
        pg.locator("#"+sid).screenshot(path=f"docs/ui-mock/{sid}.png")
        print(sid, "ok")
    b.close()
