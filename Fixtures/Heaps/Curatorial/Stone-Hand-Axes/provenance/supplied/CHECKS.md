# Publication and evidence checks

Run all applicable checks **independently for each of the three leaves**. A validator passing means the recorded state is consistent, not that 50 was reached.

1. **Population:** exactly the three configured *direct* File categories per leaf, with raw categorymember JSON requests/responses, completed continuations, execution time, hashes and unique-ID union. Keep all source category memberships. No recursive category traversal or search supplement. Scouting counts are not treated as exact snapshots.
2. **Order:** deterministic candidate IDs, fixed seed, full ordered population, decisions reconstructable in order; pending cases explicit. No reroll, no category quotas, no discretionary search results.
3. **Vision:** scope reviews only for **actually viewed** previews; candidate ID, path, byte hash and concise reason match the saved sheet/record. No classifier scores or membership ground truth. Unviewed remains pending. Small vision worker decisions may be reexamined but not silently rewritten.
4. **Identity:** frozen `File:` title, Commons page ID and resolved title, original SHA-1/file timestamp, acquired rendition URL and byte SHA-256 stay separate. Audit known alternate captures/objects/printed works and available prior fixture inventories, with coverage and uncertainty recorded.
5. **Rights:** file-specific licenses and role attributions, original raw metadata, unresolved claims null; public domain or no-restrictions statements may have no license URL. Never infer creator from uploader or invent permission.
6. **Transport:** API-returned URLs only, original/rendition classification, requested/reported/decoded dimensions, full-file decode and hashes, size-specific cache, no automatic retries, latched HTTP/API/body errors, partial-body diagnostics and explicit resumption receipts.
7. **Inputs:** every manifest input byte-identical to a preserved `sources/` file; hashes and dimensions match. `images/` is the only comparison directory; media and ZIPs Git-ignored. `manifest.json` and `manifest.csv` agree, along with source catalogs and batch lists.
8. **Semantics:** `kind=curatorial_heap`, `relation_kind=curatorial_selected`; one independent leaf per topic. No nested sub-heaps, `prompt.json`, source-family assertion across files, expected pairs or matching labels. No automatic 30-image floor here.
9. **Publication:** stage first, offline-check, publish with overwrite guards, then final-check. Run relevant unit tests; keep old fixture tests passing. Reconcile Git metadata, check status and commit only completed textual work. Image bytes remain local.

## Final short report (one line per leaf, plus exceptions)

| Leaf | Unique enumerated | Reviewed previews | Scope rejects | Provenance/rights rejects | Deferred | Visually eligible | Selected | Acquired | Remaining | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Rocks-in-Thin-Section | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Stone-Hand-Axes | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Ex-Libris | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

Also name any transport stops, excluded/retained related image pairs, unresolved metadata cases, what prior inventories were compared, the committed SHA, and the location of each local validator. Distinguish deliberate shortfall from incomplete downloads. If a set has 47 eligible and acquired images, report **47**, rather than padding it to 50.
