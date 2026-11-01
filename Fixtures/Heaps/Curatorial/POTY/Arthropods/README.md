# POTY — Arthropods

## Purpose and basis

POTY Round 1 Arthropods, 2023–2025; seeded selection, no expected matches.
Fixture ID: `hazy-poty-arthropods-v1`; kind: `curatorial_heap`.

## Completeness

The published manifest contains **43 inputs**. The detailed record below
retains the original selection counts, pending cases and acquisition limitations.
The layout migration changes no membership or completion status.

## Contents

This leaf follows the [shared fixture format](../../../../FORMAT.md).
`images/`, `sources/`, `previews/` and `batches/` retain their roles. Live commands
and dependencies are in `tools/`; the [evidence index](provenance/README.md)
locates intake/construction records, receipts and preserved packages.

## Validation

From the repository root, using Python 3.14.x:

```sh
.venv/bin/python -m pip install -r Fixtures/Heaps/Curatorial/POTY/Arthropods/tools/requirements.txt
.venv/bin/python Fixtures/Heaps/Curatorial/POTY/Arthropods/tools/check.py
```

The check is offline and includes the shared layout check and the existing
specialized validators. `--metadata-only` omits media and specialized checks.

## Limitations

Selection and source relationships retain their recorded scope; they are not
similarity scores or additional matching assertions. Technical/provenance
uncertainties and partial acquisitions remain documented below.

## Detailed record

**Complete: 43 acquired / 43 selected / 237 eligible entries.** Target: 50. Excluded in
the processed ordering: 194; unused reserve: 0; pending acquisition: 0; pending
provenance review: 0.

This is a leaf contribution to Curatorial → POTY. Membership comes from Wikimedia
Commons’ official **Arthropods** Round 1 category data pages for 2023, 2024 and 2025,
with 47, 86 and 104 entries respectively. The category’s editorial definition is
unchanged. All category entries also occur in their year’s Round 1 All list. No
finalists-only restriction, visual prompt or aesthetic judgment was applied.

The population is exhausted under the original-creator cap and documented provenance
exclusions: the shortfall is seven images, with no pending search or substituted
category.

The [source collection README](../README.md) documents the seed, exact ordering
algorithm, provenance rules, source inconsistencies, transport diagnosis, and
validation. This leaf uses `curatorial_heap`, with empty pair expectations. Its source
IDs link one input to one byte-identical downloaded source, not different photographs to
each other.

- `provenance/intake/inventory.json`: complete eligible entries, original published fields, year/category membership, data-page revisions and hashes.
- `provenance/intake/ordering.json`, `provenance/intake/selection.json`: deterministic order, selections, exclusions and conflicts.
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
.venv/bin/python Fixtures/Heaps/Curatorial/POTY/tools/integrate.py check --category "Arthropods"
```

This check is offline and needs only this contribution’s evidence and local media. It
verifies the recorded acquisition state rather than requiring 50 images. A checkout
without media fails visibly; it does not download replacements. The fixture index and
parent READMEs provide discovery at the additional directory depth.
