# bricolage fixtures

Fixtures are organized by why their images were chosen. The provenance
relationship sets and the selected image heaps have different evidential roles.

## Sampling engine

Run `Fixtures/sample N` from the repository root (or `./sample N` from here) to
draw N images uniformly from all available Heaps and Relationships inputs.
Optional `--seed TEXT` makes a draw repeatable. The command saves the original
draw and inventory, and returns JSON with `draw.sample_id`,
`population.counts.eligible` (M), and ordered `images[].sampled_path` values.
Each successful draw publishes a world, by default at `Fixtures/output/sampled/`:
hash-named byte-identical copies beside a `world.json`, with no fixture origin.
`show SAMPLE_ID` is the key that maps a world back to leaves and rows.
The originals stay in their fixtures, and durable records stay in `Sampler/records/`.
Exact-byte aliases share one ticket. An oversized request fails explicitly. Exit
code 1 with a `problems` list means a fixture or record needs attention; the JSON
still says whether the draw itself was published. A leaf whose metadata fails
validation is excluded and named, and the draw proceeds over the rest.

The engine uses `Fixtures/.venv` with Python 3.14.x. On a new checkout, run
`make -C Fixtures setup-python` at the repository root once. Run `Fixtures/sample --help`
for commands, or read the [engine guide](Sampler/README.md) to inspect saved
samples and attach annotations. `make -C Fixtures test-sampler` runs the focused tests.

## Collections

```text
Fixtures/
  AGENTS.md               # Working guidance for this directory
  Makefile                # Python 3.14 venv and test targets; run as make -C Fixtures
  sample                  # Public sampling engine
  Sampler/                # Implementation, tests and persistent JSON records
  output/                 # Disposable worlds; sampled/ is the default
  Relationships/
    Derivatives/
    Multiviews/
    Variants/
  Heaps/
    Similarity/
      RG01/
      SF01/
      PS01/
      CR01/
      TG01/
      BSP01/
    Curatorial/
      POTY/
        Arthropods/
        Constructions-and-buildings/
        People-and-human-activity/
      US-Army-SSI/
      Botanical-Illustrations/
      Evan-Amos-Uploads/
      Rocks-in-Thin-Section/
      Stone-Hand-Axes/
      Ex-Libris/
```

| Location | Role |
|---|---|
| [Relationships](Relationships/README.md) | The chosen trio: derivation, multiple captures, and variants, with recorded source relationships and comparison probes |
| [Heaps](Heaps/README.md) | Independently selected image pools, each with its own selection criteria |
| [Similarity](Heaps/Similarity/README.md) | One heap assembled from collections chosen to look alike under short visual prompts |
| [Curatorial](Heaps/Curatorial/README.md) | Published populations with mechanical sampling or exhaustive membership rules; see each contribution |

RG01, SF01, PS01, CR01, TG01 and BSP01 belong to the same Similarity heap. They retain their
own acquisition and review records. Their collection membership records human
selection intent; it is not an expected router neighborhood or matching verdict.
Curatorial occupies a sibling directory under `Heaps/`; its POTY source collection
contains three category contributions one level deeper. Their official category
membership is a sourcing fact, not a similarity judgment.
The [US-Army-SSI leaf](Heaps/Curatorial/US-Army-SSI/README.md) sits beside POTY:
150 acquired inputs from 1,641 frozen PetScan results. Eight earlier cases remain
pending; later selections are provisional. It has no sub-heaps.
[Botanical Illustrations](Heaps/Curatorial/Botanical-Illustrations/README.md) is
another single leaf, using 709 frozen direct-category File entries and a target
of 150 distinct works. It has 149 acquired inputs, one pending transfer, and
14 earlier unresolved selection cases; later selections remain provisional.
[Evan-Amos-Uploads](Heaps/Curatorial/Evan-Amos-Uploads/README.md) imports all
136 frozen direct category members minus three exact supplied exclusions,
all 133 other File identities are acquired and validated, with zero pending.
Related views and formats remain included without sampling or deduplication.
[Rocks in Thin Section](Heaps/Curatorial/Rocks-in-Thin-Section/README.md),
[Stone Hand Axes](Heaps/Curatorial/Stone-Hand-Axes/README.md) and
[Ex Libris](Heaps/Curatorial/Ex-Libris/README.md) each pool three direct category
lists into one independent leaf. Fixed seeded ordering and recorded thumbnail
scope, provenance and rights decisions determine their 50-image selections.
Each leaf separates complete acquisition from earlier deferred selection cases.

