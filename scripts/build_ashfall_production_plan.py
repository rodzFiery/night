"""ASHFALL 131 — reproducible 1,400-stage production shot list.

Uses the canonical JS registry and validated manifest without inventing images.
Run: python scripts/build_ashfall_production_plan.py
     python scripts/build_ashfall_production_plan.py --check
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "app/static/ashfall-building-registry-100.js"
MANIFEST = ROOT / "app/static/ashfall-art-manifest-116.js"
OUTPUT = ROOT / "docs/ashfall-production-plan.json"
ENTRY = re.compile(r'\["([a-z][a-z0-9_]*)","([^"]+)","(live|planned)"\]')
BANDS = (
    "survival", "reinforcement", "industrial", "fortress", "stronghold",
    "crystal-awakening", "crystal-engineering", "high-technology",
    "futuristic-campus", "apex-megastructure",
)
BENCHMARKS = {1, 13, 25, 26, 38, 50}


def registered_buildings() -> list[tuple[str, str, str]]:
    entries = ENTRY.findall(REGISTRY.read_text(encoding="utf-8"))
    if not entries or len({key for key, _, _ in entries}) != len(entries):
        raise ValueError("Building registry is missing or contains duplicate keys")
    return entries


def available_assets() -> set[str]:
    source = MANIFEST.read_text(encoding="utf-8")
    match = re.search(r'Object\.freeze\((\[[^;]*\])\)', source)
    if not match:
        raise ValueError("Invalid production art manifest")
    names = json.loads(match.group(1))
    if not isinstance(names, list) or any(not isinstance(x, str) for x in names):
        raise ValueError("Invalid production asset list")
    return set(names)


def build_plan() -> dict:
    published = available_assets()
    entries = []
    for key, name, status in registered_buildings():
        for level in range(1, 51):
            era = "standard" if level <= 25 else "crystal"
            era_level = level if level <= 25 else level - 25
            filename = f"{key}-{era}-{era_level:02d}.webp"
            entries.append({
                "building": key, "name": name, "gameplay_status": status,
                "overall_level": level, "era": era, "era_level": era_level,
                "visual_band": BANDS[(level - 1) // 5],
                "filename": filename,
                "priority": "benchmark" if key == "hq" and level in BENCHMARKS else
                            "live" if status == "live" else "planned",
                "asset_status": "published" if filename in published else "missing",
            })
    counts = {
        "buildings": len(registered_buildings()), "required": len(entries),
        "published": sum(x["asset_status"] == "published" for x in entries),
        "missing": sum(x["asset_status"] == "missing" for x in entries),
        "headquarters_benchmarks": len(BENCHMARKS),
    }
    return {"schema_version": 1, "progression": "standard-25-then-crystal-25",
            "counts": counts, "stages": entries}


def serialize() -> str:
    return json.dumps(build_plan(), indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = serialize()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            parser.exit(1, "ASHFALL production plan is stale; regenerate it.\n")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(expected, encoding="utf-8")
    print("ASHFALL production plan verified" if args.check else "ASHFALL production plan generated")


if __name__ == "__main__":
    main()
