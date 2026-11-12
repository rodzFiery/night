"""ASHFALL 140 — inspect the locally installed 50 Headquarters images.

Run from project root:
    python scripts/check_ashfall_hq_install.py
    python scripts/check_ashfall_hq_install.py --strict

Standard-library-only structural check. Pixel transparency requires Pillow,
which is optional for a basic report but mandatory with --strict.
No files are modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "app/static/ashfall-art/production"
sys.path.insert(0, str(ROOT / "scripts"))
from audit_ashfall_art import dimensions


def check() -> dict:
    try:
        from PIL import Image
    except ImportError:
        Image = None

    entries = []
    fingerprints = {}
    for level in range(1, 51):
        era = "standard" if level <= 25 else "crystal"
        stage = level if level <= 25 else level - 25
        filename = f"hq-{era}-{stage:02d}.webp"
        path = ART / filename
        row = {"level": level, "filename": filename, "exists": path.is_file(),
               "valid": False, "issues": []}
        if not path.is_file():
            row["issues"].append("missing")
            entries.append(row)
            continue
        try:
            width, height = dimensions(path)
            row["dimensions"] = [width, height]
            if width < 512 or height < 384:
                row["issues"].append("below minimum 512x384 resolution")
            if width * height > 4194304:
                row["issues"].append("exceeds 4,194,304-pixel budget")
            if Image is None:
                row["issues"].append("transparency not checked: install Pillow")
            else:
                with Image.open(path) as image:
                    image.load()
                    rgba = image.convert("RGBA")
                    alpha = rgba.getchannel("A")
                    if alpha.getextrema()[0] == 255:
                        row["issues"].append("fully opaque: no transparent pixels")
                    if alpha.getbbox() is None:
                        row["issues"].append("empty transparent image")
                    digest = hashlib.sha256(str(rgba.size).encode() + rgba.tobytes()).hexdigest()
                    if digest in fingerprints:
                        row["issues"].append(f"pixel-identical to {fingerprints[digest]}")
                    else:
                        fingerprints[digest] = filename
        except Exception as exc:
            row["issues"].append(f"unreadable image: {exc}")
        row["valid"] = not row["issues"]
        entries.append(row)
    return {
        "expected": 50,
        "present": sum(item["exists"] for item in entries),
        "verified": sum(item["valid"] for item in entries),
        "missing": [item["filename"] for item in entries if not item["exists"]],
        "issues": [{"file": item["filename"], "issues": item["issues"]}
                   for item in entries if item["issues"] and item["exists"]],
        "transparency_checked": Image is not None,
        "stages": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report")
    args = parser.parse_args()
    result = check()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"ASHFALL Headquarters: {result['present']}/50 installed; "
              f"{result['verified']}/50 fully verified")
        if not result["transparency_checked"]:
            print("Pillow unavailable: install with python -m pip install Pillow")
        for name in result["missing"]:
            print("MISSING:", name)
        for issue in result["issues"]:
            print("CHECK:", issue["file"], "; ".join(issue["issues"]))
    return int(args.strict and result["verified"] != 50)


if __name__ == "__main__":
    raise SystemExit(main())
