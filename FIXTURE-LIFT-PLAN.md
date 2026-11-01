# Lifting Fixtures out of hazy

This is a handoff for the agent who performs the lift. The decisions below are
made; the tasks are what remains. Read [WORLD.md](WORLD.md), [Fixtures/AGENTS.md](Fixtures/AGENTS.md)
and the [sampling engine guide](Fixtures/Sampler/README.md) first.

## Decisions already made

- hazy receives a **world** and nothing else. The contract is [WORLD.md](WORLD.md):
  hash-named files, a `world.json` with a world ID and the file list, no order, no
  origin. The world ID is the sample ID.
- Mapping a world back to fixtures is a Fixtures activity. The key is `Fixtures/sample
  show SAMPLE_ID`, computed on demand from the records. Nothing is stored for it.
- Each publication appends one `publication` annotation event to its draw. Whether
  anything hazy produces from a world is kept is a human decision made case by
  case; there is no scorer, no evaluation loop and no receipt schema beyond that.
- Separation is physical, not adversarial. An agent in the hazy checkout could read
  old history to learn fixture structure; that is accepted. Flattening hazy's
  history is a later, optional move.
- The new Fixtures repository keeps `Fixtures/` as a top-level directory, with
  `Fixtures/Makefile`, `Fixtures/.venv` and `Fixtures/output` beside the sets. Every
  recorded path and metadata pin starts with `Fixtures/`, so nothing in the records
  needs rewriting.
- Images are Git-ignored. The local `images/`, `sources/` and `previews/` directories
  must be moved with the checkout or restored into the new one; the records
  report what is missing.

## Already done in this repository

- The sampler publishes worlds (`--world DIR`, default `Fixtures/output/sampled/`),
  republishes an existing draw under its world ID, refuses unsafe destinations and
  writes a receipt per publication. Snapshots pin metadata by hash. Failures are
  named JSON errors. Tests: `make -C Fixtures test-sampler`.
- Fixtures is self-contained: Python venv, Makefile, output directory, guidance and
  tests all live under `Fixtures/`. Root guidance points there.
- `WORLD.md` exists at the hazy root and is linked from the README and `AGENTS.md`.
- `Research/` contains no reference to fixture collections or paths (checked by
  grep on 2026-11-01). Only `Experiments/` and the root README do.

## Remaining tasks

### 1. Make the experiment consume a world

The Apple Vision experiment is the only hazy code that reaches into `Fixtures/`.

- `Experiments/AppleVisionTranslation/Tests/AppleVisionTranslationExperimentTests/FixtureTests.swift`
  resolves `../../Fixtures` from its own path and reads
  `Relationships/Derivatives/manifest.json` and `selections.json`
  (`known_shift_families`). Rewire it to a world directory named by an environment
  variable, reading `world.json` and the files. Anything that needs provenance
  (shift families, probes, expected pairs) cannot be a hazy test under the world
  contract; it moves to the Fixtures side or is dropped. The seven mechanics tests
  (`--filter ComparisonTests`) already need no fixtures and stay.
- `Experiments/AppleVisionTranslation/Tools/fixtures.py` hard-codes
  `Fixtures/Relationships/Derivatives` and `Multiviews`. Its `check` mode validates
  fixture sets, which every leaf's `tools/check.py` now also does; its `run` mode
  drives the binary over probe pairs. Both are Fixtures-side activities. Ask the
  user whether `run` moves to Fixtures as a tool that drives the hazy binary, or is
  retired; `check` is redundant with the leaf validators.
- `Experiments/AppleVisionTranslation/Tools/test_fixtures.py` follows `fixtures.py`.
- `Experiments/AppleVisionTranslation/README.md` (fixture sets, focused selection,
  `fixtures.py` commands, the `Fixtures/.venv` note) and `IMAGE-JOURNEY.md`
  (section "Checks and fixture evidence", links into `../../Fixtures/`) describe the
  current coupling and must describe the world instead.
- Proof of completion: with `Fixtures/` absent from the checkout and a world
  directory supplied, `swift build` and `swift test` pass.

### 2. Move the fixture text out of hazy's documents

- Root `README.md`: the "Local fixture assets" section (sampling engine and
  collections) moves to the Fixtures repository's README. The project map row for
  Fixtures becomes a pointer to the Fixtures repository and to `WORLD.md`.
- Root `AGENTS.md`: the Fixtures track line and the fixtures bullet go; the
  `WORLD.md` pointer and the Python note about `Fixtures/.venv` go with them, since
  hazy will have no Python toolchain.
- `.gitignore`: the three `/Fixtures/**` media rules and the `/Fixtures/output`
  rules go with Fixtures.
- `WORLD.md` is shared text. Keep an identical copy in both repositories and note
  the counterpart in each; a change to one is a change to both.

### 3. Perform the move

- Create the Fixtures repository from this one preserving history for `Fixtures/`
  (for example `git subtree split` or `git filter-repo` keeping `Fixtures/`,
  `WORLD.md` and the `.gitignore` rules). Fixture provenance history is worth
  keeping; the sets' intake records refer to it.
- Move or restore the Git-ignored media at the same relative paths, then run
  `make -C Fixtures test-sampler`, `make -C Fixtures test-fixture-layout`,
  `Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full`,
  `Fixtures/sample verify draw-82acd83c6cd540a6bf4e29610ff5dc2d` and
  `Fixtures/sample publish draw-82acd83c6cd540a6bf4e29610ff5dc2d` in the new
  checkout. All must pass or report only the media you know to be absent.
- In hazy, delete `Fixtures/`, apply task 2, and run the proof from task 1.
- Then, if the user chooses, flatten hazy's history into a fresh repository.

## Order

Task 1 first, in hazy, while `Fixtures/` is still present to compare against. Task
2 next. Task 3 last, and only after task 1's proof passes. Each task is a checked
stopping point to commit.
