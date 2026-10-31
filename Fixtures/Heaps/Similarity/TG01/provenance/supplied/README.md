# TG01 — Tangles of growth

**Sourcing handoff, not an integrated fixture.** Prepared 2026-10-31 from the current `Protonk/hazy` `main` baseline at commit `f94e3c57655c3983e1875507836877a5263e9f00`.

**152 distinct Wikimedia Commons title-level leads**, **zero visually reviewed**, **zero preview/source files acquired**. A single attempted Wikimedia API request failed during DNS resolution in the sourcing runtime; it was not an HTTP rate-limit response. Every candidate remains `pending_visual_review` until actual preview bytes are inspected locally.

> Photographs dominated by dense, irregular plant growth: branches, vines, stems, roots, leaves and grasses cross, intertwine, overlap and occlude one another so that individual structures become difficult to follow at thumbnail scale.

**Destination:** `Fixtures/Heaps/Similarity/TG01/`, a contribution to the existing **Similarity** heap. Keep `kind=prompt_heap` and empty expected pairs. The other contributions (RG01, SF01, PS01, CR01) share this heap; the natural-growth discovery buckets are not expected clusters.

**Target:** ~65 independently selected photographs (50–80 is a planning band). **NEW floor: 30 viable acquired images.** If careful completed visual/provenance/rights screening leaves fewer than 30 usable images, abandon this contribution rather than pad it. If 30+ are accepted but acquisition is blocked, report it as *incomplete*, not abandoned, until the acquisition outcome is resolved or the contribution is deliberately closed. Do not publish any final fixture with fewer than 30 validated inputs. Preserve the entire discovery/review trail even if abandoned. See `HEAP_INSTRUCTIONS.md` and `tools/minimum_gate.py`.

**Exclusions:** known derivatives, alternate captures or visible sequence duplicates, illustrations/composites/synthetic imagery, isolated trees or individual flowers, neatly clipped hedges, and scenes dominated by a path, building, horizon or prominent single trunk. **Looseness:** dry/winter or lush/tropical growth, different distances, fine or coarse mesh, multiple leaf/branch colors, and partially overgrown structures if the tangle fills the visual field. Do not impose numeric similarity scores or membership labels.

## Sourcing evidence and package files

- `candidates.jsonl` is canonical and supplies stable `tg-0001`…`tg-0152` identities, exact Commons `File:` titles, file-page and discovery URLs, and the established PS01/CR01 fields. Unknowns remain JSON `null`.
- `candidates.csv` is regenerated from the union of the JSONL fields; future API-enriched columns must also be preserved.
- `provenance/discovery_sources.json` and `discovery_seeds.txt` document 13 discovery routes and their actual title lists. This is not thumbnail review.
- `provenance/source_page_observations.jsonl` contains three observed Commons file-page text notes; these are **not** API metadata, reviewed images, or final rights determinations.
- `provenance/possible_sequences.jsonl` identifies a few specific title-level capture questions for local review.
- `provenance/prior_seed_overlap.json` compares exact titles with the four earlier sourcing ZIP catalogs (no overlaps). Local checks must also inspect all prior **integrated** inventories, page IDs, original SHA-1s and byte hashes; distinct identifiers do not prove independence.
- `provenance/transport_probe.json` records the environment's DNS failure; no image or API evidence is invented.
- `provenance/baseline.json` pins current active PS01 helper Git blob hashes and the current repository layout.
- `tools/prepare.py` copies and verifies the seven generic active PS01 helpers from the **local checkout** (not archived `provenance/supplied/tools/`). `tools/check_pack.py` and `tools/minimum_gate.py` plus its tests are self-contained and work offline.
- `sources/` will hold successful acquired source bytes; `previews/` preview images, contact sheets and incomplete media bodies; `provenance/api/` API response evidence. All begin empty.

## Local handoff

The archive contains a top-level `hazy_tg01/` folder. Place its **contents** at `<repo>/Fixtures/Heaps/Similarity/TG01/` (rename that folder to `TG01` under `Similarity/`), then run:

```sh
# In the hazy repo root
python3 Fixtures/Heaps/Similarity/TG01/tools/check_pack.py
python3 Fixtures/Heaps/Similarity/TG01/tools/prepare.py
python3 -m pip install -r Fixtures/Heaps/Similarity/TG01/requirements.txt
python3 -m unittest discover -s Fixtures/Heaps/Similarity/TG01/tools -p 'test_*.py'
export HAZY_USER_AGENT='HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib'
python3 Fixtures/Heaps/Similarity/TG01/tools/acquire.py --stage preview --limit 1
```

After the pilot, inspect actual preview compositions, then proceed in paced, serial chunks using cached API-returned rendition URLs. Run `tools/review.py --template` and `--apply <reviewed.csv>` with a visual reason for every reviewed candidate. Four columns × five rows per contact sheet have been effective. Source acquisition must follow visual acceptance, source-identity checks, and individual rights/provenance review. Test one larger rendition before bulk acquisition.

Stop on HTTP, MediaWiki API, body-read, or decoding errors, including a 200 response with an incomplete body. Preserve partial bodies, headers, last-error latch, and pending IDs. No automatic retries, rotations, fabricated CDN URLs or oversized-original fallback. If an API-offered original violates the nominal size bound, request a separate explicit smaller API rendition, retaining both responses and actual decoded dimensions.

Use `python3 Fixtures/Heaps/Similarity/TG01/tools/minimum_gate.py` as a *count report*, not a replacement for the full audit; `--strict-publish` refuses fewer than 30 hashed acquired files. Local integration must separately enforce at least 30 validated published inputs and all usual source, rights, preview, checksum, manifest, and source-independence evidence checks. Adapt the active PS01/CR01 `audit.py` and `integrate.py` for TG01; these tools encode PS01/CR01-specific identities and previous-inventory lists and must not be copied unchanged. Publish only to fresh staging and output paths; preserve original image bytes/framing and use opaque input names.

The final archive and fixture manifests are produced by the local integration agent, not by this title-level sourcing package. GitHub holds committed textual evidence; image files remain Git-ignored and local.
