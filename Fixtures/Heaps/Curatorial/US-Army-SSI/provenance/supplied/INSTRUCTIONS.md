# Intake procedure

## 1. Freeze one source population

Use the PetScan scope in `PETSCAN_QUERY.json`: Commons, File namespace, `Shoulder Sleeve Insignia of the United States Army (SSI)`, depth 5 including descendants. Export the **entire** result set once in a machine-readable format (prefer PetScan JSON; CSV is acceptable if faithful), with an output limit high enough to avoid truncation. The prior user-visible result was **1,641 items**, not an independently verified immutable count.

Preserve the **raw PetScan response bytes**, full executed URL/parameters, query ID if available, acquisition time, SHA-256, result count, and all returned rows. Distinguish total listings from unique File-page IDs/titles, redirects, and actual distinct *insignia designs*. Verify no page cap or incomplete export. A changed result count is evidence to report, not a reason to silently alter depth or query scope.

Use PetScan's server-side descendant query; **do not walk the 17+ category branches recursively through the Commons API**. File-specific Commons API metadata queries are fine after the snapshot, using conservative batches and caches. If PetScan is unavailable, preserve diagnostics and stop; request the exported result file rather than substituting a high-volume crawl without approval.

## 2. Make selection mechanical and reproducible

Create one complete `inventory.json` covering every exported File-page identity. Retain original PetScan titles/IDs and associated metadata without imposing subject subdivisions. Resolve redirects to Commons canonical titles while preserving supplied titles and page IDs. A stable candidate ID can follow POTY's model, for example the first 20 hex characters of SHA-256(`hazy-ssi-file-v1` + LF + *frozen File title*); check for collisions and never recompute old IDs after a rename. Record the ID derivation exactly.

Choose a fixed seed, e.g. `hazy-us-army-ssi-petscan-depth5-v1`, and sort candidates by ascending SHA-256(seed + LF + candidate ID), with ID as a tie-breaker. Record the seed, exact bytes/normalization, algorithm, sorted full ID list and snapshot hash in `ordering.json`. No rerolls, visual balancing, unit quotas or intentional mix of colors, eras, design shapes, media types or ranks.

Walk the order until **200 eligible, distinct insignia designs** have been selected or the snapshot has been exhausted. Keep the complete ledger (`selection.json`) with inspected rank, decision, reason, conflicting design/source if any, selected IDs, omitted reserve and outstanding cases. A file that is excluded advances to the next ID. Transport errors instead stop the run and preserve the *current selection*; they must not silently change it.

### Eligibility and design identity

Include file pages representing a U.S. Army shoulder-sleeve insignia design. A source may be a raster illustration, an SVG original served as an API-provided raster rendition, or a photograph of an embroidered patch; **do not divide the population by depiction medium**. Keep the form of each selected image as acquired.

Exclude demonstrably out-of-scope files, repeated resolutions/rasterizations/photographs of a **previously selected insignia design**, derivatives/crops of the same design, and documented source identity collisions. Use titles, identifiers, official design descriptions where available, file-page provenance, original SHA-1, and actual preview evidence *only as needed to resolve design identity*. A different Commons title or creator does not establish a different design. Conversely, shared heraldic shapes, motifs, colors, or institutional designers are not grounds for rejecting **different insignia designs**.

Historical redesigns may be distinct designs when documented as such; alternate rendering, embroidery, outline or colorway of effectively the same design should not count twice without a clear record of why it is distinct. Mark uncertain relationships and their evidence explicitly. Do not run hazy's similarity channels or use a numerical perceptual-distance threshold to decide membership.

**Do not apply POTY's one-image-per-original-creator cap.** Army insignia often share institutional attribution and illustrators. Instead record designer/artist (if known), original creator versus digital renderer, uploader, and concentration statistics separately. Unknown creators remain unknown; do not substitute uploaders. The selection is not a competition among creators.

## 3. Rights and identity checks