## Working with the fixtures

- Share the [short web-agent guide](WEB-AGENT-GUIDE.md) with a partner helping
  source a new fixture. A clear brief and traceable leads are sufficient for a
  local handoff; the partner does not need to reproduce our repository machinery.
- Start new leaves from the [single fixture template](Template/README.md).
  It covers heaps and relationship sets, with kind-specific evidence requirements.
- Every leaf exposes `tools/check.py` and `tools/requirements.txt`. Run
  `Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full` from the repository root
  to check all 18 leaves, including their specialized offline validators.
- Shared relationship validation and the optional probe runner live in
  [tools/relationship_fixtures.py](tools/relationship_fixtures.py). Run `make -C Fixtures
  test-relationships` for their checks. The runner requires an explicit experiment
  binary; fixture validation has no dependency on the experiment checkout.
- Use `Fixtures/sample N` to draw equal tickets across active Heaps and
  Relationships inputs and preserve separate arbitrary annotations.
- Open the relevant role or heap README, then the leaf set's README for its
  prompt or relationship, status, provenance and check command.
- Put a new contribution inside its intended heap. A new contribution to
  Similarity goes beside RG01, SF01, PS01, CR01, TG01 and BSP01; its prompt, exclusions,
  acceptable looseness and review/acquisition status belong with that contribution.
  Curatorial contributions can sit below their source collection. Read the
  [POTY record](Heaps/Curatorial/POTY/README.md) for its inventories and check commands.
- Preserve supplied records and source bytes. All media, intermediate images and
  archives stay in the leaf set's `images/`, `sources/` or `previews/` directories.
  These directories remain Git-ignored at every depth.
  Disposable sampler worlds go under `Fixtures/output/` and are replaced on each draw.
- Read [FORMAT.md](FORMAT.md) for manifests, source records, checksums and the
  distinction between provenance and visual judgments. Existing fixture IDs and
  manifest kinds are unchanged by this organization.

The optional comparison runner defaults to Derivatives and uses an explicitly
supplied experiment binary. Heap collections use their fixture-local validators and
have no expected pairs. A repository checkout contains the text records and
tools; restore local media before running checks that need it.

## Locations and history

| Previous folder directly under `Fixtures/` | Current location |
|---|---|
| `hazy-derivatives-v1` | `Relationships/Derivatives` |
| `hazy-multiview-v1` | `Relationships/Multiviews` |
| `hazy-meme-fixtures-v0` | `Relationships/Variants` |
| `hazy_rg01_sourcing_v01` | `Heaps/Similarity/RG01` |
| `hazy_sf01` | `Heaps/Similarity/SF01` |
| `hazy_ps01` | `Heaps/Similarity/PS01` |
| `hazy_cr01` | `Heaps/Similarity/CR01` |
| `hazy_tg01` | `Heaps/Similarity/TG01` |
| `hazy_bsp01` | `Heaps/Similarity/BSP01` |
| `US-Army-SSI-handoff` (instruction package) | `Heaps/Curatorial/US-Army-SSI/provenance/supplied` |
| `Botanical-Illustrations-handoff` (instruction package) | `Heaps/Curatorial/Botanical-Illustrations/provenance/supplied` |
| `Evan-Amos-Uploads-handoff` (instruction package) | `Heaps/Curatorial/Evan-Amos-Uploads/provenance/supplied` |
| `hazy_curatorial_three_50_handoff` (instruction package) | `provenance/supplied` in each of Rocks-in-Thin-Section, Stone-Hand-Axes and Ex-Libris under `Heaps/Curatorial` |

Active commands and links use the current locations. Preserved supplied files,
completed run records and existing ZIP snapshots retain their creation-time
paths and instructions. Paths inside manifests remain relative to their leaf
set. The move does not alter any source, input or preview bytes.
