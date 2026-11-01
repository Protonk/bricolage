# PS01 — Pale skies, dark lower halves

Photographs with pale, quiet skies above darker, detailed lower regions.

Fixture ID: `hazy-ps01-v1`; kind: `prompt_heap`.
<!-- collection-totals:start -->
The manifest lists **58 active inputs**. [All collection totals](../../../COLLECTIONS.md).
<!-- collection-totals:end -->

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/PS01/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/PS01/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Original publication and acquisition records

Integrated: **58 inputs from 145 supplied leads**. All 145 previews were inspected:
58 accepted, 85 rejected and two deferred for possible source relationships.
All accepted sources were acquired; none remain pending. The 58 inputs fall within
the supplied planning range of 50–80, below the approximate target of 65.
The supplied discovery pack and its original checksum file are preserved unchanged
under `provenance/supplied/`.

> Photographs with a comparatively pale, broadly continuous sky occupying a
> substantial upper region and a darker, more detailed or silhouetted lower
> region. Different depicted things can look alike at thumbnail scale.

This is an addition to the existing `prompt_heap` type. Horizon height, boundary
sharpness, fog density, foreground texture and subjects may vary. Slightly blue
or pink-gray skies and layered haze are allowed. Known derivatives, related
captures, synthetic imagery, dominant close subjects and strongly saturated
sun scenes are excluded. Selection uses actual thumbnail appearance and written
judgment, with no numeric similarity threshold or membership ground truth.
The candidate `family` field remains a discovery bucket, not a fixture family or
an expected cluster. Only `images/` is comparison input.

### Review and provenance

`provenance/intake/candidates.jsonl` is canonical; CSV uses the union of its fields. Stable IDs,
original titles, discovery URLs and all supplied fields are retained. Initial
`candidate_basis` text records discovery-era uncertainty; current decisions are
in `screening_status`, `visual_reason` and the review log. Visual acceptance and
transport completion remain independent facts.

`provenance/visual-review.json` records inspection of the acquired previews;
`provenance/source-review.json` retains file-specific rights evidence and notes
about possible source relationships. `source_independence_confirmed` remains
null: different names, authors, dates and hashes cannot prove independence.
The local identity audit checks available titles, Commons IDs, original SHA-1s
and acquired hashes against five prior fixture inventories (324 comparison
inputs). It does not claim a comprehensive upstream capture/series investigation.

Credits and rights are recorded from individual Commons metadata in
[SOURCES.md](SOURCES.md), with raw replies retained. Unknowns remain null. The
collection assigns no new license. The original discovery pack's ten textual
file-page observations and DNS failure remain distinguishable from actual local
API responses and downloads.

The [acquisition receipt](provenance/acquisition.json) records 408 complete
responses, no transport failures and no automatic retries. Two sources needed an
explicit smaller 1280px rendition request after the nominal 1600px request offered
an unscaled original outside that bound. The
[identity audit](provenance/identity-audit.json) found no exact reuse in the five
prior local inventories; possible capture relationships were reviewed separately.

### Contents and checks

- `images/` contains opaque flat filenames, byte-identical to the preserved
  downloads in `sources/`. No local cropping, resizing or re-encoding is applied.
- `manifest.json`, `manifest.csv`, `sources.csv`, `SHA256SUMS.txt` record source
  mapping, actual decoded dimensions and every source/input byte hash.
- `provenance/intake/prompt.json` retains the intent and counts; `batches/batch-1.txt` lists all
  inputs. `probes.csv` is header-only and `selections.json` has no expected pairs.
- `previews/tiles/` and `previews/contact-NN.jpg` retain candidate evidence;
  `previews/selected-NN.jpg` shows the final acquired inputs.
- `provenance/api/` preserves actual API response bytes. `http_log.jsonl`,
  `acquisition.json`, `identity-audit.json`, `import-map.json`, `final-review.json`
  and `integration.json`
  distinguish transport, review, source checks and local integration.
- `previews/hazy-ps01-v1.zip` is the local handoff, including source/input bytes,
  preview evidence, metadata, credits and tools. Media and archives are ignored
  by Git; a checkout alone does not contain them.

From the repository root, using Python with the pinned Pillow dependency:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/PS01/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/PS01/tools/integrate.py check
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Similarity/PS01/tools -p 'test_*.py'
```

The offline checker verifies source/input and preview hashes, measured dimensions,
CSV/JSON agreement, review and license evidence, preserved supplied fields, batch
coverage and empty pair expectations. Missing or changed acquired files fail
visibly. The shared relationship checker does not support
`prompt_heap`; this fixture uses its local checker. `tools/audit.py` refreshes the
cross-fixture identity audit when prior inventories are locally available.

### Acquisition behavior

Acquisition begins with one small preview, then paced serial chunks of twelve;
source acquisition begins with its own one-image pilot after review. Requests use
`HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib`, `maxlag=5`, at
least three seconds after each request, cached metadata and hash-checked media.
There are no automatic retries or redirects. Source downloads require explicit
visual, license and provenance reviews, and an unchanged upstream source hash.

Requested edges of 320px and usually 1600px are nominal. The catalog records
API-reported and decoded dimensions separately, the exact returned URL, byte count, hash and
rendition kind. API-reported unscaled originals must fit the requested bound;
missing renditions never trigger oversized-original fallback. If a nominal
1600px request yields an unscaled original outside that bound, an explicitly
chosen 1280px API request can obtain a smaller rendition. Each requested size has
a distinct metadata cache entry; the catalog records the size actually requested.
Returned renditions are bounded and fully decoded before promotion to a completed file.

An HTTP error, API error, failed body transfer or decoding failure stops the run
and preserves diagnostics in `provenance/last_transport_error.json`. HTTP 200
headers do not mean a completed body. Partial media stays in `previews/partials/`;
partial API JSON stays in `provenance/partials/`. The error latch blocks subsequent
requests until the failure is diagnosed and an explicit restart is chosen;
`--acknowledge-error` preserves the previous error in acknowledgement history.
Neither retries nor acknowledgement are automated.

For deliberately resumed work, the supplied commands remain available:

```sh
export HAZY_USER_AGENT='HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib'
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/PS01/tools/acquire.py --stage preview --limit 12
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/PS01/tools/acquire.py --stage source --limit 12
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/PS01/tools/status.py
```

Valid cached files are reused. Acquisition and review share a local lock to avoid
catalog overwrites. Additional downloads do not silently update a published input
snapshot; the checker reports a catalog/import mismatch. Integration builds in a
new `previews/integration-NAME` stage and publication refuses existing outputs.
The original supplied scripts are retained for comparison with the local fixes.
