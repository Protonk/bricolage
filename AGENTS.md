# Working on hazy

Read [README.md](README.md) before substantial work. Follow the relevant track:

- Fixtures, sampling and worlds: [Fixtures/AGENTS.md](Fixtures/AGENTS.md). What hazy
  may assume about a world it receives: [WORLD.md](WORLD.md).
- Router: [Horizontal Gene Transfer](Research/Router/HORIZONTAL-GENE-TRANSFER.md)
  and [Backwards Induction](Research/Router/BACKWARDS-INDUCTION.md).
- Framework boundary and portability: [Research/Portability](Research/Portability/README.md)
  and its [capability ledger](Research/Portability/CAPABILITY-LEDGER.md).
- Current code: [Experiments/AppleVisionTranslation](Experiments/AppleVisionTranslation/README.md)
  and its [image journey](Experiments/AppleVisionTranslation/IMAGE-JOURNEY.md).

hazy is a research project for an image-similarity router. The working macOS code
is an experimental channel, physically isolated with its own package and CLI.
It is not the router architecture or the future portable API.

- Keep changes small enough to follow from input to output. Add abstractions and
  dependencies when implemented behavior needs them.
- Preserve source images. Make errors and missing results visible, and distinguish
  measurements from judgments that images match.
- Keep framework request and observation types inside their implementation.
  Record what hazy controls, what it delegates, and the result conventions callers
  can rely on. Update the portability ledger when that handoff changes.
- Keep experiment documentation consistent with code. Report meaningful changes,
  focused checks, and remaining uncertainty in plain language.
- Target Python 3.14.x only for Python tools and tests. The Python toolchain is
  Fixtures' and lives in `Fixtures/.venv` (`make -C Fixtures setup-python`); do not
  run a Python version matrix. For fixture samples, use `Fixtures/sample N` rather
  than assembling a draw by hand; it publishes a world as [WORLD.md](WORLD.md) describes.
- Handle local Git logistics. When requested work reaches a completed, checked
  stopping point, stage and commit its changes on the current appropriate branch;
  `main` is fine when no separate branch is needed. Preserve unrelated work and
  do not leave completed task changes uncommitted. Leave pushing to the user
  unless explicitly asked to push.
- Use the supplied fixtures. Do not search for or acquire a corpus. Image assets,
  worlds and sample records follow the rules in [Fixtures/AGENTS.md](Fixtures/AGENTS.md).
  Experiment output under the root `output/` is disposable; see its [guidance](output/AGENTS.md).

Router work must preserve scratch lineage for each call. Neighborhoods are
provisional and batch-relative; semantic cluster names are an enduring anti-goal.
Automatic membership refinement and churn are outside the router MVP.

Portability is a parallel research track: eventually preserve the same caller API
across macOS and a possible Linux/OpenCV implementation, while making unsupported
capabilities explicit. It does not require a backend framework or a port now.

Work on the task requested in the current conversation. The research documents do
not authorize implementing future directions. Leave the next pathway unselected
until explicitly chosen; let concrete work reveal useful shared structure. Do not
leave speculative pathway examples, candidate lists, rankings, or implied next
steps in repository guidance or planning documents.
