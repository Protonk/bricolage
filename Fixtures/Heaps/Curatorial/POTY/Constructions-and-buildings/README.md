# POTY — Constructions and buildings

**Complete: 50 acquired / 50 selected / 248 eligible entries.** Target: 50. Excluded in
the processed ordering: 40; unused reserve: 158; pending acquisition: 0; pending
provenance review: 0.

This is a leaf contribution to Curatorial → POTY. Membership comes from Wikimedia
Commons’ official **Constructions and buildings** Round 1 category data pages for 2023,
2024 and 2025, with 41, 78 and 129 entries respectively. The category’s editorial
definition is unchanged. All category entries also occur in their year’s Round 1 All
list. No finalists-only restriction, visual prompt or aesthetic judgment was applied.

The target of 50 accepted images is reached; later entries in the seeded order are
unused reserve, not pending acquisition.

The [source collection README](../README.md) documents the seed, exact ordering
algorithm, provenance rules, source inconsistencies, transport diagnosis, and
validation. This leaf uses `curatorial_heap`, with empty pair expectations. Its source
IDs link one input to one byte-identical downloaded source, not different photographs to
each other.

- `inventory.json`: complete eligible entries, original published fields, year/category membership, data-page revisions and hashes.
- `ordering.json`, `selection.json`: deterministic order, selections, exclusions and conflicts.
- `provenance/`: raw API bytes, creator/rights/relationship evidence, aliases and explicit overrides, receipts, full import mapping and checks.
- `images/`, `sources/`: opaque comparison inputs and unchanged downloaded renditions. Both are Git-ignored.
- `manifest.json`, `manifest.csv`, `sources.csv`, `SHA256SUMS.txt`: decoded dimensions, orientation, format and source/input byte mapping.
- [SOURCES.md](SOURCES.md): file-specific credits, license evidence and exact downloaded URLs.
- `batches/`: all acquired inputs plus five-image smoke and twenty-image medium subsets.
- `previews/selected-*.jpg`: contact sheets for inspection, never comparison inputs or selection evidence.

Original creators explicitly unknown in the selection: **0**. Known uploader counts are
reported separately in [the acquisition receipt](provenance/acquisition.json). Creator
and capture independence beyond the available metadata is not proven. Rights statements
are taken from individual file evidence; no new collection license is assigned.

From the repository root, with Pillow from `../requirements.txt` installed:

```sh
python3 Fixtures/Heaps/Curatorial/POTY/tools/integrate.py check --category "Constructions and buildings"
```

This check is offline and needs only this contribution’s evidence and local media. It
verifies the recorded acquisition state rather than requiring 50 images. A checkout
without media fails visibly; it does not download replacements. The fixture index and
parent READMEs provide discovery at the additional directory depth.
