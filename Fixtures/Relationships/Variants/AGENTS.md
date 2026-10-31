# Operating in this fixture folder

Your task is to build the five local variants described in `BUILD.md` for each of the six supplied sources, retain the specified stages, import the six supplied `v06` generations unchanged, and integrate the resulting 42-input fixture with the local Hazy checkout.

## Read and locate

1. Read this folder's `README.md`, `BUILD.md`, `SOURCES.md`, source manifest, and `provenance/v06-imports.json`.
2. Identify the actual Hazy repository root. Read its current `AGENTS.md`, `README.md`, `Fixtures/README.md`, and any applicable directory instructions. Inspect the working tree before editing. Repository guidance may have changed since this kit was assembled.
3. Use the repository's current fixture conventions. The suggested destination is `Fixtures/Relationships/Variants/`; resolve it from the discovered checkout. Do not overwrite another fixture set, replace unrelated guidance, or assume that an existing destination belongs to this run.
4. Verify `SOURCE_SHA256SUMS.txt` and `V06_SHA256SUMS.txt` before decoding or generating anything. Keep the six originals, six supplied generations, and six prompts intact; preserve a supplied copy of metadata if normalization requires edits.

## Scope

- Work on fixture images, fixture-local generation code, recipes, manifests, provenance, previews, and checks. A small fixture index entry is appropriate if that is the local convention.
- Keep application code, comparison implementations, router design, research plans, and unrelated fixture sets outside this task.
- Use the six original images as bases and replacement donors for `v01`–`v05`. Use `previews/supplied-v06/` only for unchanged imports of `v06`. No additional image collection or network acquisition is needed.
- Implement the five variants with explicit pixel operations, drawing, and compositing. Do not ask an image model to edit, redraw, complete, remove, or replace any part of them. Do not generate descriptions or drawings for `v06`.
- Choose routine crop boxes, masks, font sizes, and placement yourself after inspecting the sources. Record the exact choices. All six `v06` outputs are supplied: import them without rewriting their prompts, regenerating, retouching, resizing, or re-encoding them.

## Paths, assets, and reruns

- Keep comparison inputs in a flat `images/` directory, using stable opaque filenames. Keep the six upstream assets in flat `sources/`. Keep all prepared images, masks, cutouts, stage renders, and contact sheets under `previews/`, with subdirectories as needed. Textual recipes, records, and generation code belong under `provenance/`.
- Check the current ignore rules before staging files. Hazy currently ignores all contents of fixture `images/`, `sources/`, and `previews/` directories. Do not force-add image bytes or put a binary asset in a tracked metadata folder.
- Store portable paths relative to the fixture root. Resolve script paths from their own location or explicit arguments, not an assumed shell directory. Reject path traversal, unexpected symlinks, and destinations outside the chosen set.
- Build into a fresh named staging directory under `previews/`. Validate there, then publish completed inputs and metadata coherently. Reuse stable IDs on reruns; do not reshuffle filenames or mutate a completed fixture silently.
- Never recursively clean the repository or a shared output folder. Cleanup may remove only files enumerated as created by this generator in its own staging directory. Preserve user edits and externally supplied assets.
- Use an existing appropriate local image library, or an isolated environment with pinned versions. Record the interpreter, library and encoder versions, font identity, and exact generation command. Avoid changing the user's global environment.

## Construction discipline

- A recipe must name its real inputs and operation order. Save the prescribed intermediate artifacts before later lossy or global processing. For `v06`, retain source → prompt → supplied output lineage and record the final byte copy. No pixel transform or correspondence mask is established for that relationship.
- A local replacement must leave every pixel outside its declared edit region unchanged at the clean replacement stage. Enforce this by compositing onto the original working canvas, and verify it there. Record any later global resize or JPEG encoding separately.
- Preserve source attribution, donor identity, crop geometry, masks, text, fonts, transforms, resampling, color conversion, compression settings, and artifact hashes. Use masks and per-piece mappings for coverage records; do not infer them from the final appearance.
- Inspect every final image and the relevant intermediate stages. For `v01`–`v05`, fix broken layout, clipped captions, missing replacements, or empty crops by changing recorded recipe parameters and rebuilding. For `v06`, verify the supplied source mapping and bytes; preserve the image even where it differs from its prompt. Do not replace originals or use generative repair.
- Keep failed or incomplete operations visibly marked. Do not write successful records for files that are absent.

## Finish

Complete and validate all 42 comparison inputs, including six byte-identical `v06` imports and their source-to-generation pairs. Report the set path, counts of originals/constructed variants/imported generations, reproduction command, checks performed, and any limitations. Do not implement unrelated changes to make a fixture checker accept this set; follow the compatibility procedure in `BUILD.md`.
