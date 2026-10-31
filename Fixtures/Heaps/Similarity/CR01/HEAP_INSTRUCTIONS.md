# CR01 — Cool, repetitive rectangles: heap instructions

Element: `cool-repetitive-rectangles`. Existing fixture kind: **`prompt_heap`**.
These instructions record the sourcing handoff and its intake contract. See
[README.md](README.md) for the current local review and integration status.
The supplied handoff alone is not proof of visual membership.

## Intent

**Visual prompt:** Photographs visually dominated by a repeated arrangement of
rectangular cells, frames, panels or modules, often cool gray/blue/green. Compare
at thumbnail scale; the particular depicted objects needn't be the same.

**Exclusions:** Derivatives, alternate crops, known related captures or sequences,
illustrations, synthetic patterns, a single box or window portrait, and images
where repeated rectangles are only an incidental background element. Don't
retain obvious source relationships just to hit a target.

**Looseness:** Rectangles may be uneven, nested, interrupted, differently sized,
or seen in perspective. The frame may include some sky, floor, people or other
material, provided the repeated geometry remains conspicuous. Modest warm accents
are acceptable, but do not systematically replace a cool visual family with
bright colorful façades.

**Target:** ~65 visually selected independent photographs; 50–80 is useful,
not mandatory. Honest shortfall preferred to weak padding.

## Current acquisition baseline

Read current `Protonk/hazy` tools before work. This pack was prepared from
commit `88832e40aada84dc7c512868f0d1497c1abcd4b1`, active
`Fixtures/hazy_ps01/` (`README.md`, `HEAP_INSTRUCTIONS.md`, `requirements.txt`,
`tools/`). **Do not copy** archived scripts from
`Fixtures/hazy_ps01/provenance/supplied/tools/`.

After the fixture reorganization, the active local baseline is
`Fixtures/Heaps/Similarity/PS01/`; this contribution is its sibling `CR01/`.
The paths above identify the pinned historical commit. The local preparation
helper uses the current layout and verifies the same seven source-tool hashes.

The local `tools/prepare.py` can verify and copy seven pinned, generic active
scripts for previewing, visual review, transport, status and tests. It does not
copy PS01-specific final integration or audit scripts. Adapt those deliberately
for CR01, including names, prompt text, archive identity and the current list of
prior fixture inventories. If the baseline has changed, inspect it rather than
silently falling back.

## Visual review and source acquisition

- Every candidate starts `pending_visual_review` and no visual acceptance is
  asserted in this package. Each actual viewed thumbnail must receive accept,
  reject or defer with a short visual reason. Unviewed images remain pending.
  Review composition, not category names; redirect discovery where needed.
- Keep discovery buckets as acquisition aids, **not** expected similarity
  families. No ground-truth pairs, score thresholds, or core/border/outlier tags.
- Prefer large contact-sheet tiles: 4 columns × 5 rows, 20 per sheet. Preserve
  every obtained preview under `previews/` and actual decoded size/hash.
- Visual acceptance is independent of source acquisition. Accepted images remain
  accepted during HTTP/API/transport failures; the pending ID list is explicit.
- Use one ~320px pilot, then serial paced requests and caches, then review, then
  one accepted ~1600px source pilot. Trust only MediaWiki API-returned URLs; track
  actual dimensions. If API offers an unscaled original exceeding bounds, make
  an explicit smaller (`1280`) API request, never assemble a CDN URL yourself.
- Stop and preserve diagnostics on 403/429/503/529, JSON `error` (including
  `maxlag`) despite HTTP 200, timed-out HTTP 200 bodies, image decode failures,
  or unexpected redirects. No automatic retries or identity rotation. Resume
  only after deliberate review/acknowledgement of the recorded error.
- Hash-check cached files; avoid concurrent JSONL/CSV writes. Keep source
  identities stable from preview to rendition, using original SHA-1, Commons
  page ID, exact and resolved title, and acquired-byte SHA-256 distinctly.
- Check licenses from file-specific API data and keep raw responses, credits,
  missing license URL, and unknown creators without invention.
- Compare against prior fixtures when inventories are supplied, covering
  `source_sha256`, titles in `subject`, Commons `curid` URLs, page IDs, original
  SHA-1 and bytes where available. Report checked coverage, not independence.
  Flag possible sequences with candidate IDs and reasons.
- `sources/` is for successful acquired media; `previews/` for previews and
  incomplete media; `provenance/` for API responses, logs, rights evidence,
  hashes, correspondence and uncertainties. Use canonical `candidates.jsonl`
  with CSV regenerated from the union of all fields.
- Preserve source image bytes and framing. Integration produces opaque inputs,
  final manifests, batch descriptions, checksums, and a `prompt_heap` fixture.
  Only `images/` are comparator input; media/archive assets remain Git-ignored.

## Handoff boundaries

This pack supplies 168 title-level leads from Commons category listings,
**not** 168 visually accepted images. No thumbnails/media or API metadata were
acquired in the sourcing runtime (DNS failure). `provenance/` includes that
observation and the exact-title overlap check against three earlier sourcing
catalogs. More comprehensive cross-fixture audit requires local inventories.

The local integrator remains responsible for inspecting actual preview bytes,
reviewing rights, downloading accepted sources, running the full offline checks,
and committing textual evidence. Shortfalls and pending work remain visible.
