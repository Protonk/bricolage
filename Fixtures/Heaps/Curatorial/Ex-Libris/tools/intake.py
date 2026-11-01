#!/usr/bin/env python3
"""Leaf-local entry point for the three-category Commons intake."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from three_category import main
if __name__ == "__main__":
    main(Path(__file__).resolve().parents[1])
