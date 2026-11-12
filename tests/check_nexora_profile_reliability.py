"""NEXORA 81 — profile template and navigation reliability contracts."""
from pathlib import Path
from html.parser import HTMLParser
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app/templates/profile.html").read_text(encoding="utf-8")
JS = (ROOT / "app/static/nexora-command-center-80.js").read_text(encoding="utf-8")
ATLAS = (ROOT / "app/static/nexora-achievement-atlas-73.js").read_text(encoding="utf-8")


class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.duplicates = []
        self.links = []
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            if attributes["id"] in self.ids:
                self.duplicates.append(attributes["id"])
            self.ids.add(attributes["id"])
        if tag == "a" and attributes.get("href", "").startswith("#"):
            self.links.append(attributes["href"][1:])
        if tag == "script":
            self.scripts.append(attributes.get("src", ""))


def test_template_and_navigation():
    Environment().parse(HTML)
    parser = Structure()
    parser.feed(HTML)
    assert not parser.duplicates, parser.duplicates
    for target in ("nexora-collection-anchor79", "nexora-pursuits-anchor79",
                   "nexora-roadmap-anchor79", "nexora-readiness-anchor79"):
        assert target in parser.ids
        assert target in parser.links
    assert "/static/nexora-command-center-80.js" in parser.scripts
    assert "/static/nexora-achievement-atlas-73.js" in parser.scripts
    assert HTML.index("nexora-command79") < HTML.index("nexora-discovery71")
    ordered = ("nexora-discovery71", "nexora-mastery72", "nexora-pursuits74",
               "nexora-intel75", "nexora-roadmap76", "nexora-forecast77",
               "nexora-readiness78")
    positions = [HTML.index(name) for name in ordered]
    assert positions == sorted(positions)
    assert 'target.closest("details.nexora-command-module80")' in ATLAS
    assert 'window.addEventListener("hashchange", revealHash)' in JS


if __name__ == "__main__":
    test_template_and_navigation()
    print("NEXORA 81 profile template and navigation checks passed")
