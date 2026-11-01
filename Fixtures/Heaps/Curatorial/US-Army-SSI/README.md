# US Army shoulder-sleeve insignia

US Army shoulder-sleeve insignia selected from a saved Commons category list,
with one selection per identified design.

Fixture ID: `hazy-us-army-ssi-v1`; kind: `curatorial_heap`.
The manifest lists **150 inputs**.

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Curatorial/US-Army-SSI/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/US-Army-SSI/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Images and records

**Target reached: 150 selected and acquired inputs. Selection remains provisional
around eight unresolved earlier candidates.** This is one leaf of the
[Curatorial heap](../README.md), beside POTY, with no sub-heaps. The selection basis
is Commons category membership, not an award or visual prompt.

| State | Count |
|---|---:|
| Frozen PetScan listings / unique File IDs / unique titles | 1,641 / 1,641 / 1,641 |
| Candidates with metadata / entries reviewed | 300 / 199 |
| Selected / acquired / pending acquisition | 150 / 150 / 0 |
| Excluded through the selection cutoff | 35 |
| Pending before the cutoff / unused reserve | 8 / 1,448 |
| Unreviewed entries | 1,442 |

The fixed order reaches the target at **rank 193**: 150 selected + 35 excluded +
eight pending. Of the exclusions, 15 repeat a previously selected design and 20
are out of scope. Six additional reviewed entries fall in unused reserve; one
of those has its own unresolved attribution. None is a comparison input.

The user revised the supplied 200-design target to about 150 and directed that
uncertain candidates remain pending while work continues. An explicit pending
case no longer blocks later reviewed candidates. The 121 selected entries after
the first pending candidate are marked provisional in `provenance/intake/selection.json`; an earlier
case resolved later can be reconciled against the same fixed order. There is no
reroll or silent conversion of uncertainty into exclusion. An unreviewed gap
still requires review before subsequent selection.

Pending ranks are 35, 82, 89, 125, 130, 146, 153 and 166. Rank 82 needs alternate
preview evidence; the others concern historical badges, standalone organizational
tabs or SSI identity. The Fourth Army representations at 153/166 remain linked
as unresolved design evidence. A conflicting SFAB identity at rank 197 is retained
in reviewed reserve. Decisions and the user's instructions are recorded in
`provenance/design-review.json` and `provenance/scope-questions.json`.

### Population and ordering

The supplied handoff is preserved byte-for-byte in `provenance/supplied/`, with
hashes in `provenance/intake.json`. The redundant `Fixtures/US-Army-SSI-handoff/`
setup folder was removed after verifying all four files against these committed
copies; the intake record retains its historical location and cleanup receipt.
Its depth-five PetScan query covers the File
namespace under **Shoulder Sleeve Insignia of the United States Army (SSI)** and
descendants. There was no recursive client-side category crawl.

