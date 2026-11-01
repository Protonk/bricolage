# Ex Libris

Bookplates selected from three Commons categories, using a fixed order,
thumbnail review and recorded work exclusions.

Fixture ID: `hazy-ex-libris-v1`; kind: `curatorial_heap`.
<!-- collection-totals:start -->
The manifest lists **50 active inputs**. [All collection totals](../../../COLLECTIONS.md).
<!-- collection-totals:end -->

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Curatorial/Ex-Libris/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/Ex-Libris/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Original publication and acquisition records

**50 selected images, all 50 acquired and validated. Eight earlier cases remain
deferred, so 40 later selections are provisional.** This is one Curatorial leaf,
combining three direct Commons category lists without recursive descent.

| State | Count |
|---|---:|
| Frozen unique File identities | 440 |
| Actually reviewed previews | 80 |
| Scope / provenance rejects across reviewed previews | 10 / 1 |
| Deferred reviews without a decisive rejection | 8 |
| Selected / acquired / pending acquisition | 50 / 50 / 0 |
| Unused reserve after the selection cutoff | 375 |

The frozen lists contain 122 **Ex libris**, 127 **19th-century ex libris**, and
192 **20th-century ex libris** members. Their page-ID union has 440 entries;
every membership and raw category row is retained. Each last response has no
continuation. Scouting counts are not treated as the fetched inventory.

`provenance/intake/ordering.json` preserves the seed `hazy-curatorial-ex-libris-v1` and complete
hash ordering. IDs are the first 20 hex digits of SHA-256 of UTF-8
`hazy-curatorial-triplet-v1` + LF + leaf slug + LF + exact frozen title. Order is
ascending SHA-256 of seed + LF + candidate ID, with ID tie-break. The first 50
eligible candidates are reached at rank 65. Reviews extend through rank 80,
including reserve; reserve reviews do not change the cutoff. There are no
artist caps, category quotas, aesthetic balancing or similarity scores.

### Scope, relationships and uncertainty

Actual thumbnails were inspected for identifiable bookplates or printed
ownership emblems. Heraldry, woodcuts, modern graphic designs, simple library
labels and stamps are retained, including prominent plates still on their
book pages. Rejects include whole book/title-page views with incidental tiny
marks, a portrait, a publisher device, a cover crest, handwritten inscriptions
and an unlettered preparatory drawing. These are fallible scope decisions.

Reserve rank 73 repeats accepted rank 5's Santos-Dumont/Icarus printed plate
in a different book copy and photograph. Matching design, lettering and
commemorative date establish the repeated work; it is excluded. Its separate
uncertain PD-old claim remains recorded. Different plates by Allan Jordan
(ranks 30 and 61) and Jacques Hnizdovsky (45 and 63) are retained: a shared
artist does not make different named ownership designs duplicates.

Eight earlier candidates remain deferred:

- Ranks 12 and 26: Hobrecker plates with unknown original artist/date, sourced
  through a 1987 reprint; the PD-old basis is unresolved.
- Rank 18: Conde de Paraty plate with named designer/engraver but a separate
  account's self-release and no established authority link.
- Rank 28: modern institutional seal, with unresolved underlying work rights.
- Rank 31: conflicting Chris Lebeau / Chris Moret designer attributions.
- Rank 50: private 1937 Josef Váchal artwork tagged PD-CzechGov; archive custody
  alone does not establish that exemption.
- Rank 60: Julián Nadal plate released by a library account without a verified
  artist-rights link in the cached evidence.
- Rank 64: own-photo license, but original plate date/designer and rights unknown.

The title/visible owner-name discrepancy at rank 2 is retained without renaming
the Commons identity. Rank 57's malformed PD-user template is recorded alongside
its agreeing original uploader/photographer evidence. Public-domain and license
statements are file-specific source claims, not independent authentication.
Rijksmuseum's explicit public-domain/CC0 catalog claim and the Hnizdovsky estate's
Commons permission-ticket references are preserved. Unknown designers remain
null; owners, book authors, publishers, digitizers and uploaders are not silently
assigned as artists. See [SOURCES.md](SOURCES.md) and raw file-page revisions.

### Acquisition and checks

The shared [three-category tools](../tools/README.md) adapt the active Commons
workflow. Requests are serial, cached and paced by at least three seconds, with
a truthful User-Agent, `maxlag=5`, no automatic retries and a shared stop latch.
Separate preview and source pilots preceded bounded batches.

One preview stopped at the size guard: rank 30 returned a complete 500x725 JPEG
for a nominal 480px request. The unpromoted body and failure receipt remain
preserved; an explicit diagnosis preceded a separate 320px API rendition request.
Ranks 19 and 29 required explicit 640px preview requests to accept small originals
just above 480px. There were no HTTP/incomplete-body failures or source stops.

48 sources use nominal 1600px requests and two use separately requested 1280px
renditions because the larger API offered oversized unscaled originals. Actual
reported and decoded dimensions, original identities, exact rendition URLs,
formats and hashes are retained (47 JPEGs and three PNGs). TIFF originals use Commons-served raster
renditions. Source framing and bytes are unchanged: no local crop, resize,
rasterization or re-encoding. `images/` contains byte-identical copies of
`sources/`; `previews/` contact sheets remain outside comparison inputs. All
media and diagnostic bodies are Git-ignored.

Publication was staged, checked, published with overwrite guards and checked
again. The exact-identity audit covers 17 prior integrated leaves, 1,213 inputs
and 4,906 available candidate records, including all six Similarity candidate
catalogs. No selected exact overlap was found. Recorded coverage remains fixed for later offline checks;
absence of an exact match does not establish independent printed works.

The manifest uses `curatorial_heap` and `curatorial_selected`. Each family ID
connects only one preserved source to its unchanged input. There is no prompt,
child heap, expected pair, matching label or known-shift family. No router or
comparison experiment was run.

From the repository root, with Pillow 12.0.0 installed:

```sh
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/Ex-Libris/tools/intake.py check
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Curatorial/tools -p 'test_*.py'
```

The offline check replays population, order and decisions; verifies raw API and
review evidence, source/input hashes and dimensions, diagnostics, credits,
catalogs, batches, contact sheets and empty pair expectations. The six original
handoff files are preserved byte-identically in `provenance/supplied/`;
`provenance/intake.json` records their hashes and cleanup.
