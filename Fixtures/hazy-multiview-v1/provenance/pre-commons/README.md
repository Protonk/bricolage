# hazy multiview fixture v1

**11 separately captured images in four scene groups:** the supplied motorcycle
pair and nine user photographs. Use only the flat `images/` directory as input.
The source bytes, including embedded metadata, are unchanged.

| Scene ID | Original source filenames | What varies |
|---|---|---|
| `middlebury2014-motorcycle` | `motorcycle_left.png`, `motorcycle_right.png` | Two physical camera viewpoints; supplied rectified and downsampled |
| `personal-playground-rail` | `IMG_7067.JPG`, `IMG_7068.JPG`, `IMG_7069.JPG` | Pose, expression and framing at a playground railing |
| `personal-water-feature` | `IMG_7242.JPG`, `IMG_7243.JPG`, `IMG_7246.JPG` | People and water in motion against a shared rocky background |
| `personal-tent-table` | `IMG_7678.JPG`, `IMG_7679.JPG`, `IMG_7680.JPG` | Expressions, gestures and people moving through the table scene |

The three personal groups were identified by visual inspection of all nine files
and the user's statement that they comprise three groups. These are scene labels,
not person identities, calibrated camera poses, exact event timing, or a promise
that a translation can align them. Each of the eleven captures has its own source
family; scene membership is recorded separately in `scene_id`.

The motorcycle images are 741×500 PNGs. The playground and water-feature JPEGs
store 4032×3024 pixels; the playground files have EXIF orientation 6 and become
portrait images when prepared. The table JPEGs store 5712×4284 pixels. hazy prepares
the personal images to 768×1024 or 1024×768, preserving their orientation and aspect
ratio. No resizing or orientation change has been applied to the fixture bytes.

## Layout and selections

This set follows the [shared fixture schema](../README.md). `sources/` keeps the
original filenames; `images/` holds byte-identical copies under opaque names.
`sources.csv` and `provenance/import-map.csv` connect the two. The original motorcycle
README and manifests are preserved under `provenance/supplied-*`.

- Focus: all 10 unordered within-scene pairs, each run in one recorded direction
  (one motorcycle pair and three pairs for each personal group).
- Probes and full: those 10 plus six cross-scene diagnostic pairs, using one
  representative from each of the four scenes. These are different-scene examples,
  not asserted algorithmic non-matches.
- `batch-1.txt` through `batch-4.txt`: motorcycle, playground, water feature, and
  table respectively. Together they cover the eleven inputs exactly once.
- `smoke.txt`: the two motorcycle views. `medium.txt`: all eleven inputs.

No synthetic derivatives or expected transforms have been added. Pixel hashes
using the derivative set's Pillow convention are intentionally blank. Byte hashes
are present for all inputs and source assets.

## Provenance and limits

See [SOURCES.md](SOURCES.md) for the supplied Middlebury/scikit-image attribution,
processing history, and the separate status of the personal photographs.

The motorcycle pair is relatively constrained: rectification and quarter-scale
resampling happened upstream. The personal groups add scene motion and variation
in framing, but do not establish a measured viewpoint baseline. A translation may
align some background detail while leaving moving people doubled. An estimated
alignment therefore remains an observation, not a judgment that the photographs
are interchangeable. Eleven images are an exploratory set, not a general benchmark.
