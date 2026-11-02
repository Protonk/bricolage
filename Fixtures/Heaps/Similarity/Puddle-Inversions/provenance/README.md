# Evidence index

Live executable code is in `../tools/`. Only `../images/` contains comparison
inputs; sources and previews remain separate and Git-ignored. This index does
not change selection decisions, acquisition status or provenance assertions.

| Record | Role |
|---|---|
| [supplied/](supplied) | The sourcing partner's handoff of 2 November 2026, preserved unchanged with its checksum list. |
| [intake.json](intake.json) | Hashes of the supplied files, their original repository-root location and its removal. |
| [intake/](intake) | Active selection basis: `prompt.json` (brief and final counts), `HEAP_INSTRUCTIONS.md`, canonical `candidates.jsonl` and its union-column CSV. |
| [api/](api) | Raw Commons API reply bytes for every preview and source request, including the explicit 1280px requests. |
| [http_log.jsonl](http_log.jsonl) | One event per HTTP request: status, headers, bytes received and hash; no failures occurred. |
| [review_worksheet.csv](review_worksheet.csv) | The visual decisions as applied, one row per candidate. |
| [review_log.jsonl](review_log.jsonl) | Status transitions with timestamps and preview paths. |
| [visual-review.json](visual-review.json) | Final decision and visual reason per candidate. |
| [relationship-notes.json](relationship-notes.json) | Relationship review and quoted attribution notes from the handoff. |
| [source-review.json](source-review.json) | File-specific license statements with the hash of the API reply they come from; relationship reviews. |
| [identity-audit.json](identity-audit.json) | Exact identity comparison against all 18 other current leaves. |
| [acquisition.json](acquisition.json) | Acquisition receipt: counts, request totals, rendition kinds and resolution adjustments. |
| [import-map.json](import-map.json) | Published input/source mapping; bytes and paths preserved. |
| [integration.json](integration.json) | Result of publishing the integration stage into this leaf. |
| [final-review.json](final-review.json) | Inspection of the published contact sheets, with their hashes. |
| [archive.json](archive.json) | Hash and size of the local handoff archive under `../previews/`. |
| [partials/](partials) | Reserved for incomplete API bodies; empty. |
