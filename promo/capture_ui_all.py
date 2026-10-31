# 走一遍真实流程，采集每个界面的 2× 截图：python promo/capture_ui_all.py
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "assets" / "ui"
BASE = "http://127.0.0.1:8770"
OUT.mkdir(parents=True, exist_ok=True)
shot = lambda pg, n: pg.screenshot(path=str(OUT / f"ui-{n}.png"))

with sync_playwright() as p:
    b = p.chromium.launch(args=["--disable-gpu"])
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto(BASE, wait_until="networkidle"); pg.wait_for_timeout(1200)
    shot(pg, "00-empty")

    pg.fill("#cat", "沙漠牵引车")
    pg.fill("#part", "前脸、保险杠、登车踏步、大灯、前轮拱、后视镜"); pg.press("#part", "Enter")
    pg.wait_for_timeout(700); shot(pg, "01-start")

    pg.click("#next"); pg.wait_for_timeout(2500); shot(pg, "02-search")
    pg.wait_for_selector(".vcard", timeout=600000); pg.wait_for_timeout(2500)
    shot(pg, "03-assets")

    n = pg.locator(".vcard").count()
    for _ in range(max(0, n - 3)):
        pg.locator(".vcard [data-del]").last.click(); pg.wait_for_timeout(250)
    shot(pg, "03b-assets-picked")

    pg.click("#next"); pg.wait_for_timeout(4000); shot(pg, "04-analyze")
    pg.wait_for_selector("text=逐台确认裁框", timeout=900000); pg.wait_for_timeout(2500)
    shot(pg, "05-crop")

    while not ("完成" in pg.inner_text("#next")):
        pg.click("#next"); pg.wait_for_timeout(1200)
    pg.click("#next"); pg.wait_for_selector("#nextp", timeout=300000); pg.wait_for_timeout(2500)
    shot(pg, "06-result")

    pg.click("#tosettings"); pg.wait_for_timeout(1200); shot(pg, "07-settings")
    b.close()
print("captured")
