# SF01 — Speckled Fields (candidate acquisition pack)

**Target heap:** `prompt_heap` (one new element, **not** a new fixture type).  
**Element label:** `speckled-fields` / `SF01`.  
**Status:** **SOURCE DISCOVERY ONLY**. 142 distinct Wikimedia Commons leads; **0 images visually accepted**, **0 previews or comparison inputs acquired**. Count target ~65 (50–80 acceptable). No claims of independent provenance for these leads.

## Short visual prompt

> Photographs filled with many small, separated marks or objects distributed across a relatively continuous visual field. At thumbnail scale, the images look speckled, dotted, scattered, or lightly stippled, even when the individual marks depict entirely different things.

**Exclusions:** Known derivatives, different views/crops of the same capture, adjacent sequence frames, illustration or fabricated pattern, and images dominated by one large foreground object. No artificial numerical similarity threshold or core/border/outlier labels. Composition, hue, sparsity, density, regularity, orientation, object types, and scale may vary considerably.

**Selection principle:** A loose *visual* resemblance, not species recognition, a semantic cluster, a provenance family, or photographic subject uniformity. Sheep, birds, hay bales, stones, shells, trees, vehicles, boats, and scattered people/umbrellas are **discovery aids only**. The `family` field is inherited from RG01's candidate schema and denotes only a **source-search bucket**, never a fixture family or expected cluster.

## Current evidence and limitations

- Commons category listings and selected individual file pages yielded **142 candidate File: titles** across 17 discovery buckets. Every lead records `commons_title`, `file_page`, `discovery_url`, and a stable `sf-NNNN` candidate ID. URLs are actual Commons file-page identities, not fabricated thumbnail URLs.
- Individual file-page metadata (author, rights shorthand, reported original dimensions) was transcribed from 26 visible Commons pages into records and separately preserved in `provenance/source_page_observations.jsonl`. `provenance/discovery_sources.json` also records 52 discovery URLs and lead counts. All other unknown fields remain `null`, including original dimensions for unexamined pages, rights information, thumbnail dimensions, acquired URLs, and image hashes.
- **No actual thumbnails were viewable in this environment.** Wikimedia hosts could not be resolved from the local acquisition runtime; this happened before an HTTP status could be returned. The web-page browsing tool could inspect Commons HTML but could not fetch media bytes. Thus, no `accept`, `reject`, or `defer` *visual judgment* has been made. Every record remains `pending_visual_review`; this is a source pool, not a finished heap addition.
- Suspected related captures or site overlaps are flagged as *uncertainty*, not proof of dependence. The final local heap inventory was not supplied and the GitHub `main` branch does not include it; cross-addition checks must occur locally before accepting the final set.
- No file has been licensed merely because Commons hosts it. Verify per-file terms in the preserved MediaWiki API `extmetadata` before reuse. This matters especially when delivering transformed copies elsewhere.

## Pack layout

```text
README.md                      This record of intent, gaps and workflow
HEAP_INSTRUCTIONS.md           Reusable acquisition contract (integrates local-agent feedback)
candidates.jsonl               Canonical records; inherits RG01 fields
candidates.csv                 Generated directly from JSONL, not separately edited
previews/README.md             Previews/contact sheets will be written here
previews/tiles/                Acquired 320px previews (currently empty)
previews/contact-NN.jpg        Actual contact sheets when previews exist
provenance/review_template.csv  Blank accept/reject/defer decisions worksheet
provenance/transport_probe.json Local network failure evidence
provenance/source_page_observations.jsonl 26 observed file-page metadata entries, not raw API replies
provenance/discovery_sources.json  52 source URLs and source-bucket lead counts
provenance/http_log.jsonl      Populated by downloader if local run is performed
provenance/api/*.json          Raw Commons API replies, created per request
provenance/last_transport_error.json  Persisted last fetch error if any
acquired/                      Reduced source bytes after visual acceptance (currently empty)
tools/acquire.py               Single-request-first, paced/cached API downloader
tools/review.py                Apply visual decisions; never auto-label
requirements.txt               Python dependencies
```

## Local workflow

Run these commands from **inside this extracted package**. These do not touch Git, change hazy's fixture type, or assign final opaque input names.

```bash
python3 -m pip install -r requirements.txt
# Supply your own truthful client identification with a contact method.
export HAZY_USER_AGENT='hazy-heap/0.1 (contact: YOUR_REAL_CONTACT_EMAIL_OR_URL)'
# First: exactly one candidate; do NOT start with 142 downloads.
python3 tools/acquire.py --stage preview --limit 1
# Inspect provenance/http_log.jsonl, the acquired tile and its decoded dimensions.
# If clean, use additional modest, paced chunks (skips cached files):
python3 tools/acquire.py --stage preview --limit 12
# Repeat chunks only while transport remains healthy.
python3 tools/acquire.py --stage contact
# Inspect previews/contact-*.jpg. Edit provenance/review_template.csv
# with accept/reject/defer, each accompanied by a short visual_reason.
python3 tools/review.py --apply provenance/review_template.csv
# After verifying independent captures and per-file licenses, acquire accepted files.
python3 tools/acquire.py --stage image --limit 1
# Confirm actual max dimension and errors, then resume in modest chunks.
python3 tools/acquire.py --stage image --limit 12
```

- The API returns the **rendition URL** (`thumburl`). The downloader does **not** construct a CDN URL and never falls back to an oversized original image if a thumb is absent.
- It asks for a ~320px preview or a nominal max 1600px accepted rendition. The renderer may provide a different actual size, e.g. 1920px. The script **records decoded actual dimensions** and original bytes, without recropping, re-encoding or resizing them.
- All requests are serial, at least 1.8 seconds apart by default, with caching. Any HTTP/transport error stops the run immediately without retry. For 429/503/529 or similar, inspect `provenance/last_transport_error.json`; respect `Retry-After` externally. **Don't evade blocks by switching identities or sending parallel requests.** Do not put account passwords in this package.
- `candidates.jsonl` is canonical. Both `tools/acquire.py` and `tools/review.py` rewrite the CSV from the same records. Do not run `tools/seed.py` after recording review decisions; it is retained as the one-time seed recipe, not a merge tool.
- Local integration assigns opaque input names, batches and final manifests/checksums **after** acquisition. The original `File:` titles and credits remain in `provenance/`, not in comparison-facing names. Image files should be installed under the fixture's Git-ignored `images/`/`sources/` paths according to local conventions.

## Candidate pool vs. accepted set

**142** is the number of unique **leads**, not 142 suitable images. Do not declare completion until thumbnails have been inspected and provenance has been checked. If there are only 25–45 suitable independent images, report that number and preserve a shortfall; do not pad with same-series photographs or weaker scenes simply to meet 65.
