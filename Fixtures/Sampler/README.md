# Fixture sampling engine

Draw equal tickets from hazy's local fixture inputs and keep a record that other
programs can read. Python 3.14.x on macOS or Linux; standard library only. There is
no network access, image transformation, comparator or activity-specific logic.

## Use

The public executable is [`Fixtures/sample`](../sample), at the fixture root.
It selects `Fixtures/.venv` regardless of the caller's working directory
or activated environment. Python 3.14.x is the only runtime and test target.

From the repository root, set up once using an installed Python 3.14.x:

```sh
make -C Fixtures setup-python
```

The Git-ignored `Fixtures/.venv` needs no pip packages for sampling or these tests. Setup
performs no downloads. If Python 3.14 is installed at a different path, use
`make -C Fixtures setup-python PYTHON314=/path/to/python3.14`. A missing environment or a
wrong Python minor version produces an actionable error.

Ask for N images directly:

```sh
Fixtures/sample 12 --seed my-investigation
Fixtures/sample inventory
Fixtures/sample list
```

`Fixtures/sample N` is shorthand for `Fixtures/sample draw N`. Both use the same
engine and records. From inside Fixtures, use `./sample N`; from elsewhere, use
the executable's absolute path. No inventory preparation or internal Python
imports are required.

Each successful draw publishes a **world**: a directory holding independent,
byte-identical copies of the selected images named `<image-sha256>.<original-extension>`,
beside a `world.json` that lists the world ID and the files, sorted by name.
The world is what the consuming program receives, and it carries nothing else:
no draw order, no leaf names, no provenance rows. The world ID is the sample ID,
so every world leads back to its draw record here. The hazy-facing contract is
written once in [WORLD.md](../../WORLD.md); this guide describes the Fixtures side.

The default world directory is `Fixtures/output/sampled/`; `--world DIR` writes
elsewhere. The copies are Git-ignored and disposable; editing them cannot change
the fixture originals. Copies are verified and the manifest written in a staged
directory before the previous world is replaced, so a visible world is complete.
Invalid requests, unavailable inputs, and copy/checksum failures leave the previous
world intact. A successful zero-image draw leaves only `world.json`. The engine
replaces a directory only when it is empty or already a world (it contains
`world.json`); any other nonempty destination, a symlinked destination, a
destination among the fixtures, or one containing or inside the record store is
refused before a draw is made. Concurrent publications to one directory serialize;
the last one published occupies it. Persistent records remain in
`Fixtures/Sampler/records/`, independently of worlds.

Each publication appends one annotation event to the draw, key `publication`,
author `Fixtures/sample`, recording the directory, manifest path, time and image
count. That receipt is the sampler's only trace of a publication; whether to keep
anything a consumer produced from the world is a separate, human decision.
`publish SAMPLE_ID [--world DIR]` materializes an existing draw as a world again
under the same world ID, appending another receipt.

`draw` refreshes the inventory by default and returns a persistent `sample_id`.
Omit `--seed` to generate and record a seed. N may be zero; negative N or N larger
than the eligible population is an error. There is no replacement or size adjustment.

Use the returned full identifiers in these commands:

```sh
Fixtures/sample show SAMPLE_ID --paths
Fixtures/sample show SAMPLE_ID
Fixtures/sample verify SAMPLE_ID
Fixtures/sample publish SAMPLE_ID --world /path/to/world
Fixtures/sample annotate SAMPLE_ID --key purpose --json '"Notebook study"'
Fixtures/sample annotate SAMPLE_ID --image IMAGE_ID --key review --json '{"decision":"accepted","tags":["reference"],"note":"My observation"}'
Fixtures/sample annotate SAMPLE_ID --image IMAGE_ID --key review --json '{"decision":"revisit","note":"Revised observation"}'
Fixtures/sample annotate SAMPLE_ID --image IMAGE_ID --key review --delete
```

