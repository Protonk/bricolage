# Image heaps

Each directory here is a separate pool of images chosen under its own criteria.
A heap's README records those criteria and the contributions that belong to it.
Contributions retain their own source identities, review decisions and acquired
inputs; placing them in one heap does not assert pairwise similarity or dissimilarity.

| Heap | Selection basis |
|---|---|
| [Similarity](Similarity/README.md) | Collections chosen to look alike under short visual prompts, across potentially different subjects |
| [Curatorial](Curatorial/README.md) | Mechanical samples from published editorial populations; currently POTY Round 1 categories |

The `Heaps/` level imposes no common visual criterion. The provenance-led trio lives
separately under [Relationships](../Relationships/README.md).

A heap is organized as contributions with leaf-local `images/`, `sources/`,
`previews/` and evidence. The image pool comprises the acquired comparison inputs
listed in those contributions' manifests. Pending leads and downloaded previews
are not comparison inputs. There is no duplicated top-level image directory.
Contributions may be grouped under a source collection: Curatorial → POTY →
official category. Directory depth does not change leaf-local paths or asset
ignore rules. Validators are identified by each contribution's README.

See [the fixture index](../README.md) for intake locations and
[FORMAT.md](../FORMAT.md) for the existing manifest and asset conventions.
