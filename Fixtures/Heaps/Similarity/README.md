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
| [Puddle-Inversions](Puddle-Inversions/README.md) (PI01) | 43 / 45 | Puddles or small surface water reflecting part of the scene | Reviewed; selected sources acquired |

Current membership is in the [generated collection totals](../../COLLECTIONS.md).
Each folder is named for its prompt; the short code in parentheses was the folder
name until November 2026 and remains in fixture IDs, candidate IDs and records.
Puddle-Inversions was added in November 2026 under its prompt name, with `PI01`
as its code from the start and `bricolage-pi01-v1` as its fixture ID.
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

For acquisition and review, start from the [Puddle-Inversions tools](Puddle-Inversions/tools/),
which adapt [Pale-Skies-Dark-Ground's](Pale-Skies-Dark-Ground/tools/acquire.py)
[sourcing contract](Pale-Skies-Dark-Ground/provenance/intake/HEAP_INSTRUCTIONS.md)
to a CSV handoff, discover prior leaves for the identity audit from their
manifests, and identify as BricolageFixtureBot. Change the contribution's
identifiers, prompt and immutable supplied fields. Archived tools under
`provenance/supplied/` record older handoffs.
