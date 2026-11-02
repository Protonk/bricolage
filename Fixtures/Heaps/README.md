# Image heaps

A heap groups collections chosen for similar reasons. Each collection keeps its
own images, selection decisions and source records.

| Heap | Selection basis |
|---|---|
| [Similarity](Similarity/README.md) | Collections chosen to look alike under short visual prompts, across potentially different subjects |
| [Curatorial](Curatorial/README.md) | Published source populations, with contribution-specific sampling or exhaustive category membership rules |

Collections built around known source relationships are under
[Relationships](../Relationships/README.md).

The sampler draws from each leaf's manifest-listed `images/` files. Source copies,
previews and pending downloads are outside that pool. Collections can be nested,
as in Curatorial → POTY → Arthropods; paths in a manifest are always relative to
its leaf. The Similarity and Curatorial indexes list the available inputs and
remaining gaps. Each leaf's README gives its check command.

See [the fixture index](../README.md) for intake locations and
[FORMAT.md](../FORMAT.md) for the existing manifest and asset conventions.

## Visual tour

The rebuildable heap picture book at `Fixtures/output/pdf/hazy-heaps-tour.pdf`
is a 36-page tour with large plates, contact sheets and linked image credits.
Its October 2026 edition samples 144 images from the 867 acquired inputs in
its original 12 leaf collections, re-pinned in November 2026 after one insignia
was removed from US-Army-SSI. Later additions are outside that edition.
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
make -C Fixtures setup-python
Fixtures/.venv/bin/python -m pip install -r Fixtures/Heaps/tools/tour-requirements.txt
Fixtures/.venv/bin/python Fixtures/Heaps/tools/build_tour.py
```

The builder checks the edition's recorded leaf roster and counts, the selected input hashes
and decoded dimensions, and the contact-sheet ordering before writing
`Fixtures/output/pdf/hazy-heaps-tour.pdf`. It makes no network requests and changes no
fixture assets. PDF display copies retain full framing and use up to 180 dpi;
source and input bytes remain untouched. The script uses Georgia, Arial and
Arial Unicode from macOS; `--font-dir` can point to another directory containing
those fonts. The PDF and local page renders are Git-ignored. Render checks can
be kept under `Fixtures/Heaps/previews/tour-guide/`.
