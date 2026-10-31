# Hazy meme fixtures — v0 build kit

Six bundled CC0 source images, six supplied description-mediated generations with their prompts, and instructions for building a small, staged set of meme alterations inside Hazy. The five locally constructed variants have **not** been built in this kit.

Build five variants of each source and import the six supplied `v06` generations unchanged. Together with six byte-identical source copies, the completed set will contain **42 comparison inputs**: 6 originals + 30 locally constructed variants + 6 supplied generations. All external image inputs are bundled. Intermediate stages, masks, and contact sheets are separate from these counts.

## Contents

| Path | Contents |
|---|---|
| `AGENTS.md` | Operating instructions for the local agent |
| `BUILD.md` | Five recipes, retained stages, metadata, and completion checks |
| `sources/` | Six unchanged upstream image files; only local filenames were changed |
| `sources.csv` | Source catalog using Hazy's current source columns |
| `source-manifest.json` | Source URLs, license evidence links, byte hashes, dimensions, and preparation notes |
| `SOURCES.md` | Human-readable credits and CC0 provenance |
| `SOURCE_SHA256SUMS.txt` | Checksums of the six supplied source files |
| `previews/sources.jpg` | Source contact sheet; not a comparison input |
| `previews/supplied-v06/` | Six supplied generations, preserved byte-for-byte; import copies into `images/` during the build |
| `previews/v06.jpg` | Contact sheet of supplied generations; not a comparison input |
| `provenance/prompts/m01.md` through `m06.md` | Complete description prompts from the corresponding replies |
| `provenance/v06-imports.json` | Source → prompt → supplied generation mapping, hashes, and recorded metadata |
| `V06_SHA256SUMS.txt` | Checksums of the six supplied generations and six prompt files |
| `provenance/repository-context.md` | Repository conventions checked while preparing this kit |

## The six sources

| ID | File | Subject |
|---|---|---|
| `m01` | `sources/01-comic.png` | Multi-panel countryball comic |
| `m02` | `sources/02-action.jpeg` | Skateboarder airborne during a trick |
| `m03` | `sources/03-portrait.jpg` | Posed photographic portrait, viewed in a mirror |
| `m04` | `sources/04-landscape.jpg` | Tern Lake, Alaska; mountains, water, and a foreground visitor |
| `m05` | `sources/05-coffee.jpg` | Coffee press on a kitchen counter |
| `m06` | `sources/06-cat.jpg` | Cat sitting on a stone wall |

These are a small convenience selection spanning the requested subjects, not a statistically random sample. Each file's own Commons description identifies its image license as CC0 1.0; this is separate from Commons' general metadata license. Source links and credits are in `SOURCES.md`.

## Start here

Read `AGENTS.md`, then `BUILD.md`. The intended set location is `Fixtures/hazy-meme-fixtures-v0/` in the **actual local Hazy checkout**. If this folder was extracted elsewhere, inspect the checkout and its instructions before choosing the destination; do not assume the current working directory is the repository root or overwrite an existing set.

From this folder, verify the supplied bytes:

```sh
shasum -a 256 -c SOURCE_SHA256SUMS.txt
shasum -a 256 -c V06_SHA256SUMS.txt
```

The local task is to implement the five reproducible image recipes, preserve their stages, import the six supplied generations by byte copy, and produce fixture metadata. Use the source IDs in `provenance/v06-imports.json` to pair each generation with its prompt and original. Do not invoke an image-generation or image-description service for this task.

## Variant inventory

| ID | Final treatment | Status in this kit |
|---|---|---|
| `v01` | Dutch angle, grayscale, substantial border, red `WASTED` stamp | Recipe supplied |
| `v02` | Cropped source embedded in a degraded mock social post | Recipe supplied |
| `v03` | Crude local replacement, then the same crop, post wrapper, and degradation as `v02` | Recipe supplied |
| `v04` | Tight reaction crop with an oversized caption | Recipe supplied |
| `v05` | Two source regions rearranged into a captioned two-panel image | Recipe supplied |
| `v06` | Description-mediated new drawing | Six outputs and their prompts supplied; import unchanged |

The CC0 provenance applies to the six original source assets. Rights metadata for the externally generated images was not supplied; it is recorded separately without assigning them the originals' dedication.

The source files remain canonical. A prepared working image is a recorded derivative, even when the change is just applying EXIF orientation or converting a color profile. Construction records state which material came from which source and what operations were applied; they do not assert that any pair must receive a particular comparison result.
