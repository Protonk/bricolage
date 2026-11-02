# BSP01 — Blotches, stains, and spreading patches

**Destination:** `Fixtures/Heaps/Similarity/BSP01/`. **Existing fixture kind:** `prompt_heap`. The source pool is a contribution to the existing **Similarity** heap, not a new heap.

## Intent and floor

**Visual prompt:** Photographs dominated by irregular patches or regions that spread, merge, fragment, bleed, peel, or dissolve across a surface or field. Examples include lichens on stone, corroded or peeling coatings, algal scums, mineral films, discolored masonry, and weathered material. The visual resemblance is in the changing patch *boundaries*, not their depicted subject.

**Exclude:** synthetic patterns, drawings, diagrams, known derivative crops, related captures, isolated spots, repeated discrete marks better suited to SF01, nearly homogeneous surfaces, single-object portraits, or wide context where the pattern is only incidental. A file called "texture" or "lichen" can still be a poor fit.

**Looseness:** close or medium range, some recognizable context, variable scale, density, hues, contrast, fragmentation and patch boundary sharpness. Avoid requiring any exact color palette, object or photographic distance. Natural and built environments are both welcome. No numerical similarity thresholds, core/border/outlier tags, expected pairs or semantic cluster labels.

**Target:** about 65 accepted images, ordinary planning band 50–80. **Hard publication floor: 30** independently screened, rights-reviewed, successfully acquired and validated inputs. If completed visual/provenance screening yields fewer than 30 viable candidates, abandon the sub-heap and retain the review trail rather than dilute its appearance. If at least 30 are visually acceptable but download is blocked, report incomplete acquisition—not automatic abandonment. `minimum_gate.py` is an advisory check; local integration must enforce the floor.

## Current repo baseline

At sourcing time `Protonk/hazy` main is `6f789b0c36246aaa697dbee800e9c1e6c82d56f0`. Current layout is `Fixtures/Heaps/Similarity/`; the previous addition `TG01` has 31 integrated images. The **active** acquisition/review tools live in `Fixtures/Heaps/Similarity/PS01/tools/`. Read the current `PS01/README.md`, `PS01/HEAP_INSTRUCTIONS.md`, requirements, and active `tools/`; archived tools under `provenance/supplied/tools/` are historical. `provenance/baseline.json` pins Git blob hashes. `tools/prepare.py` verifies and copies generic helpers from the active checkout, refusing changed binaries. **PS01 audit/integrate scripts contain fixture-specific names and inventories: adapt deliberately.** Incorporate the TG01 minimum-floor and preview-size failure lessons.

## Acquisition and review contract

1. Each supplied file title is only a *lead*. Pilot one small preview, then inspect actual preview bytes and composition early in four-column × five-row contact sheets. Record `accept`, `reject` or `defer` and a concise visual reason. Unviewed leads remain `pending_visual_review`. If discovery buckets repeatedly produce whole-object views, redirect sourcing before bulk fetching; do not invent visual decisions based on filenames.
2. Visual acceptance, provenance/licensing review and acquisition are **separate axes**. A timeout or missing rendition cannot undo a visual acceptance. Keep all pending IDs and diagnosed errors explicit.
3. Preserve stable candidate IDs, exact `File:` titles, file-page and discovery URLs, resolved Commons titles, page ID, original SHA-1 and acquired-media SHA-256. Keep `candidates.jsonl` canonical; derive CSV from the union of all fields after enrichment. Unknown values stay JSON `null`. Preserve raw API responses and prior review notes.
4. Compare against all available integrated inventories, not only our five prior sourcing ZIPs. Recognize `source_sha256`, `subject` field titles, `curid=` URLs, page IDs and acquired byte hashes. Report coverage; absence of collisions is not proof of capture independence. Examine potential sequences named in `provenance/possible_sequences.jsonl`, preserving candidate IDs and uncertainty. Different filenames, authors or dates don't establish independence.
5. Review file-specific Commons rights and creators with actual metadata; public domain may have no license URL; unknown creator is `null`. This sourcing pack has two **textual file-page observations** only—neither image inspection nor license clearance.
6. Conservatively request MediaWiki `imageinfo` with accurate identified User-Agent, `maxlag=5`, serial pacing (at least three seconds), no concurrent clients, and hash-checked caching. Start with a single preview and a single source pilot after review. Use only API-returned rendition URLs. Never construct CDN paths, rotate identity, or automatically retry errors. On HTTP 403/429/503/529, API JSON `error`/`maxlag` even within HTTP 200, incomplete HTTP 200 bodies, redirected requests, decode failures or oversized previews: persist diagnostics and stop. Explicit acknowledgment is required before a separate attempt.
7. Nominal small preview ~320px and accepted source ~1600px are *requests*, not actual dimensions. Persist requested size, raw API replies, actual returned URL, rendition versus unscaled-original identity (even with changing tracking query parameters), actual decoded size, format, byte hash and byte count. If the returned original exceeds the bound, explicitly request smaller via API (e.g. 1280px). TG01 also required explicit preview-size adjustments after three complete bodies failed the conservative decoded size gate; preserve both metadata responses and failed/partial media rather than silently changing bounds.
8. Successful media → `sources/`; preview tiles, contact sheets, incomplete media → `previews/`; raw API JSON, transfer logs, preview/source identities, rights, license, and uncertainty → `provenance/`. Keep original bytes and framing. Local integration assigns opaque `images/` names and produces manifests, checksums, batches, a final archive, and `prompt_heap` with **empty pair expectations**. Abandoned additions retain discovery/review evidence but are not published as <30-input fixtures.

## Supplied evidence / limitations

- 185 distinct `File:` titles observed in category media lists across 13 discovery routes. None was visually reviewed or downloaded here.
- Exact-title overlap with earlier RG01/SF01/PS01/CR01/TG01 **sourcing catalogs**: 0. This does not cover all integrated prior inventories or prove capture independence.
- `provenance/source_page_observations.jsonl` holds two textual Commons file-page observations, not image bytes or API imageinfo receipts.
- The local transport probe failed at DNS resolution before HTTP; it is neither a 429 nor evidence of Commons throttling.
- All `sources/`, `previews/` and `provenance/api/` directories start empty. Review and file-specific rights work remain local.
