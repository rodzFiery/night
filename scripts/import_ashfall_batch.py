"""ASHFALL 136 — import an entire batch of approved stage images.

Example:
  python scripts/import_ashfall_batch.py --source art/
  python scripts/import_ashfall_batch.py --source art/ --apply

Input names: hq-standard-01.png, hq-crystal-13.webp, etc.
Dry-run by default. Never overwrites existing production artwork.
"""
from __future__ import annotations
import argparse
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_ashfall_art import ENTRY, REGISTRY, ART, NAME, dimensions
from build_ashfall_art_manifest import write_manifest

INPUT = re.compile(r"^([a-z][a-z0-9_]*)-(standard|crystal)-(0[1-9]|1[0-9]|2[0-5])\.(png|webp)$", re.I)


def candidates(source: Path):
    if not source.is_dir():
        raise ValueError(f"Source directory does not exist: {source}")
    keys = {entry[0] for entry in ENTRY.findall(REGISTRY.read_text(encoding="utf-8"))}
    selected = []
    errors = []
    seen = set()
    for path in sorted(source.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {".png", ".webp"}:
            continue
        match = INPUT.fullmatch(path.name)
        if not match or match.group(1) not in keys:
            errors.append(f"Invalid stage filename or unknown building: {path.name}")
            continue
        stem = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        if stem in seen:
            errors.append(f"Two inputs target the same stage: {stem}")
            continue
        seen.add(stem)
        target = ART / (stem + ".webp")
        if target.exists():
            errors.append(f"Production stage already exists (will not overwrite): {target.name}")
        else:
            selected.append((path, target))
    return selected, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="Write production assets and update manifest")
    parser.add_argument("--quality", type=int, default=94)
    args = parser.parse_args()
    if not 1 <= args.quality <= 100:
        parser.error("Quality must be between 1 and 100")
    try:
        selected, errors = candidates(args.source)
    except ValueError as exc:
        parser.error(str(exc))
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    if not selected:
        print("No new stage images found.")
        return 0
    try:
        from PIL import Image
    except ImportError:
        parser.error("Pillow is required: python -m pip install Pillow")
    validated = []
    fingerprints = {}
    for existing in ART.glob("*.webp") if ART.is_dir() else ():
        with Image.open(existing) as image:
            existing_rgba = image.convert("RGBA")
            digest = hashlib.sha256(str(existing_rgba.size).encode() + existing_rgba.tobytes()).hexdigest()
            fingerprints[digest] = existing.name
    for source, target in selected:
        with Image.open(source) as image:
            image.load()
            rgba = image.convert("RGBA")
            if image.mode not in ("RGBA", "LA", "P") or image.getbands()[-1] != "A" and "transparency" not in image.info:
                parser.error(f"{source.name}: image must contain transparency")
            if rgba.getchannel("A").getextrema()[0] == 255:
                parser.error(f"{source.name}: fully opaque images are not allowed")
            if rgba.width < 512 or rgba.height < 384 or rgba.width * rgba.height > 4194304:
                parser.error(f"{source.name}: dimensions outside 512x384 minimum / 4194304 pixel budget")
            digest = hashlib.sha256(str(rgba.size).encode() + rgba.tobytes()).hexdigest()
            if digest in fingerprints:
                parser.error(f"{source.name}: identical pixels already assigned to {fingerprints[digest]}")
            fingerprints[digest] = source.name
            validated.append((source, target, rgba.copy()))
    print(f"Validated {len(validated)} new stages:")
    for source, target, _ in validated:
        print(f"  {source.name} -> {target.name}")
    if not args.apply:
        print("DRY RUN: no files changed. Re-run with --apply to import.")
        return 0
    ART.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for _, target, rgba in validated:
            rgba.save(target, "WEBP", quality=args.quality, method=6)
            created.append(target)
            dimensions(target)
        write_manifest()
    except Exception:
        for target in created:
            target.unlink(missing_ok=True)
        raise
    print(f"Imported {len(created)} unique production images; manifest updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
