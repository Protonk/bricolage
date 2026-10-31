# US Army shoulder-sleeve insignia — Curatorial intake handoff

**Task:** Create one new, complete *leaf fixture* at `Fixtures/Heaps/Curatorial/US-Army-SSI/`, as a **peer of `POTY/`**. It must have **no category-specific sub-heaps or child fixture sets**. Aim for **200 distinct insignia designs** selected mechanically from a frozen Commons PetScan population.

This is an **instruction package, not an image acquisition or a preselected inventory**. It contains no media bytes and does not claim that PetScan was re-run. The previously reported PetScan query returned **1,641 File-page results**. Record the actual exported result count in the new fixture; if it differs, preserve and explain the difference rather than inventing 1,641 entries.

## Authority and placement

- Repository: `Protonk/hazy`; inspected `main` at `d5656df1e67e61a28903d7cec2bc1d475375bf57` (2026-10-31). Read its **current** `AGENTS.md`, `Fixtures/README.md`, `Fixtures/FORMAT.md`, `Fixtures/Heaps/Curatorial/README.md`, and `Fixtures/Heaps/Curatorial/POTY/README.md` before implementing. If `main` has moved, review the changes first.
- Reference implementation: `Fixtures/Heaps/Curatorial/POTY/tools/`, particularly `transport.py`, `poty.py`, `review.py`, `integrate.py`, and `test_poty.py`. Reuse proven patterns, not POTY's three-category/three-year or one-original-creator selection policy. Do not edit POTY to fit this intake.
- Use `kind=curatorial_heap` and `relation_kind=curatorial_selected`, *not* `prompt_heap`. No `prompt.json`, visual-acceptance labels, similarity scores, expected pairs, invented semantic clusters, or member-level similarity judgments.
- The Curatorial selection basis here is **Commons category membership**, not POTY's award/editorial selection. Say so plainly.

## What counts as done

One directory `Curatorial/US-Army-SSI/` containing its own preserved population snapshot, ordering, exclusion/selection ledger, source and rights evidence, acquisition receipts, validated source/input manifests, local media, and short README. The parent Curatorial index should link to it. There must be **no** `Divisions/`, `Brigades/`, `Corps/`, `SVG/`, `Embroidery/` or other nested contributions.

`INSTRUCTIONS.md` specifies the acquisition sequence; `CHECKS.md` defines completion and failure reporting; `PETSCAN_QUERY.json` pins the query parameters. Start with the query export, not recursive client-side category descent.
