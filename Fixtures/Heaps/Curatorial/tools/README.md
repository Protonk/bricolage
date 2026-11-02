# Three direct-category intakes

`three_category.py` and `three_category_publish.py` serve the three scoped leaves
Rocks-in-Thin-Section, Stone-Hand-Axes and Ex-Libris. Each has a leaf-local
`tools/intake.py` entry point; paths and evidence remain relative to that leaf.
The authoritative category names and fixed seeds are the preserved handoff's
`provenance/supplied/CATEGORIES.json`. These tools do not discover arbitrary heaps.

The transport, metadata batching, media acquisition, contact sheets, source
catalogs and staged publication adapt the active Botanical-Illustrations and
Evan-Amos-Uploads tools, which in turn adapt POTY/Pale-Skies-Dark-Ground (then named PS01). Existing contributions'
tools are unchanged. No router or comparison code is invoked.

Network commands (`freeze`, `metadata`, `media`) use a shared intake lock, serial
requests, at least three seconds between responses and the next request, a
truthful User-Agent, `maxlag=5`, and no automatic retries or redirects. A latched
failure in any of the three leaves blocks new network commands. `acknowledge
--diagnosis ...` records an explicit diagnosis without deleting evidence or
retrying a request. Oversized unscaled API originals are recorded as unavailable
before any media request; a different nominal size needs a separate explicit
metadata request. All distinct size-specific responses remain cached.

Activate the Python 3.14.x `Fixtures/.venv` first (`source Fixtures/.venv/bin/activate`
from the repository root). Typical bounded commands, using one leaf's entry point:

```sh
python3 tools/intake.py metadata --start 1 --end 20
python3 tools/intake.py media --start 1 --end 1 --limit 1
python3 tools/intake.py media --start 1 --end 20 --limit 20
python3 tools/intake.py sheets --start 1 --end 20
python3 tools/intake.py review --sheet previews/review-evidence/ranks-0001-0020.jpg < provenance/review-inputs/ranks-0001-0020.json
python3 tools/intake.py metadata --stage source --edge 1600 --start 1 --end 20
python3 tools/intake.py media --stage source --edge 1600 --start 1 --end 20 --limit 1
python3 tools/intake.py build
python3 tools/intake.py check
```

Run from the leaf for these examples. Pillow 12.0.0 is the only nonstandard
Python dependency. Offline checks never download or recreate missing media.
From the repository root, the focused tests are:

```sh
python3 -m unittest discover -s Fixtures/Heaps/Curatorial/tools -p 'test_*.py'
```

The human review records three independent axes: visual scope, work/specimen
provenance, and rights. Each has `accept`, `reject`, or `defer`, with actual
preview and inspected-sheet hashes bound to the record. A clear rejection on
any axis excludes the candidate; unresolved other axes remain recorded.
A deferred candidate with no decisive rejection advances provisionally.
An unreviewed gap blocks later selection. Unsupported non-image media can have
a separate metadata-bound technical exclusion, without a fabricated vision
review. Unknown work keys and creator roles stay null. No author caps,
category quotas, visual scores or matching labels apply.

`review-inputs/` retains the authored decisions; `work-review.json` is the bound
record. Existing reviews cannot be silently overwritten. The offline validator
replays the frozen population, ordering and selection, verifies all media and
review evidence, audits prior source catalogs, all six Similarity candidate catalogs and available
frozen Curatorial inventories,
and checks manifests, credits, byte copies, contact sheets, batches and empty
pair expectations. Historical audit coverage remains fixed after publication.
