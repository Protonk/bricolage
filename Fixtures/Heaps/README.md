# Image heaps

Each named heap is a separate pool of images chosen under its own criteria.
A heap's README records those criteria and the contributions that belong to it.
Contributions retain their own source identities, review decisions and acquired
inputs; placing them in one heap does not assert pairwise similarity or dissimilarity.

| Heap | Selection basis |
|---|---|
| [Similarity](Similarity/README.md) | Collections chosen to look alike under short visual prompts, across potentially different subjects |
| [Curatorial](Curatorial/README.md) | Published source populations, with contribution-specific sampling or exhaustive category membership rules |

The `Heaps/` level imposes no common visual criterion. The provenance-led trio lives
separately under [Relationships](../Relationships/README.md).

A heap is organized as contributions with leaf-local `images/`, `sources/`,
`previews/` and evidence. The image pool comprises the acquired comparison inputs
listed in those contributions' manifests. Pending leads and downloaded previews
are not comparison inputs. There is no duplicated top-level image directory.
Contributions may be grouped under a source collection: Curatorial → POTY →
official category. Directory depth does not change leaf-local paths or asset
ignore rules. Validators are identified by each contribution's README.
US-Army-SSI is a single Curatorial leaf beside POTY, with 150 acquired inputs,
explicit pending cases and its own offline validator. Botanical-Illustrations
is another direct Curatorial leaf, with 149 of 150 selected works acquired,
one pending transfer, a distinct-work review and its own offline validator.
Each README separates selected, acquired and pending counts.
Evan-Amos-Uploads is an exhaustive direct-category leaf with three exact user
exclusions and all 133 included files acquired; related captures and alternate
formats remain included.
Rocks-in-Thin-Section, Stone-Hand-Axes and Ex-Libris each combine three direct
category lists into a single leaf, with fixed ordering and recorded thumbnail
scope reviews. Their READMEs distinguish acquired inputs from deferred cases.

See [the fixture index](../README.md) for intake locations and
[FORMAT.md](../FORMAT.md) for the existing manifest and asset conventions.

## Visual tour

The rebuildable heap picture book at `output/pdf/hazy-heaps-tour.pdf`
is a 36-page tour with large plates, contact sheets and linked image credits.
Its frozen October 2026 edition samples 144 images from the 868 acquired inputs
in its original 12 leaf collections. Later additions are outside that edition.
Only the overall image and collection counts appear in the
tour; acquisition details remain in the contribution records.

[tour-guide.json](tour-guide.json) fixes the book's image selection, chapter
order and brief captions. Each contact sheet takes twelve evenly spaced entries
from its leaf manifest; the large plates reuse those entries. These are choices
for presenting the book, not fixture selection decisions or matching claims.
Credits come from the existing import maps and source catalogs, with unknown
artist roles left unknown.

To rebuild on macOS with the acquired local assets present:

```sh
make setup-python
.venv/bin/python -m pip install -r Fixtures/Heaps/tools/tour-requirements.txt
.venv/bin/python Fixtures/Heaps/tools/build_tour.py
```

The builder checks the edition's recorded leaf roster and counts, the selected input hashes
and decoded dimensions, and the contact-sheet ordering before writing
`output/pdf/hazy-heaps-tour.pdf`. It makes no network requests and changes no
fixture assets. PDF display copies retain full framing and use up to 180 dpi;
source and input bytes remain untouched. The script uses Georgia, Arial and
Arial Unicode from macOS; `--font-dir` can point to another directory containing
those fonts. The PDF and local page renders are Git-ignored. Render checks can
be kept under `Fixtures/Heaps/previews/tour-guide/`.
