# Working on bricolage

## Just draw images

From a neighboring repository, run:

```sh
../bricolage/Fixtures/sample 100
```

Replace `100` with N. From this repository, use `Fixtures/sample N`; an absolute
path to that executable also works. It uses its own Python environment and local
images. No directory change, imports, inventory preparation or further guide
reading is needed for an ordinary draw.

Read the JSON `output` block first. `published: true` means the world is ready at
`directory`; `world_id` identifies it and `image_count` counts its images.
Give that directory to the consumer, which reads `world.json` and the image files.
Check `receipt_recorded` and `problems` too; exit 1 may still have a usable world.
Follow `output.next_steps` for publication failures. Exit 2 reports an `error`.

Each draw gets its own directory under `Fixtures/output/worlds/`. Use `--world DIR`
to choose a destination deliberately; an existing world there is replaced.
Use `--seed TEXT` for a recorded seed and `--keep` **before** N only when its
records should be committed. Ordinary draws use disposable scratch records.
Do not assemble an unrecorded sample or substitute other images on failure.
If the environment is missing, run the setup command printed by the launcher.
See [WORLD.md](WORLD.md) when implementing a consumer.

To draw N images excluding an earlier world's exact bytes, run:

```sh
../bricolage/Fixtures/sampleWithout /path/to/world N
```

It reads `world.json`; the earlier world's image copies and sampler records are
not needed. IDs absent from eligible fixtures warn and reduce the exclusion list,
including images since removed through `collection remove`. Inspect `warnings`
and `exclusion` as well as the usual `output` and `problems`. No matching IDs,
invalid world JSON, or too few remaining images is an error. The input world
stays untouched. Use `--seed TEXT`, `--world DIR`, and `--keep` before the world
argument as needed; use `Fixtures/sample` for later `show`, `verify` or `publish`.

## Remove an image you are authorized to remove

Use its `sha256:...` ID from `world.json`, or the hash filename without its extension:

```sh
../bricolage/Fixtures/collection remove sha256:HASH --reason "Why this image should be removed"
```

Replace `sha256:HASH` with the full image ID. The command removes every active
byte-identical copy, updates catalogs and generated files, validates the result,
and commits only its changes. The reason is also the default commit message;
`--commit-message TEXT` overrides that message. Read the JSON: `complete: true`
and `commit` confirm completion. No further guide reading or confirmation is
needed for an authorized removal. `--dry-run` previews it without removing or
committing anything.

If it reports `incomplete`, preserve the response and repeat the same command
after resolving the named problem. The operation record lets the retry finish
without duplicate receipts. Existing edits in files it needs to change are
refused before removal; unrelated staged and unstaged work is preserved.
Removal keeps source evidence and existing worlds. Draw again for a clean world;
do not edit a saved sample, its records or its manifest by hand.

Media is untracked. In a checkout that received a removal commit rather than
making it, run `../bricolage/Fixtures/collection reconcile` once: it retires
the local copies named by the receipts and commits nothing. Draws report those
copies as `unlisted-input` problems until then.

## Change this repository

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
