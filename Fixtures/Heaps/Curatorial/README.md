# Curatorial heap

These collections start from published lists of images. Each records whether
it takes every entry or selects from a fixed ordering, and how it handles
duplicates, source credits, rights and unsupported files. Some also use thumbnail
review to exclude images outside the stated scope. The individual guides explain
those decisions and any unfinished reviews or downloads.

Current membership is in the [generated collection totals](../../COLLECTIONS.md).
The acquisition counts below describe the original publications.

| Source collection | Contributions | Acquisition record |
|---|---|---|
| [Wikimedia Commons POTY](POTY/README.md) | Arthropods; Constructions and buildings; People and human activity | Complete acquisition: 43 / 50 / 50 inputs from the full 2023–2025 Round 1 category lists; Arthropods has a seven-image shortfall |
| [US Army shoulder-sleeve insignia](US-Army-SSI/README.md) | One leaf, no sub-heaps; Commons category membership via PetScan depth 5 | Originally 150 acquisitions; one input subsequently removed; eight earlier cases remain pending, with later selections provisional |
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

These leaves use `kind=curatorial_heap`. Category membership explains where an
image came from; it supplies no expected comparison result. See the
[fixture format](../../FORMAT.md).
