# Apple Vision translation experiment

This is the implemented macOS channel experiment. Its Swift library is
`AppleVisionTranslationExperiment`; its CLI is `hazy-vision-translation`.
The router has no executable or package yet. This experiment supplies evidence to
both [router research](../../Research/Router/README.md) and
[portability research](../../Research/Portability/README.md).

Run the commands below from the repository root. [IMAGE-JOURNEY.md](IMAGE-JOURNEY.md)
describes the actual preparation, framework handoffs, and result conventions.
This package's structure and public function are experimental, not the future
router API contract.

## Build and run

Requires macOS and a Swift 6 toolchain with the macOS SDK. The package declares
macOS 14 as its minimum; older supported systems have not been tested.
There are no third-party package dependencies.

```sh
swift build --package-path Experiments/AppleVisionTranslation
mkdir -p output
swift run --package-path Experiments/AppleVisionTranslation hazy-vision-translation compare /path/to/reference.png /path/to/floating.png --output output/example
swift test --package-path Experiments/AppleVisionTranslation
```

The first image is the **reference**, which stays fixed. The second is the
**floating** image, which Vision attempts to move into alignment.
The output directory must be new, with an existing parent.

A run prints a readable account and writes:

- `reference.png` and `floating.png`: the prepared images passed to Vision.
- `comparison.json`: source and prepared dimensions, orientation, preparation
  settings, request revision, outcome, and translation when available.
- `overlay.png`: the aligned floating image at 50% opacity over the reference,
  clipped to the reference bounds. Written only when an alignment is estimated.

Exit codes are `0` for an estimated alignment, `1` for a usage/input/output error,
and `2` when no alignment is available. A reported request failure still saves
prepared images and its explanation. An output-writing failure may leave a
partial directory; choose a new directory after correcting the problem.

## Current scope

Preparation uses ImageIO to decode one image, apply EXIF orientation, and reduce
its longest side to at most 1,024 pixels while preserving aspect ratio. It then
renders 8-bit sRGB pixels with transparency flattened onto white. These are
working images, not lossless representations of every source format.

This slice requires equal prepared dimensions and uses Vision's translational
registration request. It does not estimate rotation, scale, or perspective, or
provide a similarity score. A transform can be unhelpful even when the API returns
one; inspect the images and overlay.

The three provenance-led [fixture sets](../../Fixtures/README.md) share one structure and manifest schema:
`hazy-derivatives-v1` contains the original 183-image derivative corpus;
`hazy-multiview-v1` contains the motorcycle pair, nine personal photographs, and
nine Commons crowd photographs: 20 images in eight scene or sequence groups;
`hazy-meme-fixtures-v0` adds 42 variant inputs with staged construction provenance,
two-parent replacements, and unchanged supplied description-mediated generations.
They check repeatable behavior and illustrate limitations; they do not establish
general matching quality.

## Fixture checks and exploration

The experiment's Swift tests include all 12 byte-copy pairs, lossless PNG preparation checks,
preparation of the 203 derivative/multiview inputs, and known shifts derived temporarily from three
derivative fixtures. It checks the multiview scene groups and the three personal
photos with EXIF orientation 6. Existing generated cases still cover transparency,
overlay mechanics, and errors. Test outputs are temporary; source images stay intact.
The variants set has its own build/validation command and passes the shared Python
fixture checker; it is not part of the fixed Swift test inventory. Its varied
compositions do not imply that translation registration is applicable.

The developer tools target Python 3.14.x with no third-party packages. Use the
repository's `.venv` (`make -C Fixtures setup-python`, then `source Fixtures/.venv/bin/activate`
from the repository root) for Python commands and tests below. Build the
experiment before running comparisons. The default binary is
`Experiments/AppleVisionTranslation/.build/debug/hazy-vision-translation`;
`--binary` can select another build. Each run needs a new output directory with
an existing parent.

```sh
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py check
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py check --fixtures Fixtures/Relationships/Multiviews
swift build --package-path Experiments/AppleVisionTranslation
mkdir -p output
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py run --output output/fixture-focus
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py run --selection full --output output/fixture-full
python3 Experiments/AppleVisionTranslation/Tools/fixtures.py run --fixtures Fixtures/Relationships/Multiviews --output output/multiview-focus
python3 -m unittest discover -s Experiments/AppleVisionTranslation/Tools
```

The default [focused selection](../../Fixtures/Relationships/Derivatives/selections.json) uses astronaut,
grass, and retina originals with byte copies, PNG re-encodes, strong JPEG
compression, and blur. Two diagnostic pairs add grass versus gravel and retina
versus its center crop: 14 comparisons across 17 existing files. These cover
distinctive content, repetitive texture, and reduction to the working resolution.
Known-shift derivatives are made after preparation by the tests, not stored in v1.
The multiview focused selection instead runs all 16 within-group pairs, with no
expected numerical transforms. Original filenames and supplied provenance are
retained separately from its flat, opaque-named inputs. The Commons inputs are
verified thumbnails, preserved as downloaded; their upstream resizing is recorded
separately from hazy's preparation.

For the default derivative set, `--selection probes` runs the 115 supplied pairs.
`--selection full` runs 190 pairs:
those probes, the remaining single-source variants, each composite against both
parents, and singleton self-comparisons. All 183 inputs are covered without an
all-pairs search. Batch lists are checked for consistency; hazy has no batch-import
or grouping feature yet. With `--fixtures Fixtures/Relationships/Multiviews`, probes/full
run 44 pairs: 16 within groups and 28 between group representatives. Three pairs
between Budapest sequences are labeled ambiguous diagnostics because they share
an event and nearby surroundings. `family_id` means one source and its derivatives;
`scene_id` separately groups independent captures, without asserting a non-match
between different labels.

Each run saves `run.json` plus the normal per-pair reports and overlays. It records
fixture hashes, binary identity, OS and Swift versions, preparation settings and
request revision. Estimated, unavailable, skipped, and failed alignments remain
separate. Exit 1 indicates a fixture/tool error or failed request; `notRun` and
`noObservation` remain recorded outcomes. An estimated alignment is never counted
as a correct match. Outputs live under the ignored `output/` directory in these examples.

The initial fixture review on 2026-10-28 used Swift 6.4 and macOS 26.7.1 (arm64).
All 12 byte-copy pairs returned zero shift. Of the 115 supplied probes, 58 returned
estimates and 57 stopped at the dimension check. Three different-origin pairs also
returned estimates. These are observations on that environment, not expected
matching scores. See [the image journey](IMAGE-JOURNEY.md#checks-and-fixture-evidence)
for the preparation and interpretation details.

Fixture collection is complete for the current preparation and translation scope.
Add a focused regression fixture when a concrete failure or new behavior requires
one; these sets do not justify a general matching threshold.

Read [the image journey](IMAGE-JOURNEY.md) to follow the implementation.
[AGENTS.md](../../AGENTS.md) contains the short working guidance.
