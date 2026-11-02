# Hazy prompt_heap acquisition contract

This is the recurrent procedure for adding one visually loose element to the existing `prompt_heap` fixture type. It does **not** authorize a new fixture kind, ground-truth membership taxonomy, or automatic similarity-based selection.

1. **Intent.** State the short visual prompt, exclusions, allowable looseness, approximate target count, and target heap/element. The count is a target, not a minimum; report shortfall frankly.
2. **Discovery and inspection.** Candidate search buckets are discovery aids. Inspect **actual thumbnail bytes** (contact sheets may be used). Record `accept`, `reject`, or `defer`, with a short visual reason. Explicitly keep unviewed leads `pending_visual_review`—a title, textual description, or Commons category is not a visual review. Preserve intuition or "vibes" without numerical thresholds or invented membership labels.
3. **Stable identities.** Use stable candidate IDs and exact `File:` titles, Commons file-page URLs and discovery URLs. Preserve all preexisting `candidates.jsonl` fields. Maintain JSONL as the canonical source; regenerate any CSV from those exact records.
4. **Evidence.** Bundle previously acquired preview bytes and contact sheets under `previews/`. Retain metadata responses, discovered rendition URLs, actual decoded dimensions, byte hashes, creators, licenses and review notes under `provenance/`. Unknown values are `null` rather than inferred. Preserve acquired image bytes; don't secretly re-encode or recrop.
5. **Provenance.** Exclude originals, crops, adjacent capture sequences, and reposts of the same source. When earlier heap inventories are supplied, check exact titles, upstream source IDs, and acquisition hashes against them. Different filenames, dates or photographers **do not** prove independence; record uncertainty. No expectation of pairwise links exists in this prompt_heap collection.
6. **Commons access.** Start with **one** small preview. Use paced serial requests, local caching and only API-returned rendition URLs. On 403/429/503/529 or other access/rate-limit errors, stop and preserve status, `Retry-After`, relevant response headers and diagnostic text. Don't bypass blocks. A nominal size (e.g. 1600px) is not a guarantee; record actual downloaded dimensions.
7. **Handoff.** Deliver data and a short README, with the acquired evidence attached. Let the local integrator assign comparison-facing opaque names, generate final manifests, batches and checksums, and validate files. Keep the existing `prompt_heap` type.

## SF01 specifics

- **Element:** `speckled-fields`.
- **Short prompt:** Many small separated objects or marks against a comparatively continuous field, with thumbnail-scale dotted or speckled appearance; subject matter may differ entirely.
- **Exclusions:** Known provenance links, synthetic patterns, non-photographs, and single dominant foreground objects.
- **Looseness:** Sparse/dense, regular/irregular, bright/dark, natural/artificial, distant/close; do not require identical object counts or colors.
- **Target:** ~65 accepted images, preferably 50–80 if sources support it; incomplete acquisition is not failure if accurately reported.
