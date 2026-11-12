"""ASHFALL 106 — offline production-art validation.

Run from repository root:
    python scripts/audit_ashfall_art.py
    python scripts/audit_ashfall_art.py --strict

Standard library only. Reads the canonical building registry and validates
WebP headers, dimensions, naming, and the complete registry x 50 production asset matrix.
Never creates placeholder art or changes source files.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "app/static/ashfall-building-registry-100.js"
ART = ROOT / "app/static/ashfall-art/production"
NAME = re.compile(r"^([a-z][a-z0-9_]*)-(standard|crystal)-(0[1-9]|1[0-9]|2[0-5])\.webp$")
ENTRY = re.compile(r'\["([a-z][a-z0-9_]*)","([^"]+)","(live|planned)"\]')


def dimensions(path: Path) -> tuple[int, int]:
    """Read WebP dimensions for VP8, VP8L, VP8X without Pillow."""
    with path.open("rb") as stream:
        header = stream.read(30)
    if len(header) < 30 or header[:4] != b"RIFF" or header[8:12] != b"WEBP":
        raise ValueError("invalid RIFF/WEBP header")
    tag = header[12:16]
    if tag == b"VP8X":
        return (
            1 + int.from_bytes(header[24:27], "little"),
            1 + int.from_bytes(header[27:30], "little"),
        )
    if tag == b"VP8L":
        if header[20] != 0x2F:
            raise ValueError("invalid VP8L signature")
        bits = int.from_bytes(header[21:25], "little")
        return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
    if tag == b"VP8 ":
        if header[23:26] != b"\x9d\x01\x2a":
            raise ValueError("invalid VP8 frame signature")
        return (
            struct.unpack_from("<H", header, 26)[0] & 0x3FFF,
            struct.unpack_from("<H", header, 28)[0] & 0x3FFF,
        )
    raise ValueError(f"unsupported WebP chunk {tag!r}")


def audit(min_width: int, min_height: int) -> dict:
    entries = ENTRY.findall(REGISTRY.read_text(encoding="utf-8"))
    if not entries or len({key for key, _, _ in entries}) != len(entries):
        raise RuntimeError("Building registry is empty or contains duplicate keys")
    keys = {key for key, _, _ in entries}
    expected = {
        f"{key}-{era}-{tier:02d}.webp"
        for key in keys
        for era in ("standard", "crystal")
        for tier in range(1, 26)
    }
    found = {p.name for p in ART.glob("*.webp")} if ART.is_dir() else set()
    problems = []
    verified = []
    for name in sorted(found):
        match = NAME.fullmatch(name)
        if not match or match.group(1) not in keys:
            problems.append({"file": name, "issue": "unexpected filename or building key"})
            continue
        try:
            width, height = dimensions(ART / name)
            if width < min_width or height < min_height:
                problems.append({"file": name, "issue": f"low resolution: {width}x{height}"})
            else:
                verified.append({"file": name, "width": width, "height": height})
        except (OSError, ValueError) as exc:
            problems.append({"file": name, "issue": str(exc)})
    return {
        "expected": len(expected),
        "present": len(expected & found),
        "verified": len(verified),
        "missing": len(expected - found),
        "coverage_percent": round(100 * len(expected & found) / len(expected), 2),
        "minimum_resolution": [min_width, min_height],
        "missing_by_building": {
            key: len([name for name in expected - found if name.startswith(key + "-")])
            for key in sorted(keys)
        },
        "problems": problems,
        "verified_files": verified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero if any asset is missing or invalid")
    parser.add_argument("--min-width", type=int, default=512)
    parser.add_argument("--min-height", type=int, default=384)
    args = parser.parse_args()
    report = audit(args.min_width, args.min_height)
    print(json.dumps(report, indent=2))
    return int(bool(report["problems"]) or bool(args.strict and report["missing"]))


if __name__ == "__main__":
    raise SystemExit(main())
