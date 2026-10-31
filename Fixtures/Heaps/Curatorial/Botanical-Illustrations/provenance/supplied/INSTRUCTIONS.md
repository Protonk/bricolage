# Intake procedure — Botanical illustrations (~150)

## 1. Freeze the Commons population

Use `PETSCAN_QUERY.json`: Commons (`project=wikimedia`, `language=commons`), category `Botanical illustrations`, **depth 0**, File namespace 6, enough output capacity to retrieve the **full** direct category. Do not recursively walk category descendants or add other categories. Preserve the exact executed parameters/URL, PetScan query ID if provided, UTC timestamp, original response bytes, response SHA-256, result count, and every returned row. Record raw titles and File-page identities; resolve canonical titles and redirects while retaining the originals. Detect pagination, missing rows, duplicate page IDs, and truncation. If PetScan is inaccessible, preserve diagnostics and stop instead of substituting an unapproved crawl.

The category page showed 659 direct files during scouting, but that is neither an inventory commitment nor a claim about eligibility. Whatever PetScan actually returns becomes the frozen population. If the size differs, document it rather than trying to manufacture a familiar count. A later expansion to depth 1+ is a **new deliberate scope decision**, not a repair performed silently during selection.

## 2. Use one deterministic, auditable selection

Build `inventory.json` from the frozen export, preserving source rows and the snapshot digest. Assign stable candidate IDs from a documented hash of the frozen Commons File title (or stable returned page ID when present); verify uniqueness and preserve aliases. Follow POTY's replayable scheme: an explicitly fixed seed (suggest `hazy-botanical-illustrations-direct-v1`) and ascending SHA-256 of `seed + LF + candidate_id` with an ID tie-breaker. Put the entire order and its algorithm in `ordering.json`.

Walk that order, considering candidates until about **150 eligible, distinct works/plates** are selected or the population is exhausted. Save every examined rank, decision, explicit exclusion reason, duplicate/conflicting ID where relevant, selected IDs, unused reserve, and unresolved candidates in `selection.json`. A disqualified candidate advances to the next ranked one; failed acquisition does **not** alter the selected set. Do not reroll, manually balance colors or flowers, or impose quotas by illustrator, genus, medium, century, or source book. Record creator/work concentration rather than covertly correcting it.

### What qualifies

An individual single-image botanical illustration depicting plant form, structures, or a botanical subject: e.g. scientific plate, engraving, watercolor, lithograph, line drawing, horticultural plate, or another documented illustration. Botanical illustrations involving fungi are eligible if within the frozen source category; there is no need to impose a modern taxonomic definition retroactively. Lettering, captions, plate numbers, and paper margins are part of the image, not defects to crop away.

Exclude clear non-illustrations (ordinary plant photographs, portraits of illustrators, books or title pages without a substantive plant figure, unrelated decorative scenes), corrupt/unsupported inputs, and alternative scans, sizes, crops, recolorings, or reproductions of a **previously selected plate/artwork**. Distinct plates from one book or by one artist **may** both be selected. A repeated species is not itself a duplicate; different engravings of the same plant are allowed. Resolve suspected same-plate cases from file metadata and actual previews where available, keeping a note of uncertainties. This is an identity/scope check, **not** an aesthetic visual acceptance test. Do not use hazy channel scores, perceptual-hash thresholds, or invented similarity labels to choose images.

Do **not** copy POTY's one-image-per-original-creator cap: it would distort a corpus of historical plates, where an illustrator, engraver, publisher, or institution may appear many times. Record artist, engraver/lithographer, publisher, digitizing source, and uploader separately when reported. Null is appropriate when evidence does not distinguish roles.

## 3. Source provenance and rights

Cache file-specific Commons page data and `imageinfo`/`extmetadata` responses: exact and canonical titles, page ID, original SHA-1, timestamp, MIME, dimensions, URL, artist/credit/attribution and license claims. Include file-page revision or source-work/plate identifiers when obtainable. Never infer an original artist from the uploader, a digitization repository, a copyright template, or the title alone. Different scan dimensions or file hashes do not establish different artworks.

