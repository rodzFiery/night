#!/usr/bin/env python3
"""NEXORA 81 — isolated Chromium Command Center interaction diagnostics.

Uses the actual JS/CSS assets with deterministic DOM fixtures. This is not
an authenticated end-to-end profile test. Screenshots are saved for inspection.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "artifacts" / "nexora-command-diagnostics"
JS = ROOT / "app/static/nexora-command-center-80.js"
ATLAS = ROOT / "app/static/nexora-achievement-atlas-73.js"
CSS = ROOT / "app/static/css/profile.css"
NAMES = [
    ("nexora-collection-anchor79", "nexora-discovery71", "Achievement Atlas"),
    ("nexora-mastery-anchor81", "nexora-mastery72", "Collection Mastery"),
    ("nexora-pursuits-anchor79", "nexora-pursuits74", "Achievement Pursuits"),
    ("nexora-intel-anchor81", "nexora-intel75", "Settlement Intelligence"),
    ("nexora-roadmap-anchor79", "nexora-roadmap76", "Development Roadmap"),
    ("nexora-forecast-anchor81", "nexora-forecast77", "Resource Forecast"),
    ("nexora-readiness-anchor79", "nexora-readiness78", "Economic Readiness"),
]


def fixture():
    sections = []
    for section_id, css_class, name in NAMES:
        content = f"<h2>{name}</h2><p>Server-rendered module content remains accessible.</p>"
        if css_class == "nexora-discovery71":
            content += (
                '<div class="nexora-discovery-goals71">'
                '<article class="nexora-discovery-goal71" data-key74="ashfall:level:5" '
                'data-world73="ASHFALL" data-earned73="false" '
                'data-title73="First Foundations">First Foundations</article></div>'
            )
        if css_class == "nexora-pursuits74":
            content += '<button type="button" class="nexora-pursuit-focus74" data-pursuit74="ashfall:level:5">FOCUS IN ATLAS</button>'
        sections.append(f'<section id="{section_id}" class="editor-panel {css_class}">{content}</section>')
    cards = "".join(
        f'<a href="#{target}">VIEW {name}</a>'
        for target, _, name in NAMES
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>body{background:#0b1022;color:#edf2ff;font-family:Arial,sans-serif;'
        'max-width:980px;margin:24px auto;padding:16px}'
        '.editor-panel{padding:20px;border:1px solid #40547e;border-radius:12px}'
        '.nexora-command79{padding:24px}.nexora-command79 a{display:inline-block;'
        'margin:6px;color:#a8dfff}</style></head><body>'
        '<section class="editor-panel nexora-command79"><h1>NEXORA STRATEGIC COMMAND</h1>'
        f'{cards}</section>{"".join(sections)}</body></html>'
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            for width, height in ((1440, 900), (390, 844)):
                page = browser.new_page(
                    viewport={"width": width, "height": height},
                    reduced_motion="reduce",
                )
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.set_content(fixture(), wait_until="domcontentloaded")
                page.add_style_tag(path=str(CSS))
                page.add_script_tag(path=str(ATLAS))
                page.add_script_tag(path=str(JS))
                modules = page.locator("details.nexora-command-module80")
                assert modules.count() == 7
                assert modules.first.evaluate("(element) => element.open")
                assert not modules.nth(1).evaluate("(element) => element.open")
                page.get_by_role("button", name="EXPAND ALL MODULES").click()
                assert all(modules.nth(i).evaluate("(element) => element.open") for i in range(7))
                page.get_by_role("button", name="COLLAPSE ALL MODULES").click()
                assert all(not modules.nth(i).evaluate("(element) => element.open") for i in range(7))
                page.locator('a[href="#nexora-readiness-anchor79"]').click()
                assert modules.nth(6).evaluate("(element) => element.open")
                page.locator('a[href="#nexora-pursuits-anchor79"]').click()
                assert modules.nth(2).evaluate("(element) => element.open")
                page.locator(".nexora-pursuit-focus74").click()
                assert modules.first.evaluate("(element) => element.open")
                assert page.locator(".nexora-discovery-goal71").evaluate(
                    "(element) => element.classList.contains('nexora-atlas-focus74')"
                )
                assert not errors, errors
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), (
                    f"Horizontal overflow at {width}px"
                )
                page.screenshot(
                    path=str(OUTPUT / f"command-center-{width}.png"), full_page=True
                )
                page.close()
        finally:
            browser.close()
    print("NEXORA 81 Command Center Chromium interaction checks passed")


if __name__ == "__main__":
    main()
