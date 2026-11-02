# Fixture format and evidence

See the [fixture index](README.md) for roles and current locations. Directory
organization is separate from the existing manifest schema and fixture IDs.

The [single leaf template](Template/README.md) defines the common root layout,
intake/construction evidence locations and `tools/check.py` entry point for new
sets. The [November 2026 migration](provenance/layout-2026-11/README.md) records
the baseline and completed adoption by all 18 existing leaves. Schema version 1 and all
fixture identities remain unchanged.

Only each leaf set's `images/` directory is comparison input. Integrated sets use:

```text
images/             Flat input files with opaque names
sources/            Preserved supplied/acquired bytes; original names in sources.csv
batches/            batch-*.txt partition inputs; smoke.txt and medium.txt are subsets
previews/           Local contact sheets/intermediates, outside comparison inputs
tools/              Live tools, check.py, requirements.txt
provenance/         Indexed supporting material; README.md explains each record
provenance/intake/  Selection basis, candidates, inventory/order/selection records
manifest.json       Versioned description plus image records
manifest.csv        The same image records, in the same column order
sources.csv         Source identities, original names, credits and processing history
SOURCES.md          Readable provenance and rights notes
probes.csv          Explicit comparison pairs and interpretation limits
selections.json     Focused pairs and optional controlled-shift source families
SHA256SUMS.txt      SHA-256 for every file in images/ and sources/
README.md           Contents, selection policy and limitations
```

Construction-only manifests, instructions and supplemental checksums live in
`provenance/construction/`; preserved original packages use `provenance/supplied/`.
Only applicable evidence sections are required. `provenance/import-map.json`
and other hash-bound historical records retain their original paths and bytes.
`selections.json` at the leaf root describes relationship probes; the singular
`provenance/intake/selection.json` records a Curatorial selection. Their meanings
remain distinct. Live code belongs in `tools/`, including generators.

Run `Fixtures/.venv/bin/python <leaf>/tools/check.py` for common and specialized offline
validation, or `Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full` for all
leaves. `--metadata-only` checks structure/catalogs without local media; it is
not full provenance validation. Empty ignored media directories may be absent in
a fresh checkout; restore them and the recorded assets before full checks.

The original image bytes were not re-encoded during normalization. The derivative
set retains its filenames, probes and batch lists. Original manifests and README
files are retained in `provenance/`; the multiview import mapping also records
where each of the 20 captures came from. Supplied multiview files were moved into
the combined set's `sources/`, with byte-identical copies in `images/`. The Commons
files are reduced-resolution downloads, not full-resolution originals. Their
manual download names are mapped to Commons titles by exact thumbnail byte hashes
in `Relationships/Multiviews/provenance/commons/`. There are four numbered derivative
batches and eight multiview batches.

## Local assets and Git

A published leaf changes in two recorded ways. `Fixtures/collection remove
INPUT --reason "Reason"` removes active membership, preserving the prior
catalogs in `provenance/removals/NNNN/` and the image under `previews/removed/`.
`Fixtures/collection repin INPUT --from FILE --reason "Reason"` replaces an
input's bytes with a file that decodes to the recorded size, orientation and
format, preserving the prior catalogs in `provenance/repins/NNNN/` and any bytes
that were there under `previews/repinned/`; when the input is a byte copy of
its source file, the source bytes and catalog hash follow. Each receipt holds
the exact row, the reason and before/after hashes, and the receipts form one
chain that must end at the live catalogs. Source and acquisition records stay
as published. A leaf's specialized validator describes that publication and is
not re-run after a recorded change; the shared layout check describes the live
leaf. See the [tools guide](tools/README.md) and [RECOVERY.md](RECOVERY.md).

Current counts come from [generated collection totals](COLLECTIONS.md) and the
marked blocks in leaf READMEs. Regenerate with `Fixtures/collection totals`;
do not hand-edit those blocks. Acquisition counts and supplied targets retain
their historical meaning.

