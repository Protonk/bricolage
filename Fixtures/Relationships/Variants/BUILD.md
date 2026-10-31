# Build specification

## 1. Inventory and prepare

Create one source record, five local final variants, and one imported `v06` generation for each of `m01` through `m06`. Include one byte-for-byte source copy per family in `images/`. The finished input set is 6 sources + 30 locally constructed variants + 6 supplied generations = **42 files**. All source and supplied-generation bytes are bundled. Retained stages and contact sheets are support artifacts under `previews/`, never additional comparison inputs by accident.

Use stable opaque input filenames and retain the complete mapping from `(source ID, variant ID)` to path in textual provenance. A deterministic name derived from the fixture ID and those identifiers is sufficient; do not use subject or treatment names in `images/`. Preserve the actual encoding extension.

The preparation operations below apply only to working copies of the six original sources for `v01`–`v05`. Import `v06` by byte copy as described in section 5; do not send it through this preparation pipeline.

Before editing, inspect each source at useful resolution. Create a working image by applying EXIF orientation once, converting an embedded ICC profile to a declared sRGB working representation, and flattening transparency against white. For untagged files, explicitly record the sRGB assumption. Use an 8-bit RGB working canvas for these recipes. Preserve originals unchanged, including embedded metadata. Record dimensions before and after orientation, color handling, alpha handling, and any resize.

Downscale working images to at most 1,600 pixels on their longest edge, without upscaling, using a specified resampler. The narrow comic is an exception: keep its native 662 × 3,211 canvas for selecting readable panels, then size selected regions for each composition. The cat's stored pixels are 4,080 × 3,060 with EXIF orientation 6; its displayed canvas is portrait. Define all edit coordinates on the **oriented working image**, with origin at top left and half-open integer boxes `[left, top, right, bottom]`.

Save each prepared image under `previews/stages/<source-id>/prepared.png`. Distinguish preparation from variant operations in the records. No automatic enhancement, exposure correction, or sharpening is required.

## 2. Fix the local choices before rendering

Write a machine-readable recipe file under `provenance/` containing the actual crop boxes, edit masks or mask paths, donor IDs, text, font identity, colors, sizes, transforms, and encoder settings. The defaults below are starting values. Adapt them for a legible composition and then freeze the exact values. An image should visibly contain its intended treatment; text and the replacement should not disappear at final resolution.

For the comic, select one or two complete narrative panels for the cropped variants, excluding the title/credits-only areas. Preserve the full strip as the source input. Save its selected region before wrapping. Use the same region and wrapper geometry for `v02` and `v03`.

Use one common fictional social-post template across all six sources: fixed 1,080 × 1,080 canvas, a neutral avatar drawn from simple shapes, display name `Fixture User`, handle `@fixture_user`, short post text `Had to share this.`, and a drawn footer. No screenshot of an actual account is needed. Put the source region in a fixed image slot of approximately 900 × 600 pixels, preserving aspect ratio with explicit padding. Adjust the slot height once if needed for the selected comic panels; keep a common template for the set. Save the template and its geometry once.

Use available local fonts, recording font file hash and size. If redistribution permits bundling the chosen font, place its bytes and license under `previews/assets/`; otherwise record how to obtain the same font and its local identity without copying it. Do not silently fall back to a different font. Render all text programmatically.

## 3. The five recipes

### v01 — Dutch angle, border, grayscale, WASTED

1. Start with the prepared image. For the tall comic, use a recorded panel selection so the content remains visible in a normal frame; retain that crop as a stage.
2. Rotate approximately 17° clockwise, expanding the canvas to preserve the chosen content. Record the actual forward pixel transform and resampling convention.
3. Convert to grayscale with a specified conversion, retaining RGB storage for the later colored stamp.
4. Fit the rotated content inside a substantial dark frame, approximately 20% of the final width in combined side margins. Keep the inserted image's aspect ratio. Record source footprint, corner fill, and frame rectangle separately.
5. Add a large red `WASTED` stamp across the central or lower portion, with a dark shadow or outline. It should overlap source content but leave substantial content visible. This is rendered text, not a downloaded GTA asset.
6. Write the final PNG.

