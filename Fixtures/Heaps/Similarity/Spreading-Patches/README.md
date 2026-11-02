# Spreading-Patches — Blotches, stains, and spreading patches

Photographs of irregular patches that merge or fragment across surfaces,
selected by thumbnail appearance.

Fixture ID: `hazy-bsp01-v1`; kind: `prompt_heap`; folder `BSP01` until November 2026.
<!-- collection-totals:start -->
The manifest lists **68 active inputs**. [All collection totals](../../../COLLECTIONS.md).
<!-- collection-totals:end -->

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/Spreading-Patches/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/Spreading-Patches/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Original publication and acquisition records

**Complete: 68 acquired and validated inputs from 185 supplied Commons leads; no pending downloads.**
All 185 previews were inspected. Of 77 visual fits, seven were excluded as known
or probable related captures and two for unresolved rights: **68 selected,
117 excluded, zero deferred or unreviewed**. This is within the supplied 50–80
planning range and above its hard publication floor of 30; the approximate target
was 65. The prompt was not relaxed or balanced by discovery category.

> Photographs dominated by irregular patches or regions that spread, merge,
> fragment, bleed, peel, or dissolve across a surface or field.

This contributes to the existing [Similarity heap](../README.md). The complete
prompt, exclusions and allowable variation remain in `provenance/intake/prompt.json` and
`provenance/intake/HEAP_INSTRUCTIONS.md`. Discovery categories are sourcing aids. Membership records
visual selection intent, with no expected pairs, semantic groups, matching labels
or router correctness assertions. No router or comparison experiment was run.

### Review and provenance

The unchanged 19-file setup handoff is preserved in `provenance/supplied/`, including
its original checksums. `provenance/intake.json` records those hashes and disposal
of `Fixtures/hazy_bsp01/` after verification. Supplied zero-review counts and the
original DNS probe are historical. Active `provenance/intake/candidates.jsonl` and its union-column
CSV preserve all supplied identities and discovery fields alongside review and
acquisition records.

Actual previews were inspected as a pilot and saved contact sheets. Per-image
reasons appear in `provenance/visual-review.json`, `reviewed.csv`, `review_log.jsonl`
and the exact-sheet `inspection-log.jsonl`. Rejections include isolated objects,
wide scenes, uniform textures, discrete spots and linear structures. No numerical
similarity scores were used. `visually_accepted`, `visual_screening_decision` and
`visual_screening_reason` preserve initial visual fit; `screening_status` records
final eligibility after provenance and rights checks. An acquisition failure cannot
change either decision.

`provenance/relationship-exclusions.json` preserves seven exclusions after visual
acceptance, with initial reasons and hashed preview/API evidence. These include
an apparent alternate treatment of one rusty gate and probable related painted
surface or capture sequences. Probable relationships are identified as such;
they are conservative exclusions, not fabricated matching labels. All seven
supplied sequence questions and additional shared-creator checks are addressed in
`source-review.json`. Photographer reuse alone is not an exclusion in BSP01.

Two rights exclusions retain their evidence in `rights-exclusions.json`: bsp-0080
reports CC BY 2.0 alongside an author prohibition on redistribution; bsp-0141 has
only a generic Attribution marker without sufficient terms in the retained metadata.
Neither source rendition was acquired. File-specific credits and license evidence
for accepted inputs are in `SOURCES.md`, `sources.csv`, `source-review.json` and the
raw API replies. Requested D Sharon Pruitt / Pink Sherbet attribution is retained.

The exact identity audit covers eleven previous contributions and 613 inputs:
all Relationships, five previous Similarity contributions, and three POTY
contributions. It checks available titles, page IDs, original SHA-1s and acquired
SHA-256 hashes. No exact overlaps or duplicate identities were found. These checks
and inspected metadata do not prove complete capture independence; that field
remains null. Commons rights statements are recorded, not independently
authenticated. Individual creators for archive/repository credits (bsp-0018 and
bsp-0105) remain unknown; agency credits are identified as reported organizations.
Unreported capture dates and locations remain unknown, including several imported
public-domain textures. Normal upstream processing is retained as received.

### Acquisition and local assets

Tools derive from the pinned active PS01 baseline, with deliberate TG01 preview-size,
minimum-floor and evidence checks, plus BSP01-specific identities and credit review.
`prepare.py --check-only` verifies the baseline and recorded local adaptations.
No shared fixture format, traversal, router or previous contribution was changed.

The identified HazyFixtureBot client uses MediaWiki `maxlag=5`, serial requests,
at least three-second pacing, cached metadata and only API-returned media URLs.
Each body is fully decoded and checked for dimensions, format, size and SHA-256.
Source bytes are preserved unchanged and copied byte-identically into opaque
`images/` filenames. No local cropping, resizing or re-encoding is applied to inputs.
Nominal source requests target 1600 pixels; actual dimensions are authoritative.
Explicit 1280-pixel source requests were needed for `bsp-0060`, `bsp-0079`, `bsp-0097` after nominal 1600 requests offered oversized unscaled originals. Both metadata responses are retained.
The final set contains 52 API-returned reduced renditions and
16 API-reported unscaled originals. All 511 HTTP requests completed;
there was one separate preview size-validation stop and no automatic retries.

The bsp-0083 nominal 480-pixel preview decoded to 500 × 722, two pixels above the
conservative 720-pixel guard. Acquisition stopped. Its complete 189,675-byte body,
raw response and diagnosis remain in `previews/partials/` and
`provenance/preview-size-diagnosis.json`. After inspection and explicit acknowledgment,
a separate nominal 640-pixel API request accepted the actual 500 × 722 rendition.
Both metadata responses, HTTP receipts and the acknowledgment remain intact;
the size bound was not weakened. The initial pilot requested 320 pixels, later
previews 480 pixels apart from that explicit adjustment.

Only manifest-listed `images/` files are comparison inputs. Sources, 185 preview
tiles, inspected sheets, final selected contact sheets, diagnostic bodies,
integration staging and `previews/hazy-bsp01-v1.zip` remain local and Git-ignored.
The ZIP includes source/input bytes and textual evidence; its checksum is in
`provenance/archive.json`. A checkout alone contains no media.

### Offline checks

From the repository root, with the pinned Pillow requirement installed:

```sh
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/Spreading-Patches/tools/check_pack.py
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/Spreading-Patches/tools/prepare.py --check-only
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/Spreading-Patches/tools/integrate.py check
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/Spreading-Patches/tools/minimum_gate.py --strict-publish
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Similarity/Spreading-Patches/tools -p 'test_*.py'
```

The integration validator checks the publication floor, source/input hashes,
decoded dimensions and orientation, source credits, catalog agreement, preserved
initial visual fits, full review coverage, inspected-sheet hashes, rights and
relationship evidence, HTTP/API receipts, retained failure evidence, batch coverage
and empty pair expectations. `audit.py` refreshes the exact identity audit offline.
All 18 local tests and the five existing Similarity validators passed. The count
gate alone is not a publication validator. The shared relationship checker
does not accept `prompt_heap`; use BSP01's local checker.
