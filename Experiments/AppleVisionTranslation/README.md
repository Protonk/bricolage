# Apple Vision translation experiment

This is the implemented macOS channel experiment. Its Swift library is
`AppleVisionTranslationExperiment`; its CLI is `hazy-vision-translation`.
The router has no executable or package yet. This experiment supplies evidence to
[router research](../../Research/Router/README.md) and
[portability research](../../Research/Portability/README.md).

The input is a directory satisfying [WORLD.md](../../WORLD.md), plus two explicit
image IDs. The experiment knows nothing about the world's producer, its records,
provenance, groups or intended pairs. Its function and report types remain
experimental; they are not the future router API.

## Build and run

Requires macOS 14 or later and Swift 6 with the macOS SDK. There are no third-party
package dependencies. From the repository root:

```sh
swift build --package-path Experiments/AppleVisionTranslation
mkdir -p output
swift run --package-path Experiments/AppleVisionTranslation hazy-vision-translation compare \
  --world /path/to/world --reference sha256:REFERENCE_HASH --floating sha256:FLOATING_HASH \
  --output output/example
HAZY_WORLD=/path/to/world swift test --package-path Experiments/AppleVisionTranslation
```

Replace the two placeholder IDs with IDs listed in the world's `world.json`.
The reference stays fixed; Vision attempts to move the floating image into alignment.
The output must be a new directory outside the world, with an existing parent.
Finish reading a world before its publisher reuses that directory.

The loader validates schema version 1, nonempty opaque world identity, unique
hash IDs and flat hash-named regular files, sorted filenames, exact file coverage,
and SHA-256 bytes. Unknown additive JSON fields are ignored. A world can be empty
or contain undecodable bytes; a requested image must exist and be decodable to
participate in a comparison. No fixture lookup or producer-specific ID syntax is used.

A run prints the world/image IDs and writes:

- `comparison.json`: `worldID`, `reference.id`, `floating.id`, preparation dimensions
  and orientation, request revision, outcome, and translation when available.
  Source paths and producer metadata are absent.
- `reference.png` and `floating.png`: the prepared inputs passed to Vision.
- `overlay.png`: the aligned floating image at 50% opacity over the reference,
  clipped to its bounds; written only when an alignment is estimated.

Exit codes are `0` for an estimated alignment, `1` for a usage/input/output error,
and `2` when no alignment is available. `estimated`, `noObservation`, `failed` and
`notRun` remain distinct report outcomes. A failed request still saves prepared
images and its explanation. An output-writing failure can leave a partial output;
choose a new directory after correcting it. Errors include world/image IDs when
available. An estimate is not a judgment that the images match.

## Current scope and checks

ImageIO decodes one image, applies EXIF orientation, and reduces its longest side
to at most 1,024 pixels. Core Graphics renders 8-bit sRGB with alpha flattened onto
white. These working images do not preserve every property of their source formats.
The experiment requires equal prepared dimensions and requests translation only;
it does not estimate rotation, scale or perspective, or provide a similarity score.

The seven `ComparisonTests` use generated patterns for preparation, orientation,
transparency, known translation, overlay and input/output mechanics. `WorldTests`
check the world boundary, identity reporting, malformed and altered worlds,
unknown IDs, undecodable files and output containment, including symlinked parents.
One test reads the world supplied through `HAZY_WORLD` without assuming its contents
or expected alignment. That test explicitly skips when the variable is absent;
all self-contained checks still run:

```sh
swift test --package-path Experiments/AppleVisionTranslation
swift test --package-path Experiments/AppleVisionTranslation --filter ComparisonTests
```

See [IMAGE-JOURNEY.md](IMAGE-JOURNEY.md) for the framework handoffs and result
conventions, and [AGENTS.md](../../AGENTS.md) for working guidance. These checks
establish mechanics and the input boundary, not general matching quality.
