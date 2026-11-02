# Shared fixture tools

## Removing an input and updating totals

From the repository root:

```sh
Fixtures/collection remove SHA256 --reason "Reason for removal" --dry-run
Fixtures/collection remove SHA256 --reason "Reason for removal"
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

Common validation replays every removal and verifies current catalogs, remaining
inputs and preserved image bytes. Existing specialized validators check a
temporary reconstruction of the original publication under `Fixtures/output/`;
they still verify its sources, selection and acquisition evidence. Historical
cross-collection audits resolve their manifest hashes through checked removal
snapshots. New audits use active manifests. Other changed metadata, missing
snapshots and missing media still fail. Saved sampler inventories retain their
original pins and continue to report changes; removal does not rewrite history.
The existing acquisition builders cannot reconcile removals into a new
publication; rebuilding a leaf with removal history is rejected before replacing
its active inputs. Ordinary removal and validation need no rebuild.

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
arbitrary depth. It checks common layout and input hashes by default. `--full`
runs each leaf's `tools/check.py`, including its existing specialized validator;
an explicit leaf path limits either mode. `--metadata-only` requires no local
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
`fixture_layout.former_leaf_names` and `recorded_leaf_name` let the Curatorial
identity audits match a recorded fixture name to its current leaf, tool pins
keyed by a former path still resolve, and the sampler reads snapshot aliases at
their current path. Records keep their original path strings and hashes.

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
