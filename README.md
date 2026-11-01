# bricolage

bricolage helps build image fixtures and draw repeatable test samples from them.
It keeps the images, the reasons they were chosen, and the records needed to use
them again. The code and collections live in [Fixtures/](Fixtures/README.md).

The collections offer different things to try: crops and edits of the same
source, separate photographs of a scene, pictures selected for a visual motif,
and samples from published collections. Those choices help frame a test. A crop
and its source have a known relationship; how well an image matcher connects
them is still something to test.

## Try a sample

With Python 3.14.x installed, run from the repository root:

```sh
make -C Fixtures setup-python
Fixtures/sample 12 --seed first-look
```

Sampling needs no third-party Python packages or network access. It does need
the local images: Git stores the catalogs and tools, while media is ignored.
On a fresh checkout, restore the supplied assets at their recorded paths.

The command writes a **world** to `Fixtures/output/sampled/`: twelve image
copies, named by their byte hashes, and a `world.json` listing them. The next
successful draw replaces that directory. Use `--world Fixtures/output/NAME`
to keep separate worlds. The JSON response includes the sample ID, selected
images, record store and any problems.

Each distinct file hash has an equal chance of selection. Byte-identical copies
share one place in the draw; crops and different encodings count separately.
Sampling spans all available collections and does not keep related images together.

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
