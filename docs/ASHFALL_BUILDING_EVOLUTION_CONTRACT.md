# ASHFALL — Sequential Building Evolution Contract (130)

## Decision: locked

Every facility has **50 distinct authored visual stages**, not recolors or algorithmic decorations:
- Standard 01–25 (overall levels 1–25): survival shelters evolve into fortified industrial complexes.
- Crystal 01–25 (overall levels 26–50): industrial complexes evolve into monumental crystal-powered futuristic architecture.
- Crystal 01 follows Standard 25. No alternative branch, no level reset of gameplay state.
- Buildings not yet implemented in gameplay remain `planned` in the canonical registry. Visual registration does **not** unlock them.

## Single source of truth

`app/static/ashfall-building-registry-100.js` owns building keys and the level-to-era mapping.
The renderer requests `/static/ashfall-art/production/{key}-{era}-{01..25}.webp`.
The manifest lists **only validated, present** files. Missing art may fall back to legacy visuals during development, but missing artwork must not be described as complete.

## Asset acceptance contract

Each stage must be a separate image with:
1. A consistent three-quarter isometric camera, anchor and footprint alignment.
2. Distinct, readable architectural evolution from the preceding stage.
3. Transparent background, no baked opaque backdrop, no text watermark.
4. Minimum 512×384 pixels; production target at least 1024px wide, maximum 4,194,304 source pixels for the current streaming budget.
5. Physical material continuity, plausible construction, recognizable facility silhouette.
6. Ground-contact shadows, lighting and vegetation integrated consistently across the collection.
7. Correct key, era and two-digit stage filename, validated WebP format.
8. Tested in-game at near/far zoom alongside other facilities.

## Art direction by level

| Levels | Architectural transformation |
|---|---|
| Standard 01–05 | Improvised survival structures; scavenged metal, tarps, wood |
| Standard 06–10 | Permanent reinforced construction; first power and security |
| Standard 11–15 | Industrial capacity; machinery, access roads, specialist annexes |
| Standard 16–20 | Fortified complex; defensive layers and advanced logistics |
| Standard 21–25 | Mature industrial stronghold; maximum pre-crystal capability |
| Crystal 01–05 | Crystal energy retrofit; first powered systems |
| Crystal 06–10 | Integrated crystal engineering; redesigned power and structures |
| Crystal 11–15 | High-tech infrastructure; new geometry and specialized modules |
| Crystal 16–20 | Advanced futuristic campus; monumental scale and automation |
| Crystal 21–25 | Apex crystalline megastructure; unique endgame silhouette |

**Every intermediate level still needs a unique image.** These bands define a coherent design language, not permission to reuse images.

## Production sequence

1. Establish a single approved visual benchmark: Headquarters Standard 01, 13, 25; Crystal 01, 13, 25.
2. Produce and validate the complete 50-stage Headquarters set.
3. Complete all six currently live facilities, then medical, training and research.
4. Complete remaining planned facilities in gameplay-priority order.
5. Produce separate collections for troops, heroes, Behemoths, equipment and world props.

## Quality gates

- Run `python scripts/audit_ashfall_art.py` for inventory and errors.
- Run `python scripts/audit_ashfall_art.py --strict` only when a complete registry set is expected.
- Run `python scripts/build_ashfall_art_manifest.py` after importing approved assets.
- Never claim an asset is live until its manifest entry exists and the actual game renders it.
- Gameplay progression, construction and resource costs are server-authoritative; visuals must not modify them.

## Current state

The expanded registry contains 28 facility keys (six live, 22 planned), requiring **1,400** distinct stage images. This document is a production specification, not a claim that those images already exist.
