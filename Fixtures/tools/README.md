# Shared fixture tools

## Removing or re-pinning an input and updating totals

From the repository root:

```sh
Fixtures/collection remove SHA256 --reason "Reason for removal" --dry-run
Fixtures/collection remove SHA256 --reason "Reason for removal"
Fixtures/collection repin SHA256 --from /path/to/replacement.jpg --reason "Reason"
Fixtures/collection totals
Fixtures/collection totals --check
```

`SHA256` is a placeholder for an input's byte hash (with or without `sha256:`).
An input file path also works. For ambiguous hashes or leaf-relative `images/`
paths, use `--leaf Fixtures/Heaps/Curatorial/US-Army-SSI`. Ambiguous matches and
removing a leaf's last input are rejected before changes. Repeating a recorded
removal reports `already_removed`. The command makes no acquisition or draw.

Removal updates the JSON/CSV manifests, every batch containing the input, its
input checksum, and probe/focused-pair entries that refer to it. Source catalogs,
source files, acquisition records and sampler records remain unchanged. The
removed image is preserved under `previews/removed/`, outside the sampling pool.
Each `provenance/removals/NNNN/` contains the prior catalogs and a receipt with
the exact image row, reason and before/after hashes. Later removals extend this
chain. Failed writes roll back the active catalogs and media; an interrupted
operation's incomplete record is reported by name for recovery.

Re-pinning replaces one active input's bytes and records why. The replacement
must be a regular file outside the leaf that decodes to the recorded width,
height, orientation and format; identical bytes are a no-op. The input's path
keeps its name and its hash changes in the manifests, checksum list and, when
the input is a byte copy of its source file, the source file and source catalog.
Whatever bytes were present go under `previews/repinned/`; a missing input is
recorded as missing. `provenance/repins/NNNN/` holds the prior catalogs and the
receipt. Re-pinning serves recovery of lost media and deliberate replacement
alike; the reason distinguishes them. See [RECOVERY.md](../RECOVERY.md).

Removals and re-pins form one chain, ordered by time, that the layout check
replays against the live catalogs. The check also verifies every manifest
hash against the checksum list, every batch entry against the manifest, the
source catalog against the checksum list, and preserved bytes against their
receipts. A leaf's specialized validator describes its publication; once a
leaf has a recorded change, `tools/check.py` reports that validator as
historical and does not run it, because the publication it describes is no
longer the live leaf and nothing reconstructs it. Saved sampler inventories
retain their original pins and continue to report changes; a re-pinned input
makes draws that selected it unrepeatable for that image. Acquisition builders
cannot fold recorded changes into a new publication; rebuilding a changed leaf
is rejected.

The removal command also regenerates [collection totals](../COLLECTIONS.md), the
[source index](../INDEX.csv) and marked total blocks in every leaf README. After other catalog changes, run
`make -C Fixtures collection-totals`. `make -C Fixtures check-collection-totals`
is read-only and fails on stale output; `test-fixture-layout` includes this check
and removal regression tests. Counts come from manifests, so they can be generated
without local media and do not claim that those files are present. Historical
acquisition counts, targets and frozen editions are not current input totals.

## The source index

`Fixtures/collection index` regenerates `Fixtures/INDEX.csv` from active
manifests, source catalogs and import maps; `--check` fails on a stale file.
`Fixtures/collection totals` regenerates it too, so one command and one check
cover both. The index names the leaf, bytes, decoded size and upstream identity
of every active input, classifies how each could be fetched again, and lists
other leaves holding the same bytes or upstream file. `source_index.py` reads the
three existing import-map spellings through one adapter; a new leaf that writes
the common keys needs no adapter change. The index is read by a new
contribution's identity audit and by whoever recovers ignored media; it is
never used to re-validate an older leaf.

## Validation and other tools

Use the Python 3.14.x `Fixtures/.venv`. Layout and relationship validation are
offline. The optional relationship runner invokes an explicitly supplied
experiment binary; it does not implement a comparator or download images.

```sh
make -C Fixtures setup-python
Fixtures/.venv/bin/python -m pip install -r Fixtures/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full
make -C Fixtures test-fixture-layout
make -C Fixtures test-relationships
```

`check_layout.py` discovers only active leaves under Heaps and Relationships at
arbitrary depth. By default it checks common layout, input hashes, the checksum
list, batches, the source catalog and the chain of recorded changes. `--full`
runs each leaf's `tools/check.py`, which adds the specialized publication
validator while the leaf has no recorded change; an explicit leaf path limits
either mode. `--metadata-only` requires no local
media and omits specialized checks. All modes are offline and failures exit
nonzero. Reports are JSON on stdout; redirect them outside fixture inputs.

`new_fixture.py` materializes the [single template](../Template/README.md) into a
new leaf. It refuses existing destinations and duplicate fixture IDs. An empty
scaffold is unpublished; complete real intake evidence, catalogs and the
source-specific check before using it as a fixture.

`fixture_layout.py` supplies the common checks. Its small historical-path helper
resolves only the explicitly named relocated intake/construction records. It
rejects ambiguous duplicate locations. Historical audit identifiers are not
rewritten. The migration's `tool-changes.json` records exact before/after hashes
for intentionally adapted tools, allowing existing source pins to remain intact
while rejecting unrecorded edits.

A leaf rename is recorded as a `leaf-rename` move in a
`Fixtures/provenance/*/relocations.json`, as in the
[Similarity rename record](../provenance/similarity-names-2026-11/README.md).
Tool pins keyed by a former path still resolve, and the sampler reads snapshot
aliases at their current path. Records keep their original path strings and
hashes; identity audits name leaves as they were and are not resolved again.

`check_layout.py` prints one JSON object: the number of discovered `leaves`, how
many `passed`, the `failed` paths and every per-leaf result. It exits 1 when any
leaf fails or a discovered leaf has no result. `test-fixture-layout` also checks
that live guides, tools and catalogs name only existing fixture paths; historical
records under `provenance/`, tests and the template are outside that scan.

`relationship_fixtures.py check --fixtures LEAF` validates the three relationship sets:
hashes, source copies, CSV/JSON agreement, parent and scene identities, probes,
and batch coverage. Their leaf entry points and the Variants builder use this
implementation directly. `test-relationships` needs the local relationship media;
`test-fixture-layout` uses temporary mechanics fixtures only.

`relationship_fixtures.py run --fixtures LEAF --binary /path/to/hazy-vision-translation
--world /path/to/published-world --output /path/to/new-run` drives the existing pair CLI and records all outcomes,
including failures. `--selection focus|probes|full` chooses the fixture's explicit
pairs. Both `--world` and `--binary` are required; no sibling checkout or application
build is assumed. `--store` selects the sampler records; the default is the sampler's
scratch store, so a world drawn with `--keep` needs `--store Fixtures/Sampler/records`.
The runner verifies the world against its saved draw, maps probes to hash IDs and
passes only those IDs and the world to the binary. Only that executable is required;
the Swift toolchain version is recorded in `run.json` when one is on `PATH`. Absent
endpoints are recorded as skipped, never replaced. Exact-byte aliases can become self-comparisons. The output parent must exist and the output directory must be new.
