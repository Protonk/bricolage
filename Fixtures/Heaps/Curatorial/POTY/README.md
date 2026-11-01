# Wikimedia Commons Picture of the Year — Round 1

This source collection belongs to the [Curatorial heap](../README.md). It preserves the
official **Arthropods**, **Constructions and buildings**, and **People and human
activity** category populations for 2023, 2024 and 2025, then samples each pooled
population mechanically. It is fixture acquisition, with no image-similarity experiment
or visual selection judgments.

## Current state

| Contribution | Eligible entries | Selected | Acquired | Excluded in selection | Unused reserve | Pending acquisition |
|---|---:|---:|---:|---:|---:|---:|
| [Arthropods](Arthropods/README.md) | 237 | 43 | 43 | 194 | 0 | 0 |
| [Constructions and buildings](Constructions-and-buildings/README.md) | 248 | 50 | 50 | 40 | 158 | 0 |
| [People and human activity](People-and-human-activity/README.md) | 238 | 50 | 50 | 25 | 163 | 0 |

The selection is complete. Arthropods exhausts its 237 entries at **43 accepted
creators/attributions**, a shortfall of seven against the target of 50. The other
categories reach 50. Exclusions count candidates passed over before reaching the target
(or exhausting the population); reserve entries remain unused, and are not pending
downloads. Their source metadata and provenance decisions are also retained.

Acquisition is **complete**. Only manifest-listed, acquired `images/` files are
comparison inputs. All media stays local and Git-ignored. A checkout preserves evidence
and tools but requires the recorded local assets for full validation.

## Published population

