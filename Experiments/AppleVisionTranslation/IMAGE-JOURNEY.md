# Apple Vision translation experiment image journey

The path is:

**two files → prepared images → translation request → result → overlay and report**

[ComparePair.swift](Sources/AppleVisionTranslationExperiment/ComparePair.swift) connects the stages.
[main.swift](Sources/VisionTranslationCLI/main.swift) handles command-line arguments and exit codes.

This is a useful channel example, not the router architecture. The router's
[MVP requirements](../../Research/Router/HORIZONTAL-GENE-TRANSFER.md) and
[design intent](../../Research/Router/BACKWARDS-INDUCTION.md) leave its structure open. The preparation
and result conventions below describe the current implementation only.

## 1. Prepare the images

[ImagePreparation.swift](Sources/AppleVisionTranslationExperiment/Apple/ImagePreparation.swift) asks ImageIO
for the file's image count, stored dimensions, and EXIF orientation. This first
slice accepts single-image files that ImageIO can decode. Missing orientation
means upright. Multi-image files and undecodable inputs produce an error.

hazy requests a thumbnail made from the full image, with orientation applied and
the longest side limited to 1,024 pixels. ImageIO handles decoding and resampling.
Core Graphics draws the result into an 8-bit sRGB RGBA bitmap over white, making
it opaque. Color conversion, reduced bit depth, and alpha flattening are part of
this working representation; it is not intended for exact source-pixel equality
or HDR preservation.

The report records stored dimensions, EXIF orientation, oriented dimensions,
prepared dimensions, and row stride. Orientation values 5–8 swap the width and
height. From an upright source image to the prepared image, x and y scale by
`prepared width / oriented width` and `prepared height / oriented height`.
Actual integer dimensions matter because resizing can round.

The in-memory carrier is currently an owned `CGImage`, backed by RGBA bytes with
8 bits per channel and `width × 4` bytes per row. All prepared alpha values are
255. Apple image types stay in the Apple implementation; this carrier is a place
to change when another implementation needs a different buffer representation.

## 2. Ask Vision for a translation

[Registration.swift](Sources/AppleVisionTranslationExperiment/Apple/Registration.swift) gives the floating
image to `VNTranslationalImageRegistrationRequest`, revision 1, and performs that
request with a handler containing the reference image. Both are declared `.up`
because preparation has already applied orientation. The request uses the full
image region and leaves compute-device selection to Vision.

hazy currently requires equal prepared dimensions. This is our initial scope,
not a statement that all Vision registration requests require it. Each image is
resized independently; hazy does not stretch one to match the other.

Apple owns the alignment algorithm. hazy owns the inputs, request setup, and
interpretation of the returned transform. The adapter checks that the returned
values are finite and describe a translation, then converts them into plain x/y
offsets. No Vision observation escapes this stage.

The result contract uses prepared-image pixels, a lower-left origin, positive x
to the right, and positive y upward. To map a floating point into the reference:

```text
referenceX = floatingX + translation.x
referenceY = floatingY + translation.y
```

For example, moving image content 17 pixels right and 9 pixels down should yield
an alignment of about x = -17 and y = +9. These are working-image offsets, not
necessarily original-file pixel offsets.

The outcome is `estimated`, `noObservation`, `failed`, or `notRun`, with a plain
explanation. An API error or absent observation never becomes a zero shift. An
estimated shift does not establish that two images depict the same content.

## 3. Render and explain

[Rendering.swift](Sources/AppleVisionTranslationExperiment/Apple/Rendering.swift) uses Core Image to move the
floating image by the returned translation. It composites that image at 50%
opacity over the reference and crops to the reference bounds. Where the moved
image is absent, only the reference remains. Doubled edges can reveal poor
alignment. The overlay is a viewing aid, not a quantitative difference measure.

ImageIO encodes the prepared inputs and overlay as PNGs.
[ComparisonReport.swift](Sources/AppleVisionTranslationExperiment/ComparisonReport.swift) holds the plain
report types and readable summary. The orchestrator writes these images and JSON
to a new directory. Input/preparation errors stop the comparison before writing;
an unavailable alignment still produces the prepared images and report, without
an overlay. An output-writing error is reported and can leave partial output.

## Evidence for the portability track

This implementation supplies observations to the parallel
[portability research track](../../Research/Portability/README.md) and its
[capability ledger](../../Research/Portability/CAPABILITY-LEDGER.md). The experiment
makes preparation, request ownership, coordinates, and failures inspectable so we
can decide what an eventual shared macOS/Linux API should promise. It has no Linux
implementation or backend registry. Its current types and policies are not that
future API.

## Checks and fixture evidence

`swift test --package-path Experiments/AppleVisionTranslation` generates patterns to check identity, a known translation and its
rendered overlay, EXIF orientation, resizing and alpha treatment, unequal sizes,
and input/output failures. It also checks that sources remain unchanged.
These cases establish mechanics only.

[FixtureTests.swift](Tests/AppleVisionTranslationExperimentTests/FixtureTests.swift) additionally prepares
all 183 derivative-set inputs, checks their stored dimensions against the manifest,
checks all 12 byte-copy pairs for near-zero translation, and checks the nine
PNG-source re-encodes for identical prepared pixels. It exercises a real crop
that must remain `notRun` because of unequal prepared dimensions.

