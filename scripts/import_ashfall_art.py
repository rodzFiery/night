"""ASHFALL 108 — high-resolution building artwork import pipeline.

Install Pillow: python -m pip install Pillow
Import an authored transparent PNG:
  python scripts/import_ashfall_art.py --input render.png --building hq --level 1
Import a sheet with equal-size cells (row-major):
  python scripts/import_ashfall_art.py --input sheet.png --building hq --levels 1,5,10,15 --columns 2

The tool enforces consistent canvas dimensions, alpha transparency and safe
file naming. It never synthesizes missing art or mislabels arbitrary images.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app/static/ashfall-art/production"
REGISTRY = ROOT / "app/static/ashfall-building-registry-100.js"
ENTRY = re.compile(r'\["([a-z][a-z0-9_]*)","[^"]+","(?:live|planned)"\]')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--building", required=True)
    parser.add_argument("--level", type=int)
    parser.add_argument("--levels", help="Comma-separated absolute levels, 1–50, row-major")
    parser.add_argument("--columns", type=int, default=1)
    parser.add_argument("--size", type=int, default=768, help="Output square canvas in pixels")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--quality", type=int, default=94)
    args = parser.parse_args()
    keys = set(ENTRY.findall(REGISTRY.read_text(encoding="utf-8")))
    if args.building not in keys:
        parser.error("Unknown building. Must match the canonical registry.")
    if bool(args.level is not None) == bool(args.levels):
        parser.error("Choose exactly one of --level or --levels.")
    levels = [args.level] if args.level is not None else [int(v.strip()) for v in args.levels.split(",")]
    if not levels or len(set(levels)) != len(levels) or any(n < 1 or n > 50 for n in levels):
        parser.error("Levels must be unique integers between 1 and 50.")
    if args.columns < 1 or args.size < 512 or args.quality not in range(1, 101):
        parser.error("Columns >= 1, size >= 512, quality 1–100 required.")
    try:
        from PIL import Image
    except ImportError:
        parser.error("Pillow required. Install with: python -m pip install Pillow")
    with Image.open(args.input) as source:
        if source.mode not in ("RGBA", "LA", "P"):
            parser.error("Artwork must have an alpha channel. Flat screenshots are not individual building assets.")
        source = source.convert("RGBA")
        if source.getextrema()[3][0] == 255:
            parser.error("Image is fully opaque. Supply a building render with transparent background.")
        rows = (len(levels) + args.columns - 1) // args.columns
        if source.width % args.columns or source.height % rows:
            parser.error("Sheet dimensions must divide exactly into equal cells.")
        cell_w, cell_h = source.width // args.columns, source.height // rows
        images = []
        for i, level in enumerate(levels):
            col, row = i % args.columns, i // args.columns
            crop = source.crop((col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h))
            alpha = crop.getchannel("A")
            bounds = alpha.getbbox()
            if not bounds:
                parser.error(f"Cell {i + 1} is transparent.")
            crop = crop.crop(bounds)
            # Preserve authored perspective and proportional footprint.
            margin = int(args.size * .075)
            crop.thumbnail((args.size - margin * 2, args.size - margin * 2), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (args.size, args.size), (0, 0, 0, 0))
            x = (args.size - crop.width) // 2
            y = args.size - margin - crop.height
            canvas.alpha_composite(crop, (x, y))
            era, tier = ("standard", level) if level <= 25 else ("crystal", level - 25)
            target = OUT / f"{args.building}-{era}-{tier:02d}.webp"
            if target.exists() and not args.overwrite:
                parser.error(f"Target already exists: {target}. Use --overwrite deliberately.")
            images.append((canvas, target))
    OUT.mkdir(parents=True, exist_ok=True)
    for image, target in images:
        image.save(target, "WEBP", quality=args.quality, method=6)
        print(f"Created {target.relative_to(ROOT)}")
    from build_ashfall_art_manifest import write_manifest
    manifest = write_manifest()
    print(f"Updated production manifest with {len(manifest)} existing artwork assets.")
    print(f"Imported {len(images)} authored artwork stage(s) for {args.building}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
