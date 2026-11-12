#!/usr/bin/env python3
"""ASHFALL 32 browser component smoke tests.

Run after: pip install playwright && python -m playwright install chromium
Then: python tests/browser_ashfall.py

Uses real ASHFALL scripts/artwork against a minimal DOM harness. Does not
authenticate, mutate live game data, or claim full gameplay coverage.
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"

def run():
    handler = partial(SimpleHTTPRequestHandler, directory=str(APP))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for width, height in [(1440, 900), (390, 844)]:
                page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(base + "/static/ashfall-art/hq.svg", wait_until="load")
                page.set_content("""
                    <section id="buildpanel">
                      <p id="buildqueue"></p>
                      <canvas id="afEvolutionCanvas" width="340" height="266"></canvas>
                      <p id="afPreviewStatus"></p>
                      <div id="afEvolutionTrack">
                        <button data-af-tier="5">5</button>
                        <button data-af-tier="15">15</button>
                        <button data-af-tier="30">30</button>
                        <button data-af-tier="50">50</button>
                      </div>
                    </section>
                """)
                for script in ("ashfall-art-25.js", "ashfall-preview-28.js", "ashfall-construction-29.js"):
                    page.add_script_tag(url=base + "/static/" + script)
                page.evaluate("window.ASHFALL_ARCH_PREVIEW.show('hq', 4)")
                page.wait_for_function("document.getElementById('afPreviewStatus').textContent.includes('PREVIEW LEVEL 4')")
                page.evaluate("window.ASHFALL_ARCH_PREVIEW.select(30)")
                page.wait_for_function("document.getElementById('afPreviewStatus').textContent.includes('NOT APPLIED')")
                assert page.locator('[data-af-tier="30"]').get_attribute("aria-pressed") == "true"
                page.evaluate("""() => window.ASHFALL_CONSTRUCTION.sync({
                    server_time: Date.now()/1000,
                    queue:{building_key:'hq',started_at:Date.now()/1000-20,finishes_at:Date.now()/1000+80},
                    buildings:{hq:{level:4}}
                })""")
                assert page.locator("#afConstruction").is_visible()
                assert "Command Center" in page.locator("#afConstructionName").inner_text()
                page.evaluate("""() => window.ASHFALL_CONSTRUCTION.sync({
                    server_time: Date.now()/1000,queue:null,buildings:{hq:{level:5}}
                })""")
                assert "LEVEL 5" in page.locator("#afConstructionNotice").inner_text()
                assert "ARCHITECTURAL MILESTONE" in page.locator("#afConstructionNotice").inner_text()
                assert not errors, f"Browser errors at {width}px: {errors}"
                print(f"PASS: architectural preview and construction milestone at {width}x{height}")
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    run()
