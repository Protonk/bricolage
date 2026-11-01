#!/usr/bin/env python3
"""Standard offline entry point for this fixture."""
from pathlib import Path
import sys
FIXTURES = next(p for p in Path(__file__).resolve().parents if (p/'tools/fixture_layout.py').is_file())
sys.path.insert(0, str(FIXTURES/'tools'))
from fixture_layout import check_leaf

if __name__ == '__main__':
    check_leaf(__file__, checks=[['Fixtures/Heaps/Curatorial/US-Army-SSI/tools/integrate.py', 'check']])
