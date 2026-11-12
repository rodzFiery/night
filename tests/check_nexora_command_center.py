"""NEXORA 80 — static progressive-enhancement and deep-link contracts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app/templates/profile.html").read_text(encoding="utf-8")
JS = (ROOT / "app/static/nexora-command-center-80.js").read_text(encoding="utf-8")
CSS = (ROOT / "app/static/css/profile.css").read_text(encoding="utf-8")


def test_modules_and_deep_links():
    assert 'src="/static/nexora-command-center-80.js"' in HTML
    for anchor in ("nexora-collection-anchor79", "nexora-pursuits-anchor79",
                   "nexora-roadmap-anchor79", "nexora-readiness-anchor79"):
        assert f'id="{anchor}"' in HTML
        assert anchor in JS
    for selector in ("nexora-mastery72", "nexora-intel75", "nexora-forecast77"):
        assert selector in HTML and selector in JS
    assert 'document.createElement("details")' in JS
    assert 'document.createElement("summary")' in JS
    assert 'window.addEventListener("hashchange", revealHash)' in JS
    assert "details.open = true" in JS and "details.open = false" in JS
    assert ".nexora-command-module80" in CSS
    assert "fetch(" not in JS and "localStorage" not in JS


if __name__ == "__main__":
    test_modules_and_deep_links()
    print("NEXORA 80 command center contracts passed")