- [2023 gallery](https://commons.wikimedia.org/wiki/Commons:Picture_of_the_Year/2023/Gallery)
- [2024 gallery](https://commons.wikimedia.org/wiki/Commons:Picture_of_the_Year/2024/Gallery)
- [2025 gallery](https://commons.wikimedia.org/wiki/Commons:Picture_of_the_Year/2025/Gallery)

The published `MediaWiki:POTY-gallery.js` loads each category’s `Gallery/<official
category>/data.json`; its Round 1 code uses `Gallery/All/data.json`, separately from
`Gallery/Finalists/data.json`. The loader and discovery responses are cached in
Arthropods/provenance/api. All three yearly category lists and corresponding complete
Round 1 All lists are preserved as actual API response bytes in each leaf. Shared
population cache copies are byte-identical to the first leaf’s responses; they do not
represent additional requests.

| Official category | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| Arthropods | 47 | 86 | 104 |
| Constructions and buildings | 41 | 78 | 129 |
| People and human activity | 54 | 92 | 92 |

Every inventory entry occurs in its year’s All list. Membership in the official category
data page is authoritative here: the 2023 People rows mostly spell the embedded category
`People and human actvity`, and three 2023 entries across Constructions and People
retain `Other objects` in that field. These source inconsistencies and raw records are
preserved in `provenance/population-notes.json`; nothing is reclassified. Published
static counts can differ from the actual data lists. Revision IDs, timestamps, page
identities and raw-response hashes make the acquired snapshot explicit.

## Mechanical selection and provenance

1. Candidate IDs are the first 20 hexadecimal characters of SHA-256 over `year + LF + official_category + LF + File:title`, using the preserved title with underscores normalized to spaces. IDs are checked for collisions.
2. Seed: `hazy-poty-round1-2023-2025-v1`. Order by ascending SHA-256 of UTF-8 `seed + LF + official_category + LF + candidate_id`, breaking ties by ID. This fixed hash ordering is independent of API response order or Python random-library versions; no reroll or composition balancing was performed.
3. Walk that order, accepting up to 50 candidates with verified source identity and file-specific rights evidence. Exclude unsupported media, explicit alternate crops, known repeated assets and documented related captures. An exclusion advances to the next entry. Acquisition failures stop transport rather than silently changing the selection.
4. Accept at most one image per identified original creator in each contribution. Preserve explicit original/derivative/restorer roles, resolve documented aliases, and never use uploader identity as an author substitute. A named institutional attribution is capped as an institution without inventing an individual photographer. The People selection has three unknown original photographers, explicitly recorded; its painting reproduction counts both the identified painter and photographer.
5. Creator and relationship decisions are reproducible from cached file text, API Artist evidence, small explicit overrides and alias mappings. The source evidence is not a proof that all unreported aliases or capture relationships have been discovered. No photograph was inspected to judge quality, similarity, typicality or variety.

`provenance/intake/inventory.json` preserves every eligible candidate and published field. `provenance/intake/ordering.json`
records the seed/order; `provenance/intake/selection.json` records each rank, decision, exclusion reason
and conflicting prior selection. `provenance/source-evidence.json`,
`creator-aliases.json`, `review-overrides.json`, `creator-alias-evidence.json`, and
`provenance-review.json` preserve the source review. Known other-version links are
exclusion evidence only, never expected matching pairs. Prior exact-identity checks
found no reuse in the seven existing integrated fixture inventories (439 inputs); their
snapshot hashes and scope are recorded per leaf.

Uploader concentration is separately reported in `provenance/acquisition.json` for both
the POTY-published uploader and the latest file-revision uploader. The highest selected
counts for the published uploader are 2 / 2 / 4 across the three categories. The latter
API field is not mislabeled as original upload or original creator.

## Transport and source bytes

The transport adapts PS01’s conservative workflow: truthful `HazyFixtureBot/0.1
(https://github.com/Protonk/hazy) Python-urllib`, `maxlag=5`, cached metadata, one
request at a time, at least three seconds between responses and the next request, no
automatic redirects or retries, and bounded chunks after one source pilot per category.
Metadata is batched by ten titles. Media URLs come only from the returned imageinfo
records. Wikimedia’s [API etiquette](https://www.mediawiki.org/wiki/API:Etiquette) and
[User-Agent
policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy)
informed this workflow.

Every media request asks for a nominal 1600px longest edge. Commons often returns a
1920px URL while reporting 1600px display dimensions; actual decoded dimensions are
retained separately, with PS01’s 1.5× nominal bound. The current file revision is
identified by its imageinfo SHA-1 and upload timestamp; this is not a reconstruction of
historical contest-time bytes. No original above the requested bound is used as an
unscaled fallback. Each complete file is fully decoded and hashed before promotion to
`sources/`, then copied byte-identically into opaque `images/` filenames. No local crop,
color edit, resize or re-encoding is applied to sources or inputs.

The first pilot stopped because an initial check incorrectly equated the API display
dimensions with decoded dimensions. The preserved body fully decodes as 1920×1280,
matching the API-returned 1920px URL, rather than the reported 1600×1066 display size.
The explicit acknowledgement records this diagnosis. The same complete body was reused
without a second request, and is retained under Arthropods/previews/partials. API and
measured dimensions are now checked separately. There have been no failed HTTP transfers
or automatic retries; the validation stop remains in the HTTP log and acknowledgement
history.

Any new access, rate-limit, body, API or decoding failure stops the run and retains
diagnostics. The error latch blocks network work across all three leaves until an
explicit diagnosis is passed with `--acknowledge-error`. Incomplete media stays in
leaf-local `previews/partials/`; API bodies stay under `provenance/partials/`.
`--reuse-complete-body` is an explicit recovery option that requires a matching complete
HTTP receipt and another full decode; incomplete bodies cannot use it.

## Records and offline checks

Each leaf contains normal manifests, the common source catalog, file-specific
`SOURCES.md`, source/input checksums, batch-1 plus smoke/medium lists, an import map
with year and official category, and acquisition/validation receipts. Contact sheets
live in `previews/selected-*.jpg`, outside the input set. `family_id` identifies one
byte-preserved source/input copy only; scene IDs, pair expectations and known-shift
families are empty.

From the repository root:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Curatorial/POTY/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/POTY/tools/integrate.py list
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/POTY/tools/integrate.py check
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/POTY/tools/integrate.py check --category "People and human activity"
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Curatorial/POTY/tools -p 'test_*.py'
```

The checker reconstructs category/year membership from raw published revisions, replays
ordering and exclusions, verifies original-creator limits and explicit relationship
conflicts, checks download/API receipts and exact URLs, fully decodes files, verifies
source/input byte equality, and checks manifest/source/batch coverage and empty pair
expectations. Each category can be checked independently; no sibling’s images are
needed. Missing local assets fail visibly. The existing Similarity validators are
unchanged and all four passed; PS01’s six transport tests also passed. No router or
comparison command was run.

The extra source-collection directory requires no traversal or asset-ignore change:
existing fixture paths are leaf-relative and discovery was already documentation-led.
The minimal format extension is `kind=curatorial_heap` and
`relation_kind=curatorial_selected`, with selection records instead of a fabricated
`prompt.json`. The PS01 handoff wording is scoped to visual-prompt Similarity
contributions.

For an explicitly resumed incomplete acquisition, the tools retain `initialize`,
`metadata`, `evidence`, `select`, `acquire --limit 12`, and offline `integrate.py
build`. Cached requests are hash-checked, changed existing input bytes are never
overwritten, and a shared lock prevents concurrent intake/build. Acquisition does not
silently rewrite a published manifest; rebuild and validate after a deliberate intake
update.
