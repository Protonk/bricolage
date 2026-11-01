.PHONY: setup-python test-sampler test-fixture-layout test-relationships collection-totals check-collection-totals

# Fixtures' Python toolchain. Run from the repository root as `make -C Fixtures <target>`,
# or from this directory as `make <target>`. One supported Python minor version;
# patch releases may advance. The venv lives here, beside the tools that use it.
PYTHON314 ?= python3.14
VENV := .venv/bin/python
CHECK := -c 'import sys; assert sys.version_info[:2] == (3, 14), "Run make -C Fixtures setup-python with Python 3.14.x"'

setup-python:
	$(PYTHON314) -c 'import sys; assert sys.version_info[:2] == (3, 14), "Python 3.14.x is required"'
	$(PYTHON314) -m venv .venv

test-sampler:
	$(VENV) $(CHECK)
	$(VENV) -m unittest discover -s Sampler -p 'test_*.py'

test-fixture-layout: check-collection-totals
	$(VENV) $(CHECK)
	$(VENV) -m unittest discover -s tools -p 'test_layout.py'
	$(VENV) -m unittest discover -s tools -p 'test_collection.py'

collection-totals:
	./collection totals

check-collection-totals:
	./collection totals --check

test-relationships:
	$(VENV) $(CHECK)
	$(VENV) -m unittest discover -s tools -p 'test_relationships.py'
