# Disposable Fixtures output

Contents of this directory may be removed at any time. Do not keep source
assets, durable records, or anything that must survive here. Preserve this
checked-in `AGENTS.md` when clearing output; everything else is disposable and
Git-ignored.

`worlds/<sample_id>/` is the default directory for each draw: hash-named,
byte-identical copies beside a `world.json` naming the world ID and its files.
Use the directory the sampler returns. Each `publish WORLD_ID` creates a new
directory containing that same selection. Explicit destinations must be new.

Worlds accumulate until their consumers are finished. Remove only the disposable
worlds you no longer need. Sampler tests use temporary `sampler-test-*` directories
here and remove them, including their worlds and scratch records, on completion.
Collection tests similarly use `collection-test-*`, including temporary Git
repositories, and remove them on completion. `collection.lock` serializes
collection commands; it contains no recovery state. Removal operation records
live outside this disposable directory, under `Fixtures/provenance/removal-operations/`.

`records/` holds disposable inventories, draws, annotations and publication receipts.
Use `Fixtures/sample keep WORLD_ID` before clearing scratch to retain the draw
in the versioned store. Commit those records if the draw should be shared.
