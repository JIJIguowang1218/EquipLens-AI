# -*- coding: utf-8 -*-
"""自动跑一遍完整链路并录屏（1280×720）。

用法: python scripts/demo_record.py --out data/demo
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8770"
CATEGORY = "沙漠牵引车"
PARTS = "前脸、保险杠、登车踏步、大灯、前轮拱、后视镜"
KEEP = 3


def step(name: str):
    print(f"[{time.strftime('%H:%M:%S')}] {name}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/demo")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    vid = out / "raw"
    vid.mkdir(exist_ok=True)

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(vid),
            record_video_size={"width": 1280, "height": 720},
        )
        pg = ctx.new_page()
        pg.goto(BASE, wait_until="networkidle")
        pg.wait_for_timeout(1200)

        step("立项")
        pg.fill("#cat", CATEGORY)
        pg.wait_for_timeout(600)
        pg.click("#minus"); pg.click("#minus")          # 3 → 1
        pg.wait_for_timeout(300)
        pg.fill("#part", PARTS)
        pg.keyboard.press("Enter")
        pg.wait_for_timeout(900)

        step("检索（真实抓取 + 现场爬图）")
        pg.click("#next")
        pg.wait_for_selector(".vcard", timeout=600_000)
        pg.wait_for_timeout(4000)
        cards = pg.locator(".vcard")
        n = cards.count()
        print("  候选数:", n, flush=True)

        step(f"素材确认：保留 {KEEP} 台")
        for _ in range(n - KEEP):
            pg.locator(".vcard [data-del]").last.click()
            pg.wait_for_timeout(350)
        pg.wait_for_timeout(800)

        step("分析")
        pg.click("#next")
        pg.wait_for_selector(".frame iframe", timeout=900_000)
        pg.wait_for_timeout(2500)

        step("逐台确认裁框")
        while True:
            label = pg.inner_text("#next")
            if "完成" in label:
                break
            pg.click("#next")
            pg.wait_for_timeout(1500)
        pg.wait_for_timeout(1200)
        pg.click("#next")                                # 完成 · 生成页面
        pg.wait_for_selector("#nextp", timeout=300_000)
        pg.wait_for_timeout(2500)

        step("翻页预览")
        for _ in range(3):
            if pg.locator("#nextp").count() and pg.locator("#nextp").is_enabled():
                pg.click("#nextp"); pg.wait_for_timeout(1600)
        for _ in range(2):
            if pg.locator("#prev").count() and pg.locator("#prev").is_enabled():
                pg.click("#prev"); pg.wait_for_timeout(1200)

        step("导出 PPTX")
        pg.click("#exp")
        pg.wait_for_selector("a[download]", timeout=180_000)
        pg.wait_for_timeout(1500)
        print("  导出:", pg.inner_text("#msg"), flush=True)

        ctx.close()
        b.close()

    webm = sorted(vid.glob("*.webm"), key=lambda f: f.stat().st_mtime)[-1]
    step(f"录制完成: {webm} ({webm.stat().st_size/1024/1024:.1f}MB)")
    mp4 = out / "EquipLens-demo-720p.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", str(webm),
                    "-vf", "scale=1280:-2,fps=30",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "24",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)],
                   check=True, capture_output=True)
    print(f"[ok] {mp4} ({mp4.stat().st_size/1024/1024:.1f}MB)", flush=True)
    return 0


if __name__ == "__main__":
    pick = main()
    sys.exit(pick)
