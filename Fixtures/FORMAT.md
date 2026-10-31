# Fixture format and evidence

See the [fixture index](README.md) for roles and current locations. Directory
organization is separate from the existing manifest schema and fixture IDs.

Only each leaf set's `images/` directory is comparison input. Integrated sets use:

```text
images/             Flat input files with opaque names
sources/            Preserved supplied/acquired bytes; original names in sources.csv
batches/            batch-*.txt partition inputs; smoke.txt and medium.txt are subsets
previews/           Optional local contact sheets, outside the comparison inputs
provenance/         Supplied metadata and set-specific supporting material
manifest.json       Versioned description plus image records
manifest.csv        The same image records, in the same column order
sources.csv         Source identities, original names, credits and processing history
SOURCES.md          Readable provenance and rights notes
probes.csv          Explicit comparison pairs and interpretation limits
selections.json     Focused pairs and optional controlled-shift source families
SHA256SUMS.txt      SHA-256 for every file in images/ and sources/
README.md           Contents, selection policy and limitations
```

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
Similarity tools are contribution-specific, and the experiment's relationship
checker deliberately does not validate either heap kind. There is no shared
fixed-depth heap traversal to change. The fixture indexes identify contributions
and their check commands.

`kind=curatorial_heap` records membership in an already published source
population, followed by documented mechanical selection and provenance exclusions.
It does not require `prompt.json` or visual acceptance judgments. POTY leaves use
`inventory.json`, `ordering.json` and `selection.json` for the full eligible
population, seeded ordering and per-candidate decisions. File-specific evidence,
original-creator identity decisions, explicit exceptions, acquisition receipts,
and POTY year/category mappings are in `provenance/`. Each leaf has its own
source catalog, manifests, batches, checksums and independent offline check.
US-Army-SSI uses the same kind in one leaf directly under Curatorial. Its source
population is Commons category membership, not an award/editorial selection;
its full PetScan export, stable file ordering and distinct-design decisions are
retained locally. Design keys support duplicate exclusions only. Creator/renderer
and uploader roles remain separate, with no creator cap or visual-prompt size floor.

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

