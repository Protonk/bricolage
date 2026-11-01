# Rocks in Thin Section

**50 selected images, all 50 acquired and validated. Selection remains provisional
around one earlier deferred rights case.** This is one leaf of the Curatorial
heap, combining three direct Commons category lists without recursive descent.

| State | Count |
|---|---:|
| Frozen unique File identities | 530 |
| Actually reviewed previews | 59 |
| Scope / provenance rejects across reviewed previews | 2 / 2 |
| Technical exclusions without a visual review | 1 |
| Deferred rights reviews | 1 |
| Selected / acquired / pending acquisition | 50 / 50 / 0 |
| Unused reserve after the selection cutoff | 475 |

The three frozen lists contain 243 **Rocks in thin section**, 193 **Igneous rocks
in thin section**, and 117 **Metamorphic rocks in thin section** members. Their
page-ID union has 530 entries; every membership and original row is retained.
The last response for each category has no continuation. The supplied scouting
counts are not used as the inventory.

`ordering.json` records the handoff seed `hazy-curatorial-rocks-in-thin-section-v1`
and the complete hash ordering. IDs are the first 20 hex digits of SHA-256 of
UTF-8 `hazy-curatorial-triplet-v1` + LF + leaf slug + LF + exact frozen title.
Ordering is ascending SHA-256 of seed + LF + candidate ID, with ID tie-break.
The first 50 eligible candidates are reached at rank 55. Reviews extend through
rank 60, including reviewed reserve; reserve review does not change the cutoff.

## Scope and uncertainty

Actual thumbnail sheets were inspected for microscope-scale rock microstructure
and documented repeated specimens/views, not beauty, resemblance or typicality.
Monochrome fields, historic micrographs, annotated images, paired optical panels
and documented polarized transmitted-light scans are retained where the mineral
microstructure dominates. The whole-slide photograph at rank 39 and the roughly
half-diagram composite at rank 60 were rejected. Rank 48 is an unsupported video;
no preview was fetched or visual judgment fabricated for it.

Ranks 29 and 51 are excluded alternate-polarization views of ranks 27 and 43:
Opacit3 LPL/XPL and Omphacit retrograd LPL/XPL. Matching field outlines, titles,
authors and descriptions establish the relationships. Different mineral types
or a shared photographer do not establish a repeat. Unknown specimen identities
remain null. The complete decisions, inspected-sheet/preview hashes, work keys
and raw file-page evidence are retained under `provenance/`.

Rank 16 names D.L. Whitney as photographer but carries a PD-user-en release by
Fe3Al2Si3O12 without a verified identity/authority link. It remains deferred,
not acquired or silently rejected. The 35 later selections remain provisional
for reconciliation if that case is resolved. File-specific license claims and
credits are in [SOURCES.md](SOURCES.md); reported Artist, photographer, original
creator, digitizer and current file-version uploader remain separate. Source
claims are recorded, not independently authenticated.

## Acquisition and checks

The active Commons transport was adapted into the narrowly scoped
[three-category tools](../tools/README.md). Requests are serial and cached, with
at least three seconds between requests, a truthful User-Agent, `maxlag=5`,
no automatic retries, and a shared stop latch. One preview and one source pilot
preceded bounded batches. There were no transport or decoding stops in this leaf.

41 sources use nominal 1600px requests and nine use separately requested 1280px
renditions because the larger API request offered an oversized unscaled original.
Two 500px GIF originals required explicit 640px preview metadata; their verified
preview bytes were reused by exact API URL for the source without another
transfer. The TIFF original at rank 40 uses an API-served JPEG. All acquired
bytes retain source framing, color and orientation metadata: 47 JPEGs, two static
GIFs and one PNG. No local source crop, resize, rasterization or re-encoding occurs.

`images/` contains byte-identical copies of the preserved `sources/` renditions.
`previews/` holds contact sheets, review images and diagnostic bodies, outside
comparison inputs. All media is Git-ignored. Publication was staged, checked,
then published with overwrite guards and checked again. The prior-identity audit
covers 15 integrated leaves with 1,113 inputs and 4,108 available frozen candidate
entries; it found no selected overlap. Its recorded coverage remains fixed for
offline rechecks. An absent exact match does not prove independent specimens.

The manifest kind is `curatorial_heap`, with `curatorial_selected` records.
Family IDs connect each source to its own unchanged input copy only. There is
no visual prompt, child heap, expected pair, matching label or known-shift family.
No router or comparison experiment was run.

From the repository root, with Pillow 12.0.0 installed:

```sh
python3 Fixtures/Heaps/Curatorial/Rocks-in-Thin-Section/tools/intake.py check
python3 -m unittest discover -s Fixtures/Heaps/Curatorial/tools -p 'test_*.py'
```

The offline check replays population, order and decisions; verifies API evidence,
reviewed previews, source and input hashes, decoded dimensions, rights records,
catalogs, batches, contact sheets, diagnostics and empty pair expectations.
The original six handoff files are preserved byte-identically under
`provenance/supplied/`; `provenance/intake.json` records their hashes and cleanup.