Retain: selected source crop if used, rotated color image, grayscale framed image without the stamp, stamp overlay/mask, final render. Save the original-source footprint mask transformed through the geometry so frame pixels are distinguishable from source pixels.

### v02 — Cropped image in a degraded mock social post

1. Choose a recognizable crop. For photographs, start with roughly 70–85% of each dimension and adjust to retain a useful subject. For the comic, select complete panels as described above.
2. Place it in the common post template using a recorded fit, padding, and placement rectangle. No content-aware fill.
3. Save the clean wrapped image.
4. Apply a fixed degradation sequence: downscale the whole post to 540 × 540, encode JPEG at quality 35 with an explicitly chosen chroma subsampling mode, decode it, and upscale to 1,080 × 1,080 with a specified resampler. Store the final decoded result as PNG so the intended JPEG round trip is the only lossy encoding stage.

Retain: crop, clean wrapper, the intermediate low-resolution JPEG, and final PNG. Keep the source footprint and text/interface rectangles in the construction record. Use identical degradation parameters for all sources and for `v03`.

### v03 — Crude replacement followed by the v02 treatment

Make a local cut-and-paste replacement on the prepared image before applying **exactly the same** crop, template, fit, and degradation as `v02`. The replacement must fall inside the retained crop. Avoid enlarging or recentering the crop merely because the replacement was added.

Suggested replacements, using only the six bundled sources:

| Base | Replacement |
|---|---|
| `m01` comic | Replace one countryball in a selected panel with a roughly cut-out cat from `m06` |
| `m02` action | Replace the skateboarder's head/upper-head region with the cat's head from `m06` |
| `m03` portrait | Replace the face/head region with the cat's head from `m06` |
| `m04` landscape | Replace the foreground visitor with the cat from `m06` |
| `m05` coffee | Replace the central press body with a cat cutout from `m06` |
| `m06` cat | Replace the cat's head with a roughly cut-out coffee press from `m05` |

A polygon mask, hard-edged cutout, visible paste seam, and intentionally imperfect scale are appropriate. Choose a meaningful local region rather than covering most of the base. If the old subject must be obscured, use a recorded solid patch or copied nearby patch inside the same allowed region; do not synthesize missing scenery. Record the patch as another compositing operation.

Retain: donor crop, donor alpha mask, allowed edit-region mask, positioned overlay, clean replacement before wrapping, clean wrapped replacement, low-resolution JPEG, and final PNG. Verify exact pixel equality between the base and clean replacement **outside the allowed edit mask**. The edit mask must include every overwritten, patched, or alpha-blended pixel. Later resampling and JPEG artifacts can spread beyond that area and are recorded as later operations.

The final image has two source parents. Record both; a single-family label would lose the donor relationship. The v02/v03 pair is especially useful as a direct construction pair because the wrapper and downstream processing are held constant.

### v04 — Tight reaction crop and oversized caption

Select a tight source region: a comic expression, a skateboard pose, the portrait face, a mountain/cloud detail, the coffee press, or the cat's face. Target roughly 20–40% of the prepared image's area where practical; retain actual bounds and area fraction, not just the target.

Place the crop on a new canvas with large top/bottom caption bands. Use `WHEN THE PLAN` and `MEETS REALITY`, or a recorded equally short neutral caption if layout requires it. Allocate approximately 40–50% of canvas area to caption bands. Preserve the cropped image's aspect ratio. Save as PNG.

Retain: uncaptioned crop, layout before text, caption overlay/mask, final image. Record the source crop, placement, and each caption rectangle. Do not imply that unseen portions of the original were recovered.

### v05 — Rearranged two-panel composition

