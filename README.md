# bricolage

bricolage helps build image fixtures and draw repeatable test samples from them.
It keeps the images, the reasons they were chosen, and the records needed to use
them again. The code and collections live in [Fixtures/](Fixtures/README.md).

The collections offer different things to try: crops and edits of the same
source, separate photographs of a scene, pictures selected for a visual motif,
and samples from published collections. Those choices help frame a test. A crop
and its source have a known relationship; how well an image matcher connects
them is still something to test.

## Get N images

From a neighboring repository:

```sh
../bricolage/Fixtures/sample 100
```

Replace `100` with N. From this repository, use `Fixtures/sample N`; an absolute
path to the executable also works. It uses bricolage's Python environment,
regardless of your working directory or activated environment. No imports or
inventory preparation are needed.

The JSON response starts with an `output` block after its schema and store:

```json
{
  "world_id": "draw-<32 hex digits>",
  "image_count": 100,
  "directory": "/absolute/path/to/bricolage/Fixtures/output/worlds/draw-<32 hex digits>",
  "manifest": "/absolute/path/to/bricolage/Fixtures/output/worlds/draw-<32 hex digits>/world.json",
  "published": true,
  "receipt_recorded": true,
  "next_steps": []
}
```

When `output.published` is true, give `output.directory` to the consumer. This
**world** holds N image copies named by their byte hashes and a `world.json`
listing them. Each draw has a separate directory, so later draws leave it intact.
Use `--world DIR` to choose a destination; an existing world there is replaced.
Use `--seed TEXT` to supply a seed; otherwise one is generated and recorded.

Check `problems` and `output.receipt_recorded` too. Exit 0 means no problems;
exit 1 can still leave a usable world, with publication recovery instructions in
`output.next_steps`. Exit 2 reports an `error` and the command did not complete.
The [sampler guide](Fixtures/Sampler/README.md) explains these outcomes.

If the Python environment is missing, follow the launcher's setup instruction.
With Python 3.14.x installed, setup from this repository is
`make -C Fixtures setup-python`. Sampling needs no third-party packages or
network access. It does need the local images: Git stores catalogs and tools,
while media is ignored. On a fresh checkout, restore supplied assets at their
recorded paths.

Each distinct file hash has an equal chance of selection. Byte-identical copies
share one place in the draw; crops and different encodings count separately.
Sampling spans all available collections and does not keep related images together.

## Remove an unsuitable image

When authorized to remove an image, take its `sha256:...` ID from `world.json`
(or its hash filename without the extension) and run:

```sh
../bricolage/Fixtures/collection remove sha256:HASH --reason "Why this image should be removed"
```

Replace `sha256:HASH` with the full ID. The command removes every active copy
with those exact bytes, updates the manifests and index, validates the result,
and commits its changes. The reason becomes the commit message; use
`--commit-message TEXT` for a different message. Success returns `complete: true`
and a `commit` hash. `--dry-run` previews the operation.

Unrelated staged and unstaged work stays intact. If the operation is incomplete,
its JSON report names the problem; resolve it and repeat the same command to
finish. Source evidence and already-published worlds remain available. Draw
again to get a world from the updated collection. The [removal guide](Fixtures/tools/README.md#removing-an-image)
describes scope, checks and recovery.

## Use the same sample again

Every draw saves its selection and the inventory it drew from. Use the returned
sample ID to inspect or republish it:

```sh
Fixtures/sample show SAMPLE_ID --paths
Fixtures/sample verify SAMPLE_ID
Fixtures/sample publish SAMPLE_ID --world Fixtures/output/repeat
```

`SAMPLE_ID` is a placeholder for `draw.sample_id` in the response. Republishing
keeps both the selection and world ID. A new draw with the same seed repeats the
selection only when the eligible population is the same; use
`--inventory INVENTORY_ID` to select from the saved population.

Ordinary draws live in `Fixtures/output/records/` and can be discarded. To keep a
draw in Git, put `--keep` before the command and commit its records:

```sh
Fixtures/sample --keep 12 --seed regression-example
Fixtures/sample --keep show SAMPLE_ID
Fixtures/sample --keep publish SAMPLE_ID --world Fixtures/output/regression
```

Use `--keep` on later commands for that draw too. Scratch records are copied from
the versioned store on first use and do not receive later updates automatically.
Keeping records does not put the image bytes in Git.

## Test with a world

Give the world directory to the image software being tested.
[WORLD.md](WORLD.md) specifies its files and the IDs a consumer reports back.
Collection names, source paths and selection notes stay here; `sample show`
connects a result's image IDs to those records.

A command can publish a world and still report problems elsewhere in the
collection. Check `problems`, `output.published` and `output.receipt_recorded`
in its JSON response. The [sampler guide](Fixtures/Sampler/README.md) covers
saved inventories, annotations, exit codes and publication failures. The optional
[probe runner](Fixtures/tools/README.md) runs recorded comparison pairs using a
world and an executable you supply.

## Work on fixtures

The [fixture index](Fixtures/README.md) lists the collections and their current
gaps. [CONTRIBUTING.md](CONTRIBUTING.md) discusses choosing and changing fixtures;
[AGENTS.md](AGENTS.md) gives the working rules and check commands.

bricolage was lifted from hazy. Existing IDs and Git history are retained so
older records can still be read. The
[lift receipt](Fixtures/provenance/repository-lift-2026-11.json) records the source
revision and asset checks.
