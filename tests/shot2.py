import asyncio, sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--use-angle=swiftshader","--enable-unsafe-swiftshader","--ignore-gpu-blocklist"])
        page = await b.new_page(viewport={"width":1440,"height":860})
        logs=[]; page.on("console", lambda m: logs.append(f"{m.type}: {m.text}")); page.on("pageerror", lambda e: logs.append(f"PAGEERROR: {e}"))
        page.on("pageerror", lambda e: print("PAGEERROR", e))
        await page.goto("http://localhost:5000/?debug=1")
        await page.wait_for_timeout(7000)
        import os
        await page.fill("#alias","t"+str(os.getpid())); await page.fill("#pin","1234"); await page.click("#registerBtn")
        await page.wait_for_timeout(3000)
        await page.click("#roleCards .card >> nth=0"); await page.wait_for_timeout(1500)
        await page.click("#beginBtn"); await page.wait_for_timeout(4000)
        await page.mouse.click(720, 380); await page.wait_for_timeout(12000)
        for line in sys.argv[1:]:
            await page.evaluate("l => window.__send && window.__send(l)", line)
            await page.wait_for_timeout(2500)
        await page.wait_for_timeout(3000)
        await page.screenshot(path="/tmp/shots/t_focus.png")
        await page.keyboard.press("Escape"); await page.wait_for_timeout(1500)
        await page.mouse.click(400, 400); await page.wait_for_timeout(3000)
        await page.screenshot(path="/tmp/shots/t_siem.png")
        print("\n".join(logs[-15:]))
        await b.close()
async def safe():
    try:
        await main()
    except Exception as e:
        print("FAIL", str(e)[:300])
asyncio.run(safe())
