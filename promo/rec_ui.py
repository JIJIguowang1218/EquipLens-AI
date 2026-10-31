# 录制真实操作片段（网页内点击/输入/拖拽），供宣传片使用
import sys, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent / "assets" / "rec"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://127.0.0.1:8770"

def new_ctx(p, name):
    d = OUT / name
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    return p.chromium.launch(args=["--disable-gpu"]).new_context(
        viewport={"width": 1440, "height": 900}, record_video_dir=str(d),
        record_video_size={"width": 1440, "height": 900}), d

def finish(ctx, d, name):
    ctx.close()
    f = sorted(d.glob("*.webm"))[0]
    shutil.move(str(f), str(OUT / f"{name}.webm"))
    shutil.rmtree(d, ignore_errors=True)

with sync_playwright() as p:
    # 1 立项：输入类别与部位
    ctx, d = new_ctx(p, "tmp1"); pg = ctx.new_page()
    pg.goto(BASE, wait_until="networkidle"); pg.wait_for_timeout(900)
    pg.click("#cat"); pg.type("#cat", "沙漠牵引车", delay=90)
    pg.wait_for_timeout(400)
    pg.click("#part"); pg.type("#part", "前脸、保险杠、登车踏步", delay=45)
    pg.keyboard.press("Enter"); pg.wait_for_timeout(600)
    pg.hover("#next"); pg.wait_for_timeout(500)
    finish(ctx, d, "ui-type")

    # 2 结果页：翻页 + 导出
    ctx, d = new_ctx(p, "tmp2"); pg = ctx.new_page()
    pg.goto(BASE, wait_until="networkidle"); pg.wait_for_timeout(1200)
    pg.locator(".hitem2").first.click(); pg.wait_for_timeout(2500)
    if pg.locator("#nextp").count() and pg.locator("#nextp").is_enabled():
        pg.click("#nextp"); pg.wait_for_timeout(1400)
    dl = pg.locator("a[download]").first
    if dl.count():
        dl.hover(); pg.wait_for_timeout(600); dl.click(); pg.wait_for_timeout(2500)
    finish(ctx, d, "ui-result")

    # 3 设置页
    ctx, d = new_ctx(p, "tmp3"); pg = ctx.new_page()
    pg.goto(BASE, wait_until="networkidle"); pg.wait_for_timeout(1000)
    pg.click("#tosettings"); pg.wait_for_timeout(1500)
    finish(ctx, d, "ui-settings")

print("recorded")
