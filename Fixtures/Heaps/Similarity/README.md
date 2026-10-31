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

The five integrated contributions currently provide 225 inputs. Each new
contribution belongs to this same heap and retains its short prompt, exclusions,
acceptable looseness, source evidence and per-image decisions. Counts are targets,
not quotas; TG01 additionally enforces its supplied 30-input publication minimum.
Download failures do not change visual acceptances.

These are human-selected collections, not semantic router cluster names,
membership ground truth, disjoint partitions or expected pair results. Images
can resemble images in other contributions. Discovery categories within a pack
are search aids, not additional expected groups. Only acquired `images/` entries
listed in a contribution's manifest belong to the current comparison pool.

Integrated contributions retain `kind=prompt_heap`, empty pair expectations and
the [shared fixture format](../../FORMAT.md). Their local validators check files
and evidence; the experiment's pair-fixture checker does not support this kind.

For acquisition and review, use the active [PS01 tools](PS01/tools/acquire.py)
and its [handoff contract](PS01/HEAP_INSTRUCTIONS.md) as the current baseline,
adapting contribution-specific identifiers and prompts. Archived tools under
`provenance/supplied/` record older handoffs. No acquisition or similarity
measurement is implied merely by a folder being listed here.
