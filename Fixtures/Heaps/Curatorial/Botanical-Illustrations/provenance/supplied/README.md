# Botanical illustrations — Curatorial intake handoff

**Commission:** Add one leaf fixture at `Fixtures/Heaps/Curatorial/Botanical-Illustrations/`, a **peer of `POTY/` and `US-Army-SSI/`**, with no category sub-heaps. Target **about 150 distinct botanical illustrations**, selected mechanically from a frozen Wikimedia Commons category snapshot.

This is a **small instruction package only**: no image files, candidate list, or PetScan export have been acquired here. It authorizes local intake and integration, not any change to hazy's similarity implementation.

## Selection basis

Use the **direct File members** of Commons [`Category:Botanical illustrations`](https://commons.wikimedia.org/wiki/Category:Botanical_illustrations), not its descendants on the initial run. The Commons category page displayed **659 direct files and 43 subcategories** when scouted on 2026-10-31; this is an observation, **not** a frozen PetScan result. Explicit `depth=0` in `PETSCAN_QUERY.json` keeps the population bounded and avoids unrequested by-work, by-taxon, and by-artist expansion. If that scope proves inadequate, report the shortfall rather than silently changing category depth.

Curatorial here means **mechanical selection from an existing community-maintained category**, not POTY's editorial award process. No visual-prompt selection, aesthetic balancing, similarity measurements, invented clusters, or expected pairs. The 30-image publication floor from the visual-prompt Similarity contributions **does not automatically apply** to this Curatorial leaf.

## Current repository baseline

`Protonk/hazy` `main` was read at commit `d5656df1e67e61a28903d7cec2bc1d475375bf57` (2026-10-31). At implementation time re-read the current:

- `AGENTS.md`, `Fixtures/README.md`, `Fixtures/FORMAT.md`;
- `Fixtures/Heaps/Curatorial/README.md` and `POTY/README.md`;
- `Fixtures/Heaps/Curatorial/POTY/tools/` (`poty.py`, `review.py`, `transport.py`, `integrate.py`, `test_poty.py`).

Use the active POTY code as a model for a **single source collection / single fixture leaf**, adapting the population source, count, evidence, selection, and raster handling. Do not modify POTY simply to accommodate this task. If the repository has acquired a newer `US-Army-SSI/` implementation, inspect its source-artwork handling too. Do not rely on archived or hypothetical tooling.

`INSTRUCTIONS.md` gives the sequence; `CHECKS.md` gives completion gates; `PETSCAN_QUERY.json` fixes the initial query. The final artifact is produced locally, with media Git-ignored and the checked textual record committed according to repository instructions. Leave pushing to the user.
