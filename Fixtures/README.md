# hazy fixtures

Fixtures are organized by why their images were chosen. The provenance
relationship sets and the selected image heaps have different evidential roles.

```text
Fixtures/
  Relationships/
    Derivatives/
    Multiviews/
    Variants/
  Heaps/
    Similarity/
      RG01/
      SF01/
      PS01/
      CR01/
      TG01/
      BSP01/
    Curatorial/
      POTY/
        Arthropods/
        Constructions-and-buildings/
        People-and-human-activity/
      US-Army-SSI/
      Botanical-Illustrations/
```

| Location | Role |
|---|---|
| [Relationships](Relationships/README.md) | The chosen trio: derivation, multiple captures, and variants, with recorded source relationships and comparison probes |
| [Heaps](Heaps/README.md) | Independently selected image pools, each with its own selection criteria |
| [Similarity](Heaps/Similarity/README.md) | One heap assembled from collections chosen to look alike under short visual prompts |
| [Curatorial](Heaps/Curatorial/README.md) | Published source populations sampled mechanically; POTY Round 1 categories, US Army SSI and Botanical Illustrations category membership |

RG01, SF01, PS01, CR01, TG01 and BSP01 belong to the same Similarity heap. They retain their
own acquisition and review records. Their collection membership records human
selection intent; it is not an expected router neighborhood or matching verdict.
Curatorial occupies a sibling directory under `Heaps/`; its POTY source collection
contains three category contributions one level deeper. Their official category
membership is a sourcing fact, not a similarity judgment.
The [US-Army-SSI leaf](Heaps/Curatorial/US-Army-SSI/README.md) sits beside POTY:
150 acquired inputs from 1,641 frozen PetScan results. Eight earlier cases remain
pending; later selections are provisional. It has no sub-heaps.
[Botanical Illustrations](Heaps/Curatorial/Botanical-Illustrations/README.md) is
another single leaf, using 709 frozen direct-category File entries and a target
of 150 distinct works. It has 149 acquired inputs, one pending transfer, and
14 earlier unresolved selection cases; later selections remain provisional.

## Working with the fixtures

- Open the relevant role or heap README, then the leaf set's README for its
  prompt or relationship, status, provenance and check command.
- Put a new contribution inside its intended heap. A new contribution to
  Similarity goes beside RG01, SF01, PS01, CR01, TG01 and BSP01; its prompt, exclusions,
  acceptable looseness and review/acquisition status belong with that contribution.
  Curatorial contributions can sit below their source collection. Read the
  [POTY record](Heaps/Curatorial/POTY/README.md) for its inventories and check commands.
- Preserve supplied records and source bytes. All media, intermediate images and
  archives stay in the leaf set's `images/`, `sources/` or `previews/` directories.
  These directories remain Git-ignored at every depth.
- Read [FORMAT.md](FORMAT.md) for manifests, source records, checksums and the
  distinction between provenance and visual judgments. Existing fixture IDs and
  manifest kinds are unchanged by this organization.

The current experiment still defaults to Derivatives and uses its existing
comparison workflow. Heap collections use their fixture-local validators and
have no expected pairs. A repository checkout contains the text records and
tools; restore local media before running checks that need it.

## Locations and history

| Previous folder directly under `Fixtures/` | Current location |
|---|---|
| `hazy-derivatives-v1` | `Relationships/Derivatives` |
| `hazy-multiview-v1` | `Relationships/Multiviews` |
| `hazy-meme-fixtures-v0` | `Relationships/Variants` |
| `hazy_rg01_sourcing_v01` | `Heaps/Similarity/RG01` |
| `hazy_sf01` | `Heaps/Similarity/SF01` |
| `hazy_ps01` | `Heaps/Similarity/PS01` |
| `hazy_cr01` | `Heaps/Similarity/CR01` |
| `hazy_tg01` | `Heaps/Similarity/TG01` |
| `hazy_bsp01` | `Heaps/Similarity/BSP01` |
| `US-Army-SSI-handoff` (instruction package) | `Heaps/Curatorial/US-Army-SSI/provenance/supplied` |
| `Botanical-Illustrations-handoff` (instruction package) | `Heaps/Curatorial/Botanical-Illustrations/provenance/supplied` |

Active commands and links use the current locations. Preserved supplied files,
completed run records and existing ZIP snapshots retain their creation-time
paths and instructions. Paths inside manifests remain relative to their leaf
set. The move does not alter any source, input or preview bytes.
