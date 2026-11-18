# Sampling images

`Fixtures/sample` draws images from the local collections, saves the selection,
and copies the images into a world directory. Each distinct byte hash has an
equal chance of selection. It uses Python 3.14.x on macOS or Linux, with no
third-party packages or network access.

## Use

From a neighboring repository:

```sh
../bricolage/Fixtures/sample 100
```

Replace 100 with N. The public executable is [`Fixtures/sample`](../sample), at
the fixture root. It selects `Fixtures/.venv` regardless of the caller's working
directory or activated environment. Read `output` first in its JSON response:
`published: true` means a complete world is ready at `directory`, identified by
`world_id`, with `image_count` images. Give that directory to the consumer.
Check `receipt_recorded` and `problems` too, including on exit 1. `next_steps`
explains publication recovery when needed. No imports, inventory preparation or
directory change are required.

If the environment is missing, the launcher prints a setup command that works
from any directory. Python 3.14.x is the only runtime and test target. From the
repository root, set up once using an installed Python 3.14.x:

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

## Sample without a world

```sh
../bricolage/Fixtures/sampleWithout /path/to/world 12 --seed next-investigation
```

[`Fixtures/sampleWithout`](../sampleWithout) draws N distinct images from the
current eligible fixtures minus the image IDs in a supplied world's `world.json`.
It uses the same Python environment, draw records, publication and output fields
as `sample`. Only exact bytes match: aliases of one hash share one exclusion,
while crops and different encodings remain separate tickets.

Pass a world directory, not a sample ID or a path to the manifest. The command
reads the existing [published world format](../../WORLD.md): its world ID and
sorted image entries with hash IDs and matching filenames. Unknown additive
fields are ignored. There is no separate input format or format-selection option.
Only `world.json` is read; image copies, other directory entries, and original
sampler records are not consulted. Thus an old world still works after one of
its images is removed from bricolage or its local image copies are discarded.

Each requested ID absent from the current eligible population produces an
`exclusion-unmatched` warning naming that ID, and the exclusion list shrinks.
Unavailable fixture aliases belonging to those IDs are also reported as warnings
with their paths. These warnings alone return exit 0. Other fixture and
publication problems retain their usual error handling. The command never
reduces N: insufficient remaining images is an error. A missing or malformed
`world.json`, or no matching eligible IDs (including an empty input world), is
also an error before saving a draw. N may be zero if at least one ID matches.
The no-match error counts the requested images that are recorded here without
a verified local copy and names any excluded leaf, whose images cannot match.

The response includes `warnings` and an `exclusion` object:

| Field | Meaning |
|---|---|
| `world_id`, `manifest_sha256` | Input world ID and SHA-256 of the manifest's exact bytes |
| `requested_image_ids`, `requested_count` | All IDs read from the input manifest |
| `matched_image_ids`, `matched_count` | Eligible IDs excluded from this draw |
| `unmatched_image_ids` | IDs absent from the eligible population, named in warnings |
| `remaining_eligible` | Pool size after exclusions; must be at least N |

The same `exclusion` object is saved in the draw, covered by its checksum.
`population.counts.eligible` and `draw.eligible_count` still describe the full
inventory snapshot; `exclusion.remaining_eligible` describes the filtered pool.
The inventory is always refreshed for this endpoint; there is no `--inventory`
option. A fixed seed repeats the selection when the remaining pool is identical.

Replay uses the saved inventory and exclusions. The earlier world can be gone.

## Worlds and publication

Pass the returned `output.directory` to the consumer. Each publication creates
a fresh directory. With `--world DIR`, give a path that does not yet exist.
The [world contract](../../WORLD.md) defines its manifest and hash-named image
copies. Collection paths, relationships and draw order stay in the records.

`publish WORLD_ID` writes the saved selection to another fresh directory under
`Fixtures/output/worlds/`, with the same world ID. The sampler verifies copies
before installation, then appends a `publication` event. `output.published`
reports installation and `output.receipt_recorded` reports the event. If a
receipt fails, preserve the response and follow `output.next_steps` to inspect
the log. A failed publication leaves the selection available for replay.

