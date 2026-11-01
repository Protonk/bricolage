# Shared fixture layout tools

Use the repository Python 3.14.x `.venv`. These tools never download images,
generate variants, repair evidence, or run similarity comparisons.

```sh
make setup-python
.venv/bin/python -m pip install -r Fixtures/tools/requirements.txt
.venv/bin/python Fixtures/tools/check_layout.py --full
make test-fixture-layout
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
