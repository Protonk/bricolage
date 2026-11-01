# Botanical Illustrations

Botanical plates and artworks selected from a saved Commons category list,
using a seeded order and recorded exclusions.

Fixture ID: `hazy-botanical-illustrations-v1`; kind: `curatorial_heap`.
The manifest lists **149 inputs**.

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Curatorial/Botanical-Illustrations/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/Botanical-Illustrations/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Images and records

**150 distinct works selected; 149 acquired, one transfer pending. Acquisition
remains partial and selection remains provisional around 14 earlier cases.**
This is one leaf of the
[Curatorial heap](../README.md), directly beside POTY and US-Army-SSI. It samples
the direct File members of Commons **Botanical illustrations**, without category
recursion, artist quotas or aesthetic balancing. The recorded counts are in
`provenance/acquisition.json`.

| State | Count |
|---|---:|
| Frozen direct-category listings / unique File IDs | 709 / 709 |
| Metadata-resolved identities / reviewed entries | 200 / 176 |
| Selected distinct works / acquired inputs | 150 / 149 |
| Pending acquisition | 1 (rank 102) |
| Excluded through rank 170 / pending selection | 6 / 14 |
| Unused reserve / unreviewed entries | 539 / 533 |

The fixed order reaches 150 selections at rank 170: 150 selected, six excluded
and 14 pending, leaving 539 reserve candidates. Metadata covers the first 200
ranks (200 resolved File identities, no redirects). There are 176 reviewed
entries: the extra six are reviewed reserve, including two unresolved cases.
The other 533 entries are unreviewed. Reserve metadata or previews do not make
those candidates comparison inputs.

The 143 selections after the first pending case remain provisional. An explicit
pending decision advances to the next candidate without resolving the uncertainty;
an unreviewed gap still blocks selection. Resolving an earlier pending case would
require reconciliation against the same recorded order. Failed acquisition does
not remove a selection or cause a replacement to be chosen.

Pending selection ranks are 8, 41, 42, 68, 74, 85, 91, 94, 103, 128, 141, 144,
164 and 169. They concern undocumented original classroom plates, ambiguous
illustration versus photograph/composite scope, conflicting artist/date or rights
claims, and uncertain reworkings of already selected drawings. Ranks 186 and 189
retain additional pending reviews in reserve. The detailed reasons and bound
metadata are in `provenance/work-review.json`.

Four exclusions are outside scope: two museum-display photographs, one plant
photograph, and a decorative frontispiece without a substantive botanical figure.
Two repeat earlier works: rank 126 reannotates/recolors the flower drawing at
rank 57; rank 145 is the full Weinmannia print whose earlier crop at rank 62 was
selected. The earlier crop retains its upstream framing. Explicit alternate-file
links, including related reserve candidates, are retained in
`provenance/alternate-file-evidence.json`. Distinct plates in one book can coexist;
a shared book, artist or plant name does not establish a duplicate.

### Frozen population and review

The four supplied instruction files are preserved byte-for-byte in
`provenance/supplied/`, with hashes and the original setup location in
`provenance/intake.json`. The redundant handoff folder was removed after verifying all four names,
byte-identical contents and intake hashes; the cleanup receipt is in the intake record. The handoff's scouting count of 659 direct files and 43
subcategories was not an inventory. The actual frozen export contains **709**
unique File titles and page IDs.

