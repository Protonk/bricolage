# Disposable output

Contents of this directory may be removed at any time. Do not keep source
assets, durable records, or anything that must survive here. Preserve this
checked-in `AGENTS.md` when clearing output; everything else is disposable and
Git-ignored.

`sampled/` holds byte-identical copies from the latest successful `Fixtures/sample N`
draw, with a `sample.json` sidecar naming each copy's sample, fixture origin and
provenance rows. Each successful draw deletes its previous contents and replaces
them. It is safe to edit these copies; original fixture images remain separate.
The sidecar is derived from the durable records and is disposable too.

Persistent sample inventories, original draws and annotations live in
`Fixtures/Sampler/records/` by default. Use those records to recover identities
or reproduce a sample after output is cleared. The sampler creates `sampled/`
when needed; an empty checkout directory need not be tracked.
