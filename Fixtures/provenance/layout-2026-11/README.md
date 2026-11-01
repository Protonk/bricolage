# November 2026 fixture layout migration

**Complete: all 18 active leaves conform to the single template.** This is the
evidence for a structural hygiene migration, not a new fixture intake.
The baseline is commit `fd04a3e`; fixture media, IDs, membership, source records,
selection decisions and historical evidence must survive unchanged.

The read-only survey found 18 leaves (15 heap contributions, three relationship
sets), 12 common root entries, identical image/source column schemas, and ten
complete root layouts. The modal full layout occurred four times. Seventeen
leaves had previews; eleven had leaf-local tools. Six prompt heaps had candidate
catalogs/prompts, and nine Curatorial leaves had inventory/order/selection records.

The normalization moved active intake evidence under `provenance/intake/`,
construction-only root records under `provenance/construction/`, and live code
and dependency lists into `tools/`. All leaves have a uniform offline check entry
point and evidence index. Archived packages and publications retain their bytes.
SF01's obsolete `acquired/` placeholder was removed; its supplied copy survives.

- `baseline.json`: original layout, identities, commands and SHA-256s for 10,163
  tracked records/tools and local files, including images, sources and previews.
- `baseline-checks.json`: all 25 existing offline validation commands passed.
- `baseline-tests.json`: pre-migration unit-test commands and their actual results.
- `relocations.json`: 71 explicit moves, original hashes, and the one removal.
- `tool-changes.json`: exact before/after hashes for adapted leaf tools. Historical
  PS01 pins and local adaptation receipts remain unchanged; the common resolver
  accepts only these explicitly recorded code changes.
- `pilot-checks.json`, `similarity-relationships-checks.json` and
  `curatorial-checks.json`: checks and preservation results at each migration stage.
- `final-checks.json`: all 18 leaf entry points, including 25 specialized checks.
- `final-tests.json`: 210 tests passed on Python 3.14.9 across 14 suites.
- `completion.json`: final conformance, relocation, sampler and link verification.
- The common contract and starter files are in [Template](../../Template/README.md).

The schema catalogs, core manifests, media paths, import maps and readable source
credits remain at their existing paths and retain their bytes. This protects
historical exact-identity audits and the sampler's existing population snapshot.
Current READMEs and scripts are adapted; historical command strings stay historical.

The final roots have 14 common entries, with only an optional current `AGENTS.md`
in addition. All 71 moves are complete. All 5,927 inventoried local assets are
byte-identical. Of 4,116 original non-code/non-README records, the obsolete SF01
placeholder was removed and Variants' current `AGENTS.md` was updated; its original
bytes survive in `provenance/supplied/AGENTS-before-layout.md`. The other 4,114
records retain their bytes at their existing or explicitly relocated paths.

The sampler still finds 1,263 manifest rows and 1,251 distinct eligible images.
Its inventory ID is unchanged, and the original demonstration draw, annotation
history and current-image verification all pass. No images were acquired or
regenerated, no comparisons ran, and `output/` remains unchanged.

Reviewable stages:

1. `65c822d`: survey, hash baseline, template, scaffold and layout checker.
2. `dc91f4b`: RG01, Evan-Amos and Derivatives pilots; historical audit resolution.
3. `ac7f32d`: remaining Similarity and relationship sets.
4. `198220e`: remaining Curatorial sets, including nested POTY leaves.
5. Final integration: full-check entry point, active documentation/links, and
   completion evidence in this directory.

Recheck the current structure and fixture evidence from the repository root:

```sh
Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full
make -C Fixtures test-fixture-layout
make -C Fixtures test-sampler
```

Original shortfalls and pending acquisition/provenance cases are unchanged.
Archived packages and completed run records deliberately retain creation-time
paths; use each leaf's `provenance/layout.json` to resolve moved evidence.
