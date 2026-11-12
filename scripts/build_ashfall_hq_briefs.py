"""ASHFALL 139 — deterministic HQ architectural art briefs.

Generates a precise, level-specific production brief for every HQ stage.
These are instructions for artists, NOT completed images.
Usage: python scripts/build_ashfall_hq_briefs.py
       python scripts/build_ashfall_hq_briefs.py --check
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ashfall-hq-art-briefs.json"

STANDARD = (
    "scrap-wood shelter and patched corrugated roof",
    "reinforced timber walls and a raised observation hatch",
    "salvaged steel entrance canopy and side storage",
    "stone footing with protected utility enclosure",
    "armored sheet-metal facade and watch platform",
    "concrete foundations and twin radio masts",
    "enclosed operations wing and barricaded gate",
    "reinforced roof deck with satellite communications",
    "two-level command building and floodlit perimeter",
    "integrated generator annex and protected entry",
    "concrete command tower and armored windows",
    "expanded operations courtyard and signal arrays",
    "three-story hardened headquarters with defensive parapets",
    "modular armored wings and command balcony",
    "reinforced service tunnels and dual lookout towers",
    "hardened command bunker and broad central courtyard",
    "heavy blast doors and elevated operations bridge",
    "fortified perimeter walls with integrated sentry posts",
    "layered concrete bastions and expanded radar dish",
    "multi-wing strategic command complex with protected antenna",
    "high defensive towers and enclosed vehicle gate",
    "armored command citadel with layered roof structures",
    "command fortress with elevated control room and shielded utilities",
    "large defensive compound with reinforced corner towers",
    "fully fortified industrial command stronghold and monumental gate",
)
CRYSTAL = (
    "first embedded violet energy conduits within inherited fortress walls",
    "small crystalline reactor chamber and blue power channels",
    "crystal-tipped communications spire and energized access gate",
    "reinforced alloy facade with luminous geometric seams",
    "paired crystal pylons flanking a compact command tower",
    "expanded energy collector and articulated alloy roof",
    "multi-tier command platform with shield emitters",
    "elevated crystal core beneath transparent containment dome",
    "alloy defense turrets and prismatic antenna arrays",
    "centralized reactor vault and synchronized energy pylons",
    "wide futuristic command hall with floating energy crown",
    "tiered research-command annex and blue crystal beacons",
    "advanced citadel with a towering central crystal spire",
    "orbital communications ring and crystalline buttresses",
    "high-capacity reactor towers and angular alloy wings",
    "floating defensive halo and luminous shield anchors",
    "interconnected command towers with prismatic skybridge",
    "towering crystal reactor with symmetrical defense arrays",
    "multi-ring energy distribution structure and radiant buttresses",
    "enormous high-technology command palace with crystal fins",
    "monumental alloy citadel with three energy spires",
    "suspended crystal lattice and orbital relay ring",
    "vast futuristic command campus with luminous terraces",
    "apex fortress with layered levitating crystal crowns",
    "colossal crystal-powered megastructure with radiant command core",
)


def brief(level: int) -> dict:
    if not 1 <= level <= 50:
        raise ValueError("HQ level must be 1–50")
    crystal = level > 25
    stage = level - 25 if crystal else level
    era = "crystal" if crystal else "standard"
    defining = (CRYSTAL if crystal else STANDARD)[stage - 1]
    return {
        "building": "hq",
        "overall_level": level,
        "era": era,
        "era_level": stage,
        "filename": f"hq-{era}-{stage:02d}.webp",
        "signature_feature": defining,
        "direction": (
            "Isometric three-quarter elevated camera, front entrance faces bottom-right; "
            "single complete building, centered on identical ground anchor; "
            "realistic materials, physically coherent architecture, intricate hand-authored details; "
            "consistent warm key light from upper-left and cool fill from upper-right; "
            "transparent RGBA background, no labels, UI, typography, people or scenic backdrop."
        ),
        "palette": "weathered concrete, steel, rust, amber practical lights" if not crystal
                   else "dark titanium, silver alloy, blue-violet crystal luminescence",
        "continuity": "Upgrade from previous level without losing headquarters silhouette; "
                      "make the signature feature clearly distinguishable.",
        "required_canvas": [1024, 1024],
        "approved": False,
        "production_status": "brief_only",
    }


def serialize() -> str:
    return json.dumps({
        "schema_version": 1,
        "asset_type": "architectural_production_brief",
        "note": "Briefs are not image assets and do not imply artwork completion.",
        "stages": [brief(level) for level in range(1, 51)],
    }, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = serialize()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            parser.exit(1, "HQ art briefs are stale. Regenerate them.\n")
        print("HQ art briefs verified")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(expected, encoding="utf-8")
        print("HQ art briefs generated")


if __name__ == "__main__":
    main()