For an unsuitable input, use the [collection removal guide](../tools/README.md#removing-an-image).

## Saved samples

`draw` refreshes the inventory by default and returns a saved `sample_id`.
Omit `--seed` to generate and record a seed. N may be zero; negative N or N larger
than the eligible population is an error. There is no replacement or size adjustment.
When recorded images lack a verified local copy, or a leaf was excluded, that
error says so and carries `eligible`, `unavailable_images` and `excluded_leaves`.
A fresh clone has catalogs and no media, so every draw there fails this way
until the media is restored as [RECOVERY.md](../RECOVERY.md) describes.

Use the returned full identifiers in these commands:

```sh
Fixtures/sample show SAMPLE_ID --paths
Fixtures/sample show SAMPLE_ID
Fixtures/sample verify SAMPLE_ID
Fixtures/sample publish SAMPLE_ID
Fixtures/sample annotate SAMPLE_ID --key purpose --json '"Notebook study"'
Fixtures/sample annotate SAMPLE_ID --image IMAGE_ID --key review --json '{"decision":"accepted","tags":["reference"],"note":"My observation"}'
Fixtures/sample annotate SAMPLE_ID --image IMAGE_ID --key review --json '{"decision":"revisit","note":"Revised observation"}'
Fixtures/sample annotate SAMPLE_ID --image IMAGE_ID --key review --delete
```

`SAMPLE_ID` and `IMAGE_ID` above are placeholders. `show --paths` returns an
`images` list in draw order: image ID, an available absolute path (or null), and
every alias's current status. Open those paths with the local viewer of your choice.
`show` also returns the original draw, each image's provenance rows read from the
checkout and checked against the snapshot's pins, historical leaf and branch counts, current
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

To use the same fixed sample again, use `publish SAMPLE_ID`. To make a new draw
with the same selection, use the recorded size, seed and
inventory ID:

```sh
Fixtures/sample draw 12 --seed my-investigation --inventory INVENTORY_ID
```

This creates a new sample ID with the same ordered image IDs. It does not copy
annotations from the previous sample. A saved snapshot keeps its original
eligibility: missing files discovered later are reported, never replaced in the
draw. Use a fresh `inventory` or the default `draw` to reflect today's availability.

## JSON responses

Draw responses have `schema_version: 1` and these fields. Draw and publish
responses put `output` immediately after `schema_version` and `store` for easy
inspection; programs should access JSON fields by name.

| Field | Use |
|---|---|
| `store` | Record store used, or the destination for `keep`. Default `list` also reports both `stores` and the store for each row |
| `output` | World handoff, described below; also returned by `publish` |
| `draw` | Original persistent record, including `sample_id`, `image_ids`, seed and inventory ID |
| `population` | Snapshot ID and file, `counts`, every leaf with its status, the `checkout` hint and population `problems` |
| `population.counts.eligible` | M, the number of eligible distinct images in this draw's snapshot |
| `summary.by_leaf` | Selected distinct image IDs by recorded leaf path, omitting zero counts |
| `summary.leaves` | Membership counts for each included leaf, with its stable `fixture_id`, recorded `fixture_path`, `eligible` and `selected` |
| `summary.branches` | The same two counts by recorded ancestor path, including the whole `Fixtures` population |
| `images` | Draw order; each item has `position`, `image_id`, `sampled_path` for its copy in the world, `available_path` for its fixture original, and all alias `locations` with current statuses |
| `current_check` | Record reproduction and current file/metadata verification; `ok` means no problems, while `publication_ready` means records and logs are valid, every selected image has a verified copy, and some leaf still lists it |
| `problems` | Every problem found, each with a `kind`; empty when the exit code is 0 |
| `exclusion`, `warnings` | Present for `sampleWithout`; exclusion IDs and counts, and nonfatal missing-ID or alias reports |

Draw and full `show` responses derive these counts from the saved inventory.
`eligible` counts distinct byte identities available to this request after its
exclusions. An identity with a verified copy anywhere counts in every leaf
that recorded it. Each enclosing branch counts it once. For example, if two
sibling leaves contain A,B and B,C and the draw selects B, each leaf reports
one of two and their branch reports one of three. A later leaf containing B
has no effect on this draw. Zero counts are included for known leaves. An
excluded leaf has unknown contents and is listed in the population report.
If the snapshot is unavailable, `show` omits `leaves` and `branches`.

The `output` block contains:

| Field | Use |
|---|---|
| `world_id` | Saved sample ID, also used in `world.json` when published |
| `image_count` | Number of images published by this request; zero when nothing was published or for a successful zero-image draw |
| `directory`, `manifest` | Absolute paths of the published world and its manifest; null if this request did not publish |
| `published` | Whether this request installed a complete world ready for a consumer; distinguishes an empty world from a failed publication |
| `receipt_recorded` | Whether the publication receipt was appended successfully |
| `next_steps` | Publication recovery instructions, empty on success; failed publication retains the selection and gives a command to republish it, while receipt failure requires log inspection before retrying |
| `error` | Present if installation or receipt writing failed |

`published` reports that the copies passed byte verification and the world
was installed. Consumers handle image decoding. Check `problems` for issues
elsewhere in the fixture collection.

Responses, records and the world manifest keep their `schema_version` while changes are
additive: fields may be added, never removed or retyped, and readers ignore fields
they do not know. A removal or retyping raises the version, and loaders keep
accepting earlier versions, as the population schema does.

A program can read the report before deciding whether to use its output:

```python
import json
import subprocess
import sys

result = subprocess.run(
    ["Fixtures/sample", "12", "--seed", "my-investigation"],
    capture_output=True, text=True,
)
sample = json.loads(result.stdout)
if result.returncode:
    print(json.dumps(sample, indent=2), file=sys.stderr)
    raise SystemExit(result.returncode)
world_directory = sample["output"]["directory"]
world_id = sample["output"]["world_id"]
```

This example stops on any problem. A caller can instead examine an exit-1
report's `output` fields to decide whether its published world is usable.

Commands report results and errors as JSON on stdout. Help prints plain text;
a missing environment or wrong Python version reports only to stderr.
Exit code 0 means the report lists no problems. Exit code 1 means the command
completed and its report has a nonempty `problems` list: unavailable or unlisted fixture files, a publication
failure, a damaged or snapshotless draw in `list`, or a missing snapshot in `show`
and `verify`. Read `problems` before deciding whether the result is usable; a draw
with `output.published` true is complete even when the population reports problems
elsewhere. Exit code 2 means the command could not complete. Its stdout is
`{"schema_version": 1, "error": {"code": ..., "message": ...}}` with the same
one-line message on stderr. Codes are `usage` (arguments or request), `fixture`
(a leaf's metadata, with its `leaf` path), `record-missing`, `record-invalid`,
`record-damaged` (integrity failure), `record-conflict` (divergent saved copies), `output` (the disposable directory) and `io`.
Nothing is repaired on failure; fix the fixture or record the message names.
Destination errors include `error.next_step` with guidance to choose a new
destination or resolve the named conflict. Missing-environment and wrong-version
messages include a setup command that works from the caller's directory.

`draw` persists the original selection before checking current availability; a
missing file never causes a replacement draw. An oversized request is rejected
before creating a sample. On a failed publication, `sampled_path` values are null;
the saved draw remains available and `publish` can materialize it later. `show` and
`verify` inspect fixture originals and saved records, without changing or relying
on any world. `show` connects a world's IDs to source records. `list` reports
every draw directory; a damaged record appears with status `damaged` and its error
rather than hiding the others.

## Stores

Ordinary draws go to `Fixtures/output/records/`. To keep one after inspecting it:

```sh
Fixtures/sample keep WORLD_ID
```

Commit the records under `Fixtures/Sampler/records/`. The response's `files`
lists them relative to the checkout: the draw, its annotation log and its
inventory. Commit all three; a draw committed without its inventory cannot be
replayed, explained or republished in another checkout. Keeping replays the draw
and retains its inventory, selection and full annotation history, including
publication receipts. It works without the world or the source images.
Inventories share a file when their population hashes match. Its timestamp and
checkout hint describe the scan that wrote that copy. Repeating `keep` is safe.

`show`, `verify`, `annotate` and `publish` find the draw by ID. For a kept draw,
`annotate` and `publish` therefore append to its versioned `annotations.jsonl`.
A publication receipt records this machine's absolute world path, so each
`publish` of a kept draw leaves an uncommitted line in a tracked file. Commit it
if the publication is part of the record; otherwise discard it with
`git restore`. Every response's `store` says which store was written. `list` includes
both stores and names the store for each draw. When old scratch and kept copies
exist, the sampler uses the longer compatible history and prefers the kept
copy when both agree. If the histories diverge, it names both stores for
inspection with `--store DIR`. Clearing scratch discards draws still held only
there. World directories and original image bytes are separate from the records.

Global options precede the command. `--keep` still selects the versioned store
directly. `--store DIR` selects a specific store, including the source for
`keep`. Relative paths resolve from the caller's working directory.

## Population and identity

The population is the active `manifest.json` inputs under both `Fixtures/Heaps/`
and `Fixtures/Relationships/`. Discovery walks grouping directories to any depth,
then stops at the first manifest on each branch. A fixture in a leaf's
`tools/example/` can be validated directly and contributes no tickets to the
enclosing archive. This follows [FORMAT.md](../FORMAT.md):
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
Publication uses that same availability rule. A missing redundant alias remains
a problem and causes exit 1, but does not prevent publishing the verified available
copy. A changed pinned metadata file is likewise reported as `metadata-changed`
with exit 1 and does not by itself prevent publication: removing or re-pinning
one image changes its leaf's manifest, and saved draws that selected other
images from that leaf still republish. Missing all copies of a selected image,
invalid records or annotations, and a selected image that no leaf lists any
longer prevent publication; nothing is redrawn or substituted. That last case
is an `image-unlisted` problem. It names an image removed or re-pinned after
the draw, including one whose bytes are still on disk in a checkout that has
not run `collection reconcile`. Such a selection cannot be republished from
the current catalogs; draw again, or use `sampleWithout` with its old world.
Missing, changed and inaccessible aliases stay in the inventory with their status;
changed bytes are not silently assigned a new identity. When a recorded alias lies
in a leaf that a `leaf-rename` move in `Fixtures/provenance/*/relocations.json`
has since renamed, the file is read at its current path, reported as
`current_path` beside the recorded `path`, and must still match the recorded hash. Unexpected unlisted input
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

## Selection code

Both entry points use the same internal path in `sampler.py`:

1. `request_from_args` translates arguments and the read exclusion manifest into
   a `DrawRequest`: size, optional seed, resolved exclusion record, and procedure.
   It resolves requested IDs against the inventory and reports no matches or
   insufficient remaining images before creating a draw.
2. `prepare_candidates` validates the snapshot and any resolved exclusions, then
   returns a sorted tuple of eligible byte identities. Each hash appears once,
   regardless of how many aliases it has. Preparation uses the supplied snapshot
   without reading current files or consuming randomness.
3. `select_ids` takes prepared candidates, size, seed and procedure. It checks
   bounds and delegates to the algorithm identified by `sampling_procedure`.
   The current algorithm is `uniform_sample_ids`, which copies the candidate
   tuple before shuffling. It consults no inventories, paths or annotations.
4. `create_draw` resolves an omitted seed once, prepares and selects, then saves
   the inventory and draw. `DrawRequest.record_fields` writes the effective
   selection inputs using the existing draw fields. Replay reconstructs the
   request with `DrawRequest.from_record` and uses the same preparation and
   selection functions. The recorded procedure chooses the algorithm; an
   unknown procedure fails explicitly.

Selection preferences belong to the request and candidate preparation, while
the inventory records fixture facts. Resolved inputs needed for replay belong
in the saved draw. The public commands, record formats and flat world handoff
remain as documented above. These functions are internal Python interfaces;
consumers use the public launchers.

When introducing a procedure, include a small worked example with overlapping
memberships in its compatibility test. For a procedure that chooses a leaf
first, replay must recover that leaf choice. For one that combines memberships
into image weights, replay must recover the effective weights from the recorded
rule and frozen inputs. Retain any additional input used by the rule once and
reference it from each draw that used it. A change in the odds needs its own
procedure version so older draws retain their meaning.

## Sampling procedure, version 1

`sha256-counter-rejection-partial-fisher-yates-v1` is specified independently of
Python's random-library implementation:

1. Start with eligible image IDs sorted lexicographically. For a draw with an
   `exclusion` record, remove its matched IDs before shuffling; M is the remaining
   pool size. Seed is exact UTF-8 text; numeric-looking strings are still strings.
   An omitted seed is 32 random
   bytes from the operating system, encoded as 64 lowercase hex characters.
2. Prefix = ASCII `hazy-fixture-sampler-v1`, one zero byte, the seed byte length as
   an unsigned 8-byte big-endian integer, then the seed bytes. The `hazy-` prefix is a
   frozen hash domain from the sampler's origin; renaming it would change every recorded
   draw's reproduction, so it does not follow the application's name.
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
lives in the durable store and
contains 12 images drawn once with seed `fixture-sampler-demo-2026-11-01` from
1,251 eligible byte identities: 1,263 manifest records across 18 leaves, with 12
redundant byte-identical aliases and no excluded leaves. All input hashes passed;
none were unavailable or unlisted. No strata, quota or reroll was used. The same
seed selected the same twelve identities under the first release's schema 1
snapshot, which stored metadata rows; its schema 2 snapshot pins them instead.

Eight annotation events follow: six examples with sample notes, an image note, a
revised value and a deleted value, then two `publication` receipts. The original
receipt records the earlier default world; the repository lift appended a receipt
for `Fixtures/output/lift-world` in bricolage. Their
[history](records/draws/draw-82acd83c6cd540a6bf4e29610ff5dc2d/annotations.jsonl)
preserves the prior values. The examples are investigation annotations, not fixture
judgments or eligibility changes. The copies were hash-verified at publication;
the demonstration did not review them visually. `verify` is the reproducible check
of this record against the checkout; there is no separate hand-written check file.

```sh
Fixtures/sample show draw-82acd83c6cd540a6bf4e29610ff5dc2d --paths
Fixtures/sample verify draw-82acd83c6cd540a6bf4e29610ff5dc2d
make -C Fixtures test-sampler
```

These commands change no tracked file. `Fixtures/sample publish` of this draw
also works, and appends a ninth event to the committed log, as
[Stores](#stores) describes; restore the file afterwards unless the receipt is
meant to be kept.

The mechanics tests create temporary `sampler-test-*` directories under
`Fixtures/output/` and remove them with their worlds and records on completion.
The neighboring-repository test installs the launcher and engine in a temporary
checkout, reuses the existing Python environment, and runs concurrent draws from
a sibling directory with no configuration flags. It checks the handoff using
only `output` and `world.json`, preserves earlier worlds, and republishes a saved
draw. No real sibling repository or user folder is used for test output.
Publication tests change a leaf's manifest after a draw: the draw republishes
while its images stay listed and is refused once one is listed nowhere.
Exclusion tests cover missing IDs and copies, malformed manifests, byte-identical
aliases, pool bounds, uniform selection, and replay without the original world.
The collection tests also exercise sampling, committed removal, and then
`sampleWithout` using the unchanged old world from a temporary neighbor.
Compatibility tests pin ordered selections and draw checksums captured before
the selection refactor, replay the committed demonstration draw, and check
candidate preparation after the temporary fixture files have disappeared.
