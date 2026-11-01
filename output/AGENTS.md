# Disposable output

Contents of this directory may be removed at any time. Do not keep source
assets, durable records, or anything that must survive here. Preserve this
checked-in `AGENTS.md` when clearing output; everything else is disposable and
Git-ignored.

`sampled/` holds byte-identical copies from the latest successful `Fixtures/sample N`
draw. Each successful draw deletes its previous contents and replaces them.
It is safe to edit these copies; original fixture images remain separate.

Persistent sample inventories, original draws and annotations live in
`Fixtures/Sampler/records/` by default. Use those records to recover identities
or reproduce a sample after output is cleared. The sampler creates `sampled/`
when needed; an empty checkout directory need not be tracked.
