"""ASHFALL 141 — production coverage across all 28 building families.

Checks every required exact-level WebP filename, without inventing assets.
Run:
    python scripts/ashfall_building_coverage.py
    python scripts/ashfall_building_coverage.py --json
    python scripts/ashfall_building_coverage.py --strict
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "app/static/ashfall-building-registry-100.js"
ART = ROOT / "app/static/ashfall-art/production"
ENTRY = re.compile(r'\["([a-z][a-z0-9_]*)","([^"]+)","(live|planned)"\]')


def required_names(key: str) -> list[str]:
    return [f"{key}-{era}-{stage:02d}.webp"
            for era in ("standard", "crystal") for stage in range(1, 26)]


def coverage(registry: Path = REGISTRY, art: Path = ART) -> dict:
    from audit_ashfall_art import dimensions

    entries = ENTRY.findall(registry.read_text(encoding="utf-8"))
    if len(entries) != 28 or len({key for key, _, _ in entries}) != 28:
        raise ValueError("Building registry must contain exactly 28 unique buildings")
    families = []
    for key, name, status in entries:
        present, invalid, missing = [], [], []
        for filename in required_names(key):
            path = art / filename
            if not path.is_file():
                missing.append(filename)
                continue
            try:
                width, height = dimensions(path)
                if path.stat().st_size == 0 or width < 512 or height < 384 or width * height > 4194304:
                    invalid.append(filename)
                else:
                    present.append(filename)
            except (OSError, ValueError):
                invalid.append(filename)
        families.append({
            "key": key, "name": name, "gameplay_status": status,
            "expected": 50, "valid": len(present), "missing": len(missing),
            "invalid": len(invalid), "complete": len(present) == 50,
            "next_missing": (missing + invalid)[0] if missing or invalid else None,
            "invalid_files": invalid,
        })
    return {
        "buildings": len(families), "expected": 1400,
        "valid": sum(f["valid"] for f in families),
        "complete_families": sum(f["complete"] for f in families),
        "families": families,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero until all 1400 assets are present")
    args = parser.parse_args()
    report = coverage()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"ASHFALL: {report['valid']}/{report['expected']} verified building assets; "
              f"{report['complete_families']}/28 complete families")
        for family in report["families"]:
            print(f"  {family['name']:<28} {family['valid']:>2}/50  "
                  f"[{family['gameplay_status']}]  "
                  f"next: {family['next_missing'] or 'COMPLETE'}")
    return int(args.strict and report["valid"] != 1400)


if __name__ == "__main__":
    raise SystemExit(main())
