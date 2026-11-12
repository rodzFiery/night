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