`SAMPLE_ID` and `IMAGE_ID` above are placeholders. `show --paths` returns an
`images` list in draw order: image ID, an available absolute path (or null), and
every alias's current status. Open those paths with the local viewer of your choice.
`show` also returns the original draw, each image's provenance rows read from the
checkout and checked against the snapshot's pins, a per-leaf summary, current
annotations and the complete annotation history, even if image files are missing.
If the draw's snapshot is missing or damaged, `show` still returns the draw record
and its image IDs, with the gap listed under `problems`.

Annotation keys and JSON values are arbitrary. The example words have no special
meaning to the sampler. A value can be an object, array, string, number, Boolean
or null. `--value-file FILE` or `--value-file -` reads JSON from a file or stdin
instead of `--json`; `--author TEXT` records an optional author. Reusing a key
replaces its **current annotation value**, while preserving the previous event.
`--delete` removes the current key, preserving history. Sample annotations and
image annotations are separate; neither writes fixture metadata or draw fields.

To repeat a draw against an existing population, use its recorded size, seed and
inventory ID:

```sh
Fixtures/sample draw 12 --seed my-investigation --inventory INVENTORY_ID
```

This creates a new sample ID with the same ordered image IDs. It does not copy
annotations from the previous sample. A saved snapshot keeps its original
eligibility: missing files discovered later are reported, never replaced in the
draw. Use a fresh `inventory` or the default `draw` to reflect today's availability.

Draw responses have `schema_version: 1` and these fields:

| Field | Use |
|---|---|
| `draw` | Original persistent record, including `sample_id`, `image_ids`, seed and inventory ID |
| `population` | Snapshot ID and file, `counts`, every leaf with its status, the `checkout` hint and population `problems` |
| `population.counts.eligible` | M, the number of eligible distinct images in this draw's snapshot |
| `summary.by_leaf` | How many selected images each leaf contributed |
| `images` | Draw order; each item has `position`, `image_id`, `sampled_path` for its copy in the world, `available_path` for its fixture original, and all alias `locations` with current statuses |
| `current_check` | Record reproduction and current file/metadata verification |
| `output` | Absolute world `directory` and `manifest` path, `published` Boolean, and `error` if copying or publication failed |
| `problems` | Every problem found, each with a `kind`; empty when the exit code is 0 |

Responses, records and the world manifest keep their `schema_version` while changes are
additive: fields may be added, never removed or retyped, and readers ignore fields
they do not know. A removal or retyping raises the version, and loaders keep
accepting earlier versions, as the population schema does.

An agent or program can call the engine and use the returned paths immediately:

```python
import json
import subprocess

result = subprocess.run(
    ["Fixtures/sample", "12", "--seed", "my-investigation"],
    capture_output=True, text=True, check=True,
)
sample = json.loads(result.stdout)
sample_id = sample["draw"]["sample_id"]
image_paths = [item["sampled_path"] for item in sample["images"]]
```

