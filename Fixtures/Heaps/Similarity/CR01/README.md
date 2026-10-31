# CR01 — Cool, repetitive rectangles

**Sourcing handoff, not an integrated fixture.** Prepared 2026-10-31 for hazy's
existing `prompt_heap` type. The 168 distinct Commons title-level leads have not
been visually inspected; **0 accepted, 0 rejected, 0 deferred, 168 pending**.
No preview or source media bytes were acquired here because Wikimedia hosts did
not resolve in the sourcing runtime. No API requests or media downloads occurred.

> Photographs dominated by repeated rectangular cells, panels, frames or modules,
> often in muted blues, grays, and greens. The pictured subjects may differ.

Target **about 65 accepted photographs**, with 50–80 an indicative band rather
than a quota. The actual quantity depends on real preview inspection and source
independence. Exclude obvious related captures, derivatives, invented patterns,
and images where the grid is barely visible. Perspective, uneven repetition,
nested or interrupted rectangles, modest color variation and some surrounding
context are fine. Read `HEAP_INSTRUCTIONS.md` for the full handoff contract.

## Contents

- `candidates.jsonl` — **canonical**, stable `cr-0001` … `cr-0168` identities;
  exact Commons `File:` title, file-page URL, discovery category URL and PS01
  candidate fields, with missing values represented by JSON `null`.
- `candidates.csv` — generated from the *union* of the JSONL fields.
- `provenance/discovery_sources.json` and `discovery_seeds.txt` — category
  source notes. Buckets are search aids, **not** expected clusters.
- `provenance/prior_seed_overlap.json` — exact title checks against the three
  previous **sourcing packages only**, not current local integrated inventories;
  no exact overlaps found. This does **not** establish provenance independence.
- `provenance/source_page_observations.jsonl` — three observed Commons file-page
  text summaries, **not** raw API response bytes, media previews or final rights
  judgments. More detailed metadata must come from the local Commons API.
- `provenance/transport_probe.json` — environmental DNS diagnostics; no HTTP
  status or throttling inference.
- `provenance/baseline.json` — pinned active PS01 source-tool Git blob hashes
  from `Protonk/hazy` commit `88832e40aada84dc7c512868f0d1497c1abcd4b1`.
- `tools/prepare.py` — copies seven verified current acquisition/review helpers
  from the **active** local PS01 tooling, refusing changed or missing scripts.
  The older `provenance/supplied/tools/` is deliberately not used.
- `requirements.txt` — matches the pinned PS01 Pillow dependency.
- Empty `previews/`, `sources/`, and `provenance/api/` directories are ready for
  actual media and metadata. No phantom contact sheets are supplied.

## Starting locally

This pack now lives at `Fixtures/Heaps/Similarity/CR01/`, alongside PS01 in the
same Similarity heap. Its supplied files and checksum list are preserved under
`provenance/supplied/`; `tools/check_pack.py` verifies that unchanged snapshot.
The preparation helper uses the relocated active PS01 tools and still verifies
their pinned Git blob hashes before copying.

```sh
python3 Fixtures/Heaps/Similarity/CR01/tools/prepare.py
python3 -m pip install -r Fixtures/Heaps/Similarity/CR01/requirements.txt
python3 -m unittest discover -s Fixtures/Heaps/Similarity/CR01/tools -p 'test_*.py'
export HAZY_USER_AGENT='HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib'
python3 Fixtures/Heaps/Similarity/CR01/tools/acquire.py --stage preview --limit 1
```

These use the active, Git-verified PS01 acquisition/review helpers rather than
an older bundled downloader. If the local PS01 scripts differ from the pinned
Git blob hashes, the preparation tool stops; inspect and adapt the current repo
instead of automatically taking a stale copy.

Review the pilot preview's actual appearance, then proceed cautiously in
serial chunks. `tools/acquire.py` uses the API to fetch rendition URLs and
preserves metadata, downloaded bytes, dimensions and errors; never compose
thumbnail CDN URLs by hand. Use `tools/review.py --template` and
`--apply <worksheet>` for visual accept/reject/defer decisions with reasons.
The helper enforces preview evidence before a recorded visual decision. Contact
sheets are four columns by five rows (20 images).

For source acquisition, require individual license and provenance reviews, then
run a one-image source pilot before continuing. If the Commons API returns a
throttling/error response, an HTTP 200 with an incomplete body, or a decoding
problem, stop and retain diagnostics. Do not retry automatically. Actual
unscaled originals can exceed the requested 1600px edge: request a deliberately
smaller 1280px rendition **through the API** if appropriate. Keep visual
acceptance distinct from download status.

**Final integration** is the local agent's responsibility. Adapt PS01's current
`tools/audit.py` and `tools/integrate.py` for CR01 and **all** local prior fixture
inventories; don't copy those PS01-specific scripts unchanged. Preserve
`kind=prompt_heap`, produce final opaque comparison input names, manifests,
checksums and batches, retain acquired bytes and source rights evidence, and
exclude labels for pair correctness or expected clusters. A prompt-heap shortfall
or unresolved source remains explicit.

No similarity scores have been computed; none should be used to choose members.
