# Disposable Fixtures output

Contents of this directory may be removed at any time. Do not keep source
assets, durable records, or anything that must survive here. Preserve this
checked-in `AGENTS.md` when clearing output; everything else is disposable and
Git-ignored.

`sampled/` is the default world directory: hash-named, byte-identical copies
from the latest successful `Fixtures/sample N` draw beside a `world.json`
naming the world ID and its files. Each successful draw replaces the previous
world. Treat a published world as read-only and republish rather than edit it;
original fixture images remain separate.
`--world DIR` writes a world elsewhere instead.

`records/` is the scratch record store: the default home of inventories, draws,
annotations and publication receipts, seeded from the versioned
`Fixtures/Sampler/records/` on first use. Clearing it discards every draw not made
with `--keep`, and with it the only key to the worlds those draws published. The
sampler creates `sampled/` and `records/` when needed; neither needs tracking.
