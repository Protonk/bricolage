# hazy

**0.0.1a — an experimental image-similarity router research project.**

hazy investigates how to propose overlapping neighborhoods within a batch of
images and present multiple channels of evidence about their relationships.
Membership remains provisional; semantic cluster names are an anti-goal.
The router is specified but not implemented.

## Project map

| Location | Role |
|---|---|
| [Research/Router](Research/Router/README.md) | Router requirements and design research |
| [Research/Portability](Research/Portability/README.md) | Parallel research into framework handoffs and an eventual shared API on macOS and Linux |
| [Experiments/AppleVisionTranslation](Experiments/AppleVisionTranslation/README.md) | Working macOS translation channel experiment, with its own Swift package, CLI, tests, and tools |
| [Fixtures](Fixtures/README.md) | Provenance relationship sets and separately selected image heaps; media remains local and Git-ignored |

There is no root Swift package or router executable. The existing code lives in
an explicitly named experiment so its structure cannot be mistaken for the
router architecture.

## Router design

[Horizontal Gene Transfer](Research/Router/HORIZONTAL-GENE-TRANSFER.md) defines the
CLI MVP: baseline neighborhoods, bounded pair investigation, structured output,
and scratch lineage for each call. Automatic membership refinement and churn
are outside MVP.

[Backwards Induction](Research/Router/BACKWARDS-INDUCTION.md) carries goals,
anti-goals, reservations, and architectural insistences. It leaves concrete
pathways and shared architecture open for focused work.

## Parallel portability research

[The portability track](Research/Portability/README.md) studies what hazy controls,
what it delegates to Apple frameworks, and what guarantees are visible to callers.
The goal is to make informed decisions about an eventual implementation with the
same API on Linux, potentially using OpenCV, including capabilities we deliberately
defer or decline to port. Neither a Linux implementation nor a portable API is
implemented today.

[The capability ledger](Research/Portability/CAPABILITY-LEDGER.md) starts with
observations from the current experiment. Framework behavior, hazy's policy, and
portable contract candidates remain distinct.

## Run the existing experiment

From the repository root on macOS:

```sh
swift build --package-path Experiments/AppleVisionTranslation
mkdir -p output
swift run --package-path Experiments/AppleVisionTranslation hazy-vision-translation compare /path/to/reference.png /path/to/floating.png --output output/example
swift test --package-path Experiments/AppleVisionTranslation
```

The output parent must already exist, and the destination must be new. The
experiment requires Swift 6 and declares macOS 14 as its minimum. It uses Apple
frameworks and has no third-party package dependencies.

The [experiment README](Experiments/AppleVisionTranslation/README.md) describes
reports, fixture checks, and limitations. Its
[image journey](Experiments/AppleVisionTranslation/IMAGE-JOURNEY.md) traces the
actual implementation. Tests using real fixtures require the local image assets;
a fresh checkout contains only their descriptions and checksums. The seven
self-contained mechanics tests can run with `--filter ComparisonTests`.

## Local fixture assets

`Fixtures/Relationships/` holds Derivatives, Multiviews and Variants.
`Fixtures/Heaps/Similarity/` holds the prompt-selected contributions to the
current similarity heap. `Fixtures/Heaps/Curatorial/POTY/` holds mechanical
samples from three official Wikimedia Commons Picture of the Year Round 1
categories, pooled across 2023–2025; see its README for acquisition completeness.
`Fixtures/Heaps/Curatorial/US-Army-SSI/` is one contribution from Commons
category membership with 150 acquired shoulder-sleeve insignia designs. Eight
earlier candidates remain pending, with later selections explicitly provisional.
See its README for the frozen PetScan population, pending selection and offline checks.
[Botanical Illustrations](Fixtures/Heaps/Curatorial/Botanical-Illustrations/README.md)
is one direct-category contribution with 150 selected works and 149 acquired
inputs. One transfer and 14 earlier selection cases remain pending.
[Evan-Amos category uploads](Fixtures/Heaps/Curatorial/Evan-Amos-Uploads/README.md)
imports every direct File member of its source category except three supplied
exclusions: all 133 included files are acquired, retaining related views and formats.

Fixture sets use `images/` for comparison inputs and `sources/` for preserved
source bytes. Optional `previews/` contains contact sheets, outside the input set.
Git ignores these entire directories for every fixture set, including nested files
and unknown or absent extensions. Keep future image assets in those locations.
The manifests, source catalogs, checksums, and textual provenance remain versionable.
See [Fixtures/README.md](Fixtures/README.md) for the format and local checks.

[AGENTS.md](AGENTS.md) gives working guidance. Work on the task explicitly selected
in the conversation; the research documents are not an instruction to implement
all possible directions.
