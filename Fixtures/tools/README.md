# Shared fixture tools

## Removing an image

From a neighboring repository, using the image ID in `world.json`:

```sh
../bricolage/Fixtures/collection remove sha256:HASH --reason "Reason for removal"
```

Use the full 64-character lowercase hash, with or without `sha256:`. The filename
stem of a world image is the same hash. From this repository, use
`Fixtures/collection remove HASH --reason TEXT`. The launcher uses its own
Python 3.14 environment, regardless of the caller's directory or environment.

Hash removal selects every byte-identical active copy across all collections.
It does not compare pixels or remove related images. A file path selects one
input; `--leaf PATH` limits either form to that collection. Paths resolve from
the caller's working directory. An ambiguous leaf-relative `images/` path is
refused. Use the unrestricted hash form to exclude an identity from sampling.

The command updates the records, validates affected collections and the fresh
sampler inventory, and commits only its changes on the current branch. The
required reason becomes both the receipt explanation and the default commit
message. `--commit-message TEXT` changes only the commit message. `--dry-run`
previews the operation without creating receipts or committing. Removal needs
a Git checkout with a HEAD commit and configured author/committer identity.
It neither acquires images nor draws a replacement sample, and never pushes.

Read the JSON response:

| Field | Meaning |
|---|---|
| `status` | `removed` when this invocation committed the removal, including a retry that finishes one; `already_removed` for a repeat; `planned`, `incomplete` or `error` |
| `complete` | True only after validation and a committed result; false for a preview or unfinished operation |
| `image_id` | Exact byte identity being removed |
| `checks` | Affected-collection validation, generated-file checks, and sampler check; `excluded_from_sampling` confirms no active alias remains anywhere |
| `commit` | The resulting commit hash, or on a completed repeat the latest commit that holds its receipts; null before completion |
| `receipts` | Repository-relative removal receipt paths |
| `changed_files` | Repository-relative paths committed by this operation; on a preview, the paths it would create or change |
| `operation` | Absolute path of the operation record, when one is planned or in progress |
| `error`, `next_step` | Named failure and recovery instruction when completion fails |

Exit 0 means a complete removal or a successful dry run. Exit 1 reports an
incomplete operation or a preflight error. Argument mistakes use argparse's
stderr help and exit 2; a missing environment also exits 2 on stderr.
Scoped removals can complete with `excluded_from_sampling: false` and a count
of aliases remaining elsewhere. Source evidence and existing worlds stay intact;
draw again when a consumer needs a world without the removed image.

Removal updates the JSON/CSV manifests, every batch containing the input, its
input checksum, and probe/focused-pair entries that refer to it. Source catalogs,
source files, acquisition records and sampler records remain unchanged. The
removed image is preserved under `previews/removed/`, outside the sampling pool.
Each `provenance/removals/NNNN/` contains the prior catalogs and a receipt with
the exact image row, reason and before/after hashes. Later removals extend this
chain. A collection can reach zero active inputs through recorded removals;
it retains its fixture ID, source evidence and receipt history. An empty scaffold
without a removal history still fails asset validation.

## Removal recovery and Git ownership

An immutable `Fixtures/provenance/removal-operations/remove-<id>.json` records the
selected aliases, receipt destinations, reason, commit message, original file
hashes and projected catalog and generated-file hashes. New leaf receipts name
that operation; older receipts keep their original format. This record is committed with the
catalog changes and is not scratch output.

Before starting, the command checks every selected alias, requires current
generated totals, and refuses existing staged or unstaged edits in files it
will change or preserve in receipt snapshots. Unrelated staged and unstaged work
stays intact. The commit uses an explicit file list and honors Git hooks. Re-pinning retains its existing
behavior and does not create a Git commit.

If removal succeeds but generating totals, validating, or committing fails,
preserve the JSON response and repeat the same command after resolving the
named problem. The retry accepts only the operation's recorded intermediate
states, finishes remaining aliases and bookkeeping, and creates no duplicate
removal receipts. It retains the original reason and commit message. A different
removal must wait until that pending operation is finished. Unexpected edits
in an affected file or its index entry are named and left intact. A sampler
failure during validation is reported the same way. There is no abandon
command: an operation whose problem cannot be resolved is undone by hand, by
restoring its files from Git and its receipts' images from `previews/removed/`.

Ordinary write failures within one leaf roll back that leaf's catalogs and media.
Completed removals in other leaves remain recorded and are resumed. A process
interruption inside a leaf write can leave an incomplete receipt or inconsistent
catalogs; the existing history checks name that state and require explicit repair.
The operation record does not promise a transaction across the filesystem and
Git. Repeating a completed operation returns `already_removed` and its commit
without creating another commit. Historical removals made before operation
records existed must already be committed to be recognized as complete.

## Reconciling local media with recorded removals

```sh
Fixtures/collection reconcile
Fixtures/collection reconcile --dry-run
```

A removal commit carries catalogs and receipts. Media is untracked, so a
checkout that receives the commit by pull, merge or checkout still holds the
image under `images/`. The sampler then reports it as an `unlisted-input`
problem on every draw, and the layout check refuses further removals in that
leaf. A refused `remove` names this command when it applies.

`reconcile` reads every leaf's removal receipts. A file at a removed input's
path that is absent from the active manifest and has exactly the receipt's
bytes moves to the receipt's `previews/removed/` path, or is deleted when that
preserved copy already exists intact. Files with other bytes, and files beside
a preserved copy with other bytes, are listed under `refused` and left alone.
The response lists `preserved`, `deleted` and `refused`; `complete` is true
when nothing was refused, and a refusal exits 1. Nothing tracked changes: it
writes no receipts and makes no commit, and repeating it does nothing more.
`--dry-run` reports the same lists without moving anything.

## Re-pinning an input and updating totals

From the repository root:

```sh
Fixtures/collection repin INPUT --from /path/to/replacement.jpg --reason "Reason"
Fixtures/collection totals
Fixtures/collection totals --check
```

`INPUT` is a hash or input path. Re-pinning requires an unambiguous match;
use `--leaf PATH` and an `images/` path when necessary. `--dry-run` previews it.

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

The removal tests run in disposable `collection-test-*` checkouts under
`Fixtures/output/`. They exercise the public neighboring-repository commands,
exact aliases within and across leaves, an emptied population, scoped paths,
unrelated staged/unstaged work, interrupted bookkeeping, rejected commits and
safe retries. They also cover leaf-limited hash removal, the commit named by a
repeat, preflight refusals (a held lock, an unfinished merge, stale committed
totals), sampler failures during validation, and a second checkout that
reconciles its media after receiving a removal commit. Their worlds, repositories and records are removed at teardown.

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