Select two distinct, preferably non-overlapping regions from the prepared image. Use two complete narrative panels for the comic. For other sources, use left/right or top/bottom portions containing recognizable detail. Place them in reversed order on a fresh two-panel canvas, with a conspicuous gutter and the short headings `PLAN` and `RESULT`. Preserve each piece's aspect ratio using explicit padding. Do not mirror or redraw the pieces unless a separately recorded recipe revision calls for it. Save as PNG.

Retain: both source crops, the assembled layout before captions, caption overlay, final image. Record a separate source-to-output mapping for each piece. If crops overlap, record the overlap; a single global transform is not an adequate record of this composition.

## 4. Record construction and integrate metadata

Use the current shared Hazy schema for the runnable set, with `fixture_id=hazy-meme-fixtures-v0` and `kind=derivatives` if those conventions remain current. Keep richer operation histories in a fixture-local sidecar such as `provenance/construction.json` rather than changing the shared schema.

Produce `manifest.json`, equivalent `manifest.csv`, `sources.csv`, `SOURCES.md`, `probes.csv`, `selections.json`, `batches/`, and `SHA256SUMS.txt` following the local fixture documentation. Keep `SOURCE_SHA256SUMS.txt` and `V06_SHA256SUMS.txt` as immutable checks of the supplied assets and prompts. The finished checksum file must cover every file in flat `images/` and flat `sources/`; intermediate artifacts get their own hashes in the construction sidecar.

Use one numbered batch containing all 42 inputs. At the checked repository revision, `smoke.txt` and `medium.txt` for derivative sets are defined by specific transformation names from the older set; for this set both can contain only the six `transformation=source` inputs. Use explicit `probes.csv` and `selections.json` for the new pairs. Do not add extra variants just to fill those legacy subsets.

Each final image's construction entry must identify its source ID, variant ID, immediate input artifacts, complete source-parent list, ordered operations and parameters, retained stage paths and hashes, and final path/hash. Every crop/mask must name its coordinate frame. Record actual widths, heights, and stored EXIF orientation in the shared manifest. Use original stored dimensions/orientation for byte-identical source copies, and orientation 1 for prepared final renders. For `v06`, retain the actual stored dimensions and orientation from the unchanged supplied file. If computing decoded RGB hashes, document the decoding convention; do not confuse them with prepared-image hashes.

Single-source variants have their source's family ID and one parent. `v03` is a two-source composite with empty `family_id`, two pipe-separated source parents, and `origin_count=2`. Drawn wrapper shapes and text are construction assets, not additional photographic parents. Leave `scene_id` empty: these records describe supplied assets and edits, not independent captures of one scene.

Include explicit pairs for:

- Each source against its five local final variants: 30 pairs.
- Each source against its supplied `v06` generation: 6 pairs.
- Each `v02` against its matching `v03`: 6 pairs.
- Each donor source against the corresponding `v03`: 6 pairs.
- Different sources with the same wrapper: choose three fixed source pairs and include each in `v01` and `v02`, giving 6 more pairs.

This produces 54 distinct ordered probes if none is duplicated. Describe the actual construction relationship in `interpretation`; do not prescribe a score, alignment, or membership verdict. At the checked schema, use `diagnostic` for composite, wrapper, and `v06` comparisons; ordinary one-parent pixel-derived comparisons may use `same_origin_<variant-id>`. For `v06`, state `source → description prompt → supplied generation; no asserted pixel correspondence` in the interpretation. Put a small explicit subset in `selections.json`, covering every treatment, the comic replacement, a donor pair, and a shared-wrapper pair. Set `known_shift_families` to an empty list.

## 5. Import the six supplied v06 generations

All six outputs and their description prompts are already bundled. `provenance/v06-imports.json` is the authoritative mapping between each original source, its prompt, and its supplied generation. `V06_SHA256SUMS.txt` checks the six PNG files and six prompt files. No external handoff or service call is needed.

