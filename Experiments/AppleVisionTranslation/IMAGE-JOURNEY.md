# Apple Vision translation experiment image journey

The path is:

**world + two image IDs → validated bytes → prepared images → translation request → result → report**

[ComparePair.swift](Sources/AppleVisionTranslationExperiment/ComparePair.swift) connects the stages.
[main.swift](Sources/VisionTranslationCLI/main.swift) handles command-line arguments and exit codes.

This is a useful channel example, not the router architecture. The router's
[MVP requirements](../../Research/Router/HORIZONTAL-GENE-TRANSFER.md) and
[design intent](../../Research/Router/BACKWARDS-INDUCTION.md) leave its structure open. The preparation
and result conventions below describe the current implementation only.

## 1. Validate the world and prepare the images

[World.swift](Sources/AppleVisionTranslationExperiment/World.swift) reads the public
manifest, checks schema, unique identities, flat regular files, exact coverage and
SHA-256 hashes, then resolves two explicitly requested image IDs. CryptoKit hashes
bytes; Foundation reads the manifest and files. Unknown additive fields are ignored.
The world ID is opaque. No producer records or fixture metadata are read. Output
containment resolves its existing parent, including symlinks, before any write.


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

The report records the world ID and image IDs, never source paths, along with stored dimensions, EXIF orientation, oriented dimensions,
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

## Checks and world evidence

[ComparisonTests.swift](Tests/AppleVisionTranslationExperimentTests/ComparisonTests.swift)
retains seven self-contained mechanics cases: identity, a known translation and
rendered overlay, EXIF orientation, resizing and alpha treatment, unequal sizes,
and input/output failures. Source preservation is checked as well.

[WorldTests.swift](Tests/AppleVisionTranslationExperimentTests/WorldTests.swift)
checks identity/schema validation, additive fields, empty worlds, path safety,
missing or altered bytes, symlinks, extra files, report identities and output
containment. A hash-valid but undecodable image produces an ordinary input error
naming its world and image ID; it does not become an alignment result.

`HAZY_WORLD=/path/to/world swift test --package-path Experiments/AppleVisionTranslation`
also exercises a supplied world. It assumes neither image count nor relationships,
format support or numerical transforms. Without the variable, that external-input
check explicitly skips while self-contained cases run. The CLI's real-world
acceptance check additionally verifies reports and unchanged source hashes from a
checkout with no producer code or records.

These checks establish mechanics and the consumer boundary. Neither a returned
transform nor shared dimensions establishes visual correspondence. Upstream image
processing is unknown unless visible in the bytes. The experiment's preparation
and Apple's registration remain distinct from any producer's selection decisions.

Apple references: [ImageIO](https://developer.apple.com/documentation/imageio)
and [Aligning Similar Images](https://developer.apple.com/documentation/vision/aligning-similar-images).
