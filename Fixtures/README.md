# hazy fixture sets

There are two sets, using the same schema and directory structure:

| Set | Inputs | Purpose | Focus / probes / full |
|---|---:|---|---:|
| [hazy-derivatives-v1](hazy-derivatives-v1/README.md) | 183 | Original synthetic-derivative corpus, renamed from `hazy-fixtures-v1` | 14 / 115 / 190 pairs |
| [hazy-multiview-v1](hazy-multiview-v1/README.md) | 20 | Motorcycle pair, nine personal photos, nine Commons crowd photos; eight scene/sequence groups | 16 / 44 / 44 pairs |

Only `images/` is comparison input. Both sets contain:

```text
images/             Flat input files with opaque names
sources/            Preserved source bytes, with filenames as supplied
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
in `hazy-multiview-v1/provenance/commons/`. There are four numbered derivative
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
`images`. `kind` is `derivatives` or `multiview`. Image records use these columns:

```text
file, batch, family_id, scene_id, parents, transformation, relation_kind,
origin_count, width, height, exif_orientation, format, byte_sha256,
pixels_rgb_sha256
```

- Paths are relative to the fixture-set root. Width and height are stored-file
  dimensions, before EXIF orientation; orientation is recorded explicitly.
- `family_id` identifies one source asset and its derivatives. Separate captures
  have separate family IDs even when they show the same scene. Composites have an
  empty family ID and pipe-separated `parents` identifying their source families.
- `scene_id` groups independent captures of a scene or short sequence. It is empty for the
  derivative corpus, whose supplied labels establish source derivation. Neither
  family nor scene membership is a matching score or a guaranteed alignment.
- `transformation=source` means the bytes match the bundled source asset, not
  that the camera file was raw or never processed upstream. See `sources.csv`.
- `pixels_rgb_sha256` is the supplied Pillow RGB hash in the derivative set.
  Empty means no such hash was supplied or computed, as in the multiview set.
  It is not a hash of hazy's Apple-prepared pixels.

`sources.csv` uses identical columns in both sets. `family_id` connects an image's
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
controlled shifts; it is empty for the independently captured multiview set.

## Use

From the repository root:

```sh
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py check
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py check --fixtures Fixtures/hazy-multiview-v1
swift build --package-path Experiments/AppleVisionTranslation
mkdir -p output
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py run --output output/derivatives-focus
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py run --fixtures Fixtures/hazy-multiview-v1 --output output/multiview-focus
```

Use `--selection probes` or `--selection full` to expand a run. Each output must
be new. The default set remains `hazy-derivatives-v1`. The same validator and runner
read either set; the Swift comparison API receives only the selected image files.
