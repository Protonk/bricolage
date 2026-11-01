# November 2026 fixture layout migration

This is the evidence for a structural hygiene migration, not a new fixture intake.
The baseline is commit `fd04a3e`; fixture media, IDs, membership, source records,
selection decisions and historical evidence must survive unchanged.

The read-only survey found 18 leaves (15 heap contributions, three relationship
sets), 12 common root entries, identical image/source column schemas, and ten
complete root layouts. The modal full layout occurred four times. Seventeen
leaves had previews; eleven had leaf-local tools. Six prompt heaps had candidate
catalogs/prompts, and nine Curatorial leaves had inventory/order/selection records.

The planned normalization moves active intake evidence under `provenance/intake/`,
construction-only root records under `provenance/construction/`, and live code
and dependency lists into `tools/`. All leaves gain a uniform offline check entry
point and evidence index. Archived packages and publications retain their bytes.
SF01's obsolete `acquired/` placeholder is removed; its supplied copy survives.

- `baseline.json`: original layout, identities, commands and SHA-256s for 10,163
  tracked records/tools and local files, including images, sources and previews.
- `baseline-checks.json`: all 25 existing offline validation commands passed.
- `baseline-tests.json`: pre-migration unit-test commands and their actual results.
- `relocations.json`: 71 explicit moves, original hashes, and the one removal.
- The common contract and starter files are in [Template](../../Template/README.md).

The schema catalogs, core manifests, media paths, import maps and readable source
credits remain at their existing paths and retain their bytes. This protects
historical exact-identity audits and the sampler's existing population snapshot.
Current READMEs and scripts are adapted; historical command strings stay historical.
