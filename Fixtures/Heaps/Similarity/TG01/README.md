# TG01 — Tangles of growth

## Purpose and basis

TG01 tangles of growth: dense, irregular, interlaced plant growth selected by actual thumbnail appearance. No pair or membership ground truth.
Fixture ID: `hazy-tg01-v1`; kind: `prompt_heap`.

## Completeness

The published manifest contains **31 inputs**. The detailed record below
retains the original selection counts, pending cases and acquisition limitations.
The layout migration changes no membership or completion status.

## Contents

This leaf follows the [shared fixture format](../../../FORMAT.md).
`images/`, `sources/`, `previews/` and `batches/` retain their roles. Live commands
and dependencies are in `tools/`; the [evidence index](provenance/README.md)
locates intake/construction records, receipts and preserved packages.

## Validation

From the repository root, using Python 3.14.x:

```sh
.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/TG01/tools/requirements.txt
.venv/bin/python Fixtures/Heaps/Similarity/TG01/tools/check.py
```

The check is offline and includes the shared layout check and the existing
specialized validators. `--metadata-only` omits media and specialized checks.

## Limitations

Selection and source relationships retain their recorded scope; they are not
similarity scores or additional matching assertions. Technical/provenance
uncertainties and partial acquisitions remain documented below.

## Detailed record

**Complete: 31 acquired and validated inputs from 152 supplied Commons leads; no pending downloads.**
All previews have been inspected. There were 32 visual fits, followed by one
conservative exclusion for a probable related subject: **31 accepted, 121 rejected,
zero deferred or unreviewed**. The resulting selection is below the 50–80 planning
range and approximate target of 65, but above the supplied hard publication floor
of 30. The prompt and exclusions were not relaxed to increase the count.

> Photographs dominated by dense, irregular plant growth in which branches,
> stems, vines, roots, leaves or grasses interweave, overlap and occlude one
> another, confusing the boundaries of individual structures at thumbnail scale.

This is a contribution to the existing [Similarity heap](../README.md).
Discovery categories were sourcing aids. Membership records selection intent,
not semantic groups, matching labels or expected router results. The existing
`prompt_heap` kind, leaf-local paths and empty pair expectations apply. No router
or comparison experiment was run.

### Review and provenance

The unchanged 19-file setup handoff is preserved in `provenance/supplied/`, with
its original package checksums. `provenance/intake.json` records the copy hashes
and setup-folder disposal. The handoff's zero-review counts are historical.
Active `provenance/intake/candidates.jsonl` and its union-column CSV retain all supplied identities,
discovery fields, actual API replies, review decisions and acquisition fields.

Actual previews were inspected, first as a pilot and then on saved contact sheets.
`provenance/visual-review.json`, `reviewed.csv`, `review_log.jsonl` and
`inspection-log.jsonl` record individual decisions and the exact inspected sheets.
Most rejections are isolated trunks, flowers, sparse vines, or scenes dominated
by buildings, paths, open water or horizons. No similarity scores were used.

`provenance/source-review.json` records file-specific rights, creators, uploaders
and relationship checks. The three supplied possible-sequence groups were resolved
without retaining both related views. Additional inspection of tg-0117 and tg-0125
found a probable shared Everglades fig subject; tg-0125 was excluded despite fitting
visually. This is a conservative provenance decision, not a proven capture relation;
its initial visual decision and supporting evidence remain in
`relationship-exclusions.json`.

The identity audit covers ten prior contributions and 582 inputs, including all
Relationships, four earlier Similarity contributions and three POTY contributions.
It compares available exact titles, page IDs, upstream SHA-1s and acquired hashes.
No exact overlaps or duplicate candidate identities were found. Different identities,
dates and photographers do not establish complete independence; that field remains
null. The accepted photographs have no asserted relationships to one another.

Commons rights statements are recorded, not independently authenticated. tg-0109
reports Public domain, `License=pd`, `Copyrighted=False` and no required attribution;
it credits Andrew McMillan and public-domain-image.com but supplies no license URL,
location or capture date. Those fields remain unknown. Credits and license evidence
for every acquired input are in `SOURCES.md`, `sources.csv`, and the raw API replies.

### Acquisition and local assets

The tools derive from the pinned active PS01 baseline, with TG01-specific audit,
integration and floor checks. `prepare.py --check-only` verifies the pinned source
blobs and explicitly recorded local adaptations. No previous contribution's tools
were changed.

Requests identify HazyFixtureBot and its repository contact, use MediaWiki `maxlag=5`,
and run serially with at least three seconds between requests. Only API-returned
media URLs are used. Metadata is cached; downloaded bodies receive a full decode,
dimension, format and SHA-256 check. Source bytes are preserved unchanged and copied
byte-identically into opaque `images/` filenames. Actual decoded sizes, which can
differ from API display sizes, remain authoritative. Source requests target a nominal
1600-pixel edge; no local reframing, resizing or re-encoding is applied. Two files (tg-0093 and tg-0152)
needed explicit 1280-pixel API requests after the nominal request offered oversized
originals; both metadata responses are retained. The final set has 26 API-returned
reduced renditions and five API-reported unscaled originals. All 375 HTTP requests
completed; the three separate preview size-validation stops are described below.

Three preview runs stopped when Commons thumbnail buckets exceeded the conservative
1.5× nominal-edge limit. The complete, decodable bodies for tg-0023, tg-0124 and
tg-0152 remain in `previews/partials/`. Each stop was diagnosed and explicitly
acknowledged before a separate request at 640 or 480 pixels; no automatic retries
or weakened size bounds were used. The original API replies, failed bytes and
acknowledgments remain available. tg-0029 separately received an explicit 320-pixel
request after a 640-pixel request offered an oversized unscaled original, which was
not downloaded. See `preview-size-diagnosis.json`,
`preview-rendition-adjustments.json`, `http_log.jsonl` and `acquisition.json` in
`provenance/`.

Only manifest-listed `images/` files are comparison inputs. Sources, all 152 preview
tiles, inspected contact sheets, selected contact sheets, diagnostic bodies,
integration staging and `previews/hazy-tg01-v1.zip` remain local and Git-ignored.
The ZIP contains the source/input bytes and textual evidence; its checksum is in
`provenance/archive.json`. A checkout alone contains no media.

### Offline checks

From the repository root, with the pinned Pillow requirement installed:

```sh
.venv/bin/python Fixtures/Heaps/Similarity/TG01/tools/check_pack.py
.venv/bin/python Fixtures/Heaps/Similarity/TG01/tools/prepare.py --check-only
.venv/bin/python Fixtures/Heaps/Similarity/TG01/tools/integrate.py check
.venv/bin/python Fixtures/Heaps/Similarity/TG01/tools/minimum_gate.py --strict-publish
.venv/bin/python -m unittest discover -s Fixtures/Heaps/Similarity/TG01/tools -p 'test_*.py'
```

The integration check verifies the publication floor, unchanged source/input hashes,
decoded dimensions, source catalogs, candidate CSV/JSON agreement, review coverage,
inspected sheets, rights evidence, API/HTTP receipts, retained failure evidence,
manifest/import consistency, batch coverage and empty pair expectations. The count
report alone is not a publication validator. `audit.py` refreshes the exact identity
audit against local prior inventories without network access. Existing Similarity
validators were also checked. The experiment's relationship checker does not accept
`prompt_heap`; use TG01's local checker.
