# Similarity heap

This heap collects images in groups chosen to look alike under short visual
prompts. Selection is based on observed composition and visual impression across
subjects. Provenance is checked to exclude known duplicates or related captures;
it does not define visual similarity here.

| Contribution | Acquired inputs / supplied leads | Selection prompt | Status |
|---|---:|---|---|
| [RG01](RG01/README.md) | 31 / 107 | Small red accents in predominantly green outdoor photographs | Reviewed; selected sources acquired |
| [SF01](SF01/README.md) | 48 / 142 | Small separated marks or objects across a continuous field | 59 visual accepts; 11 downloads pending after a recorded timeout |
| [PS01](PS01/README.md) | 58 / 145 | Pale quiet upper skies above darker, detailed lower regions | Reviewed; selected sources acquired |
| [CR01](CR01/README.md) | 57 / 168 | Cool, repetitive rectangular cells, panels or frames | Reviewed; selected sources acquired |
| [TG01](TG01/README.md) | 31 / 152 | Dense interlaced, overlapping plant growth | Reviewed; selected sources acquired |
| [BSP01](BSP01/README.md) | 68 / 185 | Irregular spreading, merging or fragmenting surface regions | Reviewed; selected sources acquired |

The six integrated contributions currently provide 293 inputs. Each new
contribution belongs to this same heap and retains its short prompt, exclusions,
acceptable looseness, source evidence and per-image decisions. Counts are targets,
not quotas; TG01 and BSP01 additionally enforce their supplied 30-input publication minimum.
Download failures do not change visual acceptances.

The prompts record human choices about appearance. Images can resemble images
in other collections, and membership does not prescribe a comparison result.
Discovery categories helped find candidates. Only acquired `images/` entries
listed in a contribution's manifest are available for sampling.

Integrated contributions retain `kind=prompt_heap`, empty pair expectations and
the [shared fixture format](../../FORMAT.md). Their local validators check files
and evidence; the shared relationship checker does not support this kind.

For acquisition and review, use the active [PS01 tools](PS01/tools/acquire.py)
and its [sourcing instructions](PS01/provenance/intake/HEAP_INSTRUCTIONS.md) as a starting point,
adapting contribution-specific identifiers and prompts. Archived tools under
`provenance/supplied/` record older handoffs.
