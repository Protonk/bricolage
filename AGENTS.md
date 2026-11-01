# Working on bricolage

Read [README.md](README.md), then [Fixtures/AGENTS.md](Fixtures/AGENTS.md) and the
relevant fixture or sampler guide. bricolage's application lives in `Fixtures/`.
[WORLD.md](WORLD.md) is the whole contract offered to consumers.

- Work on the task selected in the conversation. No next research pathway is
  selected. Do not add speculative roadmaps, rankings or architectural frameworks.
- Keep changes small enough to trace from input to output. Preserve supplied
  records, source bytes, IDs and metadata pins. Report errors and missing results
  explicitly; provenance and measured alignments are not matching judgments.
- Use Python 3.14.x only, with `Fixtures/.venv` and `make -C Fixtures setup-python`.
  For samples use `Fixtures/sample N`, which records the draw in the disposable scratch
  store and publishes a world. A draw meant to be committed is made with `--keep`
  before the command. Do not construct an undocumented sample or acquire another corpus.
- Keep all media under a leaf's `images/`, `sources/` or `previews/`, and disposable
  worlds and scratch records under `Fixtures/output/`. Never force-add ignored image
  assets. Durable sampler records stay in `Fixtures/Sampler/records/`, are versioned,
  and change only through `--keep`.
- Consumers receive a world, never fixture origins. Any provenance lookup, probe
  selection or interpretation belongs here. The optional runner requires an explicit
  executable and world; no consumer source tree is a dependency.
- Keep documentation and focused tests consistent with implemented behavior.
  Unsupported operations and failed publication receipts must remain visible.
- Handle local Git logistics: at a completed, checked stopping point, stage and
  commit the task changes on the appropriate current branch; main is fine. Preserve
  unrelated work. Do not push unless explicitly asked.
- WORLD.md is shared with hazy. Keep both copies identical when changing the
  boundary; the counterpart links in the document locate them.
