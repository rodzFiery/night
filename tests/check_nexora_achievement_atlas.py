"""NEXORA 73 — static Atlas wiring and progressive-enhancement contracts."""
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TEMPLATE=ROOT/"app/templates/profile.html"
SCRIPT=ROOT/"app/static/nexora-achievement-atlas-73.js"
STYLE=ROOT/"app/static/css/profile.css"


def test_atlas_contract():
    html=TEMPLATE.read_text(encoding="utf-8")
    js=SCRIPT.read_text(encoding="utf-8")
    css=STYLE.read_text(encoding="utf-8")
    assert 'src="/static/nexora-achievement-atlas-73.js"' in html
    for key in ("data-world73", "data-earned73", "data-title73"):
        assert key in html
    assert 'document.querySelector(".nexora-discovery71")' in js
    assert "aria-live" in js and "role" in js
    assert "card.hidden = !match" in js
    assert "grid.append(card)" in js
    assert ".nexora-discovery-goal71[hidden]" in css
    assert "DOMContentLoaded" in js
    assert "fetch(" not in js and "XMLHttpRequest" not in js
    assert "localStorage" not in js
    assert "document.createElement" in js


if __name__=="__main__":
    test_atlas_contract()
    print("NEXORA 73 Atlas wiring checks passed")