1. Verify the supplied PNG and prompt hashes against the mapping and checksum file.
2. Copy each `previews/supplied-v06/<source-id>.png` into the flat `images/` directory with a stable opaque filename. Preserve the complete file bytes, including embedded metadata. Do not resize, recolor, crop, retouch, re-encode, or regenerate it. Keep the supplied copy as the immutable import input.
3. Add the six imported files to the shared manifest, numbered batch, checksum inventory, and source-to-generation probes. Record the final opaque path and byte-copy operation in the construction sidecar, retaining the mapping to the supplied asset and prompt. The `local_import.final_input_path` field in the supplied mapping is intentionally null because the local build assigns that path; it is not a missing image.
4. Under the current shared schema, use the original source's `family_id` and sole `parents` ID, `origin_count=1`, an empty `scene_id`, and `transformation=description_mediated_generation` plus `relation_kind=description_mediated_generation`. Here the parent relationship records derivation through a description; it does not assert copied source pixels. Keep the full source → prompt → generation chain explicit in the sidecar. Do not mark the generation as `source`, `byte_copy`, or `same_decoded_pixels` relative to the original photograph/comic.
5. Retain the prompt text exactly as supplied, including any omissions or inaccuracies. The six prompt files contain the complete descriptions from the corresponding replies, excluding thumbnail embeds. Read `provenance/prompts/README.md` for what is and is not recorded about the external generation.
6. Preserve unknown model, seed, settings, and rights fields as unknown. Keep any embedded generation provenance in the PNGs. Do not assign the original sources' CC0 dedication to these outputs. No pixel transform, mask correspondence, or copied-region coverage is established for `v06`; use null/not-applicable fields rather than fabricating one.

The five local recipes operate on the six original sources only. Do not apply them to the supplied generations. Successful completion includes all six `v06` imports and yields the complete 42-input set.

## 6. Validate and finish

Implement a fixture-local generator and a compact check command. Reuse existing tools where they fit. Verification should cover:

1. All six source bytes and all six supplied generations still match their supplied checksums; the six prompt files also match. Every source, supplied generation, and final input decodes.
2. Exactly 42 primary inputs exist, all mapped once: 6 source copies, 30 locally constructed variants, and 6 `v06` imports. Each imported image is byte-identical to its mapped supplied generation; there are no pending slots.
3. The shared CSV and JSON metadata agree, all local paths resolve within the set, parent IDs exist, and hashes/dimensions/orientations are actual measurements.
4. Every prescribed local stage exists, has a recorded hash, and traces through operation inputs back to the source bytes. Each `v06` entry resolves its original source, exact prompt, and supplied generation without invented spatial mappings. Comparison inputs contain the six deliberate imported copies, not their contact sheet, masks, or intermediate stages.
5. Clean replacements pass the outside-mask equality check. Each `v02`/`v03` pair shares crop, template geometry, fonts, and degradation settings.
6. Batch and pair lists contain only real inputs; source/composite parent counts are correct.
7. Visually inspect all 30 locally constructed alterations and stage contact sheets. Check source visibility, text bounds, intended panel order, comic legibility, and the replacement's presence. Verify each of the six `v06` imports against its supplied file and mapping; do not repair or replace their content.
8. Rebuild the 30 local variants and re-import the six supplied generations into a separate fresh staging directory in the same environment and compare output hashes. Reproduction of `v06` is a byte copy from its bundled input, not a new service call. Record any unavoidable encoder or font reproducibility limitation explicitly rather than silently updating canonical bytes.

Run the existing fixture checker with this set's explicit path if its current schema supports it. At preparation time the command was `python3 Experiments/AppleVisionTranslation/Tools/fixtures.py check --fixtures Fixtures/hazy-meme-fixtures-v0` from the repository root. Inspect current code/help before relying on that command. If a legacy checker rejects a set-specific convention, document the exact mismatch and use a fixture-local validator for this task; do not broaden the task into application or shared tooling changes.

The deliverable is the built local fixture folder, reproducible generation code and parameters, complete metadata, retained stages, and a short completion report. Running comparison experiments is not required to finish generation.
