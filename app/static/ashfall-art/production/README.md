# ASHFALL — production raster assets

The renderer in `/static/ashfall-art-13.js` automatically loads transparent, isometric WebP assets from this directory. The generated concept screenshots are **not** valid standalone assets and must not be substituted for these files.

## Required buildings

`hq-1.webp`, `hq-2.webp`, `hq-3.webp`
`farm-1.webp`, `farm-2.webp`, `farm-3.webp`
`lumber-1.webp`, `lumber-2.webp`, `lumber-3.webp`
`salvage-1.webp`, `salvage-2.webp`, `salvage-3.webp`
`fuel-1.webp`, `fuel-2.webp`, `fuel-3.webp`
`barracks-1.webp`, `barracks-2.webp`, `barracks-3.webp`

## Asset contract

- Transparent background; one building per image; no HUD, labels, UI or text.
- Identical isometric camera angle, lighting direction, palette and ground-anchor convention.
- Native 1024–2048px resolution; WebP with alpha.
- Level tiers: 1 = early, 2 = fortified, 3 = elite.
- Artwork ground contact near lower center, with consistent empty padding.
- Test all tiers at in-game zoom before merging.
- Existing SVG assets remain as fallback until production artwork is actually delivered.

## Important

A visually detailed *full-scene concept image* cannot be dropped into the interactive game without losing correct independent building interactions and world movement. Do not mark this milestone complete until the 18 building assets exist and render in the browser.

## Full 50-level art progression (ASHFALL 99)

**Each of six buildings has 50 progression levels: 25 standard + 25 Crystal Era.**
The runtime chooses the appropriate era and level, using these optional image names:

- `hq-standard-01.webp` through `hq-standard-25.webp`
- `hq-crystal-01.webp` through `hq-crystal-25.webp`

Repeat for `farm`, `lumber`, `salvage`, `fuel`, and `barracks`. Full coverage is **300 independently authored images**, not 18. The runtime requests the current exact level and nearest 5-level milestone lazily. Existing `hq-1.webp` to `hq-3.webp` style art is retained as a temporary fallback. The Crystal Era begins at overall level 26 (Crystal I), ending at overall level 50 (Crystal XXV).

The renderer's stage selection is **visual-only**. Economy caps, unlock costs, and actual Crystal Era upgrade rules must be implemented and tested separately before claiming 50 playable upgrade levels. The 18-image starter ZIP is not yet present in this repository.

## Expanded target — 15 buildings × 50 visual levels

The earlier six-building/300-image specification is the **current prototype**, not the finished scope.
The agreed target is **15 distinct building types**, each supporting 25 standard levels plus 25 Crystal Era tiers: **750 visual progression states**.

The remaining nine building identities, functions, upgrade mechanics and footprints must be defined in the gameplay design before assigning final asset keys. Do not invent or ship placeholder building functions. Use the same `{key}-{standard|crystal}-{01..25}.webp` naming contract for every registered building.

Production may use authored modular layers (base structure, additions, era-specific attachments, lighting) instead of 750 unrelated files, but every progression level must have an intentional and testable visual result. Building gameplay unlocks and economy progression are separate from rendering.


## ASHFALL 108 — Authoring-to-runtime import

The canonical production contract is **20 buildings × 50 levels**, each with a transparent, individually authored render. Legacy `{key}-1.webp` / `-2.webp` / `-3.webp` files are transitional fallback only.

For a standalone transparent PNG, from repository root:

```powershell
python -m pip install Pillow
python scripts/import_ashfall_art.py --input .\\renders\\hq-level-01.png --building hq --level 1
python scripts/audit_ashfall_art.py
```

For a 2-column, 2-row sheet with four transparent building renders, ordered left-to-right then top-to-bottom:

```powershell
python scripts/import_ashfall_art.py --input .\\renders\\hq-sheet.png --building hq --levels 1,5,10,15 --columns 2
```

The importer crops transparency, scales the isolated structure proportionally, aligns the bottom-center anchor on a standard square canvas, and writes the correct `{key}-{standard|crystal}-{01..25}.webp` filename. It rejects fully opaque screenshots and unknown building IDs; it does not invent missing stages. Input must already be cleanly separated artwork with transparency. The importer cannot automatically separate buildings from a full settlement screenshot or repair inconsistent perspective.

**Art direction:** preserve a consistent 3/4 isometric camera, physically plausible surface materials, readable rooftop silhouette, subtle wear, coherent shadows and lighting. Crystal Era designs should evolve the same building's recognizable identity, not replace it with unrelated glowing shapes.
