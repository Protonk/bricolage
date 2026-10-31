# US Army shoulder-sleeve insignia

**Partial: 29 selected and acquired inputs against a target of 200.** This is one
leaf of the [Curatorial heap](../README.md), beside POTY, with no sub-heaps. The
selection basis is Commons category membership, not an award or visual prompt.

| State | Count |
|---|---:|
| Frozen PetScan listings / unique File IDs / unique titles | 1,641 / 1,641 / 1,641 |
| Metadata obtained / entries reviewed | 300 / 160 |
| Selected / acquired / pending acquisition | 29 / 29 / 0 |
| Excluded before the unresolved rank | 5 |
| Pending ordered decisions / unused reserve | 1,607 / 0 |
| Unreviewed entries | 1,481 |

The fixed order is held at **rank 35**, `File:SPAM_VIII_CORPS_2_DIV.png`.
Its file page identifies a Spanish–American War corps/division drawing but does
not establish shoulder-sleeve use. The handoff permits exclusion of demonstrably
out-of-scope files. The user has directed that unverified SSI candidates remain
**pending**, so the ordered selection stays held until the source evidence is
resolved. This policy decision is recorded in `provenance/scope-questions.json`.
No later candidate has been substituted silently.
This is an unresolved selection, not an exhausted-population shortfall.

Independent reviews through rank 160 are preserved: 134 provisionally eligible
records (including repeat designs), 19 scope exclusions, and seven pending cases.
Only decisions through rank 34 have been applied to selection. Those five
exclusions are two event photographs, a qualification tab, an award tab, and a
standalone auxiliary tab. Later reviews do not imply that 134 designs are distinct
or selected. Pending cases and available evidence are in
`provenance/scope-questions.json`; one needs an alternate preview size, and the
others concern historical badges, standalone band tabs, or SSI identity.

## Population and ordering

The supplied handoff is retained byte-for-byte in `provenance/supplied/`, with
hashes in `provenance/intake.json`. Its depth-five PetScan query includes the File
namespace under **Shoulder Sleeve Insignia of the United States Army (SSI)** and
descendants. There was no recursive client-side category crawl.

