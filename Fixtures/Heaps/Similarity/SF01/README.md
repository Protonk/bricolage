# SF01 — Speckled Fields

## Purpose and basis

SF01 speckled-fields: photographs with many small separated marks/objects over a continuous visual field. Visual curation, no pair or membership ground truth.
Fixture ID: `hazy-sf01-v1`; kind: `prompt_heap`.

## Completeness

The published manifest contains **48 inputs**. The detailed record below
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
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/SF01/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/SF01/tools/check.py
```

The check is offline and includes the shared layout check and the existing
specialized validators. `--metadata-only` omits media and specialized checks.

## Limitations

Selection and source relationships retain their recorded scope; they are not
similarity scores or additional matching assertions. Technical/provenance
uncertainties and partial acquisitions remain documented below.

## Detailed record

**48 acquired photographs are integrated**, from **59 visual selections** among
142 supplied Commons leads (**59 accept, 82 reject, 1 defer**). All 142 previews
were inspected and have written decisions. **11 selected images await acquisition.**
The acquired count is below the preferred 50–80 range and the approximate target
of 65; the set was not padded.

Acquisition stopped on `sf-0111`: Commons returned HTTP 200 headers, then the image
body read timed out. No access/rate-limit status or `Retry-After` was received.
The cause is unproven; these diagnostics cannot distinguish machine sleep, local
connectivity and remote delivery. No retry was attempted. The stop record remains
active and blocks further requests. See `provenance/acquisition.json` for the exact
pending IDs and `provenance/last_transport_error.json` for diagnostics. Downloads
followed candidate order, so the missing tail reflects the interruption, not
additional visual rejections.

This adds `speckled-fields` to the existing `prompt_heap` fixture type. It is a
curated input heap, with no expected pairs, membership truth or semantic cluster
labels. Only `images/` is comparison input. The experiment's pair-fixture checker
does not support `prompt_heap`; use the fixture-local checker below.

> Photographs filled with many small, separated marks or objects distributed
> across a relatively continuous visual field. At thumbnail scale, the images
> look speckled, dotted, scattered, or lightly stippled, even when the individual
> marks depict entirely different things.

The selection allows sparse or dense marks, regular or irregular spacing,
different colors, subjects and scales. It excludes known related captures,
non-photographs, fabricated patterns, and compositions dominated by a single
foreground object. No numerical similarity score was used. The inherited
candidate `family` field is a **discovery bucket**, not a source family or an
expected cluster; opaque manifest family IDs identify individual acquired sources.

### What was reviewed

All 142 actual preview files were inspected on contact sheets. Decisions and
short reasons are in `provenance/visual-review.json`, `provenance/reviews.csv`,
and the canonical `provenance/intake/candidates.jsonl`; `provenance/intake/candidates.csv` is generated from JSONL.
The catalog retains every supplied field. Discovery-era `candidate_basis` text
is historical; current decisions live in `screening_status` and `visual_reason`.

One Moucha Island bird photograph (`sf-0024`) is deferred because another selected
photograph (`sf-0036`) shares its photographer, location and reported day. Other
possible relationships, repeated creators and file-specific license evidence are
recorded in `provenance/source-review.json`. The source audit compares available
Commons titles, page IDs, original SHA-1s and acquired byte hashes with the four
existing local fixture inventories (276 comparison inputs). No exact reuse was
found. See `provenance/identity-audit.json` for coverage and limits.

These checks do **not** establish exhaustive capture independence. Different
filenames, dates and photographers are not proof; `source_independence_confirmed`
remains null. Credits and rights come from each file's preserved Commons metadata,
with terms links where supplied, in [SOURCES.md](SOURCES.md). Unknown creators stay
null. The collection assigns no new license.

### Local contents and validation

- `images/`: opaque, flat comparison inputs, byte-identical to their `sources/`
  downloads (36 renditions and 12 API-reported unscaled originals). They are not locally resized, cropped or re-encoded.
- `manifest.json`, `manifest.csv`, `sources.csv`, `SHA256SUMS.txt`: the shared
  fixture columns, source mapping, actual decoded dimensions and byte checksums.
- `provenance/intake/prompt.json`, `batches/batch-1.txt`: the prompt and one complete input batch.
  `probes.csv` is header-only; `selections.json` has no expected pairs.
- `previews/tiles/`, `previews/contact-NN.jpg`: all candidate preview evidence.
  `previews/selected-NN.jpg` shows the final acquired inputs.
- `provenance/api/`, `provenance/http_log.jsonl`: cached metadata and request
  receipts, including URLs, response status, headers, bytes and hashes.
- `provenance/import-map.json`: the 48 acquired catalog snapshots with final
  input paths. `acquisition.json` records the stopped acquisition and 11 pending
  selections; `integration.json` and `archive.json` validate the acquired subset.
- `previews/hazy-sf01-v1.zip`: local handoff containing source/input bytes,
  preview evidence, metadata, credits and tools. Image and archive files are
  Git-ignored; a checkout alone does not contain them.

From the repository root, with Pillow installed in the chosen Python environment:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/SF01/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/SF01/tools/integrate.py check
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Similarity/SF01/tools -p 'test_*.py'
```

