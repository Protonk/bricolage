# Completion checks

## Population and selection

- The frozen category inventory comes only from *direct* File members of
  `Category:Media uploaded by Evan Amos`; no recursive children and no broad
  Evan-Amos category/user-upload search. API request/response evidence, page
  IDs, timestamps, continuation, count and hashes survive in `provenance/`.
- Each inventory member has exactly one candidate identity and exactly one
  selection outcome. Three user-specified titles appear in `EXCLUSIONS.txt` and
  are the **only** `excluded_by_user` entries. All other File pages remain
  included, even when related, visually similar, or another format of a file.
- **Expected on 2026-10-31 page listing:** 136 direct members, 3 excluded,
  133 included. If live membership differs, report and freeze actual counts.
  Do not silently force the expected count.
- No one-per-object/one-per-photographer cap, generated sample order, visual
  accept/reject, or additional convenience exclusions.

## Transport, provenance and rights

- All members have original category identity and resolved API identity stored
  separately; original SHA-1 and downloaded byte SHA-256 are never conflated.
- Raw rights/API response evidence and file-specific credits retained; unknown
  facts remain null. Missing evidence produces explicit pending/blocking status.
- Download URLs are API-returned. Actual dimensions, format, bytes, and
  acquisition rendition/original distinction are recorded; no local conversion.
- Each completed acquisition has a transfer receipt, byte hash, and full decode;
  cached files are checked. Errors stop further requests until acknowledged;
  partial bodies and diagnostics remain preserved.
- Previous-heap identity overlaps and known related captures may be noted, but
  **must not remove an in-scope file** under this exact-category instruction.

## Published fixture

- Exactly one peer leaf: `Heaps/Curatorial/Evan-Amos-Uploads/`, not sibling
  contributions by device, console, photographer, file type, or view.
- Every `images/` entry maps to one included acquired File identity, and its
  `sources/` copy has the same bytes and hash. An included file not yet acquired
  stays in the inventory with its pending/blocked reason.
- `manifest.json` kind `curatorial_heap`; input relation
  `curatorial_selected`; source/manifest CSVs and hashes agree; pair expectations
  and known-shift families are empty. Source/image bytes stay Git-ignored.
- `complete` is allowed **only when all included file pages are acquired and
  validated**, without outstanding acquisition/rights/identity blockers.
  Otherwise report `partial` or `blocked` with exact IDs; do not substitute
  other Commons files, abandon under a 30-image rule, or report the count as
  a selection cutoff.
- Run the leaf's offline checker, relevant acquisition tests, and existing
  Curatorial validation checks; record failures and their coverage honestly.
