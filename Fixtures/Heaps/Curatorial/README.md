# Curatorial heap

This heap collects images from existing published source populations. Each
contribution records its sampling or exhaustive membership rule. The
source's category definitions remain intact; local selection follows each
contribution's recorded order and scope, provenance, rights, supported-file and
acquisition checks. Some contributions reject obvious category outliers through
documented thumbnail review. No aesthetic balancing or similarity measurement
is applied.

| Source collection | Contributions | Current selection |
|---|---|---|
| [Wikimedia Commons POTY](POTY/README.md) | Arthropods; Constructions and buildings; People and human activity | Complete acquisition: 43 / 50 / 50 inputs from the full 2023–2025 Round 1 category lists; Arthropods has a seven-image shortfall |
| [US Army shoulder-sleeve insignia](US-Army-SSI/README.md) | One leaf, no sub-heaps; Commons category membership via PetScan depth 5 | Target reached: 150 selected and acquired from 1,641 frozen File identities; eight earlier cases remain pending, with later selections provisional |
| [Botanical Illustrations](Botanical-Illustrations/README.md) | One leaf, no sub-heaps; direct Commons category membership via PetScan depth 0 | Partial acquisition: 149 of 150 selected works acquired from 709 frozen File entries; one transfer pending, 14 earlier selection cases unresolved |
| [Evan-Amos category uploads](Evan-Amos-Uploads/README.md) | One exhaustive leaf; direct File members minus three exact user exclusions | Complete: 136 frozen members, exactly three user exclusions, all 133 included files acquired; zero pending |
| [Rocks in Thin Section](Rocks-in-Thin-Section/README.md) | Three direct category lists, one leaf; fixed order and thumbnail scope review | 50 selected and acquired; one earlier rights case deferred |
| [Stone Hand Axes](Stone-Hand-Axes/README.md) | Three direct category lists, one leaf; photographs and archaeological drawings | 50 selected and acquired; three earlier cases deferred |
| [Ex Libris](Ex-Libris/README.md) | Three direct category lists, one leaf; bookplates and printed ownership emblems | 50 selected and acquired; eight earlier cases deferred |

Curatorial is the heap, POTY is the source collection, and the three category
directories are independent leaf fixture sets. US-Army-SSI is itself a leaf beside
POTY, as are Botanical-Illustrations and Evan-Amos-Uploads; these use category
membership rather than award selection. Rocks-in-Thin-Section, Stone-Hand-Axes
and Ex-Libris are also independent leaves, each pooling its three configured
direct categories without recursive descent or category quotas. Only each leaf's
manifest-listed `images/` files are inputs. `sources/` preserves downloaded bytes and `previews/`
holds contact sheets and diagnostic bodies. All three asset directories remain
Git-ignored at this depth; metadata and tools are versioned.

The `curatorial_heap` kind records this sourcing basis without inventing a
visual prompt. It makes no expected pairs, matching verdicts, semantic clusters
or claim of independent capture origins. See the [fixture format](../../FORMAT.md).
