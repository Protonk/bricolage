#!/usr/bin/env python3
"""Check the standard layout, relationships and decoded arrow pixels."""
from pathlib import Path
import sys

LEAF = Path(__file__).resolve().parents[1]
FIXTURES = next(p for p in LEAF.parents if (p / "tools/fixture_layout.py").is_file())
sys.path.insert(0, str(FIXTURES / "tools"))
from fixture_layout import check_leaf

if __name__ == "__main__":
    check_leaf(__file__, checks=[[str(LEAF / "tools/check_pixels.py")]])
