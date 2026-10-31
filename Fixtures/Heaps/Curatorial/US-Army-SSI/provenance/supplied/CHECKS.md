# Completion checks and reporting

**Deliverable:** One Curatorial leaf, `Fixtures/Heaps/Curatorial/US-Army-SSI/`, containing up to 200 defensibly distinct U.S. Army shoulder-sleeve insignia designs from a frozen PetScan depth-5 File-namespace population. It is a **peer of `POTY/` with zero sub-heaps**.

## Must be verifiable offline

1. **Population:** Raw PetScan export and exact query preserved with time, digest, unique-result count, titles/IDs; no silent truncation or re-crawl. `inventory.json` reconstructs the export without fabricated entries.
2. **Selection:** Stable IDs and one fixed seeded order. `ordering.json` matches a fresh offline recomputation; `selection.json` replays exclusions and reaches the recorded selected count. Every accepted design has a recorded source basis; duplicate representations of one design cannot both be selected. No one-creator cap or aesthetic balancing.
3. **Provenance:** Original Commons identity distinct from acquired rendition identity. Rights and designer/artist/uploader roles retain evidence and nulls. Cross-fixture audit states available inventories, match fields, collisions and limits. Source relationships remain uncertain where not established.
4. **SVG/raster:** Test at least an SVG-original → Commons PNG-rendition case and a raster-original case. Each retains original page ID, title, SHA-1 and MIME separately from downloaded URL, rendition kind, MIME, actual dimensions, format, byte count and SHA-256; no local rasterization. Media outside bounds is refused or resolved by an explicit separate API request.
5. **Transport:** Tests cover `maxlag` JSON under HTTP 200, 429 with `Retry-After`, an interrupted HTTP 200 body, cache hash mismatch, size-specific metadata caching, and the persistent stop-and-explicit-resume behavior. No automatic retries.
6. **Fixture:** Every `images/` entry is in the manifest and has one preserved, byte-identical `sources/` counterpart. Checksums, dimensions, CSV, credits, source mapping, batch coverage and the selection record agree. `kind=curatorial_heap`, `relation_kind=curatorial_selected`, no `prompt.json`, empty expected probes/pairs. The local checker succeeds with actual assets present.
7. **Layout:** `US-Army-SSI/` directly beneath `Heaps/Curatorial/`; no child category collections. Image data and archives remain Git-ignored. The Curatorial index reports final counts and links to the new leaf.

## Tests and stopping policy

Follow the current POTY test discipline, but implement tests specific to PetScan inventory handling, distinct-design exclusion, SVG renditions, and the single-leaf layout. Do not assert unrun tests or claim to have viewed images that were not available locally.

**Target = 200**, not a quota overriding source integrity. The 30-image abandonment threshold adopted for *visual-prompt sub-heap additions* is not automatically a rule for this Curatorial contribution. If 200 viable designs cannot be established, report the actual count and the reason for shortfall. Never pad with duplicates. If transport stops, report *selected*, *acquired*, and *pending acquisition* independently; do not alter selection merely because acquisition failed.

Final short report: source export count (and previous 1,641 observation if different), deduplicated File identities, entries examined, designs selected, sources acquired, exclusions by reason, unresolved design/provenance issues, transport stops, rights coverage, actual output path, tests run/results, commit SHA, and any Git-ignored assets not included in the repository.

This task ends with a reproducible curated source population, not a similarity finding or a router experiment.
