# 采集网页端真实界面（2×），供宣传片使用：python promo/capture_ui.py
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "assets" / "ui"
BASE = "http://127.0.0.1:8770"
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(args=["--disable-gpu"])
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
    pg = ctx.new_page()
    pg.goto(BASE, wait_until="networkidle"); pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / "ui-00-empty.png"))
    pg.fill("#cat", "沙漠牵引车")
    pg.fill("#part", "前脸、保险杠、登车踏步、大灯、前轮拱、后视镜"); pg.press("#part", "Enter")
    pg.wait_for_timeout(800)
    pg.screenshot(path=str(OUT / "ui-01-start.png"))
    pg.locator(".hitem2").first.click(); pg.wait_for_timeout(2600)
    pg.screenshot(path=str(OUT / "ui-02-result.png"))
    b.close()
print("captured to", OUT)
