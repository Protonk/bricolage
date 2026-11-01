# Shared fixture tools

Use the Python 3.14.x `Fixtures/.venv`. Layout and relationship validation are
offline. The optional relationship runner invokes an explicitly supplied
experiment binary; it does not implement a comparator or download images.

```sh
make -C Fixtures setup-python
Fixtures/.venv/bin/python -m pip install -r Fixtures/tools/requirements.txt
Fixtures/.venv/bin/python Fixtures/tools/check_layout.py --full
make -C Fixtures test-fixture-layout
make -C Fixtures test-relationships
```

`check_layout.py` discovers only active leaves under Heaps and Relationships at
arbitrary depth. It checks common layout and input hashes by default. `--full`
runs each leaf's `tools/check.py`, including its existing specialized validator;
an explicit leaf path limits either mode. `--metadata-only` requires no local
media and omits specialized checks. All modes are offline and failures exit
nonzero. Reports are JSON on stdout; redirect them outside fixture inputs.

`new_fixture.py` materializes the [single template](../Template/README.md) into a
new leaf. It refuses existing destinations and duplicate fixture IDs. An empty
scaffold is unpublished; complete real intake evidence, catalogs and the
source-specific check before using it as a fixture.

`fixture_layout.py` supplies the common checks. Its small historical-path helper
resolves only the explicitly named relocated intake/construction records. It
rejects ambiguous duplicate locations. Historical audit identifiers are not
rewritten. The migration's `tool-changes.json` records exact before/after hashes
for intentionally adapted tools, allowing existing source pins to remain intact
while rejecting unrecorded edits.

`relationship_fixtures.py check --fixtures LEAF` validates the three relationship sets:
hashes, source copies, CSV/JSON agreement, parent and scene identities, probes,
and batch coverage. Their leaf entry points and the Variants builder use this
implementation directly. `test-relationships` needs the local relationship media;
`test-fixture-layout` uses temporary mechanics fixtures only.

`relationship_fixtures.py run --fixtures LEAF --binary /path/to/hazy-vision-translation
--world /path/to/published-world --output /path/to/new-run` drives the existing pair CLI and records all outcomes,
including failures. `--selection focus|probes|full` chooses the fixture's explicit
pairs. Both `--world` and `--binary` are required; no sibling checkout or application
build is assumed. `--store` selects the sampler records (default `Sampler/records`).
The runner verifies the world against its saved draw, maps probes to hash IDs and
passes only those IDs and the world to the binary. Absent endpoints are recorded
as skipped, never replaced. Exact-byte aliases can become self-comparisons. The output parent must exist and the output directory must be new.
