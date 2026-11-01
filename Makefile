.PHONY: setup-python test-sampler test-fixture-layout

# One supported Python minor version; patch releases may advance.
PYTHON314 ?= python3.14

setup-python:
	$(PYTHON314) -c 'import sys; assert sys.version_info[:2] == (3, 14), "Python 3.14.x is required"'
	$(PYTHON314) -m venv .venv

test-sampler:
	.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 14), "Run make setup-python with Python 3.14.x"'
	.venv/bin/python -m unittest discover -s Fixtures/Sampler -p 'test_*.py'

test-fixture-layout:
	.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 14), "Run make setup-python with Python 3.14.x"'
	.venv/bin/python -m unittest discover -s Fixtures/tools -p 'test_*.py'