The original CLI request to `petscan.wmcloud.org` stopped at HTTP 301. The user
then authorized accessibility use of the already loaded Safari results at
[PetScan query 58481052](https://petscan.toolforge.org/?psid=58481052). The loaded
HTML and a separate full JSON export were saved with Safari's Page Source option.
All 1,641 titles and page IDs agree, in order, between them. The JSON output limit
was 10,000, and no cap was reached. `provenance/population/browser-export.json`
records exact executed parameters, save times, hashes, counts, and this acquisition
route. These are unchanged browser-export bytes; HTTP status and headers were
not observable and are explicitly unknown. Safari is no longer needed.

`inventory.json` preserves every returned row. Candidate IDs are the first 20 hex
characters of SHA-256 over UTF-8 `hazy-ssi-file-v1` + LF + the exact frozen
`File:` title; underscores and Unicode are retained. IDs are not recomputed after
Commons normalization or redirects. `ordering.json` records seed
`hazy-us-army-ssi-petscan-depth5-v1` and the full ascending SHA-256 order of UTF-8
seed + LF + candidate ID, with ID as tie-breaker. There is no reroll.

This samples ordered **files**, deduplicated by design; it is not a uniform random
sample of all distinct designs. No unit, color, era, shape or medium quotas apply.
Design keys in `provenance/design-review.json` are duplicate-exclusion evidence
only, not semantic clusters or matching labels. Source text, explicit history,
and locally inspected previews establish scope/design identity. Alternate formats,
colorways, embroidery, crops and unit redesignations do not establish a new design;
documented historical redesigns can. Unknown or ambiguous relationships stay
explicit. No aesthetic or numerical similarity selection was performed.

## Acquisition and rights

The serial transport adapts POTY's workflow: truthful HazyFixtureBot User-Agent,
`maxlag=5`, at least three seconds between requests, ten-title metadata batches,
size-specific caches, no automatic redirects or retries, and persistent failure
latches. A single SVG pilot preceded bounded batches. Every source URL comes from
its retained Commons API response. All 29 acquired sources were requested at a
nominal 1600px edge; smaller originals are retained where the API returned them.
Actual decoded dimensions, format, orientation, mode, alpha, hashes and byte counts
are recorded separately from API display dimensions and original-file MIME/SHA-1.
SVG originals are represented by API-served PNGs, with no local rasterization.

Two preview size checks stopped after complete, decodable responses: a 480px
request yielded 500×721, and a 640px request yielded 960×1059. Both exceeded the
unchanged 1.5× longest-edge guard. The original bodies, API replies, diagnosis and
explicit acknowledgements are retained; separate 640px and 1280px requests resolved
those cases. One later 1280px request offered an oversized unscaled original;
that preview was not downloaded and remains pending. There were no failed Commons
media transfers. The PetScan redirect and both validation stops remain recorded.

File-specific licenses, credits, raw Artist fields, restrictions and file-page
templates are retained in the API evidence and [SOURCES.md](SOURCES.md). All 29
acquired files have public-domain claims; these claims were reviewed, not
independently authenticated. Missing license URLs are not invented. Original
creator, designer, digital renderer and current file-version uploader are separate
fields. Five selected original creators, all individual designers, and 25 digital
renderers remain unknown. There is no creator cap. Concentration counts retain
reported attribution labels; spelling variants such as “US Army” and “U.S. Army”
are not proof of separate institutions or people.

The exact-identity audit covers all 12 prior integrated sets (681 inputs), checking
available supplied/canonical titles, page IDs, curid URLs, upstream SHA-1s and
acquired SHA-256s. It found no exact collisions. Coverage and inventory hashes are
in `provenance/identity-audit.json`; this does not establish complete provenance
independence or detect undocumented design relationships.

## Local files and checks

Only the 29 manifest-listed `images/` files are comparison inputs. Each is a
byte-identical copy of its `sources/` rendition. `previews/` holds 159 review
previews, contact sheets, and preserved diagnostic bodies. All media remains
Git-ignored; a checkout requires those local assets for full validation.

The manifest uses `curatorial_heap` and `curatorial_selected`. Each family ID
connects one source/input byte copy; scene IDs are empty, `probes.csv` is header-only,
and `selections.json` has zero pairs and known-shift families. There is no
`prompt.json`. The 30-image floor for Similarity contributions does not apply.

From the repository root:

```sh
python3 -m pip install -r Fixtures/Heaps/Curatorial/US-Army-SSI/requirements.txt
python3 Fixtures/Heaps/Curatorial/US-Army-SSI/tools/population.py
python3 Fixtures/Heaps/Curatorial/US-Army-SSI/tools/integrate.py list
python3 Fixtures/Heaps/Curatorial/US-Army-SSI/tools/integrate.py check
python3 -m unittest discover -s Fixtures/Heaps/Curatorial/US-Army-SSI/tools -p 'test_*.py'
```

The checker reconstructs the population and order, replays selection, verifies
review/API/receipt identities, credits, duplicate rules, SVG/raster distinctions,
decoded attributes, checksums, byte equality, catalogs, batches and empty pair
expectations. The publication was built in a fresh ignored stage, checked, then
published and checked again. A pass establishes consistency of this **partial**
state, not completion of the 200-design target.

All 20 SSI tests passed, along with POTY's 10 tests and PS01's six transport tests.
The six existing Similarity validators and all three POTY leaf checks passed.
Commands and results are preserved in `provenance/checks.json`. No shared traversal
or manifest-kind change was needed for this leaf.

`ssi.py` retains bounded metadata/media commands and explicit `acknowledge
--diagnosis` handling. Acknowledgement records the failure and does not make a
request. Partial bodies are preserved. `integrate.py build` refuses an existing
publication: resumption must explicitly reconcile the selection and stage a new
publication rather than silently overwrite this snapshot. No router or comparison
experiment was run.
