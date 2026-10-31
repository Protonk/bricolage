# Curatorial heap

This heap samples images from existing published source populations. The
source's category definitions remain intact; local selection is mechanical and
subject to provenance, rights, supported-file and acquisition checks. No visual
selection prompt, aesthetic balancing or similarity measurement is applied.

| Source collection | Contributions | Current selection |
|---|---|---|
| [Wikimedia Commons POTY](POTY/README.md) | Arthropods; Constructions and buildings; People and human activity | Complete acquisition: 43 / 50 / 50 inputs from the full 2023–2025 Round 1 category lists; Arthropods has a seven-image shortfall |
| [US Army shoulder-sleeve insignia](US-Army-SSI/README.md) | One leaf, no sub-heaps; Commons category membership via PetScan depth 5 | Partial: 29 selected and acquired of a 200-design target; 1,641 frozen File identities; ordered selection held at an unresolved historical-badge scope case |

Curatorial is the heap, POTY is the source collection, and the three category
directories are independent leaf fixture sets. US-Army-SSI is itself a leaf beside
POTY, based on category membership rather than award selection. Only each leaf's manifest-listed
`images/` files are inputs. `sources/` preserves downloaded bytes and `previews/`
holds contact sheets and diagnostic bodies. All three asset directories remain
Git-ignored at this depth; metadata and tools are versioned.

The `curatorial_heap` kind records this sourcing basis without inventing a
visual prompt. It makes no expected pairs, matching verdicts, semantic clusters
or claim of independent capture origins. See the [fixture format](../../FORMAT.md).
