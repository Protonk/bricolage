# PS01 — Pale skies, dark lower halves

**Heap:** existing `prompt_heap`, new loose collection element `pale-skies-dark-lower-halves` (`PS01`). This is a **candidate sourcing package**, not a completed fixture and not a new fixture type.

## Intent

> Photographs with a large, relatively pale and quiet sky in the upper portion, set against a darker and more visually complicated lower portion. The dividing structure may be water, land, trees, buildings, snow-shadow, distant mountains or haze. Different depicted things can look alike at thumbnail scale.

Avoid known derivatives, crops, bursts, sequential captures, illustrations, major foreground subjects obliterating the split, and dramatically saturated sunsets. Accept loose variation in horizon height, weather, texture, temperature, and how abrupt the dark/light boundary appears. **No numerical similarity thresholds or core/border/outlier taxonomy.**

**Target:** around **65 accepted** independent photographs, with 50–80 an acceptable planning range. This is not a quota. Report whatever number survives inspection and provenance checks, even if considerably fewer.

## Status at handoff (2026-10-30)

- **145 unique Commons leads** recorded from actual category listings and individual Commons file pages; 13 search buckets. File titles and discoverer URLs are source identities, not guessed CDN URLs. The search buckets are purely collection aids, not intended clusters.
- **0 visually accepted, 0 rejected, 0 deferred.** All 145 remain `pending_visual_review` because actual Commons preview bytes could not be acquired from this environment. In particular, fog/cloud category membership does **not** establish pale-sky / dark-bottom composition.
- **0 previews acquired, 0 source image bytes acquired, 0 contact sheets generated.** No image is represented as downloaded or inspected. There are 10 independently observed Commons file-page metadata summaries in `provenance/source_page_observations.jsonl`, not API metadata replies.
- The runtime's transport probe failed at DNS lookup (`Temporary failure in name resolution`) before an HTTP status. This does not demonstrate a Wikimedia rate limit, an authentication failure, or a completed image transfer.
- Comparison with the **earlier RG01/SF01 SOURCING lists only** found no exact Commons title overlaps. The *final locally integrated heap inventory was not supplied*; verify against it locally before finalizing. No provenance-independence conclusion was drawn from unmatched names or authors.

## Layout

```text
candidates.jsonl                     Canonical candidate records; preserves the earlier fields
candidates.csv                       Generated from JSONL union of fields
HEAP_INSTRUCTIONS.md                 Updated reusable `prompt_heap` acquisition contract
provenance/discovery_seeds.txt        Exact titles transcribed from actual category and file pages
provenance/discovery_sources.json     Discovery pages and counts
provenance/source_page_observations.jsonl  10 page descriptions; NOT API replies
provenance/prior_seed_overlap.json    Limited RG01/SF01 source-pool title check
provenance/transport_probe.json      DNS diagnostic from this environment
provenance/review_template.csv       Editable visual-review worksheet
provenance/api/                     Raw API responses when locally acquired
provenance/http_log.jsonl            Network log, generated on local acquisition
provenance/last_transport_error.json Error evidence, generated only on failure
provenance/review_log.jsonl          Local visual judgment history
previews/tiles/                      Acquired 320px-ish thumbnails
previews/partials/                   Incomplete downloaded MEDIA (including HTTP-200 body timeout)
previews/contact-NN.jpg             Contact sheets made from actual acquired previews
sources/                            Acquired ~1600px-ish source bytes, no transcoding or cropping
tools/common.py                     Lossless record/CSV and log helpers
tools/acquire.py                    Serial, paced, single-preview-first downloader
tools/review.py                     Explicit preview-based accept/reject/defer; independent of download
tools/status.py                     Show visual and transport counts separately
tools/check_prior.py                Optional cross-heap source check from local inventories
requirements.txt                   Pillow
```

Empty media directories are included as directory entries in the archive. Files named `ps-XXXX` are **candidate IDs**, not final hazy `images/` input names. Local integration assigns opaque comparison-facing names.

## Local procedure

Run from the extracted `hazy_ps01/` directory. Supply your own honest client identity and contact address in the environment; do not put account credentials in this package.

```sh
python3 -m pip install -r requirements.txt
export HAZY_USER_AGENT='hazy-heap/0.1 (your actual contact email or project URL)'
python3 tools/acquire.py --stage preview --limit 1
# Examine previews/tiles, decoded dimensions and provenance/http_log.jsonl.
# On an error, STOP and inspect provenance/last_transport_error.json.
# Resume by explicit invocation with --acknowledge-error only after diagnosing it.
python3 tools/acquire.py --stage preview --limit 12
python3 tools/acquire.py --stage contact
python3 tools/review.py --template
# Visually inspect contact sheets and edit provenance/review_template.csv.
# Only reviewed thumbnails receive decisions and short visual reasons.
python3 tools/review.py --apply provenance/review_template.csv
python3 tools/status.py
# After checking related captures and local prior heap inventory:
python3 tools/check_prior.py --prior /path/to/previous/sources.csv
# Acquire only accepted images. Start with one, then paced batches.
python3 tools/acquire.py --stage source --limit 1
python3 tools/acquire.py --stage source --limit 12
python3 tools/status.py
```

`--limit` counts **new completed image files**, not metadata requests or candidate entries. Cached previews, source bytes and API responses are reused, without repeating downloads. Scripts never decide similarity, automatically accept candidates, or change a visual acceptance after transport failure.

Wikimedia may return a rendition larger than the nominal request (1600px can become e.g. 1920px). The downloader records both API-reported and actually decoded dimensions and distinguishes `api_returned_rendition` from `api_reported_unscaled_original` (only when the reported original itself fits the limit). If a large source has no API-returned rendition URL, it is not downloaded.

When a response supplies HTTP 200 headers but the body read fails, `http_log.jsonl` retains **status=200** with **response_complete=false**, the partial byte count, and partial media under `previews/partials`. There is no automatic retry. API JSON response bytes are preserved under `provenance/api/` if fully acquired; incomplete API bodies belong under `provenance/partials/`.

Acquired file terms remain subject to the individual Commons metadata, and author/credit/license fields stay null until observed. Metadata from 10 file pages is clearly distinguished from downloaded API responses. Never infer missing terms from the Commons hosting domain alone.

The local agent may accept an image visually while it is not acquired; acceptance and acquisition are separate facts. A smaller complete set is preferable to replacing failed downloads with related photographs solely to meet the count.
