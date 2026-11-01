#!/usr/bin/env python3
"""Check one or all active fixture leaf layouts, independently of source-specific checks."""
import argparse
import json
from pathlib import Path
from fixture_layout import check_layout, discover

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('leaves', nargs='*', type=Path)
parser.add_argument('--metadata-only', action='store_true')
args = parser.parse_args()
results = []
for leaf in args.leaves or discover():
    try:
        results.append(dict(path=str(leaf), **check_layout(leaf, assets=not args.metadata_only)))
    except (ValueError, OSError, KeyError) as error:
        results.append(dict(path=str(leaf), layout='failed', error=str(error)))
print(json.dumps(results, indent=2))
raise SystemExit(any(r['layout'] != 'passed' for r in results))
