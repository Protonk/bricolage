# bricolage fixtures

This directory contains the image collections, their records, and the tools for
checking and sampling them. A **leaf** is a collection directory with its own
`manifest.json`; the directories above it group related collections.

## Draw a sample

From the repository root:

```sh
make -C Fixtures setup-python
Fixtures/sample 12 --seed first-look
```

The sampler selects uniformly across available inputs in Heaps and Relationships.
Exact byte copies count once. It saves the draw and inventory in the scratch store
at `Fixtures/output/records/` and publishes image copies with `world.json` under
`Fixtures/output/sampled/`. Put `--keep` before the command for records to commit.

Use `show SAMPLE_ID` to inspect the selection and source records,
`verify SAMPLE_ID` to check them, and `publish SAMPLE_ID` to reuse that draw.
Use the same store option on those commands. The [sampler guide](Sampler/README.md)
explains saved inventories, annotations, output paths and errors.

## Collections

| Location | What it contains |
|---|---|
| [Relationships](Relationships/README.md) | Derivatives of known sources, separate captures of scenes, and constructed or generated variants |
| [Heaps / Similarity](Heaps/Similarity/README.md) | Six collections chosen by visual prompts: red accents in green surroundings, speckled fields, pale skies, repeated rectangles, tangled growth, and spreading patches |
| [Heaps / Curatorial](Heaps/Curatorial/README.md) | Selections from published collections: Commons POTY categories, insignia, botanical illustrations, Evan Amos uploads, rocks, hand axes and bookplates |

The relationship sets record how images are connected. The heaps record why
images were selected. Both can inform a test, but neither supplies the result an
image matcher should return.

The [heap guide](Heaps/README.md) also describes the local picture book of
selected images and how to rebuild it.

Current catalogs list 1,263 inputs across 18 leaves, representing 1,251 distinct
byte hashes. Acquisition is incomplete in SF01 (11 accepted images pending) and
Botanical Illustrations (one transfer pending). POTY Arthropods has 43 inputs
against a target of 50. Some Curatorial selections also have earlier unresolved
review cases; their later selections remain provisional. Each collection's README
and records give the details.

## Tools and records

| Path | Contents |
|---|---|
| `sample` | Public sampler command |
| [Sampler/](Sampler/README.md) | Sampler code, tests and versioned records |
| [tools/](tools/README.md) | Layout checks, fixture creation and the optional comparison runner |
| [Template/](Template/README.md) | Starting files for a new leaf |
| [output/](output/AGENTS.md) | Disposable worlds, scratch records and check reports |

Each leaf keeps inputs in `images/`, original assets in `sources/` and previews
or intermediate images in `previews/`. These directories are ignored by Git.
Text catalogs, checksums, source records and tools are versioned. Restore the
supplied media at its recorded paths before running checks that need it.

## Check or change a collection

Read [AGENTS.md](AGENTS.md), the collection's README and
[FORMAT.md](FORMAT.md) before changing its files. For a new leaf, use the
[template](Template/README.md); the [handoff guide](WEB-AGENT-GUIDE.md) describes
what a sourcing partner can supply. Put new contributions alongside the existing
collections with the same selection basis.

Every leaf has `tools/check.py` and `tools/requirements.txt`. From the repository
root, install the shared validator dependency and check all leaves:

```sh
Fixtures/.venv/bin/python -m pip install -r Fixtures/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full
```

`--metadata-only` checks layout and catalogs without local media; it omits the
specialized validators. The [tools guide](tools/README.md) describes narrower
checks and the test targets. The optional comparison runner needs a published
world and an executable supplied by the caller.

Older paths and supplied instructions remain in the provenance records. The
[layout record](provenance/layout-2026-11/README.md) describes the directory move;
current commands use the locations above. Fixture IDs and media bytes were kept.
