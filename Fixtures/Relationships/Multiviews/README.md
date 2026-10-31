# hazy multiview fixture v1

**20 separately captured images in eight scene or sequence groups:** the motorcycle
pair, nine personal photographs, and nine Commons crowd photographs. Use only the
flat `images/` directory as input. All supplied image bytes, including embedded
metadata, are unchanged.

| Scene ID | Source filenames as supplied | What varies |
|---|---|---|
| `middlebury2014-motorcycle` | `motorcycle_left.png`, `motorcycle_right.png` | Two physical camera viewpoints; supplied rectified and downsampled |
| `personal-playground-rail` | `IMG_7067.JPG`, `IMG_7068.JPG`, `IMG_7069.JPG` | Pose, expression and framing at a playground railing |
| `personal-water-feature` | `IMG_7242.JPG`, `IMG_7243.JPG`, `IMG_7246.JPG` | People and water in motion against a shared rocky background |
| `personal-tent-table` | `IMG_7678.JPG`, `IMG_7679.JPG`, `IMG_7680.JPG` | Expressions, gestures and people moving through the table scene |
| `kumbh-mauni-amavasya` | `image-01.jpg`, `image-02.jpg` | Dense crowd, repeated forms and changing framing |
| `budapest-pride-1424` | `image-03.jpg`, `image-04.jpg` | Crowd, flags and framing in a landscape sequence |
| `budapest-pride-1428` | `image-05.jpg`, `image-06.jpg` | Nearby landscape sequence, with people and flags in motion |
| `budapest-pride-1435` | `image-07.jpg`, `image-08.jpg`, `image-09.jpg` | Portrait sequence with moving people and occlusion |

The personal groups follow visual inspection and the user's grouping description.
The four Commons labels retain the supplied kit's sequence grouping. These labels
are not person identities, calibrated camera poses, verified capture intervals, or
a promise that translation can align the images. The Budapest sequences share an
event and nearby surroundings, so different labels do not prove different physical
scenes. Each of the 20 captures has its own source family; `scene_id` records the
scene/sequence grouping separately.

## Input and preparation

| Group | Stored dimensions | hazy's prepared dimensions |
|---|---|---|
| Motorcycle | 741×500 | 741×500 |
| Playground | 4032×3024, EXIF orientation 6 | 768×1024 |
| Water feature | 4032×3024 | 1024×768 |
| Tent/table | 5712×4284 | 1024×768 |
| Kumbh | 1280×851 | 1024×681 |
| Budapest 1424 and 1428 | 1280×720 | 1024×576 |
| Budapest 1435 | 960×1706 | 576×1024 |

The Commons files are thumbnails manually downloaded when access to full-resolution
originals was blocked. All nine were matched to the named Commons thumbnails by
exact SHA-256 comparison, including the distinct `143521` and `143521_1` images.
Their upstream reduction is recorded in `sources.csv`; hazy subsequently applies
its normal ImageIO orientation/resizing and sRGB preparation. No resizing,
re-encoding, or orientation change was applied to fixture bytes during ingestion.

## Layout and selections

This set follows the [shared fixture schema](../../FORMAT.md). `sources/` keeps names
as supplied; `images/` holds byte-identical copies under opaque names.
`sources.csv` and `provenance/import-map.csv` connect the two. The original motorcycle
metadata is under `provenance/supplied-*`; the Commons kit, download-name mapping,
and hash verification evidence are under [provenance/commons/](provenance/commons/README.md).
`provenance/pre-commons/` preserves the previous 11-image set's metadata.

- Focus: all 16 unordered within-group pairs, each run in one recorded direction.
- Probes and full: those 16 plus all 28 pairs between one representative per group,
  for 44 comparisons. Of the 28, three between Budapest sequences use `diagnostic`;
  the other 25 use `distinct_scene`. Neither relation asserts an algorithmic non-match.
- `batch-1.txt` through `batch-8.txt`: the eight groups in table order, covering all
  20 inputs exactly once.
- `smoke.txt`: the two motorcycle views. `medium.txt`: all 20 inputs.

No additional image variants or expected transforms were created by hazy. Pixel
hashes using the derivative set's Pillow convention are intentionally blank. Byte
hashes cover all 20 inputs and their 20 preserved source assets.

## Provenance and limits

See [SOURCES.md](SOURCES.md) for the supplied Middlebury/scikit-image attribution,
personal photographs' status, and Commons source pages and credits. The archived
Commons kit describes intended full-resolution downloads; the canonical manifest
and source catalog describe the thumbnail files actually supplied.

The motorcycle pair is relatively constrained: rectification and quarter-scale
resampling happened upstream. The other groups add motion, crowd repetition,
occlusion, and variation in framing, without a measured viewpoint baseline. A
translation may align some background detail while leaving moving people doubled.
An estimate remains an observation, not a judgment that photographs are
interchangeable. This is an exploratory set, not a general matching benchmark.

Collection is complete for hazy's current preparation and translation scope.
Further additions should address a specific failure or newly implemented behavior.
