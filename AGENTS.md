# Working on bricolage

Read [README.md](README.md), then [Fixtures/AGENTS.md](Fixtures/AGENTS.md) and the
guide for the sampler or collection being changed. [CONTRIBUTING.md](CONTRIBUTING.md)
describes fixture design and how the documentation fits together.

- Work on the task in the conversation. Do not invent a next research direction
  or add speculative roadmaps, rankings or architectures.
- Preserve supplied records, source bytes, IDs and metadata hashes; change a
  published leaf's membership or bytes only through `Fixtures/collection`, which
  writes receipts. Keep changes small enough to follow from input to output. Report missing files and failed
  operations by name. A source relationship or measured alignment does not by
  itself establish a visual match.
- Use Python 3.14.x in `Fixtures/.venv`, created by `make -C Fixtures setup-python`.
  Use `Fixtures/sample N` for samples. Put `--keep` before the command for draws
  meant to be committed. Do not assemble unrecorded samples or acquire another
  corpus for sampling; fixture intake from a recorded handoff follows
  [Fixtures/AGENTS.md](Fixtures/AGENTS.md).
- Keep media under a collection leaf's `images/`, `sources/` or `previews/`.
  Never force-add ignored media. Put disposable worlds and scratch records under
  `Fixtures/output/`. Change versioned sampler records in `Fixtures/Sampler/records/`
  only through `--keep`.
- Give consumers a world as specified in [WORLD.md](WORLD.md). Resolve provenance
  and choose probes here. The optional runner needs an explicit executable and
  world; it must not depend on a consumer's source tree.
- Update the affected guides and run the relevant checks in
  [Fixtures/AGENTS.md](Fixtures/AGENTS.md). Preserve reports of unsupported
  operations, missing results and failed publication receipts.
- At a completed, checked stopping point, stage and commit the task's changes on
  the current branch; main is fine. Preserve unrelated work. Do not push unless asked.
- Keep both copies of WORLD.md identical when changing it. Its counterpart links
  locate the copy in hazy.
