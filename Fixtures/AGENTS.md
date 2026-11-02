# Working on Fixtures

Read [README.md](README.md), then the guide for the work:

- Collection files and intake: [FORMAT.md](FORMAT.md), the
  [template](Template/README.md), and the relevant leaf README.
- Sampling, saved draws and annotations: [Sampler/README.md](Sampler/README.md).
- Shared validators and comparison runner: [tools/README.md](tools/README.md).
- Files given to consumers: [WORLD.md](../WORLD.md).

Use Python 3.14.x in `Fixtures/.venv`. From the repository root, create it with
`make -C Fixtures setup-python`. Sampling and layout checks use the standard
library; install a leaf's `tools/requirements.txt` when its tools need packages.

Use `Fixtures/sample N` for draws. Scratch records go to `output/records/`;
`--keep` selects the versioned `Sampler/records/` store. Use the same store for
later `show`, `verify`, `publish` and `annotate` commands. Generated test patterns
can check tool mechanics; use the supplied images to examine image behavior.

Keep original media in a leaf's `images/`, `sources/` or `previews/`, and
preserve supplied records. Follow [output/AGENTS.md](output/AGENTS.md) for
scratch files. Fix a catalog problem in the collection that owns the catalog,
with its validator, so tools and records continue to describe the same files.

Name a new leaf's fixture ID `bricolage-<code>-v1`, as in `bricolage-pi01-v1`;
leaves lifted from hazy keep their `hazy-` IDs and are not renamed. Identify
Commons requests as `BricolageFixtureBot/0.1 (https://github.com/Protonk/bricolage) Python-urllib`.
Older leaf records and READMEs name `HazyFixtureBot` and the hazy repository
because that is what their acquisitions used. The newest Similarity intake,
[Puddle-Inversions](Heaps/Similarity/Puddle-Inversions/README.md), is the
current starting point for a handoff of Commons leads.

The archive is additive and flat. A leaf is published once; afterwards its
membership and bytes change only through `Fixtures/collection remove INPUT
--reason "Reason"` and `Fixtures/collection repin INPUT --from FILE --reason
"Reason"`, which write receipts. The generated [source index](INDEX.csv) is the
membership table and the recovery contract described in [RECOVERY.md](RECOVERY.md);
there is no category structure and no restore pipeline. Identity audits are
written at publication and never recomputed, and a leaf's specialized validator
describes its publication rather than a changed leaf. A new leaf reads the
index and changes nothing elsewhere.
After other catalog changes, run `make -C Fixtures collection-totals`; current
totals, the source index `INDEX.csv` and marked README blocks are generated,
not maintained by hand.

Run the checks relevant to the change, from the repository root:

```sh
make -C Fixtures test-sampler
make -C Fixtures test-fixture-layout
make -C Fixtures test-relationships
Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full
```

`test-relationships` and full leaf validation need local media; the sampler and
layout tests create temporary test inputs. Report what passed and anything that
could not be checked. Follow the [root rules](../AGENTS.md) for Git and for
changes shared with consumers.
