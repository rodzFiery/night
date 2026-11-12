"""ASHFALL 142 — 250 distinct stage briefs for the five other live facilities.

Produces reproducible art direction, not images. All stage names correspond to
automatic building-level art paths. No skins or manual appearance controls.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs/ashfall-live-facility-art-briefs.json"

FAMILIES = {
    "farm": ("Farm", "greenhouse bays, irrigation, seed storage, vertical hydroponics", "cultivation beds", "seed vault", "irrigation tower", "greenhouse spine", "harvest conveyors"),
    "lumber": ("Lumber Yard", "timber sorting, sawmill, log cranes, reinforced processing", "log racks", "saw bench", "sorting gantry", "drying kiln", "industrial saw hall"),
    "salvage": ("Salvage Station", "scrap sorting, magnetic cranes, dismantling and recycling", "scrap cages", "dismantling bay", "sorting crane", "metal press", "reclamation furnace"),
    "fuel": ("Fuel Collector", "sealed tanks, pumps, refinery piping and storage safety", "fuel drums", "pump shelter", "filter bank", "tank gantry", "distillation stack"),
    "barracks": ("Infantry Barracks", "living quarters, training yards, armories and defenses", "bunkhouse", "equipment shed", "drill yard", "armored armory", "guard tower"),
}

# Ten visual bands of five levels, each with a distinct authored focal element.
STANDARD = (
    "hand-built scavenged shelter", "timber-framed functional annex",
    "corrugated steel workshop", "reinforced concrete compound",
    "large industrial fortified facility",
)
CRYSTAL = (
    "first crystal conduits integrated into inherited structure",
    "alloy-framed energy automation",
    "high-technology integrated facility",
    "luminous multi-wing crystal campus",
    "monumental crystal-powered apex complex",
)
MODIFIERS = (
    "visible external service ladder", "expanded weatherproof roof geometry",
    "additional utility piping and protective barriers", "elevated operating platform",
    "fully enclosed specialized service wing",
)


def brief(key: str, level: int) -> dict:
    if key not in FAMILIES or not 1 <= level <= 50:
        raise ValueError("Unknown facility or invalid level")
    name, purpose, *features = FAMILIES[key]
    era = "standard" if level <= 25 else "crystal"
    stage = level if era == "standard" else level - 25
    band = (stage - 1) // 5
    variation = (stage - 1) % 5
    style = (STANDARD if era == "standard" else CRYSTAL)[band]
    return {
        "building": key, "name": name, "overall_level": level,
        "era": era, "era_level": stage,
        "filename": f"{key}-{era}-{stage:02d}.webp",
        "primary_function": purpose,
        "architectural_phase": style,
        "signature_feature": features[band],
        "stage_specific_change": MODIFIERS[variation],
        "composition": (
            "Three-quarter isometric camera; entrance facing bottom-right; "
            "identical ground anchor and building footprint alignment across levels; "
            "physically coherent architecture and functional machinery; "
            "warm upper-left key light, cool upper-right fill; "
            "single isolated structure on transparent RGBA background; "
            "no characters, typography, UI, scenic backdrop or level numbers."
        ),
        "materials": (
            "weathered timber, rusted steel, concrete, worn tarpaulin"
            if era == "standard" else
            "dark titanium, machined silver alloy, violet-blue crystal energy"
        ),
        "required_canvas": [1024, 1024],
        "production_status": "brief_only",
        "approved": False,
    }


def serialize() -> str:
    stages = [brief(key, level) for key in FAMILIES for level in range(1, 51)]
    return json.dumps({
        "schema_version": 1,
        "note": "These 250 entries are production briefs, NOT completed image assets.",
        "families": list(FAMILIES), "stages": stages,
    }, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = serialize()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != expected:
            parser.exit(1, "Facility briefs missing or stale; regenerate first.\n")
        print("ASHFALL: 250 facility art briefs verified")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(expected, encoding="utf-8")
        print("ASHFALL: 250 facility art briefs generated")


if __name__ == "__main__":
    main()
