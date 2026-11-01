# hazy derivatives fixture v1

## Purpose and basis

Synthetic derivatives with source provenance; family_id is not an asserted matching cluster.
Fixture ID: `hazy-derivatives-v1`; kind: `derivatives`.

## Completeness

The published manifest contains **183 inputs**. The detailed record below
retains the original selection counts, pending cases and acquisition limitations.
The layout migration changes no membership or completion status.

## Contents

This leaf follows the [shared fixture format](../../FORMAT.md).
`images/`, `sources/`, `previews/` and `batches/` retain their roles. Live commands
and dependencies are in `tools/`; the [evidence index](provenance/README.md)
locates intake/construction records, receipts and preserved packages.

## Validation

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Relationships/Derivatives/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Relationships/Derivatives/tools/check.py
```

The check is offline and includes the shared layout check and the existing
specialized validators. `--metadata-only` omits media and specialized checks.

## Limitations

Selection and source relationships retain their recorded scope; they are not
similarity scores or additional matching assertions. Technical/provenance
uncertainties and partial acquisitions remain documented below.

## Detailed record

A fixed batch of **183 images** intended to exercise coarse image-similarity grouping without using anyone's personal photo library.

This is the originally supplied `hazy-fixtures-v1`, renamed to distinguish it
from the multiview set. It follows the [shared fixture schema](../../FORMAT.md).
Image and source bytes, opaque filenames, probes, and batch lists are unchanged.
The manifests now add schema identity, stored EXIF orientation, and an empty
`scene_id` column; the original manifests are retained under `provenance/`.

**Use `images/` as the input set.** It is a single flat directory with opaque filenames so the expected group membership is not conveyed by names or directories. The answer key and provenance are separate.

### What's in the corpus

- **12 source families**, with **14 images each**: an untouched source, byte-for-byte copy, pixel-preserving PNG re-encode, two JPEG compressions, half-scale image, two crops, a 90° rotation, mirror, color shift, letterbox, mock interface overlay, and blur.
- **3 singleton photographs**, with no deliberate variants in `images/`.
- **12 composite images**, pairing pieces from two unrelated sources. These are deliberately ambiguous and do not belong to one asserted ground-truth family.
- **4 overlapping-in-content batches**, with 45–46 images apiece, containing variants of the same sources across different batches.

No source is one of your own images. These originals come from the public-domain and CC0 sample data distributed with scikit-image. See `SOURCES.md` and `sources.csv` for provenance.

### Contents

| File/folder | Purpose |
|---|---|
| `images/` | **Only folder to give hazy** (183 files) |
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

`family_id` means **derived from the same original bytes**, not "the correct Apple Vision cluster." Deliberate crops, rotation, and composites are useful precisely because visual similarity under these operations may vary considerably. The ground-truth assertions here are limited to provenance, byte identity, and pixel identity; no image similarity scores were computed and no threshold has been prescribed.

- `byte_copy` is a raw duplicate, with identical file bytes to `source`.
- `reencode_png` has identical decoded RGB pixels to `source`, but can have a different encoding and byte representation.
- Other single-parent variants share an original, but aren't automatically asserted to be visually equivalent at a particular threshold.
- A `family_id` of empty string and `parents` containing two names denotes a composite with multiple origins.
- Different family IDs denote different original source images. They may nevertheless be semantically similar.

`probes.csv` lists explicit comparison pairs, including different-origin images that might resemble one another in feature space. The `interpretation` field avoids pretending the supplied labels are Vision's answers.

### Batches

`batch-1.txt` to `batch-4.txt` together partition all 183 `images/` files. They do not partition by source family: copies of one image are spread across batches. Lists are stable and relative to the corpus root.

For a short trial, use the 24 files in `batches/smoke.txt`. For the full trial, import the four lists independently, or import `images/` in one pass. The same files and manifest can be used for every subsequent revision.

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

From the repository root, `Fixtures/.venv/bin/python Experiments/AppleVisionTranslation/Tools/fixtures.py check` validates this
package without Pillow. See the [experiment README](../../../Experiments/AppleVisionTranslation/README.md#fixture-checks-and-exploration)
for the focused comparison runner and tests. The manifest's pixel hashes describe
Pillow's decoded RGB representation, not hazy's Apple-prepared working pixels.

### Scope limitation

Almost all related images here are **synthetic transformations of a single exposure**. This is suitable for duplicate families and repeatable import behavior but not sufficient for real multi-view retrieval. The external **INRIA Holidays** corpus (1,491 images in 500 scene groups) complements it with genuine photographs of the same scenes; **INRIA Copydays** offers a larger collection of established copy-detection transformations. The external datasets are not included in this zip. Their rights and redistribution terms are theirs, not this corpus's.

### Redistribution

The bundled upstream samples are identified in `SOURCES.md`, and are documented by scikit-image as public-domain or CC0, except for one museum image described as having *no known copyright restrictions*. The source/credit claims are taken from scikit-image's image documentation, rather than a separate legal assessment. The generated variants and manifest can be reproduced and revised freely subject to any rights in the originals.
