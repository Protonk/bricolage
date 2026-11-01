# CR01 — Cool, repetitive rectangles

Photographs dominated by repeated rectangular cells, panels, frames or modules.

Fixture ID: `hazy-cr01-v1`; kind: `prompt_heap`.
<!-- collection-totals:start -->
The manifest lists **57 active inputs**. [All collection totals](../../../COLLECTIONS.md).
<!-- collection-totals:end -->

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/CR01/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/CR01/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Original publication and acquisition records

Integrated: **57 inputs from 168 supplied leads**. All 168 acquired previews were
inspected: 57 accepted, 109 rejected and two deferred for possible source
relationships. All accepted sources were acquired; none remain pending. This is
within the supplied 50–80 planning range, below the approximate target of 65.
The original sourcing pack is preserved unchanged in `provenance/supplied/`.

> Photographs dominated by repeated rectangular cells, panels, frames or modules,
> often in muted blues, grays and greens. The pictured subjects may differ.

CR01 is a contribution to the [Similarity heap](../README.md), using the existing
`prompt_heap` kind. Perspective, uneven or interrupted repetition, nested cells,
some surrounding context and modest warm accents are allowed. Known derivatives,
related captures, synthetic imagery, single-box/window portraits and incidental
grids are excluded. Selection uses actual thumbnail appearance and written
judgment. Discovery buckets are search aids, not expected clusters or pair
correctness labels. Only `images/` belongs to the comparison input pool.

### Review and provenance

`provenance/intake/candidates.jsonl` is canonical; CSV contains the union of its fields. Stable
candidate IDs, original titles, discovery URLs and supplied fields are retained.
Initial `candidate_basis` text records discovery-era uncertainty; current
judgments live in `screening_status`, `visual_reason` and the review log. Visual
acceptance and acquisition status are independent facts.

[Visual review](provenance/visual-review.json) records decisions from actual
previews. [Source review](provenance/source-review.json) records file-specific
rights evidence and possible source relationships. It excludes the related
Paulista facade and paired library view, and defers one Bonn building and one
Northwestern school hallway. Repeated creators and possible wider numbered
series are documented. `source_independence_confirmed` remains null; differences
in names, dates and hashes do not prove independence.

The [identity audit](provenance/identity-audit.json) compares available titles,
Commons page IDs, original SHA-1s and acquired byte hashes against all six prior
local fixture inventories, containing 382 inputs. No exact reuse was found. This
is not an exhaustive investigation of upstream capture relationships.

[SOURCES.md](SOURCES.md) retains individual creators, Commons file pages, terms
URLs where supplied, and actual acquired-byte hashes. Raw API responses remain
in `provenance/api/`. These record Commons rights statements; the collection
assigns no new license. The sourcing runtime's original DNS failure and three
textual file-page observations remain separate from the successful local
preview/source requests.

The [acquisition receipt](provenance/acquisition.json) records 450 complete
responses, no transport failures and no automatic retries. All 57 sources used
the nominal 1600px request: 50 API-returned renditions and seven API-reported
unscaled originals within the bound. No smaller-rendition requests were needed.

### Files and checks

- `images/` has opaque flat filenames, byte-identical to the preserved downloads
  in `sources/`. No local cropping, resizing or re-encoding is applied.
- Manifests, `sources.csv` and `SHA256SUMS.txt` record source mapping, decoded
  dimensions and source/input hashes. `batches/batch-1.txt` lists every input.
- `provenance/intake/prompt.json` records intent and counts. `probes.csv` is header-only and
  `selections.json` has no expected pairs.
- `previews/tiles/` and nine `previews/contact-NN.jpg` sheets retain all candidate
  evidence. Three `previews/selected-NN.jpg` sheets show acquired inputs.
- `provenance/` holds transport logs, reviews, the identity audit, import map,
  final visual review and integration receipt.
- `previews/hazy-cr01-v1.zip` is the local archive of inputs, sources, preview
  evidence, metadata, credits and tools. Media and archives remain Git-ignored;
  a checkout alone does not contain them.

From the repository root, using Python with the pinned Pillow dependency:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/CR01/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/CR01/tools/integrate.py check
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/CR01/tools/check_pack.py
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Similarity/CR01/tools -p 'test_*.py'
```

The integration checker verifies hashes, decoded sizes, CSV/JSON agreement,
review and rights evidence, supplied fields, transfer receipts, batch coverage
and empty pair expectations. Missing or changed acquired files fail visibly.
`check_pack.py` separately verifies the unchanged original handoff, whose counts
are historical. The shared relationship checker does not support
`prompt_heap`; CR01 uses its local checker. `tools/audit.py` refreshes the identity
audit when the six prior fixture inventories are available.

### Acquisition tools

Seven generic helpers were copied from active [PS01 tools](../PS01/tools/acquire.py),
verified against the Git blob hashes pinned in `provenance/baseline.json`.
`tools/prepare.py --check-only` verifies that baseline without copying. CR01's
`audit.py` and `integrate.py` were adapted for its identity, prompt and all six
prior fixture inventories. Archived scripts under `provenance/supplied/` retain
the handoff; they are not the active downloader baseline.

Acquisition used a one-preview pilot, paced serial chunks of twelve, visual and
source review, then a separate one-source pilot. Requests use
`HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib`, `maxlag=5`,
at least three seconds after each request, cached metadata and hash-checked
media. Only API-returned media URLs are used. There are no automatic retries
or HTTP redirects. Source acquisition requires visual, license and provenance
review and an unchanged upstream source identity and license statement.

Requested 320px preview and usually 1600px source edges are nominal; actual
API-reported and decoded sizes are recorded separately. Unscaled originals must
fit the requested bound. Larger originals never serve as fallback for missing
renditions. A deliberately requested 1280px API rendition can be considered when
needed, retaining each size's metadata separately.

HTTP/API errors, incomplete bodies and decoding failures stop the run and leave
a persistent error record. HTTP 200 alone does not mean success. A later attempt
requires diagnosis and explicit acknowledgement, preserving the previous error.
Acquisition and review share a local lock. Valid cached files are reused.

Further downloads do not silently update published inputs: the checker reports
a catalog/import mismatch. Integration builds in a new
`previews/integration-NAME` stage and publication refuses existing outputs.
No similarity scores were used to select these images.