The check is offline. It verifies all source/input hashes, dimensions, CSV/JSON
agreement, batch coverage, empty pair expectations, all 142 preview hashes,
review coverage, retained supplied fields, license evidence and the correspondence
between acquired candidates and final inputs. The 11 pending selections must
agree with the preserved stop receipt; they are never treated as acquired inputs.
Missing or changed acquired assets fail visibly. `tools/audit.py` refreshes the separate cross-fixture identity audit when
all four prior inventories are locally available; it performs no downloads.

### Acquisition record and resumption

The supplied discovery pack had no media bytes and recorded a DNS failure in its
own environment. Its original README, instructions, catalog and scripts remain
under `provenance/supplied/`; `provenance/transport_probe.json` retains that earlier
failure. Current local request outcomes are recorded separately in `http_log.jsonl`.
The original `acquired/` placeholder is preserved only in `provenance/supplied/`. Downloads go to
`sources/`, and temporary media stays under `previews/`, as required by hazy.

Local acquisition started with one preview, then serial chunks of twelve. After
visual, rights and source review, one accepted rendition was piloted before the
remaining chunks. The client identifies itself as
`HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib`, waits at least
three seconds after each request, uses `maxlag=5`, caches metadata and verified
media, and follows only API-returned Wikimedia URLs. It makes no automatic retry.

The requests ask for approximately 320px previews and a nominal 1600px maximum
edge for accepted images. Commons may return a different rendition size; actual
stored dimensions are authoritative. The client checks decoded images, bounds
response size, refuses oversized-original fallback, and stops if upstream source
bytes changed after preview review. Only accepted images with recorded license
and provenance reviews can enter the image phase.

If a run is interrupted without a recorded failure, the same command hash-checks
and reuses valid local files. An HTTP/transport/API error stops acquisition, saves
status, relevant headers (including `Retry-After` when present) and diagnostics,
and leaves `provenance/last_transport_error.json`. That latch blocks subsequent
requests until the failure has been diagnosed. Do not automatically delete it,
retry a block, change identities to evade it, or run parallel clients.

After the recorded failure has been diagnosed and a restart deliberately chosen,
the existing commands are (from the repository root):

```sh
export HAZY_USER_AGENT='HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib'
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/SF01/tools/acquire.py --stage preview --limit 12
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/SF01/tools/acquire.py --stage image --limit 12
```

The current failure latch intentionally prevents both commands from issuing
requests. With no unresolved failure, an already complete stage reuses its files
without fetching media again. Additional downloads do not silently rewrite the
published 48-input snapshot; its checker reports any catalog/import mismatch.
Do not rerun `seed.py` or `flag_provenance.py` over this reviewed catalog: they
are retained one-time discovery recipes. Rebuilding uses a fresh staging name:
`tools/integrate.py build --stage NAME`; publication refuses existing outputs.

### Guidance for another addition

The supplied [provenance/intake/HEAP_INSTRUCTIONS.md](provenance/intake/HEAP_INSTRUCTIONS.md) made the handoff clear:
keep stable IDs, exact Commons titles, canonical JSONL, explicit unknowns, and
honest separation between leads and viewed selections. Continue that contract.

Two packaging adjustments avoid local repairs: put acquired bytes in `sources/`
and partial media in `previews/`; generate CSV columns from the union of JSONL
fields, since API enrichment adds fields incrementally. Include reviewed preview
bytes when transport permits; when it does not, preserve the failure and leave
leads pending. Retain actual rendition dimensions and a persistent stop record
for errors. The local tools demonstrate these changes; the original supplied
scripts remain available for comparison. Opaque input names and final manifests
remain the local integrator's responsibility.