The [source index](INDEX.csv) is generated with the totals: one row per active
input across every leaf, with its leaf path, byte hash, decoded size, family and
source file, upstream origin, page ID, upstream SHA-1, the URL fetched, requested
edge, rendition kind, license, a `recovery` class (`commons-api`, `source-url`,
`regenerate` or `none`) with a note, and `shared_with` naming other leaves that
hold the same bytes or upstream file. It reads the existing import maps through
one adapter and rewrites none of them. It is a flat membership table and the
recovery contract in [RECOVERY.md](RECOVERY.md); a sub-heap is only a longer
leaf path, and sharing is information, not a failure.

All files under any set's `images/`, `sources/`, and optional `previews/` directories
are Git-ignored, including nested paths, new formats, and files with no extension.
Keep all future image assets in these locations. Metadata, checksums, textual
provenance, and tools remain versionable; a checkout alone does not contain the
images. Restore local assets at their manifest paths before running fixture checks.
Missing or changed files are reported by the validator, not downloaded or recreated.

The supplied derivative contact sheet was moved unchanged from
`provenance/preview.jpg` to `previews/preview.jpg`. It is not a comparison input;
the generator writes it into that same ignored directory. Archived supplied
metadata retains the original path description as provenance.

## Shared schema, version 1

`manifest.json` has `schema_version`, `fixture_id`, `kind`, `description`, and
`images`. The provenance-led sets use `kind=derivatives` or `kind=multiview`;
visual-prompt heap additions use `kind=prompt_heap` with empty pair expectations.
Published-source curatorial contributions use `kind=curatorial_heap`, also with
empty pair expectations. Image records use these columns:

```text
file, batch, family_id, scene_id, parents, transformation, relation_kind,
origin_count, width, height, exif_orientation, format, byte_sha256,
pixels_rgb_sha256
```

- Paths are relative to the fixture-set root. Width and height are stored-file
  dimensions, before EXIF orientation; orientation is recorded explicitly.
- `family_id` identifies one source asset and its derivatives. Separate captures
  have separate family IDs even when they show the same scene. For the variants
  set's supplied generations, a family instead records derivation through a
  description prompt, with no asserted pixel correspondence. Composites have an
  empty family ID and pipe-separated `parents` identifying their source families.
- `scene_id` groups independent captures of a scene or short sequence. It is empty for the
  derivative corpus, whose supplied labels establish source derivation. Neither
  family nor scene membership is a matching score or a guaranteed alignment.
- `transformation=source` means the bytes match the bundled source asset, not
  that the camera file was raw or never processed upstream. See `sources.csv`.
- `pixels_rgb_sha256` is the supplied Pillow RGB hash in the derivative set.
  Empty means no such hash was supplied or computed, as in the multiview set.
  It is not a hash of hazy's Apple-prepared pixels.

`sources.csv` uses identical columns across the integrated sets. `family_id` connects an image's
parent to its source; `source_filename` names its `sources/` file. The remaining
fields record scene, subject, credit, byte hash, stored dimensions, orientation,
source URL, preprocessing, physical view/exposure when supplied, and original
import path. Empty provenance fields mean unknown or not supplied. Exact locations
and capture timestamps are not extracted into these catalogs; embedded source
metadata remains intact with the source bytes.

`probes.csv` columns are `file_a`, `file_b`, `relation`, `interpretation`. The first
file is the fixed reference. Identity/derivation labels describe source provenance;
`same_scene` describes independent captures with a shared scene label;
`distinct_scene` describes different scene labels. A cross-group pair can still
share people or objects. The three comparisons between nearby Budapest sequences
use `diagnostic` because a physical-scene distinction is ambiguous. None prescribes
a Vision similarity score or transform.

`selections.json` contains a description, explicit `pairs` using the probe columns,
and `known_shift_families`. The latter is used only by tests that create temporary
controlled shifts; it is empty for the multiview and variants sets.

The variants set retains the shared `kind=derivatives` convention. Richer recipes,
operation lineage, masks, per-piece transforms, source/prompt/generation imports,
and build verification are in its `provenance/`. Two-parent replacements and
description-mediated generations must not be interpreted as ordinary single-source
pixel edits. Legacy smoke/medium lists select only its six originals.