Retain raw file-page evidence and identify duplicate plates, alternate editions/images, and derivative scans where reasonably apparent. For a reprint or altered plate, document whether it is actually a distinct work; if uncertain, mark it for review and advance. A public-domain statement can legitimately lack `LicenseUrl`; do not invent links or automatically reject it. Preserve the source's rights statements and doubts without claiming a collection-wide license. Check available earlier fixture inventories for exact title/page ID/original SHA-1/acquired-byte hash matches (including `source_sha256`, title-in-`subject`, and `curid=` URLs); record scope and limitations. A no-collision result is not proof of upstream independence.

## 4. Acquire conservatively

Adapt the active POTY serial transport: truthful User-Agent, `maxlag=5`, paced/cached API requests, a one-image pilot, small bounded chunks, no concurrent crawling, redirects, invented CDN URLs, automatic retries or evasive identity changes. Use only Commons API-returned rendition URLs. Preserve exact requests and replies, and keep media and metadata caches independent of selection.

Aim for a **nominal 1600px longest edge** without cropping, local resizing, conversion, or re-encoding. Preserve the downloaded framing and color. Fully decode and hash source media before calling it complete; record requested and API-reported dimensions separately from decoded dimensions, MIME/format, URL, byte count and SHA-256. Use explicit smaller API requests (such as 1280px) when Commons offers an oversized unscaled original, preserving both size-specific API replies. Do not fetch huge originals just to reduce them locally.

If upstream original is SVG, an **API-served PNG rendition** can be the preserved source; retain SVG original identity/SHA-1/MIME and PNG acquired-byte hash/format distinctly. For multipage PDF/DjVu books, do not arbitrarily render or extract a page: those are not single-plate inputs for this pass unless a standalone Commons File-page image for the plate is available. Ordinary JPEG/PNG/TIFF/WebP artwork is fine where supported and fully decodable. Never collapse a transparent raster onto a new background for comparison input; contact sheets may use a display background only.

On HTTP 403/429/503/529, JSON `error`/`maxlag` inside HTTP 200, unexpected redirect, incomplete HTTP 200 body, cache corruption, decode failure or other transport problem: stop; save status, headers, bytes, partials, and an error latch; require *diagnosis and explicit acknowledgement* for resumption. No automatic retry. Preserve `selected`, `acquired`, `pending`, and `unavailable_rendition` as separate facts. Acquired bytes live in `sources/`, preview tiles/contact sheets/partial media in `previews/`, and raw API/rights/logs/diagnostics in `provenance/`.

## 5. Integrate ONE leaf

Publish **only** `Fixtures/Heaps/Curatorial/Botanical-Illustrations/` directly under Curatorial; do not create `Artists/`, `Books/`, `Flowers/`, `Centuries/`, or other sub-fixtures. If work/source/taxon information is useful, retain it as provenance metadata, not fixture membership. One leaf owns:

- `inventory.json`, `ordering.json`, `selection.json`, a short README, tools/tests and provenance receipts;
- `images/` (opaque manifest-listed comparison inputs), `sources/` (unchanged acquired rendition bytes), `previews/` and `provenance/`;
- `manifest.json`, `manifest.csv`, `sources.csv`, `SOURCES.md`, `SHA256SUMS.txt`, `batches/`, header-only `probes.csv`, and `selections.json` with **zero expected pairs**.

Use `kind=curatorial_heap`, `relation_kind=curatorial_selected`, no `prompt.json`, no inferred `scene_id` relationships. Derive opaque input names from stable source identity; copied input bytes must equal their preserved `sources/` counterparts. Build in a fresh stage, validate offline, and refuse silent overwrites. Update `Fixtures/Heaps/Curatorial/README.md` and relevant indexes with accurate selected/acquired/pending counts. Images and archives remain Git-ignored, while text, code, tests and evidence can be committed locally. Do not modify the router or comparison implementation.
