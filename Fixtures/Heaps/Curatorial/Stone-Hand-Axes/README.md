# Stone Hand Axes

Photographs and drawings of hand axes selected from three Commons categories,
using a fixed order, thumbnail review and recorded artifact exclusions.

Fixture ID: `hazy-stone-hand-axes-v1`; kind: `curatorial_heap`.
<!-- collection-totals:start -->
The manifest lists **50 active inputs**. [All collection totals](../../../COLLECTIONS.md).
<!-- collection-totals:end -->

Use the [shared fixture format](../../../FORMAT.md) for the directory layout and the
[provenance index](provenance/README.md) for source and selection records.

## Check this collection

From the repository root, using Python 3.14.x:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/Curatorial/Stone-Hand-Axes/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/Stone-Hand-Axes/tools/check.py
```

The check is offline. `--metadata-only` checks layout and catalogs without
media or the specialized validators.

## Original publication and acquisition records

**50 selected images, all 50 acquired and validated. Three earlier cases remain
deferred, so 33 later selections are provisional.** This is one Curatorial leaf,
combining three direct Commons category lists without recursive descent.

| State | Count |
|---|---:|
| Frozen unique File identities | 268 |
| Actually reviewed previews | 79 |
| Scope / provenance rejects across reviewed previews | 15 / 6 |
| Technical exclusions without a visual review | 1 |
| Deferred reviews without a decisive rejection | 4 |
| Selected / acquired / pending acquisition | 50 / 50 / 0 |
| Earlier deferred selection cases | 3 |
| Unused reserve after the selection cutoff | 197 |

The frozen lists contain 147 **Stone hand axes**, 61 **Acheulean hand axes**, and
74 **Drawings of stone hand axes** members. Their page-ID union has 268 entries;
every membership and original row is retained. Each category's last response has
no continuation. The supplied scouting counts are not treated as the inventory.

`provenance/intake/ordering.json` preserves the seed `hazy-curatorial-stone-hand-axes-v1` and full
hash ordering. IDs are the first 20 hex digits of SHA-256 of UTF-8
`hazy-curatorial-triplet-v1` + LF + leaf slug + LF + exact frozen title. Order is
ascending SHA-256 of seed + LF + candidate ID, with ID tie-break. The first 50
eligible candidates are reached at rank 71. Reviews extend through rank 80,
including reserve; reserve decisions do not change that cutoff. There are no
artist caps, category quotas, aesthetic balancing or similarity scores.

### Scope and uncertainty

Actual thumbnails were inspected for prehistoric hand axes/bifaces, including
archaeological drawings, damaged artifacts, multi-view plates and close museum
arrays. Irregular silhouettes and different graphic media are retained. Scope
rejects include cleaver drawings, a scraper, maps, incidental artifacts in wider
scenes, polished celt-like objects and a smooth stone without hand-axe context.
These are fallible scope decisions, not archaeological ground truth.

Five provenance rejects concern documented modern replicas or a repeated plate
crop: ranks 7, 36, 52 and 69 are replicas; rank 50 is a crop of accepted rank 42's
1912 archaeological plate. The reserve photograph at rank 75 also includes the
same Kůlna breccia-chert artifact as rank 4, alongside a different citrine object.
The two replica photographs at ranks 7 and 36 depict the same replica scene.
Shared photographers or similar-looking tools alone do not establish repetition.

Ranks 25 and 31 remain deferred as possible alternate object views of ranks 2
and 13. Rank 51 credits photographer A. Lesch but has a self-license by S. J. Miba,
without an established identity/authority link. Reserve rank 74 remains deferred
against rank 37's Palmones artifact. Rank 18 is decisively out of scope as a
portrait, while its separate photographer/release uncertainty remains recorded.
Unknown artifact makers and specimen identities stay null; photographers,
drawing artists, digitizers and current file-version uploaders remain separate.

Rank 72 is an unsupported 13-frame GIF. No static frame was extracted and no
visual review was fabricated. It lies after the selection cutoff. All technical,
visual, provenance and rights decisions remain separate in `provenance/`.
File-specific claims and credits are in [SOURCES.md](SOURCES.md); they are
recorded source evidence, not independent authentication.

### Acquisition and checks

The shared [three-category tools](../tools/README.md) adapt the active Commons
workflow. Requests are serial, cached and paced by at least three seconds, with
a truthful User-Agent, `maxlag=5`, no automatic retries and a shared stop latch.
One preview pilot and one source pilot preceded bounded batches.

Two preview requests stopped at the decoded-size guard: ranks 61 and 66 returned
complete 500x722 and 500x725 JPEGs for nominal 480px requests. Their bodies remain
unpromoted; explicit diagnoses preceded separate 320px rendition requests.
The third stop identified rank 72's complete animated GIF. All 13 frames decoded;
the body remains preserved and the candidate is technically excluded. There
were no HTTP/incomplete-body failures or source-acquisition stops.

48 sources use nominal 1600px requests and two use separately requested 1280px
renditions because the larger API offered oversized unscaled originals. Actual
reported and decoded dimensions, original identities, exact rendition URLs,
formats and hashes are retained (40 JPEGs and ten PNGs). Source framing and bytes are unchanged; no
local crop, resize or re-encoding is applied. `images/` contains byte-identical
copies of `sources/`. All media and diagnostic bodies remain Git-ignored;
`previews/` contact sheets are outside comparison inputs.

Publication was staged, checked, published with overwrite guards and checked
again. The exact-identity audit covers 16 prior integrated leaves, 1,163 inputs
and 4,638 available candidate records, including all six Similarity candidate
catalogs. No selected exact overlap was found. Recorded coverage is fixed for
later offline rechecks; absence of an exact match does not establish independent
artifacts or captures.

The manifest uses `curatorial_heap` and `curatorial_selected`. Each family ID
connects only one preserved source to its unchanged input. There is no prompt,
child heap, expected pair, matching label or known-shift family. No router or
comparison experiment was run.

From the repository root, with Pillow 12.0.0 installed:

```sh
Fixtures/.venv/bin/python Fixtures/Heaps/Curatorial/Stone-Hand-Axes/tools/intake.py check
Fixtures/.venv/bin/python -m unittest discover -s Fixtures/Heaps/Curatorial/tools -p 'test_*.py'
```

The offline check replays population, order and decisions; verifies raw API and
review evidence, source/input hashes and dimensions, diagnostics, credits,
catalogs, batches, contact sheets and empty pair expectations. The six original
handoff files are preserved byte-identically in `provenance/supplied/`;
`provenance/intake.json` records their hashes and cleanup.
