"""Captura pantallas del juego con Chrome headless (verificación visual)."""
import asyncio
import sys

from playwright.async_api import async_playwright

URL = "http://localhost:5000/"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/shots"


async def main():
    import os
    os.makedirs(OUT, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome",
                                    args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        page = await b.new_page(viewport={"width": 1440, "height": 860})
        logs = []
        page.on("console", lambda m: logs.append(f"{m.type}: {m.text}"))
        page.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e}"))
        await page.goto(URL)
        await page.wait_for_timeout(9000)
        await page.screenshot(path=f"{OUT}/1_login.png")
        await page.fill("#alias", "tester" + str(os.getpid()))
        await page.fill("#pin", "1234")
        await page.click("#registerBtn")
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{OUT}/2_roles.png")
        role = sys.argv[2] if len(sys.argv) > 2 else "0"
        await page.click(f"#roleCards .card >> nth={role}")
        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{OUT}/3_niveles.png")
        lvl = sys.argv[3] if len(sys.argv) > 3 else "1"
        await page.click(f"#levelList .level >> nth={lvl}")
        await page.wait_for_timeout(2500)
        await page.screenshot(path=f"{OUT}/4_brief.png")
        await page.click("#beginBtn")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=f"{OUT}/4_seated.png")
        for line in ["help", "objetivos"]:
            await page.keyboard.type(line, delay=20)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(1500)
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{OUT}/5_term.png")
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(15000)
        await page.screenshot(path=f"{OUT}/6_alert.png")
        await page.mouse.click(330, 430)
        await page.wait_for_timeout(4000)
        await page.screenshot(path=f"{OUT}/7_side.png")
        print("\n".join(logs[-30:]))
        await b.close()


asyncio.run(main())
