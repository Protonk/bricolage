# Working on Fixtures

Fixtures is the fixture collection, its intake tools and the sampling engine. It
is self-contained: its Python toolchain, tests, output and records all live under
this directory. Read [README.md](README.md) first, then the relevant guide:

- Fixture design, organization and intake: [README.md](README.md),
  [FORMAT.md](FORMAT.md) and the [single leaf template](Template/README.md).
- Sampling, worlds, records and annotations: [the sampling engine](Sampler/README.md).
- What a consumer of a world may assume: [WORLD.md](../WORLD.md) at the repository root.

Rules of work:

- Target Python 3.14.x only. Use `Fixtures/.venv` (`make -C Fixtures setup-python`
  from the repository root); do not run a Python version matrix. The sampler and
  the layout tools need no third-party packages; leaf tools keep their own
  `tools/requirements.txt`.
- For fixture samples, use `Fixtures/sample N` rather than assembling a draw by
  hand. Records go to the scratch store under `output/records/` unless `--keep`
  precedes the command. A draw publishes a world; `show SAMPLE_ID` is the key that maps a world back
  to leaves and rows. Worlds carry no fixture structure, and nothing in this
  directory should start to assume they do.
- Use the supplied fixtures. Do not search for or acquire a corpus. Put image
  assets only in a leaf's `images/`, `sources/` or `previews/` directory; all
  contents of those directories are Git-ignored regardless of type. Do not
  force-add them. Generated patterns check mechanics, not usefulness on real images.
- The sampler writes disposable worlds, by default to `output/sampled/` here,
  replacing that directory on each successful draw, and scratch records to
  `output/records/`. Keep original fixture assets outside any `output/`; see
  [output guidance](output/AGENTS.md). Durable sample records live in
  `Sampler/records/`, are versioned, and are written only with `--keep`.
- Preserve supplied records and source bytes. Make errors and missing results
  visible; a fixture problem is reported by name and fixed at the fixture, never
  patched around in the tools. Distinguish provenance facts from visual judgments.
- Keep documentation consistent with code. Report meaningful changes, focused
  checks and remaining uncertainty in plain language.
- Handle local Git logistics as the repository root guidance describes.

Checks from the repository root:

```sh
make -C Fixtures test-sampler
make -C Fixtures test-fixture-layout
make -C Fixtures test-relationships
Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full
```
