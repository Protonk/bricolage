# Derivatives

Crops, re-encodings, edits and composites made from known source images.

Fixture ID: `hazy-derivatives-v1`; kind: `derivatives`.
<!-- collection-totals:start -->
The manifest lists **183 active inputs**. [All collection totals](../../COLLECTIONS.md).
<!-- collection-totals:end -->

Use the [shared fixture format](../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Relationships/Derivatives/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Relationships/Derivatives/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Original publication and acquisition records

A fixed batch of **183 images** intended to exercise coarse image-similarity grouping without using anyone's personal photo library.

This is the originally supplied `hazy-fixtures-v1`, renamed to distinguish it
from the multiview set. It follows the [shared fixture schema](../../FORMAT.md).
Image and source bytes, opaque filenames, probes, and batch lists are unchanged.
The manifests now add schema identity, stored EXIF orientation, and an empty
`scene_id` column; the original manifests are retained under `provenance/`.

The sampler uses `images/` as the input set. Filenames carry no source-family
labels; the manifests record the source and transformations separately.

### What's in the corpus

- **12 source families**, with **14 images each**: an untouched source, byte-for-byte copy, pixel-preserving PNG re-encode, two JPEG compressions, half-scale image, two crops, a 90° rotation, mirror, color shift, letterbox, mock interface overlay, and blur.
- **3 singleton photographs**, with no deliberate variants in `images/`.
- **12 composite images**, pairing pieces from two unrelated sources. These are deliberately ambiguous and do not belong to one asserted ground-truth family.
- **4 overlapping-in-content batches**, with 45–46 images apiece, containing variants of the same sources across different batches.

No source is one of your own images. These originals come from the public-domain and CC0 sample data distributed with scikit-image. See `SOURCES.md` and `sources.csv` for provenance.

### Contents

| File/folder | Purpose |
|---|---|
| `images/` | Fixture inputs (183 files); consumers receive them only through a published world |
| `manifest.csv` / `manifest.json` | Image filename, provenance family, transformation, dimensions, hash, and assigned batch |
| `probes.csv` | Selected pairs: byte identity, equal decoded pixels, derivation, and potential false friends |
| `batches/batch-1.txt` through `batch-4.txt` | Four ordered lists of *relative paths* for repeatable separate imports |
| `batches/smoke.txt` | Short list: 12 originals and their byte-for-byte copies |
| `batches/medium.txt` | Medium list: originals plus copy, lossless conversion, and two alterations per family |
| `sources/`, `sources.csv`, `SOURCES.md` | Unaltered source assets with credits and source hashes (not part of input set) |
| `SHA256SUMS.txt` | Expected raw hashes for all `images/` and `sources/` assets |
| `selections.json` | Focused comparison pairs and sources for controlled-shift tests |
| `tools/generate.py` | Rebuilds variants from bundled originals; Pillow 12.3.0 was used for this release |
| `previews/preview.jpg` | Original source contact sheet; *not* part of input set |
| `provenance/supplied-*` | Original metadata before schema normalization |

### What the labels mean

`family_id` records derivation from the same source image. Cropping, rotation and
compositing change how much of that source remains visible. The records describe
those operations, byte identity and decoded pixel identity; comparison scores
and thresholds are left to the test using the images.

- `byte_copy` is a raw duplicate, with identical file bytes to `source`.
- `reencode_png` has identical decoded RGB pixels to `source`, but can have a different encoding and byte representation.
- Other single-parent variants share an original, but aren't automatically asserted to be visually equivalent at a particular threshold.
- A `family_id` of empty string and `parents` containing two names denotes a composite with multiple origins.
- Different family IDs denote different original source images. They may nevertheless be semantically similar.

`probes.csv` lists comparison pairs, including images from different sources that
may resemble one another. Its `interpretation` field explains each pair's source
relationship and why the pair was chosen.

### Batches

`batch-1.txt` to `batch-4.txt` together partition all 183 `images/` files. They do not partition by source family: copies of one image are spread across batches. Lists are stable and relative to the corpus root.

`batches/smoke.txt` lists 24 originals and byte copies; the four numbered lists
cover the whole set. These lists describe fixture subsets. Consumers receive
worlds published through `Fixtures/sample`.

### Reproduction and checks

To confirm unchanged input bytes on a Mac, run from the corpus root:

```sh
shasum -a 256 -c SHA256SUMS.txt
```

To regenerate derivatives (changes the current `images/` directory), install Pillow and run:

```sh
Fixtures/.venv/bin/python -m pip install 'Pillow==12.3.0'
Fixtures/.venv/bin/python Fixtures/Relationships/Derivatives/tools/generate.py
```

The supplied image bytes are canonical fixture v1; do not silently regenerate
them when comparing across revisions. JPEG encoder output can change between
image-library versions. The generator writes the shared manifest/source schema;
the explicit `selections.json` is maintained separately.

hazy's integration keeps the supplied assets and batch lists unchanged, and
preserves the supplied manifests in `provenance/` alongside the normalized versions.
The generator's small-batch writer has been corrected to recreate `smoke.txt` and
`medium.txt`; those lists previously disappeared on regeneration. The correction
was checked against the supplied lists without rerunning the image encoders.

From the repository root, `Fixtures/.venv/bin/python Fixtures/tools/relationship_fixtures.py check` validates this
package without Pillow. See the [shared tools guide](../../tools/README.md)
for tests and the optional comparison runner, which requires an explicit world
and experiment binary. The manifest's pixel hashes describe
Pillow's decoded RGB representation, not hazy's Apple-prepared working pixels.

### Scope limitation

Almost all related images here are transformations of a single exposure. They
allow repeated tests of crops, edits and encodings. For separate captures of a
scene, see the local [Multiviews collection](../Multiviews/README.md).

### Redistribution

The bundled upstream samples are identified in `SOURCES.md`, and are documented by scikit-image as public-domain or CC0, except for one museum image described as having *no known copyright restrictions*. The source/credit claims are taken from scikit-image's image documentation, rather than a separate legal assessment. The generated variants and manifest can be reproduced and revised freely subject to any rights in the originals.