Every command writes JSON to stdout, including failures. Exit code 0 means the
report lists no problems. Exit code 1 means the command completed and its report
has a nonempty `problems` list: unavailable or unlisted fixture files, a publication
failure, a damaged or snapshotless draw in `list`, or a missing snapshot in `show`
and `verify`. Read `problems` before deciding whether the result is usable; a draw
with `output.published` true is complete even when the population reports problems
elsewhere. Exit code 2 means the command could not complete. Its stdout is
`{"schema_version": 1, "error": {"code": ..., "message": ...}}` with the same
one-line message on stderr. Codes are `usage` (arguments or request), `fixture`
(a leaf's metadata, with its `leaf` path), `record-missing`, `record-invalid`,
`record-damaged` (a checksum differs), `output` (the disposable directory) and `io`.
Nothing is repaired on failure; fix the fixture or record the message names.

`draw` persists the original selection before checking current availability; a
missing file never causes a replacement draw. An oversized request is rejected
before creating a sample. On a failed publication, `sampled_path` values are null;
the saved draw remains available and `publish` can materialize it later. `show` and
`verify` inspect fixture originals and durable records, without changing or relying
on any world. `show` is the key: it joins a world's IDs back to leaves and rows. `list` reports
every draw directory; a damaged record appears with status `damaged` and its error
rather than hiding the others.

Global `--repo CHECKOUT` and `--store DIRECTORY` options go **before** the command.
The checkout and default store resolve from the engine; custom relative option
paths resolve from the caller's working directory.
The default store is [records/](records/). It contains versionable text only;
original image bytes remain at their fixture locations. Custom stores under
`output/` are disposable too, so keep durable stores elsewhere. Back up or version
the whole store, including inventories.

## Population and identity

The population is the active `manifest.json` inputs under both `Fixtures/Heaps/`
and `Fixtures/Relationships/`, at any depth. This follows [FORMAT.md](../FORMAT.md):
`images/` files are fixture inputs. Source copies, previews, archived manifests,
candidate leads and staged publications are not extra fixture inputs. There is
no test of collection kind, transformation, origin, source relationship or content.

Each expected byte SHA-256 is one image ID: `sha256:` followed by 64 lowercase
hex digits. Exact byte copies, hard links and in-tree symbolic file aliases share
one ticket; all their manifest identities and locations are retained. Byte-different
variants and encodings remain separate tickets. No visual or pixel-equivalence
deduplication is attempted, and no relationship groups are preserved during draws.

Inventory creation reads and hashes every manifest input. An identity is eligible
when at least one recorded input alias is readable and matches its expected hash.
Missing, changed and inaccessible aliases stay in the inventory with their status;
changed bytes are not silently assigned a new identity. Unexpected unlisted input
files are reported for catalog reconciliation, not silently added. Out-of-tree
symlinks are reported as inaccessible. Filesystem observations occur during the
scan; they are not a lock on the whole checkout. The sampler checks bytes against
fixture records and relies on fixture validators for image decoding/format checks.

A leaf whose `manifest.json`, `sources.csv` or `provenance/import-map.json` cannot
be read and validated is **excluded**: the inventory records the leaf with the
error that names the file and field, its images are not tickets, and `draw` still
proceeds over the remaining population with exit code 1. Fix the leaf, then rescan;
the population and therefore the snapshot identity change when it returns.

Metadata is pinned, not stored. The snapshot records the path and SHA-256 of each
leaf's manifest, source catalog, import map and readable credits, which Git already
versions. `show` reads the manifest row, its parent/family source-catalog rows and
the matching import-map row from the checkout and compares every pinned file: a
`frozen` leaf still has its recorded bytes, so the rows shown are exactly the ones
present at the draw; a `changed` leaf shows current rows with the differing file
named; an `unreadable` leaf reports its error. Unknown source fields stay unknown.
No provenance field is interpreted as a sampling weight or investigation decision.

## Durable format

```text
records/
  inventories/<inventory_id>.json
  draws/<sample_id>/
    draw.json
    annotations.jsonl          # created by the first annotation
```

These files need no database or sampler process to read. All paths identifying
fixture inputs are checkout-relative POSIX paths. Moving a checkout or restoring
its media works with `--repo`; absolute paths in `show` are calculated at read time.
Upstream metadata is retained as supplied and may itself contain historical paths.

| Record | Contents |
|---|---|
| Inventory | `inventory_id`, `created_at`, a `checkout` hint (Git commit and dirty flag, or null) and a `population` object with schema/policy, `leaves` with status, sorted `images`, metadata-file pins, counts and unlisted inputs |
| Inventory image | `image_id`, `byte_sha256`, frozen `eligible`, and `aliases`; each alias has its path, leaf path, fixture ID, kind and observed availability |
| Draw | Schema, sample ID, timestamp, inventory ID/store-relative reference, versioned procedure, exact seed text, requested size, eligible count, ordered `image_ids`, draw checksum |
| Annotation event | Schema, sequence, event ID, timestamp, sample ID/draw checksum, nullable `image_id` (null means sample), optional author, arbitrary key, `set`/`delete`, and a value for `set`. Publication receipts are ordinary events with key `publication` |

Inventory IDs hash the `population` object, excluding its creation timestamp and
checkout hint. Identical rescans reuse one snapshot. Population schema 2 pins
metadata by hash; schema 1 snapshots, which embedded metadata rows per alias, still
load, replay and show. The hint is where the scan happened as Git saw it; the
file pins remain the authority, so a scan outside Git or in a dirty tree is valid.

A draw's checksum covers all its fields except `draw_sha256`. Canonical JSON for these hashes is UTF-8, sorted object keys,
no ASCII escaping, separators `,` and `:`, and no NaN/infinities. These checks detect
accidental changes; they are not signatures or authentication.

Inventory and draw files are published atomically without overwriting existing
records. The sampler never edits them. Annotation events append under a local
file lock and are flushed to disk. Sequence order is authoritative. To reconstruct
current annotations, start with empty sample/image maps; set or delete each event's
key on its target in order. The whole value is replaced, not recursively merged.
An incomplete or malformed log is reported and left intact for explicit repair.
Use the CLI for concurrent writes; local file locks are not a distributed service.

`verify` checks snapshot/draw integrity, replays the original selection, validates
annotation history, and rehashes all selected aliases and their pinned fixture
metadata files. A changed pin is reported with both hashes; recovering the recorded
bytes is a Git step, not a sampler one. New inventories and all later annotations
leave an existing draw unchanged.

## Sampling procedure, version 1

`sha256-counter-rejection-partial-fisher-yates-v1` is specified independently of
Python's random-library implementation:

1. Start with eligible image IDs sorted lexicographically. Seed is exact UTF-8
   text; numeric-looking strings are still strings. An omitted seed is 32 random
   bytes from the operating system, encoded as 64 lowercase hex characters.
2. Prefix = ASCII `hazy-fixture-sampler-v1`, one zero byte, the seed byte length as
   an unsigned 8-byte big-endian integer, then the seed bytes.
3. For counter 0, 1, ... hash prefix plus the counter as an unsigned 16-byte
   big-endian integer. Interpret each SHA-256 digest as an unsigned big-endian
   256-bit integer `x`.
4. For a bound `b`, let `limit = 2^256 - (2^256 mod b)`. Discard words `x >= limit`;
   otherwise return `x mod b`. Rejection removes modulo bias.
5. For `i = 0 .. N-1`, take `j = i + randbelow(M-i)` and swap positions i and j.
   Return the first N IDs in their resulting order.

This partial Fisher–Yates shuffle gives each eligible ticket equal pseudorandom
probability without replacement. It does not consult annotations. The tests
enumerate every equally likely random-index path in a small population, check
rejection at the boundary, and pin a stream vector to protect recorded-draw
reproduction. Tests run only under the repository's Python 3.14.x environment.

## Demonstration and checks

The committed [demonstration draw](records/draws/draw-82acd83c6cd540a6bf4e29610ff5dc2d/draw.json)
contains 12 images drawn once with seed `fixture-sampler-demo-2026-11-01` from
1,251 eligible byte identities: 1,263 manifest records across 18 leaves, with 12
redundant byte-identical aliases and no excluded leaves. All input hashes passed;
none were unavailable or unlisted. No strata, quota or reroll was used. The same
seed selected the same twelve identities under the first release's schema 1
snapshot, which stored metadata rows; its schema 2 snapshot pins them instead.

Seven annotation events follow: six examples with sample notes, an image note, a
revised value and a deleted value, then one `publication` receipt from
`Fixtures/sample publish` writing the default world. Their
[history](records/draws/draw-82acd83c6cd540a6bf4e29610ff5dc2d/annotations.jsonl)
preserves the prior values. The examples are investigation annotations, not fixture
judgments or eligibility changes. The copies were hash-verified at publication;
the demonstration did not review them visually. `verify` is the reproducible check
of this record against the checkout; there is no separate hand-written check file.

```sh
Fixtures/sample show draw-82acd83c6cd540a6bf4e29610ff5dc2d --paths
Fixtures/sample verify draw-82acd83c6cd540a6bf4e29610ff5dc2d
Fixtures/sample publish draw-82acd83c6cd540a6bf4e29610ff5dc2d
make -C Fixtures test-sampler
```
