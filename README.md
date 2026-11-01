# bricolage

bricolage owns local image collections, their provenance, and a sampling engine
that publishes opaque worlds for independent image-analysis applications.
The application lives under `Fixtures/`; those paths preserve the existing records
and metadata pins. Its public entry point is `Fixtures/sample`.

## Set up and sample

Use installed Python 3.14.x. From the repository root:

```sh
make -C Fixtures setup-python
Fixtures/.venv/bin/python -m pip install -r Fixtures/tools/requirements.txt
Fixtures/sample 12 --seed my-investigation
```

Sampling itself uses only the standard library. Pillow 12.0.0 supports the current
fixture validators; optional tools retain separate requirements. A fresh checkout
contains versioned text, not the ignored media. Restore the supplied assets at their
existing relative paths before using media-dependent commands. Do not acquire a new
corpus to fill missing files.

A draw publishes hash-named, byte-identical copies beside `world.json`, normally
under `Fixtures/output/sampled/`. `--world DIR` chooses another destination.
[WORLD.md](WORLD.md) is the consumer contract. No selection order, fixture paths,
groups or provenance enter the world manifest. World IDs identify saved draws;
republishing a draw preserves its ID, while repeating its seed creates a new draw
with the same selection. Finish consuming a directory before replacing its world.

Durable snapshots, draws and annotations live in `Fixtures/Sampler/records/`.
Use `Fixtures/sample show SAMPLE_ID` to map identities back to their provenance,
`verify SAMPLE_ID` to check a record, and `publish SAMPLE_ID --world DIR` to publish
it again. Receipt and cleanup failures are explicit even if installation succeeded;
read the command's `problems`, `output.published` and `output.receipt_recorded` fields.
The [sampler guide](Fixtures/Sampler/README.md) explains recovery and record formats.

## Collections and validation

The [fixture index](Fixtures/README.md) describes the relationship sets and image
heaps, including their existing acquisition shortfalls. Selection facts do not
establish visual matches or expected neighborhoods. Original source bytes,
metadata identities and historical evidence remain preserved.

```sh
make -C Fixtures test-sampler
make -C Fixtures test-fixture-layout
make -C Fixtures test-relationships
Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full
```

The optional [probe runner](Fixtures/tools/README.md) needs explicit `--world` and
`--binary` arguments. It resolves saved-draw provenance here, maps probes to image
IDs, and passes only the world and IDs to a compatible comparison executable.
Missing endpoints are recorded as skipped. No sibling application's source tree,
build location or repository name is assumed.

All media belongs in leaf `images/`, `sources/` or `previews/` directories and remains
Git-ignored, including nested files and unfamiliar extensions. Disposable worlds
belong under `Fixtures/output/`; records and source assets do not. Read
[AGENTS.md](AGENTS.md), [fixture guidance](Fixtures/AGENTS.md) and the
[shared format](Fixtures/FORMAT.md) before changing the application or evidence.

The repository retains the original hazy history so existing provenance commit
IDs remain resolvable. Its current tree is the standalone bricolage application.
The [lift receipt](Fixtures/provenance/repository-lift-2026-11.json) records the
source revision, asset verification and checks. No remote is configured.
