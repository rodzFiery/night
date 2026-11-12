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
    "doctrine": {"focus":"balanced","resource":None,"bonus":0,"can_change":True,"next_change_at":0},
    "mastery": {focus: {"rank":0,"active_seconds":0,"production_bonus":0,"next_rank_seconds":86400} for focus in ("agriculture","forestry","industry","energy")},
    "production_rates": {
        "food":{"facility":"farm","level":1,"per_hour":120,"research_level":0,"alliance_bonus":0,"doctrine_bonus":0},
        "wood":{"facility":"lumber","level":1,"per_hour":100,"research_level":0,"alliance_bonus":0,"doctrine_bonus":0},
        "metal":{"facility":"salvage","level":1,"per_hour":80,"research_level":0,"alliance_bonus":0,"doctrine_bonus":0},
        "gas":{"facility":"fuel","level":1,"per_hour":25,"research_level":0,"alliance_bonus":0,"doctrine_bonus":0},
    },
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
                assert page.locator('[role="tab"]').count() == 4, "Expected four development tabs"
                page.locator("#afTab40-facilities").focus()
                page.keyboard.press("ArrowRight")
                assert page.locator("#afTab40-architecture").get_attribute("aria-selected") == "true", "Keyboard tab navigation failed"
                page.keyboard.press("End")
                assert page.locator("#afTab40-strategy").get_attribute("aria-selected") == "true", "End key navigation failed"
                page.locator("#afTab40-strategy").click()
                page.locator("#afStrategy39").wait_for(state="visible")
                page.locator("#afDoctrine44").wait_for(state="visible")
                assert page.locator("[data-af-doctrine]").count() == 5
                assert page.locator('[data-af-doctrine="balanced"]').get_attribute("aria-pressed") == "true"
                assert "BALANCED" in page.locator("#afDoctrineStatus44").inner_text()
                assert page.locator(".af-mastery-row46").count() == 4, "Expected four mastery progression tracks"
                assert page.locator(".af-production-row53").count() == 4, "Expected four authoritative production rows"
                assert "120 / H" in page.locator("#afProduction53").inner_text()
                assert "RESEARCH LV 0" in page.locator("#afProduction53").inner_text()
                assert "RANK 0/5" in page.locator("#afMastery46").inner_text()
                assert "UNTRAINED" in page.locator("#afMastery46").inner_text()
                assert page.locator('.af-mastery-track46[role="progressbar"]').count() == 4
                assert page.locator(".af-mastery-hint51").count() == 4
                assert all(not hint.startswith("ACTIVE SPECIALIZATION") for hint in page.locator(".af-mastery-hint51").all_inner_texts())
                mastered = json.loads(json.dumps(ECONOMY))
                mastered["doctrine"] = {
                    "focus":"agriculture","resource":"food","bonus":.08,
                    "can_change":False,"next_change_at":1800086400
                }
                mastered["mastery"]["agriculture"] = {
                    "rank":2,"active_seconds":2.5*86400,
                    "production_bonus":.02,"next_rank_seconds":3*86400
                }
                page.evaluate("""fixture => window.ASHFALL_DOCTRINE44.sync(fixture)""", mastered)
                assert "SPECIALIST" in page.locator("#afMastery46").inner_text()
                assert "ACTIVE SPECIALIZATION" in page.locator("#afMastery46").inner_text()
                assert page.locator('.af-mastery-track46[aria-label="AGRICULTURE mastery progress"]').get_attribute("aria-valuenow") == "50"
                page.evaluate("""fixture => window.ASHFALL_DOCTRINE44.sync(fixture)""", ECONOMY)
                # A rejected doctrine POST must keep its error visible after
                # the UI unlocks and re-renders the controls.
                page.evaluate("""() => window.ASHFALL_DOCTRINE44.configure({
                    state_id: 1, csrf_token: "synthetic-browser-test"
                })""")
                page.locator('[data-af-doctrine="agriculture"]').click()
                page.wait_for_function("""() => document.getElementById('afDoctrineMessage44')
                    ?.textContent.includes('Not supplied by isolated test fixture')""")
                assert page.locator('[data-af-doctrine="agriculture"]').is_enabled()


                # A server-confirmed doctrine response updates the visible resource bar.
                page.evaluate("""fixture => {
                    const next = JSON.parse(JSON.stringify(fixture));
                    next.resources.food = 4321;
                    window.dispatchEvent(new CustomEvent("ashfall:doctrine-updated", {detail: next}));
                }""", ECONOMY)
                assert "FOOD 4,321" in page.locator("#resourceBar").inner_text()
                page.evaluate("""fixture => {
                    window.dispatchEvent(new CustomEvent("ashfall:doctrine-updated", {detail: fixture}));
                }""", ECONOMY)

                assert page.locator("#afStrategyList39 button").count() == 3, "Expected three strategy recommendations"
                page.locator('[data-af-strategy="economy"]').click()
                assert page.locator('[data-af-strategy="economy"]').get_attribute("aria-pressed") == "true"
                assert "production" in page.locator("#afStrategyExplanation39").inner_text().lower()
                page.locator("#afStrategyList39 button").first.click()
                assert page.locator("#buildpanel").is_visible(), "Strategy selection did not open inspector"
                assert page.locator("#afTab40-facilities").get_attribute("aria-selected") == "true", "Strategy selection should return to facility details"
                page.evaluate("showBuilding('hq')")
                page.locator("#afTab40-priorities").click()
                page.locator("#afPriorities38").wait_for(state="visible")
                assert page.locator("#afPrioritiesList38 button").count() == 6, "Expected six priority entries"
                page.locator('[data-af-priority-filter="ready"]').click()
                assert page.locator("#afPrioritiesList38 button").count() == 6, "Expected six affordable facilities in fixture"
                page.locator('[data-af-priority-filter="milestone"]').click()
                assert page.locator("#afPrioritiesList38 button").count() == 6, "Expected six architectural targets"
                page.locator("#afPrioritiesList38 button").filter(has_text="Farm").click()
                assert page.locator("#buildtitle").inner_text() == "Farm", "Priority navigation failed"
                assert page.locator("#afTab40-facilities").get_attribute("aria-selected") == "true", "Priority selection should return to facility details"
                page.evaluate("showBuilding('hq')")
                page.locator("#afTab40-facilities").click()
                page.locator("#afRoster36").wait_for(state="visible")
                assert page.locator("#afRosterList36 button").count() == 6, "Expected six facilities"
                page.locator("#afRosterList36 button").filter(has_text="Farm").click()
                assert page.locator("#buildtitle").inner_text() == "Farm", "Roster navigation failed"
                assert page.locator("#afRosterList36 button").filter(has_text="Farm").get_attribute("aria-pressed") == "true"
                page.evaluate("showBuilding('hq')")
                page.locator("#buildpanel").wait_for(state="visible")
                page.locator("#afTab40-architecture").click()
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
                for view in ("facilities", "architecture", "priorities", "strategy"):
                    page.locator(f"#afTab40-{view}").click()
                    assert page.locator(f"#afView40-{view}").is_visible(), f"{view} view not visible"
                    for other in ("facilities", "architecture", "priorities", "strategy"):
                        if other != view:
                            assert page.locator(f"#afView40-{other}").is_hidden(), f"{other} view overlaps {view}"
                    layout = page.evaluate("""() => {
                        const panel = document.getElementById('buildpanel');
                        const view = panel.querySelector('.af-command-view40:not([hidden])');
                        const bounds = view.getBoundingClientRect();
                        return {
                            viewportWidth: innerWidth,
                            viewWidth: bounds.width,
                            viewLeft: bounds.left,
                            viewRight: bounds.right,
                            viewScrollWidth: view.scrollWidth,
                            viewClientWidth: view.clientWidth,
                            documentWidth: document.documentElement.scrollWidth
                        };
                    }""")
                    assert layout["viewLeft"] >= -1, f"{view} extends left: {layout}"
                    assert layout["viewRight"] <= width+1, f"{view} extends right: {layout}"
                    assert layout["viewScrollWidth"] <= layout["viewClientWidth"]+2, f"{view} has horizontal overflow: {layout}"
                    page.screenshot(
                        path=str(OUTPUT / f"ashfall-{width}x{height}-{view}.png"),
                        full_page=True,
                        animations="disabled",
                    )
                page.locator("#afTab40-architecture").click()
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
                # Scenario coverage: shortages, occupied slot, max-level and filter behavior.
                # Reuse the same server-shaped fixture without mutating production state.
                scenario = json.loads(json.dumps(ECONOMY))
                scenario["resources"]["wood"] = 10
                scenario["queue"] = {"building_key": "farm", "finishes_at": 1800000600, "target_level": 2}
                scenario["buildings"]["barracks"]["level"] = 55
                page.evaluate("""scenario => {
                    window.ASHFALL_ROSTER36.sync(scenario);
                    window.ASHFALL_UPGRADE_INTEL37.sync(scenario);
                    window.ASHFALL_PRIORITIES38.sync(scenario);
                    window.ASHFALL_STRATEGY39.sync(scenario);
                }""", scenario)
                page.locator("#afTab40-priorities").click()
                assert "0 READY" in page.locator("#afPrioritiesSummary38").inner_text(), "Occupied queue must block readiness"
                page.locator('[data-af-priority-filter="short"]').click()
                assert page.locator("#afPrioritiesList38 button").count() == 6, "All six fixture facilities require wood"
                page.locator('[data-af-priority-filter="all"]').click()
                assert "MAX LEVEL" in page.locator("#afPrioritiesList38").inner_text()
                page.locator("#afTab40-facilities").click()
                assert "BUILDING" in page.locator("#afRosterList36").inner_text()
                assert "MAX" in page.locator("#afRosterList36").inner_text()
                page.locator("#afTab40-strategy").click()
                assert page.locator("#afStrategyList39 button").count() == 3, "Strategy must exclude max-level facility"
                # Restore the original economy fixture for the remaining close/escape checks.
                page.evaluate("""scenario => {
                    window.ASHFALL_ROSTER36.sync(scenario);
                    window.ASHFALL_UPGRADE_INTEL37.sync(scenario);
                    window.ASHFALL_PRIORITIES38.sync(scenario);
                    window.ASHFALL_STRATEGY39.sync(scenario);
                }""", ECONOMY)
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
