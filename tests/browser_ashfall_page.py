#!/usr/bin/env python3
"""ASHFALL 33 — full-page browser diagnostic with isolated API fixtures.

Run: python tests/browser_ashfall_page.py
Requires: pip install playwright && python -m playwright install chromium

This is a diagnostic, not an end-to-end authenticated production test.
It exercises the actual HTML and real static files, but replaces API calls
with deterministic test responses and saves screenshots for visual review.
"""
from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright
import json

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
OUTPUT = ROOT / "artifacts" / "ashfall-diagnostics"

WORLD = {
    "state_id": 1,
    "haven": {"name": "Test Haven", "x": 0, "y": 0, "command_center_level": 5},
    "players": [],
}
BUILDINGS = {
    key: {
        "name": name, "level": 5 if key == "hq" else 1,
        "next_level": 6 if key == "hq" else 2,
        "resource": resource, "rate": 20, "cost": {"wood": 50},
        "seconds": 60, "rare_cost": {},
    }
    for key, name, resource in [
        ("hq", "Command Center", None),
        ("farm", "Farm", "food"),
        ("lumber", "Lumber Yard", "wood"),
        ("salvage", "Salvage Station", "metal"),
        ("fuel", "Fuel Collector", "gas"),
        ("barracks", "Barracks", None),
    ]
}
ECONOMY = {
    "server_time": 1800000000,
    "queue": None,
    "resources": {"food": 1000, "wood": 1000, "metal": 1000, "gas": 1000},
    "buildings": BUILDINGS,
    "rare_materials": {},
}

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    handler = partial(SimpleHTTPRequestHandler, directory=str(APP))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/ashfall_world.html"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            for width, height in [(1440, 900), (390, 844)]:
                page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1, reduced_motion="reduce")
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                def api(route):
                    path = route.request.url.split("/ashfall/api/", 1)[-1].split("?", 1)[0]
                    if path == "world":
                        body, status = WORLD, 200
                    elif path == "economy":
                        body, status = ECONOMY, 200
                    else:
                        body, status = {"detail": "Not supplied by isolated test fixture"}, 404
                    route.fulfill(status=status, content_type="application/json", body=json.dumps(body))
                page.route("**/ashfall/api/**", api)
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_function("document.getElementById('heading')?.textContent === 'Test Haven'", timeout=20000)
                page.wait_for_function("document.getElementById('resourceBar')?.textContent.includes('FOOD')", timeout=20000)
                page.evaluate("showBuilding('hq')")
                page.locator("#afUpgradeIntel37").wait_for(state="visible")
                assert "RESOURCES READY" in page.locator("#afUpgradeState37").inner_text()
                assert "LEVEL 15" in page.locator("#afUpgradeMilestone37").inner_text()
                page.locator("#afStrategy39").wait_for(state="visible")
                assert page.locator("#afStrategyList39 button").count() == 3, "Expected three strategy recommendations"
                page.locator('[data-af-strategy="economy"]').click()
                assert page.locator('[data-af-strategy="economy"]').get_attribute("aria-pressed") == "true"
                assert "production" in page.locator("#afStrategyExplanation39").inner_text().lower()
                page.locator("#afStrategyList39 button").first.click()
                assert page.locator("#buildpanel").is_visible(), "Strategy selection did not open inspector"
                page.evaluate("showBuilding('hq')")
                page.locator("#afPriorities38").wait_for(state="visible")
                assert page.locator("#afPrioritiesList38 button").count() == 6, "Expected six priority entries"
                page.locator('[data-af-priority-filter="ready"]').click()
                assert page.locator("#afPrioritiesList38 button").count() == 6, "Expected six affordable facilities in fixture"
                page.locator('[data-af-priority-filter="milestone"]').click()
                assert page.locator("#afPrioritiesList38 button").count() == 6, "Expected six architectural targets"
                page.locator("#afPrioritiesList38 button").filter(has_text="Farm").click()
                assert page.locator("#buildtitle").inner_text() == "Farm", "Priority navigation failed"
                page.evaluate("showBuilding('hq')")
                page.locator("#afRoster36").wait_for(state="visible")
                assert page.locator("#afRosterList36 button").count() == 6, "Expected six facilities"
                page.locator("#afRosterList36 button").filter(has_text="Farm").click()
                assert page.locator("#buildtitle").inner_text() == "Farm", "Roster navigation failed"
                assert page.locator("#afRosterList36 button").filter(has_text="Farm").get_attribute("aria-pressed") == "true"
                page.evaluate("showBuilding('hq')")
                page.locator("#buildpanel").wait_for(state="visible")
                page.locator("#afEvolutionCanvas").wait_for(state="visible")
                page.wait_for_function("document.getElementById('afPreviewStatus')?.textContent.includes('PREVIEW LEVEL 5')", timeout=20000)
                page.locator('[data-af-tier="30"]').click()
                page.wait_for_function("document.getElementById('afPreviewStatus')?.textContent.includes('NOT APPLIED')")
                geometry = page.evaluate("""() => {
                    const panel = document.getElementById('buildpanel');
                    const rect = panel.getBoundingClientRect();
                    return {
                        panel: {left:rect.left,right:rect.right,top:rect.top,bottom:rect.bottom},
                        viewport: {width:innerWidth,height:innerHeight},
                        panelScrollable:panel.scrollHeight>panel.clientHeight,
                        canvasWidth:document.getElementById('afEvolutionCanvas').getBoundingClientRect().width
                    };
                }""")
                assert geometry["panel"]["left"] >= -1, f"Inspector clipped on left: {geometry}"
                assert geometry["panel"]["right"] <= width+1, f"Inspector clipped on right: {geometry}"
                assert geometry["panel"]["top"] >= -1, f"Inspector clipped at top: {geometry}"
                assert geometry["panel"]["bottom"] <= height+1, f"Inspector clipped at bottom: {geometry}"
                assert geometry["canvasWidth"] > 0, f"Preview canvas invisible: {geometry}"
                screenshot = OUTPUT / f"ashfall-{width}x{height}.png"
                page.screenshot(path=str(screenshot), full_page=True, animations="disabled")
                report = {
                    "viewport": f"{width}x{height}",
                    "geometry": geometry,
                    "title": page.title(),
                    "preview": page.locator("#afPreviewStatus").inner_text(),
                    "console_exceptions": errors,
                    "screenshot": str(screenshot.relative_to(ROOT)),
                }
                (OUTPUT / f"ashfall-{width}x{height}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                page.locator("#afInspectorClose35").click()
                assert page.locator("#buildpanel").is_hidden(), "Close control failed to dismiss inspector"
                page.evaluate("showBuilding('hq')")
                page.locator("#buildpanel").wait_for(state="visible")
                page.keyboard.press("Escape")
                assert page.locator("#buildpanel").is_hidden(), "Escape failed to dismiss inspector"
                assert not errors, f"JavaScript errors at {width}x{height}: {errors}"
                print(f"PASS {width}x{height}: {screenshot}")
                page.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

if __name__ == "__main__":
    main()
