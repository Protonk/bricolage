#!/usr/bin/env python3
"""Check one or all active fixture leaf layouts, independently of source-specific checks."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from fixture_layout import check_layout, discover

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('leaves', nargs='*', type=Path)
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--metadata-only', action='store_true')
mode.add_argument('--full', action='store_true', help='Run each leaf entry point, including its specialized offline checks')
args = parser.parse_args()
results = []
for leaf in args.leaves or discover():
    try:
        if args.full:
            run = subprocess.run([sys.executable, str(leaf / 'tools/check.py')], text=True, capture_output=True)
            if run.returncode:
                raise ValueError(run.stderr or run.stdout)
            results.append(dict(path=str(leaf), **json.loads(run.stdout)))
        else:
            results.append(dict(path=str(leaf), **check_layout(leaf, assets=not args.metadata_only)))
    except (ValueError, OSError, KeyError) as error:
        results.append(dict(path=str(leaf), layout='failed', error=str(error)))
print(json.dumps(results, indent=2))
raise SystemExit(any(r['layout'] != 'passed' for r in results))
