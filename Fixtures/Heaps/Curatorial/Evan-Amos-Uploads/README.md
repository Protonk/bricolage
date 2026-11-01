# Evan-Amos category uploads

## Purpose and basis

Every frozen direct File member of Media uploaded by Evan Amos except three exact user exclusions; no sampling, deduplication or expected matches.
Fixture ID: `hazy-evan-amos-uploads-v1`; kind: `curatorial_heap`.

## Completeness

The published manifest contains **133 inputs**. The detailed record below
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
.venv/bin/python -m pip install -r Fixtures/Heaps/Curatorial/Evan-Amos-Uploads/tools/requirements.txt
.venv/bin/python Fixtures/Heaps/Curatorial/Evan-Amos-Uploads/tools/check.py
```

The check is offline and includes the shared layout check and the existing
specialized validators. `--metadata-only` omits media and specialized checks.

## Limitations

Selection and source relationships retain their recorded scope; they are not
similarity scores or additional matching assertions. Technical/provenance
uncertainties and partial acquisitions remain documented below.

## Detailed record

One leaf of the [Curatorial heap](../README.md): **every frozen direct File
member** of [Media uploaded by Evan Amos](https://commons.wikimedia.org/wiki/Category:Media_uploaded_by_Evan_Amos),
minus exactly three supplied exclusions. **Complete: all 133 included File pages
are acquired and validated, with zero pending or blocked files.**

| State | Count |
|---|---:|
| Frozen direct File members / metadata-resolved identities | 136 / 136 |
| Exact user exclusions | 3 |
| Included / acquired | 133 / 133 |
| Pending / blocked | 0 / 0 |
| JPEG / PNG inputs | 126 / 7 |
| Failed transfers / retries | 0 / 0 |

The frozen API inventory contains **136 direct File members**, matching the
handoff observation. All three exact titles are present, leaving **133 included**:

- `File:12in-Vinyl-LP-Record-Angle.jpg`
- `File:12in-LP-Vinyl-Record-Macro-Grooves.jpg`
- `File:Apple-iPod-Shuffle-Display.jpg`

Those are the only selection exclusions. Different angles, close-ups, components,
related captures, crops and JPEG/PNG versions remain included. There is no random
sample, creator cap, object-level deduplication, aesthetic review, replacement
selection or minimum-size floor. Technical or rights problems keep the affected
included identity pending or blocked; they do not change membership.

### Population and provenance

`provenance/intake/inventory.json` reconstructs the complete direct category from the raw
`list=categorymembers` response in `provenance/api/`. The query uses the exact
category, `cmtype=file`, `cmprop=ids|title|timestamp`, `cmlimit=max`, `formatversion=2`
and `maxlag=5`. The category request began at 2026-10-31 23:00:52 UTC. Its response contains
all 136 entries and no continuation token.
The client follows any category continuations serially, without treating the
expected count as a cap. No descendant category, user-upload search or PetScan
query was used. Safari was not needed.

Candidate IDs are the first 20 hex characters of SHA-256 over UTF-8
`hazy-evan-amos-file-v1` + LF + frozen page ID + LF + exact category-member title.
The complete order is ascending exact Unicode title, then numeric page ID; it is
an enumeration order, not a sample. `provenance/intake/selection.json` assigns each member exactly
one `included` or `excluded_by_user` outcome. Category membership timestamps are
preserved as such, not treated as capture dates.

All 136 members, including the exclusions, have cached current `imageinfo` and
file-page revision content. Category IDs/titles, resolved IDs/titles, original
file MIME/SHA-1/timestamp, and acquired rendition URL/format/SHA-256 remain separate.
The frozen member identities agree with their API-resolved identities; there are
no redirects or identity discrepancies in this snapshot.

The file-specific Public domain usage claims, `Copyrighted=False` and retained
`PD-self` declarations agree for every member. `provenance/rights-review.json`
replays these checks against the cached evidence. Original creator is attributed
from each file's explicit Author field, not its category or uploader: all 133
included files name Evan-Amos. Two additionally name Gunnar.offel as modifier.
The other files' modifiers and all copyright holders remain unknown. Current
file-version uploaders are recorded separately and include several accounts.
Null license URLs are retained without invented links. Commons claims are
recorded, not independently authenticated; no blanket collection license is asserted.

Explicit related-file links and their raw passages are retained in
`provenance/related-file-evidence.json`; they do not exclude any member or become
expected pairs. The prior-fixture exact-identity audit covers 14 integrated leaves
and 980 inputs, using available titles, page IDs, original SHA-1s and byte hashes.
No exact overlap was found, including after acquired-byte checks. The audit
reports overlaps without removing files. Its scope and limitations are in
`provenance/identity-audit.json`; absence of an exact match cannot prove capture
independence. Historical audit coverage stays fixed when later leaves are added.

The five supplied handoff files are preserved byte-identically under
`provenance/supplied/`, with their hashes and original location in
`provenance/intake.json`. The leaf's `provenance/intake/EXCLUSIONS.txt` is also byte-identical to the
supplied file. The redundant setup folder was removed after verifying all five files against
these preserved copies and hashes; the intake record includes the cleanup receipt.

### Acquisition and fixture records

The transport adapts the active POTY/SSI workflow: truthful HazyFixtureBot
identification, at least three seconds between serial requests, ten-title metadata
batches, one pilot, bounded media chunks, independent metadata/media caches,
`maxlag=5`, and no automatic redirects or retries. HTTP/API/body/decode errors
stop acquisition with a persistent latch, retained diagnostics and explicit
acknowledgement before resumption. Existing completed media is hash-checked and
not downloaded again.

Every media URL comes from its retained Commons API response. Requests aim for a
nominal 1600px longest edge; the actual returned bucket can differ from the API's
display dimensions. Both are recorded, with the existing 1.5× decoded-size guard.
An oversized unscaled original is not downloaded as fallback; a smaller rendition
requires a separate explicit API request and cache. Sources are fully decoded and
hashed before promotion. All 133 source requests used the nominal 1600px bound;
actual longest edges range from 561 to 2349 pixels. Two small originals (561×271
and 966×482) remain unscaled, and their bytes also match the API original SHA-1.
All seven PNGs retain alpha. There were no unavailable renditions, failed
requests, decode stops or retries. Framing, color, orientation metadata and alpha remain
unchanged. No local image conversion, resizing or cropping is applied to inputs.

Only manifest-listed `images/` files are comparison inputs. Each is a byte-identical
copy of its `sources/` rendition, with an opaque stable filename. `previews/`
contains contact sheets and any diagnostic bodies, outside the input set. All
three media directories are Git-ignored; a fresh checkout lacks the local assets.
Textual source catalogs, credits in [SOURCES.md](SOURCES.md), manifests, hashes,
batches, API responses, review decisions and receipts are versioned.

The manifest uses `kind=curatorial_heap` and `relation_kind=curatorial_selected`.
Each family ID connects one source/input copy only. Scene IDs are empty,
`probes.csv` is header-only, and `selections.json` has zero pairs and known-shift
families. There is no `prompt.json` or child fixture. Known related captures are
not given artificial matching labels. No router or comparison experiment is run.

Publication builds a fresh ignored stage, checks it offline, then publishes once
and checks again. The builder refuses an existing publication so a subsequent
repair must preserve old output before an explicit replacement. No existing
manifest-kind, nesting, shared discovery or router change is required.

### Offline checks

From the repository root, with Pillow installed from the pinned requirements:

```sh
.venv/bin/python Fixtures/Heaps/Curatorial/Evan-Amos-Uploads/tools/population.py
.venv/bin/python Fixtures/Heaps/Curatorial/Evan-Amos-Uploads/tools/integrate.py list
.venv/bin/python Fixtures/Heaps/Curatorial/Evan-Amos-Uploads/tools/integrate.py check
.venv/bin/python -m unittest discover -s Fixtures/Heaps/Curatorial/Evan-Amos-Uploads/tools -p 'test_*.py'
```

The checker replays the raw category inventory, complete ordering and exact
exclusions; verifies rights/identity evidence and API URLs; fully decodes and hashes
sources/inputs; checks byte equality, CSV/JSON catalogs, batches and contact sheets;
and verifies empty pair expectations and honest completion status. Duplicate byte
hashes and prior-fixture overlaps are allowed because they do not change the exact
File-member instruction. `provenance/checks.json` records executed checks and their
coverage. All 24 focused tests passed, as did this leaf’s offline check, all
three POTY leaves, SSI and Botanical Illustrations. No media is fetched by an
offline check.
