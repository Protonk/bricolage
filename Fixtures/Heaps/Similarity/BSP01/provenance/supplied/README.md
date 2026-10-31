# BSP01 — Blotches, Stains, and Spreading Patches

**Sourcing handoff; not an integrated fixture.** Prepared 2026-10-31 from `Protonk/hazy` main `6f789b0c36246aaa697dbee800e9c1e6c82d56f0`. Destination: `Fixtures/Heaps/Similarity/BSP01/`. **Kind:** `prompt_heap`.

**185 distinct Commons title-level leads**, **zero visually accepted**, **zero media acquired**. All candidates remain `pending_visual_review`, since Wikimedia media/API hosts cannot be resolved in this sourcing runtime. Category listings are not thumbnail inspection. See `provenance/transport_probe.json` for the network diagnosis.

> Photographs where irregular patches expand, merge, break into islands, or fade across a continuous surface or field: lichens, rust, peeling paint, algae, salt/mineral films, stains, or analogous effects on other materials.

Unlike Speckled Fields, emphasize **contiguous or merging regions**, not many separated dots. Unlike Tangles of Growth, emphasize boundaries between surface regions, not interlaced fine lines. Preserve visual looseness across material, scale, hue and camera distance, but reject photographs where the blotched surface is incidental or overpowered by an object or conventional scene composition. These differences describe sourcing intent, not similarity truth.

**Target:** about 65, ordinary planning range 50–80. **Minimum viable input count: 30.** Under 30 after completed visual + provenance screening → abandon rather than pad. An unresolved download shortfall is a separate, incomplete acquisition state, not a rejection. No acceptance, license clearance, or independent-capture claims are made in this source-only ZIP.

## What's supplied

- `candidates.jsonl` canonical list with stable IDs `bsp-0001`…`bsp-0185`; `candidates.csv` generated from union of JSONL fields. Every title has exact Commons `File:` identity, file-page URL and discovery category link. All unknown media identities, license/creator and sizes remain `null`.
- `provenance/discovery_sources.json` and `discovery_seeds.txt`: 13 documented category discovery routes (lichen, painted/coated surfaces, corrosion, algal blooms/mats, efflorescence, mineral and concrete surfaces). These are sourcing buckets, not target clusters or quotas.
- `provenance/possible_sequences.jsonl`: source-relationship questions that deserve follow-up with actual metadata and previews, without preemptively rejecting candidates.
- `provenance/source_page_observations.jsonl`: two text-only Commons file-page observations; *not* acquired previews, rights clearance or imageinfo API responses.
- `provenance/prior_seed_overlap.json`: exact-title check against five previous **sourcing packages** (0 hits). Local integrator must check full **integrated** fixture inventories and source identities.
- `provenance/transport_probe.json`: an attempted MediaWiki API access that failed before HTTP. No preview or full image was retrieved.
- `provenance/baseline.json`: latest active PS01 script Git blob pins, known repo layout, and current head. No archived tools substituted.
- `tools/prepare.py`: copy/verify seven generic **active** PS01 review/acquisition helpers. `tools/check_pack.py`: offline integrity test; `tools/minimum_gate.py`: count report and basic publication floor assertion with separate tests. `audit.py` and `integrate.py` require contribution-specific adaptation by local agent.
- `requirements.txt`: Pillow==12.0.0. `sources/`, `previews/`, and `provenance/api/` are empty placeholders to receive evidence without inventing downloads.

## Local handoff

Extract the archive's `hazy_bsp01/` contents to `<hazy repo>/Fixtures/Heaps/Similarity/BSP01/` (the destination folder name is uppercase). From the repository root:

```sh
python3 Fixtures/Heaps/Similarity/BSP01/tools/check_pack.py
python3 Fixtures/Heaps/Similarity/BSP01/tools/prepare.py
python3 -m pip install -r Fixtures/Heaps/Similarity/BSP01/requirements.txt
python3 -m unittest discover -s Fixtures/Heaps/Similarity/BSP01/tools -p 'test_*.py'
export HAZY_USER_AGENT='HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib'
python3 Fixtures/Heaps/Similarity/BSP01/tools/acquire.py --stage preview --limit 1
```

Then inspect preview *composition* (4 columns × 20 per sheet), record decisions and reasons with `review.py`, check provenance and individual licenses, and pilot one larger source. Continue only through cached, paced, serial API-returned rendition requests; follow the stop-on-error contract in `HEAP_INSTRUCTIONS.md`. `tools/minimum_gate.py --strict-publish` checks the 30-image floor but does not replace full rights/provenance/manifest integration checks. Local integration produces opaque input names and final archive. Nothing is pushed or committed by this source package.

If a category yields nothing but isolated objects, architectural context or uniform textures, reconsider discovery rather than relaxing the visual prompt to reach 30. The reviewed collection may be small; the full review trail remains useful even if BSP01 is abandoned.
