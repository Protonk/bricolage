# Disposable Fixtures output

Contents of this directory may be removed at any time. Do not keep source
assets, durable records, or anything that must survive here. Preserve this
checked-in `AGENTS.md` when clearing output; everything else is disposable and
Git-ignored.

`sampled/` is the default world directory: hash-named, byte-identical copies
from the latest successful `Fixtures/sample N` draw beside a `world.json`
naming the world ID and its files. Each successful draw replaces the previous
world. It is safe to edit these copies; original fixture images remain separate.
`--world DIR` writes a world elsewhere instead.

Persistent sample inventories, original draws, annotations and publication
receipts live in `Fixtures/Sampler/records/` by default. Use those records to
recover identities or republish a world after output is cleared. The sampler
creates `sampled/` when needed; an empty checkout directory need not be tracked.