For each considered source, retain file-specific Commons `imageinfo` evidence (`pageid`, canonical title, original SHA-1/upload timestamp, MIME, dimensions, available rendition URLs and `extmetadata`). Preserve licensing text, attribution, terms URL if supplied, and raw API responses. A public-domain assertion need not have a LicenseUrl; inspect the supplied evidence and do not invent one. Record any separate limitations noted for official military insignia, without claiming a blanket collection license.

Check selected identities against the other local fixture manifests and source catalogs, including canonical and supplied `File:` titles, page IDs, original SHA-1s, byte SHA-256s and `?curid=` file-page URLs. Record comparison coverage and conflicts. An absence of exact matches is not proof of independent design or provenance.

## 4. Acquire conservatively, with SVG support

Adapt POTY's tested transport rather than adding parallel downloads. Identify the client truthfully, use `maxlag=5`, cache the exact API response bodies, request serially with at least three seconds between requests, and begin with one small pilot. No automatic retries, identity rotation, redirects or guessed Wikimedia CDN URLs. Restrict media URLs to **API-returned** URLs.

For a selected **SVG original**, request a Commons-provided PNG thumbnail/rendition through `imageinfo` (`iiurlwidth`/`iiurlheight`); do **not** reject it because the upstream MIME is `image/svg+xml`, nor locally rasterize, resize, crop, composite transparency onto white, or masquerade the PNG as the original SVG bytes. Preserve the distinction:
- Commons original identity and SHA-1: SVG (or other source file) recorded from API.
- Downloaded `sources/` bytes and SHA-256: the actual API-served PNG/JPEG/etc. rendition, with decoded dimensions and format.

For raster originals, likewise prefer a nominal ~1600-pixel-edge rendition; accept an API-reported unscaled original only within the size bound. Compare *actual decoded* dimensions to API-reported display dimensions and record both. If the API offers an oversized original for a nominal request, make an **explicit smaller API request** (e.g. 1280px), preserving both metadata replies and size-specific cache keys. Never manufacture a resized URL or substitute full-resolution originals.

Fully download, decode, hash-check and receipt the bytes before promoting them to `sources/`. Preserve framing, colors, format, and alpha channel. Contact sheets may add a presentation background but must not change comparison inputs.

Stop and retain diagnostic headers, response codes, API error bodies and partial data on HTTP 403/429/503/529, an API `error`/`maxlag` under HTTP 200, a timed-out HTTP 200 body, unexpected media or decode failure. Separate complete responses from partial transfers. Persist a stop latch; resumption requires diagnosis and explicit acknowledgement, with no automatic retry. Source selection and source acquisition are separate states.

## 5. Integrate one leaf, not sub-heaps

The new `Fixtures/Heaps/Curatorial/US-Army-SSI/` **is itself the only fixture leaf**. It owns:

- `inventory.json`, `ordering.json`, `selection.json`, its README, acquisition/rights/source evidence and validated checks.
- `images/`: only opaque comparison inputs listed in `manifest.json`; `sources/`: byte-identical preserved API-served renditions; `previews/`: optional contact sheets, review evidence, partial media; `provenance/`: API responses, transport and decision logs, selection and source-identity evidence, hashes, and recorded uncertainties.
- `manifest.json`, `manifest.csv`, `sources.csv`, `SOURCES.md`, `SHA256SUMS.txt`, `batches/`, header-only `probes.csv`, and `selections.json` with **zero expected pairs**. All source/input byte copies must match. Keep `scene_id` and inferred similarity relations empty.

Use `kind=curatorial_heap` and `relation_kind=curatorial_selected`; update `Fixtures/Heaps/Curatorial/README.md`, `Fixtures/Heaps/README.md` if necessary, and any relevant index. No change to similarity/router implementation. Keep all images and archives Git-ignored; only textual metadata/tools are committed.

Adapt `POTY/tools/` for one population and one leaf. Tests and output conventions should follow the active repository. Do not copy POTY's three category directories, fixed 50-per-category target, 2023–2025 galleries, or original-creator cap. Preserve the evidence from the exact run (rather than a clean-room substitute for it).

Build/validate in a fresh stage and publish only after checking. Never silently overwrite a prior published set; completed changes should be committed locally per repository instructions, leaving push to the user.