The original CLI request to `petscan.wmcloud.org` stopped at HTTP 301. The user
then authorized accessibility use of the already loaded Safari results at
[PetScan query 58481052](https://petscan.toolforge.org/?psid=58481052). The loaded
HTML and a full JSON export were saved with Safari's Page Source option. All
1,641 titles and page IDs agree, in order, between them. The JSON output limit
was 10,000; no cap was reached. `provenance/population/browser-export.json` records
executed parameters, save times, hashes and counts. These are unchanged browser
export bytes; HTTP status and headers were unobservable and remain explicitly
unknown. Safari is no longer required.

`provenance/intake/inventory.json` preserves every returned row. IDs are the first 20 hexadecimal
characters of SHA-256 over UTF-8 `hazy-ssi-file-v1` + LF + the exact frozen
`File:` title; underscores and Unicode are retained. IDs are not recomputed after
Commons normalization or redirects. The seed is
`hazy-us-army-ssi-petscan-depth5-v1`; `provenance/intake/ordering.json` records the full ascending
SHA-256 order of UTF-8 seed + LF + candidate ID, with ID as tie-breaker.

This samples ordered files, deduplicated by design; it is not a uniform random
sample of all distinct designs. No unit, color, era, shape or medium quotas apply.
Design keys support duplicate exclusions only, not semantic clusters or matching
labels. Source text, documented history and previews establish scope and design
identity. Alternate formats, colorways, embroidery, crops and unit redesignations
do not establish a new design; documented historical redesigns can. Source
inconsistencies and uncertain relationships remain explicit. No aesthetic or
numerical similarity selection was performed.

### Acquisition and rights

The serial transport adapts POTY's workflow: truthful HazyFixtureBot User-Agent,
`maxlag=5`, at least three seconds between requests, ten-title metadata batches,
size-specific caches, no automatic redirects or retries, and persistent failure
latches. Every media URL comes from its retained Commons API response. Source
requests used nominal longest edges of 148 at 1600px and
2 at 1280px. Actual decoded dimensions, format,
orientation, mode, alpha, hashes and byte counts are recorded separately from
API display dimensions and original-file MIME/SHA-1. SVG originals use API-served
PNGs, with no local rasterization. Source and input bytes are unchanged.

The two explicit 1280px source requests resolve oversized unscaled originals
offered at nominal 1600px (ranks 40 and 105); both API responses are preserved.
No oversized original was downloaded as a fallback. The earlier preview checks
stopped on complete 500×721 and 960×1059 bodies that exceeded the unchanged 1.5×
nominal bound. Those bodies, diagnoses and explicit acknowledgements remain
preserved; separate size requests resolved the cases. The initial PetScan redirect
and both preview validation stops remain recorded. There have been no failed
Commons media transfers or automatic retries.

All 150 sources have file-specific rights evidence in raw API/file-page records
and [SOURCES.md](SOURCES.md): 141 public-domain claims, four CC BY-SA 3.0, three
CC BY-SA 4.0, and two CC0. Claims were reviewed, not independently authenticated;
no blanket collection license or missing license URL is invented. Insignia and
other supplied restrictions remain attached to their files. Original creator,
designer, digital renderer and current file-version uploader are separate fields.
Original creator is unknown for 68 selections, individual designer for all 150,
and renderer for 112. There is no creator cap. Concentration statistics retain
reported labels; spelling variants are not proof of separate institutions.

The exact-identity audit covers the 12 prior integrated sets (681 inputs), checking
available supplied/canonical titles, page IDs, curid URLs, upstream SHA-1s and
acquired SHA-256s. No exact conflicts were found. Coverage and snapshot hashes are
in `provenance/identity-audit.json`; this does not prove complete provenance
independence or identify undocumented design relationships. Offline rechecks use
that recorded set of 12 prior leaves; adding a newer contribution does not expand
this historical audit. Missing or changed covered evidence still fails. A fresh
publication audits all current prior leaves.

### Local files and checks

Only the 150 manifest-listed `images/` files are comparison inputs. Each is a
byte-identical copy of its preserved `sources/` rendition. `previews/` contains
218 acquired review previews, inspection sheets, selected contact sheets,
and diagnostic bodies. The bounded preview run extended to rank 220; reserve
previews are not selected inputs. One reserve OGG file was identified as unsupported
without a media request. All media remains Git-ignored; a checkout alone lacks it.

The manifest uses `curatorial_heap` and `curatorial_selected`. Each family ID
connects only one source/input byte copy. Scene IDs are empty, `probes.csv` is
header-only, and `selections.json` has zero pairs and known-shift families. There
is no `prompt.json`, similarity ground truth or visual-prompt size floor.

The prior 29-input publication is preserved in
`provenance/publications/initial-29/`; its contact sheets are under
`previews/publications/initial-29/`. These are historical records, not child
fixture sets. Original source/input paths and bytes are retained. The expanded
publication is built in a fresh ignored stage, validated, then published using
the exact prior manifest hash and preserved snapshot as replacement guards.

From the repository root:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Curatorial/US-Army-SSI/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/US-Army-SSI/tools/population.py
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/US-Army-SSI/tools/integrate.py list
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/US-Army-SSI/tools/integrate.py check
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Curatorial/US-Army-SSI/tools -p 'test_*.py'
```

The checker reconstructs the population/order, replays exclusions and provisional
selection, and verifies review/API/receipt identities, credits, SVG/raster handling,
decoded attributes, checksums, byte equality, source catalogs, batches and empty
pair expectations. The original 23 SSI tests, six existing Similarity validators, and
three POTY leaf checks passed; results are recorded in `provenance/checks.json`.
No shared traversal or manifest-kind change was required. A subsequent audit
coverage regression test checks that adding a newer leaf preserves the historical
receipt while changed or missing covered catalogs are detected.

`ssi.py` retains bounded metadata/media commands and explicit
`acknowledge --diagnosis` handling. Acknowledgement preserves failure evidence
and makes no request. Existing publication replacement requires an explicit
`--replace-manifest-sha` and `--preserved-publication`; it refuses changed inputs
and unpreserved output. No router or comparison experiment was run.
