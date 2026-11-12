"""Generate the ASHFALL production-art manifest from actual files.

Run: python scripts/build_ashfall_art_manifest.py
No image files are fabricated. Only existing, canonically named WebP assets
are listed. Importer runs this automatically after successful imports.
"""
from __future__ import annotations

import json
import re
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "app/static/ashfall-art/production"
DEST = ROOT / "app/static/ashfall-art-manifest-116.js"
REGISTRY = ROOT / "app/static/ashfall-building-registry-100.js"
ENTRY = re.compile(r'\["([a-z][a-z0-9_]*)","[^"]+","(?:live|planned)"\]')
ASSET = re.compile(r"([a-z][a-z0-9_]*)-(standard|crystal)-(0[1-9]|1[0-9]|2[0-5])\.webp")


def build() -> list[str]:
    from audit_ashfall_art import dimensions
    keys = set(ENTRY.findall(REGISTRY.read_text(encoding="utf-8")))
    assets = []
    if ART.exists():
        for path in ART.glob("*.webp"):
            match = ASSET.fullmatch(path.name)
            if match and match.group(1) in keys and path.stat().st_size > 0:
                try:
                    width, height = dimensions(path)
                    if width >= 512 and height >= 384 and width * height <= 4194304:
                        assets.append(path.name)
                except (OSError, ValueError):
                    continue
    return sorted(assets)


def manifest_source(assets: list[str]) -> str:
    return (
        "/* ASHFALL 116 — generated from real production artwork. "
        "Run scripts/build_ashfall_art_manifest.py. */\n"
        "window.ASHFALL_ART_MANIFEST_116 = Object.freeze("
        + json.dumps(assets, separators=(",", ":")) + ");\n"
    )


def write_manifest() -> list[str]:
    assets = build()
    DEST.write_text(manifest_source(assets), encoding="utf-8")
    return assets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail when committed manifest is stale")
    args = parser.parse_args()
    if args.check:
        expected = manifest_source(build())
        if not DEST.exists() or DEST.read_text(encoding="utf-8") != expected:
            parser.exit(1, "ASHFALL artwork manifest is stale. Run python scripts/build_ashfall_art_manifest.py\\n")
        print("ASHFALL production manifest matches validated artwork.")
    else:
        assets = write_manifest()
        print(f"ASHFALL production manifest: {len(assets)} verified assets.")
