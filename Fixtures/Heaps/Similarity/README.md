# Similarity heap

This heap collects images in groups chosen to look alike under short visual
prompts. Selection is based on observed composition and visual impression across
subjects. Provenance is checked to exclude known duplicates or related captures;
it does not define visual similarity here.

| Contribution | Originally acquired / supplied leads | Selection prompt | Status |
|---|---:|---|---|
| [Red-Accents-in-Green](Red-Accents-in-Green/README.md) (RG01) | 31 / 107 | Small red accents in predominantly green outdoor photographs | Reviewed; selected sources acquired |
| [Speckled-Fields](Speckled-Fields/README.md) (SF01) | 48 / 142 | Small separated marks or objects across a continuous field | 59 visual accepts; 11 downloads pending after a recorded timeout |
| [Pale-Skies-Dark-Ground](Pale-Skies-Dark-Ground/README.md) (PS01) | 58 / 145 | Pale quiet upper skies above darker, detailed lower regions | Reviewed; selected sources acquired |
| [Repeated-Rectangles](Repeated-Rectangles/README.md) (CR01) | 57 / 168 | Cool, repetitive rectangular cells, panels or frames | Reviewed; selected sources acquired |
| [Tangled-Growth](Tangled-Growth/README.md) (TG01) | 31 / 152 | Dense interlaced, overlapping plant growth | Reviewed; selected sources acquired |
| [Spreading-Patches](Spreading-Patches/README.md) (BSP01) | 68 / 185 | Irregular spreading, merging or fragmenting surface regions | Reviewed; selected sources acquired |

Current membership is in the [generated collection totals](../../COLLECTIONS.md).
Each folder is named for its prompt; the short code in parentheses was the folder
name until November 2026 and remains in fixture IDs, candidate IDs and records.
The [rename record](../../provenance/similarity-names-2026-11/README.md) maps old
paths to new ones.
Each new contribution belongs to this same heap and retains its short prompt, exclusions,
acceptable looseness, source evidence and per-image decisions. Counts are targets,
not quotas; Tangled-Growth and Spreading-Patches additionally enforce their supplied 30-input publication minimum.
Download failures do not change visual acceptances.

The prompts record human choices about appearance. Images can resemble images
in other collections, and membership does not prescribe a comparison result.
Discovery categories helped find candidates. Only acquired `images/` entries
listed in a contribution's manifest are available for sampling.

Integrated contributions retain `kind=prompt_heap`, empty pair expectations and
the [shared fixture format](../../FORMAT.md). Their local validators check files
and evidence; the shared relationship checker does not support this kind.

For acquisition and review, use the active [Pale-Skies-Dark-Ground tools](Pale-Skies-Dark-Ground/tools/acquire.py)
and its [sourcing instructions](Pale-Skies-Dark-Ground/provenance/intake/HEAP_INSTRUCTIONS.md) as a starting point,
adapting contribution-specific identifiers and prompts. Archived tools under
`provenance/supplied/` record older handoffs.
