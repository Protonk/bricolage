# Variants

Six originals, thirty constructed edits and six supplied images generated from
descriptions of the originals.

Fixture ID: `hazy-meme-fixtures-v0`; kind: `derivatives`.
<!-- collection-totals:start -->
The manifest lists **42 active inputs**. [All collection totals](../../COLLECTIONS.md).
<!-- collection-totals:end -->

Use the [shared fixture format](../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Relationships/Variants/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Relationships/Variants/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Original publication and acquisition records

Built and validated: **42 inputs** from six bundled sources: six unchanged source
copies, 30 locally constructed variants, and six unchanged supplied generations.
Its manifest uses `kind=derivatives`; separate construction records describe
the steps used to make each image.

| Treatment | Count | Construction |
|---|---:|---|
| source | 6 | Byte-identical upstream asset copies, including original EXIF/ICC metadata |
| v01 | 6 | 17° clockwise rotation, grayscale, dark frame, red WASTED stamp |
| v02 | 6 | Recorded crop in a fictional post; 540px JPEG quality 35 round trip, upscaled to PNG |
| v03 | 6 | Local donor replacement, then exactly the matching v02 crop/wrapper/degradation |
| v04 | 6 | Tight reaction crop and two large caption bands |
| v05 | 6 | Two independently mapped source regions in reversed panel order |
| v06 | 6 | Supplied description-mediated generation; byte-copy import only |

Only the flat `images/` directory is comparison input. Sources, stages, masks,
contact sheets and staging builds stay in Git-ignored asset directories. No
source or supplied generation was re-encoded. No new image generation was used.

### Provenance and interpretation

[Sources and credits](SOURCES.md), [source manifest](provenance/construction/source-manifest.json), six
[prompts](provenance/prompts/README.md), and the
[supplied generation mapping](provenance/v06-imports.json) remain as delivered.
The source manifest's status describes the original kit; current completion is
recorded in [publication.json](provenance/publication.json). Its six originals
carry recorded CC0 provenance; rights/settings for the supplied generations are
unknown and are not inherited from their sources.

[recipes.json](provenance/recipes.json) freezes crop boxes, polygons, donor IDs,
font, colors, text, layout and encoder choices.
[construction.json](provenance/construction.json) records 242 artifact hashes,
immediate inputs, ordered operations, preparation, transforms, per-piece and
per-parent masks, and `(source, variant)` → opaque input names. The originals'
EXIF orientation and ICC profiles are retained; only local working copies are
oriented, converted to sRGB, flattened over white and reduced. The comic retains
its native canvas for panel selection. Pixel-hash fields are empty rather than
claiming agreement with another decoder or hazy's prepared pixels.

The six v03 composites have an empty `family_id` and two source parents. Their
clean replacement stages preserve every pixel outside the declared edit mask;
global resizing and JPEG compression follow separately. The landscape replacement
uses a recorded copied background patch. Cutout seams are intentional. Geometric
coverage is recorded before compression, not inferred from the final appearance.

The v06 family/parent records describe source → prompt → supplied generation.
They assert no copied pixels, spatial correspondence, expected score, or matching
verdict. No scene membership or semantic cluster label is assigned.

There is one 42-input numbered batch. Legacy `smoke` and `medium` lists both
contain just the six originals. Focus selects **15 pairs**; probes/full select
**54 pairs**: 30 source/local-variant pairs, six source/generation pairs, six
v02/v03 pairs, six donor/composite pairs, and six shared-treatment comparisons
between distinct sources. Known-shift families are empty.

### Reproduce and check

From the repository root, using an isolated environment:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Relationships/Variants/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Relationships/Variants/tools/build.py build --stage another-run
Fixtures/.venv/bin/python Fixtures/Relationships/Variants/tools/build.py check --stage another-run
Fixtures/.venv/bin/python Fixtures/tools/relationship_fixtures.py check --fixtures Fixtures/Relationships/Variants
```

Each build requires a fresh stage name and writes under `previews/build-NAME/`.
`publish --stage NAME` validates first and refuses existing published outputs;
reruns do not silently replace a completed fixture. There is no cleanup command.
Use `build.py check` without `--stage` to validate the published fixture and stages.

The build uses Pillow 12.0.0 and the hash-checked macOS Arial Bold font named in
the recipe; no font fallback or global environment modification is performed.
Interpreter, Pillow, JPEG, FreeType, LittleCMS and compression versions, font
identity, and exact command are recorded in the construction sidecar. The font
is supplied with macOS and is not redistributed here. Reproduction across other
font/library versions is not guaranteed.

[Validation](provenance/validation.json) records the independent rebuild: all
42 final bytes and 242 artifact hashes matched. Shared manifests, checksums,
parents, batches and probes passed; all six clean replacement masks passed;
all 30 constructed variants and relevant stage sheets were visually reviewed.
The six generations and prompts matched supplied hashes. Local review sheets
are in `previews/review/`. Comparison experiments were not required or run.

The original [kit README](provenance/supplied-README.md) and [build specification](provenance/construction/BUILD.md)
retain the supplied construction intent. These fixtures exercise changed
composition and representation; they do not establish retrieval quality.
