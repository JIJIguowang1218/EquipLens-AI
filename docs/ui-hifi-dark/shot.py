from pathlib import Path
from playwright.sync_api import sync_playwright
import sys

ROOT = Path(__file__).resolve().parent
SHOTS = ROOT / "shots"
SHOTS.mkdir(exist_ok=True)

PAGES = [
    ("s0", "s0.html", ["ready"]),
    ("s1", "s1.html", ["loading", "ready"]),
    ("s2", "s2.html", ["loading", "ready"]),
    ("s3", "s3.html", ["loading", "ready"]),
]
WAIT = {("s1", "loading"): 250, ("s2", "loading"): 1200, ("s3", "loading"): 1100}


def main():
    problems = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        page.on("console", lambda m: problems.append(f"console {m.type}: {m.text}")
                if m.type == "error" else None)
        page.on("pageerror", lambda e: problems.append(f"pageerror: {e}"))

        for name, file, states in PAGES:
            for state in states:
                url = (ROOT / file).as_uri() + f"?s={state}"
                page.goto(url, wait_until="load")
                page.wait_for_timeout(WAIT.get((name, state), 650))
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(250)
                metrics = page.evaluate("""() => {
                    const de = document.documentElement;
                    const over = [];
                    for (const el of document.querySelectorAll('body *')) {
                        if (el.scrollWidth > el.clientWidth + 2 && getComputedStyle(el).overflowX === 'visible') {
                            over.push(el.className || el.tagName);
                        }
                    }
                    return {
                        scrollW: de.scrollWidth, clientW: de.clientWidth,
                        scrollH: de.scrollHeight, clientH: de.clientHeight,
                        overflow: over.filter(x => !String(x).includes('bx')).slice(0, 8),
                        fonts: [...new Set([...document.fonts].filter(f => f.status === 'loaded').map(f => f.family + ' ' + f.weight))],
                        bodyOpacity: getComputedStyle(document.body).opacity,
                    };
                }""")
                label = f"{name}-{state}"
                page.screenshot(path=str(SHOTS / f"{label}.png"))
                print(label, metrics)

        # 关键交互态：Desk 选中 / dock 展开 / S2 切图与选中 / S3 选中块
        def go(file, state="ready", wait=800):
            page.goto((ROOT / file).as_uri() + f"?s={state}", wait_until="load")
            page.wait_for_timeout(wait)
            page.evaluate("document.fonts.ready")

        go("s1.html")
        page.locator(".vcard").first.locator(".vbody").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "s1-unselected.png"))
        print("s1-unselected ok")

        page.locator("#ask").click()
        page.wait_for_timeout(350)
        page.screenshot(path=str(SHOTS / "s1-dock.png"))
        print("s1-dock ok")

        go("s2.html")
        page.locator("#prows .prow").nth(2).click()
        page.wait_for_timeout(500)
        page.screenshot(path=str(SHOTS / "s2-state.png"))
        print("s2-state ok")

        go("s3.html")
        page.locator("#page .b-top").click()
        page.wait_for_timeout(300)
        page.screenshot(path=str(SHOTS / "s3-selected.png"))
        print("s3-selected ok")

        page.goto((ROOT / "index.html").as_uri(), wait_until="load")
        page.wait_for_timeout(900)
        page.screenshot(path=str(SHOTS / "index.png"), full_page=True)
        print("index ok")

        browser.close()

    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(" ", p)
        sys.exit(1)


if __name__ == "__main__":
    main()
