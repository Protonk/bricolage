# One leaf fixture template

Use this template for every Similarity or Curatorial contribution and every
relationship set. Collection/group directories are indexes; only leaves have
manifests. Arbitrary nesting under Heaps or Relationships is supported.

The template deliberately uses `.in` filenames and lives outside both population
roots, so neither the sampler nor legacy audit discovery can mistake it for a set.
Run `../../.venv/bin/python ../tools/new_fixture.py --help` from this directory,
or use the repository-root command below:

```sh
.venv/bin/python Fixtures/tools/new_fixture.py Fixtures/Heaps/Curatorial/My-Set --id my-set-v1 --kind curatorial_heap
```

The destination must be new. The scaffold contains empty catalogs and media
directories; it does not invent prompts, candidate evidence, credits or results.
Complete its README, source catalog and provenance records as part of intake.
Heap kinds require their real intake evidence before validation can pass. Add
the source-specific offline check command to `tools/check.py` before publication.
`check.py --metadata-only` checks structure/catalogs without decoding or requiring
the ignored media directories; it is not an acquisition or provenance approval.

Every leaf has this root:

```text
README.md             Purpose, basis, completeness, contents, checks, limitations
SOURCES.md            File-specific credits and rights
manifest.json         Fixture identity/kind and image records
manifest.csv          Same image records in shared column order
sources.csv           Source catalog with the shared columns
SHA256SUMS.txt         Input/source checksums
probes.csv            Relationship probes; header only for heaps
selections.json       Focused relationship pairs; empty for heaps
images/               Local comparison inputs
sources/              Preserved local source bytes
previews/             Local previews, intermediates and archives
batches/              Input path lists
tools/                Live code, check.py, requirements.txt
provenance/           Indexed selection/construction evidence and history
```

An `AGENTS.md` may additionally express current set-specific instructions.
Place prompts, candidates, inventories, ordering, selection ledgers, exclusions
and intake instructions in `provenance/intake/`. Construction-only manifests,
instructions and supplemental checksums belong in `provenance/construction/`.
`provenance/supplied/` retains original packages unchanged. Other existing evidence
may retain its filenames: index its role in `provenance/README.md`. In particular,
published import maps and hash-bound historical records remain stable.

Keep image/source IDs, paths and bytes stable during organizational changes.
Selection bases are different from relationship assertions. Do not invent a
visual prompt for a curatorial set or expected matching pairs for a heap.

Use Python 3.14.x in the root `.venv`. Install the leaf's `tools/requirements.txt`
there when its tools need dependencies. Run its `tools/check.py` for the common
checks plus its specialized validator. A shared implementation may serve several
leaves, with a small entry point per leaf.
