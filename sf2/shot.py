import asyncio, sys
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width':1280,'height':1400})
        html=open('sf2-web-guide.html',encoding='utf-8').read()
        await pg.set_content('<!doctype html><meta charset="utf-8"><body style="margin:0">'+html)
        await pg.evaluate("location.hash='schedule'")
        await pg.wait_for_timeout(800)
        await pg.screenshot(path='shot.png', full_page=False)
        await b.close()
asyncio.run(main())