The user authorized access to the already loaded Safari result for
[PetScan query 58483581](https://petscan.toolforge.org/?psid=58483581). The loaded
HTML and complete JSON export were saved through Safari's Page Source option;
all 709 titles and IDs agree in order. The executed query was Commons, category
`Botanical illustrations`, depth 0, namespace 6, limit 5000. The limit was not
reached. Raw bytes, exact parameters, save timestamps, hashes and count checks
are in `provenance/population/`. Browser HTTP status and headers were unobservable
and remain null. Safari is no longer required.

`provenance/intake/inventory.json` retains every exported row. Stable opaque IDs are the first 20
hexadecimal characters of SHA-256 over UTF-8 `hazy-botanical-file-v1` + LF + exact
frozen `File:` title, retaining underscores and Unicode. IDs do not change after
Commons title normalization. The seed is `hazy-botanical-illustrations-direct-v1`;
`provenance/intake/ordering.json` records ascending SHA-256 over UTF-8 seed + LF + candidate ID,
with ID as tie-breaker. `provenance/intake/selection.json` accounts for all 709 candidates.

This is a seeded file sample with documented work exclusions, not a uniform
sample of all distinct artworks. Scope and work identity use retained Commons
metadata, file-page revisions and actual previews where needed. One singleton metadata
response offers an older upload-history continuation while providing both current
records. The validator accepts only that narrow case and rejects missing current
evidence or other continuation types; see `provenance/metadata-continuation-review.json`
and [MediaWiki imageinfo semantics](https://www.mediawiki.org/wiki/API:Imageinfo). Named Bauer
folios have explicit manuscript and illustrator evidence; those do not require
visual judgments about quality. Preview inspection checks only scope, identity
and known alternate works. No similarity scores, perceptual hashes, artistic
rankings, subject quotas or composition balancing were used. Fungal illustrations
and substantive botanical figures on title pages are within the supplied scope.

Original artist, engraver/lithographer, publisher, digitizer and current
file-version uploader remain separate. Among the 150 selections, original artist
is unknown for 67, engraver/lithographer for 147, publisher for 112 and digitizer
for 31. A book author or repository in Commons' rendered Artist field is not
silently made the original illustrator. Reported Artist and raw source claims
are retained alongside these role decisions.

The source concentration includes 46 distinct Bauer folios from MS Sherard 244
and ten figures from the 1857 Elements of Botany translation. There is no creator
or publication cap. `provenance/source-publication-labels.json` documents short
publication/collection labels for counting only; 14 selections have no assigned
label. They do not define sub-heaps or relationships. The 150 individual work keys
support duplicate exclusion, not matching labels.

### Acquisition and rights

The transport adapts the active Commons workflow: HazyFixtureBot User-Agent,
`maxlag=5`, at least three seconds between serial requests, ten-title metadata
batches, bounded media runs, separate size-specific caches, and no automatic
redirects or retries. Every media URL comes from its saved Commons API response.
Nominal 1600px longest-edge requests can return rounded CDN sizes; API dimensions
and decoded dimensions are recorded separately. The unchanged guard rejects
renditions over 1.5 times the requested edge and unscaled originals larger than
the request. Of the acquired sources, 135 use nominal 1600px requests, 13 use 1280px and one
at 640px. Explicit 1280px requests handle oversized originals and the rank 166
size mismatch. Rank 90 still offered the unscaled original at 1280px, so an
explicit 640px request obtained 500×911 bytes. All size-specific replies and
unavailable-rendition decisions remain recorded.

An SVG original (rank 77) and a TIFF original (rank 148) use API-served PNGs.
Rank 115 was already a standalone Commons PNG extracted upstream from a DjVu;
no arbitrary book-page extraction or local rasterization was performed. Sources
are fully decoded, hashed, and copied byte-identically into `images/`, preserving
framing, alpha and all acquired bytes. If a completed preview's URL is exactly the
source API's returned URL, its verified bytes and original transfer receipt are
reused without another request. Contact sheets alone use display resizing and a
background; they are outside comparison inputs.

Two preview size checks stopped after complete HTTP bodies: rank 16 returned
500×725 rather than the API display dimensions 331×480, and rank 166 returned
250×747 rather than 160×480. Both exceed the 720px bound for a nominal 480px
request. The original partial-path bodies, diagnoses and explicit acknowledgements
remain preserved; neither preview was retried. Separate source-size requests use
the original reviewed identities. Four other previews needed explicit alternate
API sizes because 480px offered an oversized unscaled original; those were
recorded before any media request. Rank 166 also stopped at source size: the
1600px API request returned a complete 960×2870 body, exceeding the 2400px
guard. That body remains preserved and unpromoted; after diagnosis and explicit
acknowledgement, a separate smaller API rendition was requested.

The rank 102 source transfer timed out after 393,216 of 456,943 declared bytes.
Its incomplete body and SHA-256 remain in `previews/partials/` and the HTTP log.
After offline diagnosis, the failure was explicitly acknowledged solely to continue
later candidates. Rank 102 remains selected but pending acquisition; no retry or
alternate-size attempt was made for it. Download failure does not become an
eligibility exclusion. There was one failed transport, three post-transfer size-validation stops, and
zero automatic retries. All stops have preserved diagnoses and explicit
acknowledgements. The 149 acquired inputs comprise 123 JPEGs and 26 PNGs; nine
retain alpha. Four completed preview transfers were reused by exact URL.

File-specific rights evidence is in raw API/file-page records and [SOURCES.md](SOURCES.md).
For the selected set, Commons reports 114 Public domain, 16 No restrictions,
11 CC BY-SA 4.0, five CC0, three CC BY 4.0 and one CC BY-SA 3.0. These are source
claims, not independent authentication or a blanket collection license. Public
domain claims without URLs remain without invented URLs. Conflicting rights
claims are pending. Historical date/title inconsistencies and unknown roles remain
explicit; differing editions are not alone evidence of distinct plates.

The exact-identity audit covers 13 prior integrated leaves and 831 inputs,
checking available titles, page IDs, `curid` URLs, original SHA-1s and acquired
SHA-256s. Coverage and manifest/catalog snapshot hashes are recorded in
`provenance/identity-audit.json`. No exact collision was found. This cannot prove
independent origins or detect undocumented reprints. Rechecking uses that recorded
coverage; a new publication audits all current prior leaves.

### Local files and checks

Only manifest-listed `images/` files are comparison inputs, each a byte-identical
copy of one `sources/` rendition. `previews/` holds review tiles, inspection and
contact sheets, and diagnostic bodies. All media remains Git-ignored. A fresh
checkout contains the evidence and tools but lacks media required for full checks.

The manifest kind is `curatorial_heap`, with `curatorial_selected` image records.
Each family ID connects only its own source/input byte copy. Scene IDs are empty,
`probes.csv` is header-only, and `selections.json` has zero pairs and known-shift
families. There is no `prompt.json`, 30-image prompt-heap floor, similarity ground
truth or child fixture. Publication uses a fresh ignored stage, checks it offline,
and refuses silent overwrites before publishing.

From the repository root, with Pillow installed from the pinned requirements:

```sh
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/Botanical-Illustrations/tools/population.py
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/Botanical-Illustrations/tools/integrate.py list
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/Botanical-Illustrations/tools/integrate.py check
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Curatorial/Botanical-Illustrations/tools -p 'test_*.py'
```

The checker replays population IDs, ordering, decisions and provisional selection;
verifies work exclusions, role evidence, source identities, licenses, exact API
renditions, diagnostic bodies, decoded attributes, byte equality and checksums;
and checks CSV/JSON manifests, catalogs, batches, contact-sheet coverage and empty
pair expectations. All 33 Botanical tests, 24 SSI tests and ten POTY tests
passed, as did the Botanical/SSI offline checks, three POTY leaves and all six
Similarity validators. `provenance/checks.json` records the commands and results.

Existing leaf discovery, fixture-local paths, asset ignore rules and curatorial
kind semantics already support this depth. The only existing-tool change makes
SSI's historical audit recheck its recorded prior leaves, rejecting changed or
missing evidence without absorbing newly added contributions. No router or
comparison experiment was run.
