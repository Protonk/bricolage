# November 2026 Similarity leaf names

On 2026-11-02 the six Similarity leaves were renamed from short codes to names
that describe their selection prompts, matching the Curatorial leaves. Each move
is a `git mv` of the whole leaf directory, including its Git-ignored `images/`,
`sources/` and `previews/`. [relocations.json](relocations.json) lists each move
with its fixture ID, manifest hash and file counts, taken before and after the move.

| Former folder | Current folder | Fixture ID |
|---|---|---|
| `RG01` | [Red-Accents-in-Green](../../Heaps/Similarity/Red-Accents-in-Green/README.md) | `hazy-rg01-v1` |
| `SF01` | [Speckled-Fields](../../Heaps/Similarity/Speckled-Fields/README.md) | `hazy-sf01-v1` |
| `PS01` | [Pale-Skies-Dark-Ground](../../Heaps/Similarity/Pale-Skies-Dark-Ground/README.md) | `hazy-ps01-v1` |
| `CR01` | [Repeated-Rectangles](../../Heaps/Similarity/Repeated-Rectangles/README.md) | `hazy-cr01-v1` |
| `TG01` | [Tangled-Growth](../../Heaps/Similarity/Tangled-Growth/README.md) | `hazy-tg01-v1` |
| `BSP01` | [Spreading-Patches](../../Heaps/Similarity/Spreading-Patches/README.md) | `hazy-bsp01-v1` |

Fixture IDs, manifests, candidate IDs (`rg-0001`, `sf-0111`, and so on), media
bytes and every file under `provenance/` are unchanged. Historical records that
spell the old paths, such as Curatorial identity audits, leaf validation receipts
and the layout-migration baselines, keep their original bytes; read them against
this table. Live references were updated: each leaf's README commands,
`tools/check.py`, the `prepare.py` baseline path and the `audit.py` prior-inventory
paths, the Similarity index, the heap tour guide's `leaf` fields, the layout test
and the generated collection totals.

## Checks that keyed on the old paths

Immediately after the move, `Fixtures/tools/check_layout.py --full` failed for
nine leaves while the layout, catalog and media checks of all 18 passed. Both
failure classes compared a historical record keyed by leaf path with the live tree:

- Six Curatorial leaves (Botanical-Illustrations, Evan-Amos-Uploads, Ex-Libris,
  Rocks-in-Thin-Section, Stone-Hand-Axes, US-Army-SSI) recompute their recorded
  `provenance/identity-audit.json` and require equality. The record names prior
  fixtures by path (`Heaps/Similarity/RG01`), so recomputation stopped with
  `Recorded audit fixture is missing`.
- Three Similarity leaves (Repeated-Rectangles, Tangled-Growth, Spreading-Patches)
  run `prepare.py --check-only`, which accepts the shared helper's layout-migration
  adaptation through `layout-2026-11/tool-changes.json`, keyed by the old path
  `Fixtures/Heaps/Similarity/PS01/tools/common.py`.

The same day, the audits, the tool-revision resolver and the sampler were taught
to read this record's `leaf-rename` moves: a recorded name or path resolves to the
current leaf, hashes are still required to match, and recomputed audits keep the
record's order. The records themselves were not edited. All 18 leaf checks pass.

The sampler records a leaf's path in every inventory snapshot. Snapshots taken
before this rename still name the old paths. The committed demonstration draw has
one such image, from `SF01`, plus that leaf's four pinned metadata files. `verify`,
`show` and `publish` now read them at the current path and report it as
`current_path`; the recorded hashes must still match. A new draw with the same
seed selects the same images from a new inventory.
