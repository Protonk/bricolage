# Puddle-Inversions — Puddles reflecting part of the scene

Still photographs in which a puddle or similar small accumulation of surface
water reflects some of the scene, selected by preview appearance.

Fixture ID: `bricolage-pi01-v1`; kind: `prompt_heap`; short code `PI01`.
<!-- collection-totals:start -->
The manifest lists **43 active inputs**. [All collection totals](../../../COLLECTIONS.md).
<!-- collection-totals:end -->

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Similarity/Puddle-Inversions/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Similarity/Puddle-Inversions/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Original publication and acquisition records

**Complete: 43 acquired and validated inputs from 45 supplied Commons leads; no pending downloads.**
All 45 previews were inspected: 43 accepted, 2 rejected, none deferred. The two
rejections (PI-22, a night street in Esztergom; PI-35, a cruise ship on a wet
quay) showed no legible puddle reflection at preview scale. The 43 fall inside
the requested 35–50; the brief gave no single target number.

> Still photographs in which a puddle or similarly small, localized rain- or
> surface-water accumulation reflects some part of the scene, offering inverted,
> duplicated, displaced or fragmented scenery inside the picture.

This contributes to the existing [Similarity heap](../README.md). The brief is
the sourcing partner's [handoff README](provenance/supplied/README.md), kept
unchanged; the prompt, looseness and exclusions are in
`provenance/intake/prompt.json` and the local contract in
`provenance/intake/HEAP_INSTRUCTIONS.md`. Commons category membership was the
discovery method, not the definition of the heap. Membership records a visual
selection, with no expected pairs, semantic groups or matching labels.

The selection is deliberately loose. Some members stretch "puddle": PI-12
mirrors peaks in a small mountain lake, PI-15 in a tarn-sized sheet of water,
PI-38 in a flooded street, and PI-16 in continuous wet paving. Others keep the
reflection faint or incidental (PI-01, PI-19, PI-32, PI-43). Each decision's
reason is recorded per image; none asserts that the images resemble one another
by any measure.

### Review and provenance

The sourcing partner supplied 45 file-page leads from the first listing page of
`Category:Reflections in puddles`, opened 19 file pages for text and inspected
no pixels. Its handoff (six files and its checksum list) is preserved unchanged
in `provenance/supplied/`; `provenance/intake.json` records the hashes and the
removal of the repository-root copy. `provenance/intake/candidates.jsonl` is
canonical and keeps every supplied column verbatim as a string; the CSV is the
union of its fields.

Visual decisions were made from the acquired 320px previews and the contact
sheets, with a short reason per image in `provenance/visual-review.json`,
`review_worksheet.csv` and `review_log.jsonl`. Transport status is recorded
separately; no acquisition result changed a visual decision.

Rights come from each file's Commons `imageinfo` reply at intake, not from the
handoff, and are listed in [SOURCES.md](SOURCES.md), `sources.csv` and
`provenance/source-review.json` with the reply's hash. Among the 43 accepted:
CC BY-SA 4.0 (18), CC BY 2.0 (9), CC BY-SA 3.0 (6), CC BY-SA 2.0 (5), CC BY 3.0
(1), CC BY 3.0 de (1), CC0 (1), Public domain (1) and one institutional
"No restrictions" statement (PI-20, a 1948 Daily Herald Archive photograph via
Flickr Commons), retained in that form and not restated as public domain. The
handoff's notes of extra attribution requests on five file pages (PI-01, PI-02,
PI-13, PI-14, PI-39) are quoted in `source-review.json`; those pages were not
re-read locally. The collection assigns no new license.

`provenance/relationship-notes.json` records the relationship review: three
photographers appear more than once with different scenes, the handoff withheld
same-site siblings and a documented crop, and no shared capture was seen among
the 45 previews. The [identity audit](provenance/identity-audit.json) compared
titles, page IDs, upstream SHA-1s and byte hashes against all 18 other current
leaves (1,251 known byte hashes) and found no collision. Different titles,
creators or hashes do not establish capture independence.

### Acquisition

Requests used `BricolageFixtureBot/0.1 (https://github.com/Protonk/bricolage) Python-urllib`
with `maxlag=5` and at least five seconds between requests: one preview pilot,
four preview chunks of twelve, one source pilot, four source chunks and three
single explicit requests. The [acquisition receipt](provenance/acquisition.json)
records 179 requests, 179 complete responses, no transport failures and no
automatic retries. Nominal previews were 320px and sources 1600px; 34 sources
are API-returned renditions and 9 are API-reported unscaled originals within the
bound. For PI-04, PI-13 and PI-19 the nominal request offered an unscaled
original above 1600px, so a 1280px rendition was requested explicitly and the
first reply kept. Both API-reported and decoded dimensions are recorded; no
image was cropped, resized or re-encoded locally.

### Contents and checks

- `images/` contains opaque flat filenames, byte-identical to the preserved
  downloads in `sources/`.
- `manifest.json`, `manifest.csv`, `sources.csv` and `SHA256SUMS.txt` record the
  source mapping, decoded dimensions and every source/input byte hash.
- `batches/batch-1.txt` lists all inputs. `probes.csv` is header-only and
  `selections.json` has no pairs.
- `previews/tiles/` and `previews/contact-NN.jpg` hold the reviewed previews;
  `previews/selected-NN.jpg` shows the published inputs and
  `provenance/final-review.json` records their inspection.
- `provenance/api/` preserves the raw API replies; `http_log.jsonl`,
  `acquisition.json`, `identity-audit.json`, `import-map.json` and
  `integration.json` separate transport, review, source checks and integration.
- `previews/bricolage-pi01-v1.zip` is the local handoff archive with media,
  previews and records. Media and archives are ignored by Git.

The offline checker (`tools/integrate.py check`, run by `tools/check.py`)
verifies source/input and preview hashes, measured dimensions, CSV/JSON
agreement, review and license evidence, preserved supplied fields, batch
coverage and empty pair expectations. The shared relationship checker does not
support `prompt_heap`. `tools/audit.py` refreshes the identity audit against the
current leaves; `python -m unittest discover -s tools -p 'test_*.py'` runs the
offline transport tests.

For deliberately resumed work, the tools follow the
[Pale-Skies-Dark-Ground](../Pale-Skies-Dark-Ground/README.md) acquisition
behavior: one small pilot, serial chunks, cached metadata, hash-checked media,
a stop on any transport error with `--acknowledge-error` for an explicit
restart, and no automatic retries. The user agent is read from
`BRICOLAGE_USER_AGENT` or `--user-agent`.

## Limitations

Visual decisions were made at 320px and contact-sheet scale by the local
integrator alone; a later look at full renditions may find reflections fainter
or stronger than recorded. The candidate population is the partner's 45 leads
from one cached listing page of a 432-file category, not a sample of the
category. Rights are Commons' reported statements, not legal determinations,
and file-page attribution requests were not re-read locally. Sources are
reduced renditions, not full-resolution originals.