## Curatorial source heaps

Heap contributions may be nested below a source collection, for example
`Heaps/Curatorial/POTY/Arthropods/`. A manifest identifies a leaf fixture set;
its paths remain relative to that leaf, irrespective of directory depth. Existing
Similarity tools are contribution-specific, and the shared relationship
checker deliberately does not validate either heap kind. There is no shared
fixed-depth heap traversal to change. The fixture indexes identify contributions
and their check commands.

`kind=curatorial_heap` records membership in an already published source
population, followed by documented mechanical selection and provenance exclusions.
It does not require `prompt.json` or visual acceptance judgments. A contribution
may add documented thumbnail scope checks to reject obvious category outliers;
those fallible decisions do not assert visual similarity or category ground truth.
POTY leaves use `inventory.json`, `ordering.json` and `selection.json` inside
`provenance/intake/` for the full eligible
population, seeded ordering and per-candidate decisions. File-specific evidence,
original-creator identity decisions, explicit exceptions, acquisition receipts,
and POTY year/category mappings are in `provenance/`. Each leaf has its own
source catalog, manifests, batches, checksums and independent offline check.
US-Army-SSI uses the same kind in one leaf directly under Curatorial. Its source
population is Commons category membership, not an award/editorial selection;
its full PetScan export, stable file ordering and distinct-design decisions are
retained locally. Design keys support duplicate exclusions only. Creator/renderer
and uploader roles remain separate, with no creator cap or visual-prompt size floor.
Explicit pending cases can remain unresolved while later candidates are selected
provisionally in the same fixed order. Reaching the acquisition target does not
resolve those cases; the selection ledger retains them and marks affected later
selections for reconciliation. Botanical-Illustrations uses this same single-leaf
format for direct category membership, with distinct plate/artwork keys and
separate artist, engraver/lithographer, publisher, digitizer and uploader roles.
Different plates from one publication are permitted; work keys record duplicate
exclusions, not source families or expected relationships.

Evan-Amos-Uploads uses this same kind for an exhaustive direct-category import,
minus three exact user exclusions. It enumerates every File identity without
sampling, creator limits or deduplication. Related files and prior-fixture overlaps
remain included; technical or rights problems are independent pending/blocked
acquisition states, not selection exclusions. Completion requires every included
File identity to have a validated acquired input.

Rocks-in-Thin-Section, Stone-Hand-Axes and Ex-Libris each freeze the union of
three direct File category lists. They record separate visual-scope, work/specimen
provenance and rights decisions bound to actual inspected preview bytes. Clear
rejection on any axis excludes; otherwise an explicit defer allows provisional
later selection, while an unreviewed gap blocks it. Metadata-bound unsupported
media exclusions do not fabricate visual reviews. Known repeated objects or
printed works are excluded, unknown identities remain null, and neither artist
caps nor category quotas apply. Acquisition failures never replace selections.

Cross-fixture identity audits are written once, at publication, and read as
frozen evidence afterward; no validator recomputes them or re-resolves the
leaves they named. A new publication audits every current leaf through the
[source index](INDEX.csv), whose `shared_with` column lists exact byte or
upstream-file sharing between leaves as information, not failure.

The common image/source columns are retained. `relation_kind=curatorial_selected`
records selection basis only. A unique `family_id` and its single `parents`
value connect one unchanged input copy to its downloaded source; they do not
connect different selected images. `scene_id` and optional decoded-pixel hashes are
empty, `probes.csv` is header-only, and `selections.json` contains no pairs or
known-shift families. No curator category is a router cluster or matching label.

The target count, selected count, acquired count, exclusions, unused reserve,
pending review/acquisition, and any exhausted-population shortfall are distinct.
An incomplete acquisition can have a valid partial manifest; its status and
missing selections must remain explicit. A validation pass means the recorded
state is consistent, not that the target count was achieved. API-reported display
dimensions may differ from decoded rendition dimensions; preserve both without
locally changing the downloaded image.

