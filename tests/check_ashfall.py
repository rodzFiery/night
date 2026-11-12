#!/usr/bin/env python3
"""ASHFALL static integration checks. Run: python tests/check_ashfall.py
Requires Python 3.10+ and Node.js; no third-party dependencies.
"""
from __future__ import annotations
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "app" / "ashfall_world.html"
STATIC = ROOT / "app" / "static"
REQUIRED_IDS = (
    "buildpanel", "buildtitle", "buildqueue", "afEvolutionCanvas",
    "afEvolutionTrack", "afPreviewCurrent", "afPreviewNext",
    "afPreviewStatus", "upgrade", "builderror",
)
REQUIRED_SCRIPTS = (
    "ashfall-ground-20.js", "ashfall-scenery-21.js",
    "ashfall-art-25.js", "ashfall-preview-28.js",
    "ashfall-construction-29.js", "ashfall-art-13.js",
    "ashfall-inspector-35.js", "ashfall-roster-36.js",
    "ashfall-upgrade-intel-37.js", "ashfall-priorities-38.js",
    "ashfall-strategy-39.js", "ashfall-command-center-40.js",
    "ashfall-doctrine-44.js", "ashfall-development-planner-55.js",
)

class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.refs = []
        self.inline = []
        self.in_script = False
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "script":
            self.in_script = "src" not in attrs and attrs.get("type", "text/javascript") in ("", "text/javascript", "application/javascript", "module")
            self.chunks = []
        if tag in ("script", "link", "img"):
            for attr in ("src", "href"):
                if attrs.get(attr):
                    self.refs.append(attrs[attr])

    def handle_data(self, data):
        if self.in_script:
            self.chunks.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_script:
            self.inline.append("".join(self.chunks))
            self.in_script = False
            self.chunks = []

def check_js(path):
    result = subprocess.run(["node", "--check", str(path)], capture_output=True, text=True)
    if result.returncode:
        raise AssertionError(f"JavaScript syntax failure: {path}\n{result.stderr}")

def main():
    errors = []
    if not PAGE.exists():
        raise SystemExit(f"Missing ASHFALL page: {PAGE}")
    doc = Document()
    doc.feed(PAGE.read_text(encoding="utf-8"))
    for element in REQUIRED_IDS:
        if element not in doc.ids:
            errors.append(f"Missing required UI id: {element}")
    for name in REQUIRED_SCRIPTS:
        if not any(urlsplit(ref).path.endswith("/" + name) for ref in doc.refs):
            errors.append(f"Missing script integration: {name}")
    for ref in doc.refs:
        path = urlsplit(ref).path
        if path.startswith("/static/"):
            asset = STATIC / path.removeprefix("/static/")
            if not asset.is_file():
                errors.append(f"Missing referenced static asset: {path}")
    for name in ("hq", "farm", "lumber", "salvage", "fuel", "barracks"):
        asset = STATIC / "ashfall-art" / (name + ".svg")
        if not asset.is_file():
            errors.append(f"Missing facility artwork: {asset.relative_to(ROOT)}")
    if errors:
        raise AssertionError("\n".join(errors))
    scripts = sorted(STATIC.glob("ashfall-*.js"))
    for script in scripts:
        check_js(script)
    with tempfile.TemporaryDirectory() as directory:
        for index, source in enumerate(doc.inline):
            if source.strip():
                path = Path(directory) / f"ashfall-inline-{index}.js"
                path.write_text(source, encoding="utf-8")
                check_js(path)
    print(f"ASHFALL QA PASS: {len(scripts)} external JS files, {len(doc.inline)} inline scripts, {len(doc.refs)} asset references, {len(REQUIRED_IDS)} required UI elements.")

if __name__ == "__main__":
    try:
        main()
    except (AssertionError, FileNotFoundError) as error:
        print(f"ASHFALL QA FAIL: {error}", file=sys.stderr)
        sys.exit(1)
