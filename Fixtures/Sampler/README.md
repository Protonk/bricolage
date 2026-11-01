# Fixture sampler

Draw equal tickets from hazy's local fixture inputs and keep a record that other
programs can read. Python 3.9+ on macOS or Linux; standard library only. There is
no network access, image transformation, comparator or activity-specific logic.

## Use

From the repository root:

```sh
python3 Fixtures/Sampler/sampler.py inventory
python3 Fixtures/Sampler/sampler.py draw 12 --seed my-investigation
python3 Fixtures/Sampler/sampler.py list
```

`draw` refreshes the inventory by default and returns a persistent `sample_id`.
Omit `--seed` to generate and record a seed. N may be zero; negative N or N larger
than the eligible population is an error. There is no replacement or size adjustment.

Use the returned full identifiers in these commands:

```sh
python3 Fixtures/Sampler/sampler.py show SAMPLE_ID --paths
python3 Fixtures/Sampler/sampler.py show SAMPLE_ID
python3 Fixtures/Sampler/sampler.py verify SAMPLE_ID
python3 Fixtures/Sampler/sampler.py annotate SAMPLE_ID --key purpose --json '"Notebook study"'
python3 Fixtures/Sampler/sampler.py annotate SAMPLE_ID --image IMAGE_ID --key review --json '{"decision":"accepted","tags":["reference"],"note":"My observation"}'
python3 Fixtures/Sampler/sampler.py annotate SAMPLE_ID --image IMAGE_ID --key review --json '{"decision":"revisit","note":"Revised observation"}'
python3 Fixtures/Sampler/sampler.py annotate SAMPLE_ID --image IMAGE_ID --key review --delete
```

`SAMPLE_ID` and `IMAGE_ID` above are placeholders. `show --paths` returns ordered
image IDs, an available absolute path per image (or null), and every alias's
current status. Open those paths with the local viewer of your choice. `show`
also returns the original draw, frozen fixture/source metadata, current
annotations and the complete annotation history, even if image files are missing.

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
python3 Fixtures/Sampler/sampler.py draw 12 --seed my-investigation --inventory INVENTORY_ID
```

This creates a new sample ID with the same ordered image IDs. It does not copy
annotations from the previous sample. A saved snapshot keeps its original
eligibility: missing files discovered later are reported, never replaced in the
draw. Use a fresh `inventory` or the default `draw` to reflect today's availability.

All successful commands output JSON. Exit codes are 0 for success, 1 for a
`verify` report with current file/metadata problems, and 2 for invalid arguments,
damaged records or I/O errors. `draw` persists the original selection and includes
a `current_check`; a file becoming unavailable never causes a replacement draw.

Global `--repo CHECKOUT` and `--store DIRECTORY` options go **before** the command.
Defaults resolve from this script, so commands also work from another directory.
The default store is [records/](records/). It contains versionable text only;
image bytes remain at their fixture locations. Use `--store output/samples` for
a local Git-ignored store. Back up or version the whole store, including inventories.

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

Metadata is copied from each full manifest row, its parent/family source-catalog
rows (including multiple parents), and the matching import-map row when present.
Unknown source fields stay unknown. Metadata-file paths and SHA-256s identify
the surrounding manifest, catalog, import map and readable credits. No provenance
field is interpreted as a sampling weight or investigation decision.

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
| Inventory | `inventory_id`, `created_at`, and a `population` object with schema/policy, sorted `images`, metadata-file checksums, counts and unlisted inputs |
| Inventory image | `image_id`, `byte_sha256`, frozen `eligible`, and `aliases`; each alias has fixture ID/kind/path, full manifest/source/import records and observed availability |
| Draw | Schema, sample ID, timestamp, inventory ID/store-relative reference, versioned procedure, exact seed text, requested size, eligible count, ordered `image_ids`, draw checksum |
| Annotation event | Schema, sequence, event ID, timestamp, sample ID/draw checksum, nullable `image_id` (null means sample), optional author, arbitrary key, `set`/`delete`, and a value for `set` |

Inventory IDs hash the `population` object, excluding its creation timestamp.
Identical rescans reuse one snapshot. A draw's checksum covers all its fields
except `draw_sha256`. Canonical JSON for these hashes is UTF-8, sorted object keys,
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
annotation history, and rehashes all selected aliases and their fixture metadata
files. Changed provenance is reported while the frozen metadata remains readable.
New inventories and all later annotations leave an existing draw unchanged.

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
rejection at the boundary, and pin a stream vector for cross-version reproduction.

## Demonstration and checks

The committed [demonstration draw](records/draws/draw-74427fcd61234647bc46613f73deeecd/draw.json)
contains 12 images drawn once with seed `fixture-sampler-demo-2026-11-01` from
1,251 eligible byte identities: 1,263 manifest records across 18 leaves, with 12
redundant byte-identical aliases. All input hashes passed; none were unavailable
or unlisted. No strata, quota or reroll was used.

All twelve local images were opened for inspection. Eight example annotation
events include sample notes, image notes/roles, a revised value, a deleted value
and an artifact reference. Their [history](records/draws/draw-74427fcd61234647bc46613f73deeecd/annotations.jsonl)
preserves the prior values. [demo-checks.json](demo-checks.json) records the reload,
original draw byte equality and current-file verification. The examples are
investigation annotations, not fixture judgments or eligibility changes.

```sh
python3 Fixtures/Sampler/sampler.py show draw-74427fcd61234647bc46613f73deeecd --paths
python3 Fixtures/Sampler/sampler.py verify draw-74427fcd61234647bc46613f73deeecd
python3 -m unittest discover -s Fixtures/Sampler -p 'test_*.py'
```
