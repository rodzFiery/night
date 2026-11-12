"""Generate the ASHFALL production-art manifest from actual files.

Run: python scripts/build_ashfall_art_manifest.py
No image files are fabricated. Only existing, canonically named WebP assets
are listed. Importer runs this automatically after successful imports.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "app/static/ashfall-art/production"
DEST = ROOT / "app/static/ashfall-art-manifest-116.js"
REGISTRY = ROOT / "app/static/ashfall-building-registry-100.js"
ENTRY = re.compile(r'\["([a-z][a-z0-9_]*)","[^"]+","(?:live|planned)"\]')
ASSET = re.compile(r"([a-z][a-z0-9_]*)-(standard|crystal)-(0[1-9]|1[0-9]|2[0-5])\.webp")


def build() -> list[str]:
    keys = set(ENTRY.findall(REGISTRY.read_text(encoding="utf-8")))
    assets = []
    if ART.exists():
        for path in ART.glob("*.webp"):
            match = ASSET.fullmatch(path.name)
            if match and match.group(1) in keys and path.stat().st_size > 0:
                assets.append(path.name)
    return sorted(assets)


def write_manifest() -> list[str]:
    assets = build()
    content = (
        "/* ASHFALL 116 — generated from real production artwork. "
        "Run scripts/build_ashfall_art_manifest.py. */\n"
        "window.ASHFALL_ART_MANIFEST_116 = Object.freeze("
        + json.dumps(assets, separators=(",", ":")) + ");\n"
    )
    DEST.write_text(content, encoding="utf-8")
    return assets


if __name__ == "__main__":
    assets = write_manifest()
    print(f"ASHFALL production manifest: {len(assets)} existing assets.")
