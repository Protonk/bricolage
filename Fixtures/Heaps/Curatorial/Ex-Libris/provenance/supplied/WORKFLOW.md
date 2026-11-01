# Workflow — three Curatorial leaves

## 0. Boundaries

- Keep each contribution directly under `Fixtures/Heaps/Curatorial/`; no child contribution folders and no further category branches.
- Preserve the Curatorial selection principle: a frozen published category population + deterministic file ordering + documented, narrow eligibility/repetition decisions.
- Do not apply one-author-per-collection caps, per-category quotas, equal proportions, aesthetics, pHash, Vision features, CLIP or semantic similarity ranking. One person/institution can contribute multiple independent examples.
- Do not impose the 30-image publication floor from the earlier *Similarity* prompt heaps. The ~50 target is approximate. If viable material is exhausted, document the shortfall; don't fabricate eligibility or recruit unrelated files.

## 1. Enumerate and freeze populations

For **each** of the nine exact categories in `CATEGORIES.json`:

- Use the provided `action=query&list=categorymembers&cmtype=file&cmlimit=500` URL. Make serial requests with a truthful User-Agent, `maxlag=5`, conservative pacing and no retries. No recursive descent, no category search, and no PetScan required.
- Preserve *every raw JSON response body*, complete query parameters, execution time, hash, HTTP diagnostic metadata, and `cmcontinue` / `continue` values when present. Explicitly verify the last page has no continuation and there was no API `error`/`warnings` response.
- Each File row must retain its `pageid`, frozen `File:` title and all original category memberships. Union the three lists **within** each leaf and deduplicate by page ID. If the same title maps to different IDs, or one ID has inconsistent titles, flag it rather than silently choosing one.
- Save `inventory.json` containing the complete union and its provenance, including membership lists. Also save the raw category-list exports and a receipt documenting the actual unique count. The previous public category counts are scouting figures, not assertions of fetched totals.
- Avoid reading categorymembers pages via a name-only / text-only guess. Canonical identity at download time is resolved separately and may have changed; keep frozen title and API-resolved title.

## 2. Stable mechanical order

For each leaf `slug` from the catalog, use a documented fixed seed (catalog `seed`) and deterministic ordering:

- candidate ID: first 20 hexadecimal digits of SHA-256(UTF-8(`hazy-curatorial-triplet-v1` + LF + `slug` + LF + exact frozen `File:` title)); keep case, spaces, Unicode and underscore spelling as supplied. Detect ID collisions.
- sort ascending by SHA-256(UTF-8(`seed` + LF + candidate ID)), tie-breaking by candidate ID. Preserve the resulting full candidate-ID list as `ordering.json`, along with seed/algorithm.
- The category memberships do **not** influence ordering or quotas. Record decisions against this fixed order in `selection.json`. Do not reroll to obtain attractive images.
- If a decision is truly uncertain, record `defer` and its reason. Later selections may be provisional, exactly as in the current SSI/Botanical approaches. Never silently transform uncertainty into rejection or substitute an acquisition failure as a new candidate.

## 3. Small thumbnail review, only when useful

Use file-specific Commons API `imageinfo` metadata and bounded, API-returned small previews. Inspect actual preview bytes. Prefer 4-column contact sheets with ~20 candidates per sheet, so a local vision agent can handle short tasks. Use `THUMBNAIL_REVIEW.md` for *scope*, not visual similarity sorting.

- Explicit `accept`, `reject`, or `defer`, one short reason, preview path and SHA-256.
- An obvious category error or a known alternate of the same specimen/artwork can be excluded after checking evidence.
- Do not reject a valid unusual picture merely because it diverges from the most common appearance in its leaf.
- Never infer appearance from filename/category if the preview was not viewed. Unknown remains pending.

## 4. Provenance and rights before acquisition

For proposed selections record Commons page ID, exact/resolved title, original SHA-1 and upload version/timestamp, source page, rights evidence, creator/artist/photographer/scan roles where available, reviewed preview hash, and known alternatives or possible repeated physical specimens/printed works. Keep unknown fields null and raw API/file-page evidence.

Cross-check available earlier Curatorial/Similarity/Relationships inventories by page ID, title/`curid`, original SHA-1, and acquired-byte hashes. Record which inventories and how many records were examined; no exact match is not proof of independence. **Do not automatically omit previously used images unless the commission or explicit provenance rule requires it.** Flag reuse and make a documented inclusion decision.

## 5. Media acquisition

Reuse/adapt current working Commons transport from the repository rather than reimplementing it from this outline:

- One reduced preview pilot, then paced serial cached requests; a separate source pilot after review. Use only API-returned URLs. No local composition changes, cropping, resizing, or re-encoding of source/input media.
- Nominal longest-edge source request ~1600px; actual image dimensions can differ. Record requested size, API-reported size, decoded size, kind (`api_returned_rendition` or `api_reported_unscaled_original`), byte size and SHA-256. Never download an oversized unscaled original as fallback; ask the API separately for a smaller rendition when appropriate. Preserve every distinct size-specific metadata response.
- SVG/TIFF originals: if a suitable **Commons-served raster rendition** is provided, preserve it as the acquired source and retain original MIME/hash identities; do not rasterize locally without a separately documented decision.
- Respect 403/429/503/529, API JSON errors including `maxlag` inside HTTP 200, HTTP 200 truncated/timed-out bodies, unexpected redirects and decoder failures. Preserve error, headers, received byte counts and partial media. Stop without an automatic retry. Explicit diagnosis/acknowledgment is required to resume. Cache entries are hash-checked; serialize catalog writes.
- Successful reduced source bytes go in leaf `sources/`; input copies in `images/` are byte-identical. Preview tiles/contact sheets/partial media in `previews/`; raw JSON/API and evidence in `provenance/`. All media remains Git-ignored as the repository specifies.

## 6. Integrate and publish

For **each** leaf, produce its own `README.md`, `inventory.json`, `ordering.json`, `selection.json`, `manifest.json`, `manifest.csv`, `sources.csv`, `SOURCES.md`, `SHA256SUMS.txt`, `probes.csv`, `selections.json`, batches, provenance and offline validator/tests. Use existing shared columns and `kind=curatorial_heap`, `relation_kind=curatorial_selected`. Pair expectations and known-shift family lists are empty; no `prompt.json` or artificial family labels.

Build to a fresh ignored staging area, run offline validation, and publish without overwriting existing assets. Keep original byte framing. Update the Curatorial/fixture index with actual counts and statuses. Commit code and textual provenance using current AGENTS.md instructions; do not force-add image assets. Leave pushing to the user unless separately requested.