It also prepares the 20 multiview captures and checks their eight scene/sequence
groups and orientation. The three playground JPEGs store 4032×3024 with EXIF orientation 6:
ImageIO applies that orientation once, giving hazy 768×1024 working images. The
other personal groups prepare to 1024×768; the motorcycle views remain 741×500.
The nine Commons inputs were downloaded as thumbnails: the Kumbh pair stores
1280×851 and prepares to 1024×681; four landscape Budapest images store 1280×720
and prepare to 1024×576; three portrait images store 960×1706 and prepare to
576×1024. Their identity was verified by exact SHA-256 matches to the named Commons
thumbnails. This upstream resizing precedes hazy's own decoding and preparation.
No expected Vision translation or matching judgment is attached to a scene label.

The [derivative focused selection](../../Fixtures/hazy-derivatives-v1/selections.json) uses astronaut,
grass, and retina for distinctive structure, repetitive texture, and downsampling.
The tests prepare each original, write temporary working PNGs, and move content
17 pixels right and 9 down on a same-size white canvas. Expected alignment is
x = -17, y = +9, within 0.5 working pixels. The shift happens after preparation:
retina's original 1411×1411 image becomes 1024×1024 before we move it. These are
controlled transformations, not independent photographs of the same scene.

[Tools/fixtures.py](Tools/fixtures.py) validates asset hashes, agreement of
CSV/JSON manifests, source copies, probe references and identity labels, and batch
membership for either [fixture set](../../Fixtures/README.md), using one shared schema.
It does not recompute the supplied Pillow pixel hashes; multiview pixel-hash fields
are empty because none were computed under that convention. Its optional runner
passes only file paths to the existing CLI; family and scene labels are joined
to the returned report outside the Apple implementation. The default derivative
selection runs 14 comparisons; `probes` runs 115; `full` runs 190 and covers all
derivative inputs, including each composite against both parents. The multiview
selection runs 16 within-group pairs; probes/full add 28 comparisons between group
representatives, for 44 total. Three of those compare Budapest sequences from the
same event and nearby surroundings; they carry the neutral `diagnostic` relation.
The other 25 carry `distinct_scene`, which describes labels, not proven non-matches.
Each capture has a different `family_id`, even when `scene_id` is shared. The
motorcycle pair's supplied rectification/downsampling, the Commons thumbnails,
and the personal photos' unknown prior processing history are recorded in the
source catalog. These are
properties of the inputs, before hazy's preparation and Apple's requests.
The runner writes an incremental
`run.json`, per-pair output, diagnostics, and environment/fixture identities to a
new output directory. Request failures cause a nonzero exit but do not hide other
pairs. An interrupted run retains completed results with `complete: false`.

The complete multiview run on 2026-10-29 returned 18 estimates: all 16 within-group
pairs and two comparisons between group representatives. The other 26 comparisons
stopped at hazy's unequal-dimensions guard; no requests failed. All 44 produced
reports, with overlays only for estimates. This checks the input-to-report path,
not the quality of those estimated alignments.

The initial review on Swift 6.4 / macOS 26.7.1 illustrates three boundaries:

- The corpus's `pixels_rgb_sha256` hashes describe Pillow's orientation-adjusted
  RGB decoding, including width and height. They do not describe hazy's sRGB RGBA
  preparation, white alpha treatment, or resizing. The galaxies, retina, and rocket
  JPEG-to-PNG pairs differ slightly in Apple's prepared pixels despite identical
  supplied RGB hashes. Byte identity, decoder-specific pixel identity, and visual
  relationship are separate properties.
- Equal prepared dimensions do not guarantee equal content scale. Retina and
  its center crop both become 1024×1024; the request runs, but translation cannot
  undo the scale difference. Conversely, most other crops stop at hazy's dimension
  guard before any Vision request is performed.
- All three dimension-compatible different-origin probes returned estimates.
  For grass versus gravel, the returned shift was x = 194, y = 382. This is evidence
  that the API returned an alignment, not that the images match. These diagnostic
  transforms are exploratory results, not numerical snapshots asserted by tests.

Keep v1's image bytes and provenance meanings fixed. The derivative set was renamed
from `hazy-fixtures-v1` to `hazy-derivatives-v1`; both sets now use the documented
schema. Original metadata is retained in each set's `provenance/` directory.
`provenance/generate.py` in the derivative set is an optional Pillow tool, not a
build/test dependency; its small-batch writer was corrected to recreate
`smoke.txt` and `medium.txt`, without regenerating this corpus. Most related inputs
remain synthetic edits of one exposure, and the four batches share source families.
They support repeatable import experiments, not independent evaluation sets.
The multiview set adds real scene motion, crowd repetition, occlusion, and framing
changes. Its personal groups were identified by visual inspection and the user's
grouping description; its Commons sequence labels retain the supplied grouping.
These are not calibrated camera views. Fixture collection is complete for the
current preparation and translation scope; a concrete failure or new capability
can motivate a focused addition later. The usefulness of overlays when people and
objects move within the scene remains a matter for inspection. No similarity
threshold or grouping policy follows from these small sets.

Apple references: [ImageIO](https://developer.apple.com/documentation/imageio)
and [Aligning Similar Images](https://developer.apple.com/documentation/vision/aligning-similar-images).
