# TG01 — Tangles of growth: Similarity heap contribution contract

Existing fixture kind **`prompt_heap`**, addition `TG01`, destination `Fixtures/Heaps/Similarity/TG01/`. This file records intent and the acquisition/review handoff; it does not declare reviewed membership.

## Intent

**Prompt:** Photographs visually dominated by interlaced, densely overlapping natural plant growth: roots, vines, tangled stems, brambles, branches, leaves, and grasses. Follow the *composition*, not the botanical subject or category name. Different subjects and colors may have the same confused, branching/occluding impression.

**Exclude:** related photos, crops/derivatives, synthetic images, isolated portraits of trees/plants or flowers, neat hedges, and landscapes where a path, horizon, building or single large trunk outweighs entangled growth.

**Acceptable looseness:** Green or brown, leafy or bare, fine or thick lines, undergrowth or exposed roots, close or medium range, light or dense occlusion, partial artificial context if the tangle stays dominant. No numerical acceptance threshold, core/border/outlier tags, expected pairs or semantic cluster labels.

**Count:** Aim ~65; planning band 50–80. **Do not publish TG01 with fewer than 30 independently screened, rights-reviewed, actually acquired and validated inputs.** If finished review yields fewer than 30 viable candidates, abandon TG01 rather than dilute its prompt or fill with obvious related captures. Preserve all evidence and record the shortfall. An unresolved download failure is `incomplete_acquisition`, not grounds to reverse visual acceptance or automatically abandon.

## Use current active baseline

This sourcing package reads `Protonk/hazy` `main` commit `f94e3c57655c3983e1875507836877a5263e9f00`, after the fixture reorganization. Active baseline is `Fixtures/Heaps/Similarity/PS01/`, with the CR01 integration alongside it. The archived `provenance/supplied/tools/` versions are not active. `tools/prepare.py` pins and copies seven common PS01 tools from the local repo checkout. If hashes differ, inspect changes and adapt consciously. Current `audit.py`/`integrate.py` are contribution-specific and must be adapted for TG01 and the full prior-inventory coverage.

## Visual review, provenance and transport

1. Each lead begins `pending_visual_review`. View actual acquired previews early. Record `accept` / `reject` / `defer` and a concise *visual* reason per inspected candidate. Never accept a title or category as proxy for appearance. Keep unviewed IDs pending. Redirect discovery when it produces single-object portraits or unrelated landscapes. Contact sheets: four columns × five rows.
2. Keep visual acceptance, license/provenance review and source acquisition separate; an accepted file remains accepted through a transport interruption. Keep pending and abandoned states explicit.
3. Preserve candidate IDs, exact and resolved Commons titles, file-page/discovery URLs, page IDs, original SHA-1, acquired-byte SHA-256 and all supplied JSONL fields. Rebuild CSV from union of JSONL columns. Unknown values remain null; retain raw API replies.
4. Exclude duplicates and related captures using metadata, dates, source IDs, hashes, actual previews and obvious shared views. Check prior `Relationships/` and `Similarity/` inventories, report coverage; note doubts and possible sequences with candidate IDs. Distinct titles and photographers cannot certify independence.
5. Review Commons rights evidence file by file; a missing `license_url` is not itself disqualifying. An unreported author is null, not an invented name. Record raw metadata and uncertainty.
6. Pilot one ~320px preview, then use serial requests with truthful User-Agent, `maxlag=5`, ≥3 seconds pacing and checked caches. Follow only API-returned rendition URLs, not guessed CDN paths. Stop, retaining diagnostics and media partials, on 403/429/503/529, API `error`/`maxlag` inside HTTP 200, incomplete HTTP 200 bodies, unexpected redirects, image decoding errors or other failed requests. Require explicit acknowledgment before resuming; no automatic retry or concurrency.
7. Source acquisition comes *after* preview review and individual rights/provenance reviews. Pilot a larger nominal ~1600px file and verify original SHA-1/page ID/rights still match the reviewed source; record requested and actual decoded dimensions, format, URL and hashes. Handle oversized API-reported originals only through a separate API request for a smaller rendition (e.g. 1280px), retaining separate cached metadata for both sizes. Do not recrop or re-encode.
8. Successful downloaded media → `sources/`; small previews, contact sheets and partial media → `previews/`; API metadata, transport, review decisions, credits, licenses, provenance notes → `provenance/`. The local integrator assigns opaque `images/` input names and makes validated manifests/batches/checksums, with `kind=prompt_heap`, no expected pairs, and **>=30 verified published inputs**. Abandoned contributions retain their candidate/review evidence instead of becoming a too-small fixture.

## Supplied handoff status (historical)

152 exact Commons file-title leads supplied; none visually inspected or accepted and no media acquired in the sourcing runtime. Four previous sourcing-catalog title checks found no exact overlaps, but comprehensive local identity audit remains outstanding. The current Git-ignored media and prior archives are not accessible through GitHub. `tools/minimum_gate.py` illustrates and tests the minimum-count rule, but is not a substitute for the integrator's full checks.

Current review and acquisition status is recorded in [README.md](README.md). The unchanged supplied contract remains in `provenance/supplied/HEAP_INSTRUCTIONS.md`.
