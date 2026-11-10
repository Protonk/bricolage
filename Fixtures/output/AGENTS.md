# Disposable Fixtures output

Contents of this directory may be removed at any time. Do not keep source
assets, durable records, or anything that must survive here. Preserve this
checked-in `AGENTS.md` when clearing output; everything else is disposable and
Git-ignored.

`worlds/<sample_id>/` is the default directory for each draw: hash-named,
byte-identical copies beside a `world.json` naming the world ID and its files.
New draws leave earlier worlds intact. Default `publish SAMPLE_ID` replaces that
draw's world. Treat a published world as read-only and republish rather than edit
it; original fixture images remain separate. `--world DIR` chooses a destination
explicitly and replaces an existing world there. Older `sampled/` worlds remain
untouched unless explicitly chosen with `--world`.
`sampleWithout WORLD_DIRECTORY N` publishes here too, leaving its input world
untouched. Saved exclusions let its draw be republished after that input is gone.

Worlds accumulate until their consumers are finished. Remove only the disposable
worlds you no longer need. Sampler tests use temporary `sampler-test-*` directories
here and remove them, including their worlds and scratch records, on completion.
Collection tests similarly use `collection-test-*`, including temporary Git
repositories, and remove them on completion. `collection.lock` serializes
collection commands; it contains no recovery state. Removal operation records
live outside this disposable directory, under `Fixtures/provenance/removal-operations/`.

`records/` is the scratch record store: the default home of inventories, draws,
annotations and publication receipts, seeded from the versioned
`Fixtures/Sampler/records/` on first use. Clearing it discards every draw not made
with `--keep`, and with it the only key to the worlds those draws published. The
sampler creates `worlds/` and `records/` when needed; neither needs tracking.
