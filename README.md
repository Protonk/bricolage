# bricolage

bricolage collects image fixtures and draws repeatable samples from them.
A draw gives your program a directory of images. Its saved record tells you
where those images came from and what else could have been chosen.

## Draw a world

From a neighboring repository, ask for the number of images you need. The
checkout needs local image files. Git holds the catalogs and sampling records.

```sh
../bricolage/Fixtures/sample 100
```

From this repository, use `Fixtures/sample 100`. The launcher uses its own
Python environment and prints the setup command if needed. Each distinct byte
hash gets one ticket, even when several files contain the same image bytes.

When `output.published` is true, pass `output.directory` directly to your
program. Every publication gets a fresh directory. Treat it as read-only.
Check `problems` and `output.receipt_recorded`, and follow `output.next_steps`
if the sampler reports a problem.

## Explain or keep a world

Use the returned `output.world_id` in place of `WORLD_ID`.

```sh
Fixtures/sample show WORLD_ID
Fixtures/sample keep WORLD_ID
```

`show` reports the images and their membership in the archive at draw time.
For example, the [saved elbow draw](Fixtures/Sampler/records/draws/draw-4622e72641da4b64a3c6296f4942b565/draw.json)
selected 12 of the 171 eligible Derivatives images. Later additions to the
archive leave that denominator intact. Ordinary draws are disposable.
If a draw becomes evidence, `keep` saves its records and lists the `files` to commit.

Browse the [fixture catalog](Fixtures/README.md), read the [consumer contract](WORLD.md),
or use the [sampler guide](Fixtures/Sampler/README.md) for exclusion and replay.
The [collection tools](Fixtures/tools/README.md) cover removal and recovery.
