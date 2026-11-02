#!/usr/bin/env python3
"""Check one or all active fixture leaf layouts, independently of source-specific checks."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from fixture_layout import check_layout, discover


def main(argv=None, fixtures=None, stdout=sys.stdout):
    """Check the given leaves, or every discovered one. Returns the exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('leaves', nargs='*', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--metadata-only', action='store_true')
    mode.add_argument('--full', action='store_true', help='Run each leaf entry point, including its specialized offline checks')
    args = parser.parse_args(argv)
    leaves = args.leaves or discover(fixtures)
    results = []
    for leaf in leaves:
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
    failed = [r['path'] for r in results if r['layout'] != 'passed']
    print(json.dumps(dict(leaves=len(leaves), passed=len(results) - len(failed), failed=failed, results=results),
                     indent=2), file=stdout)
    return 1 if failed or len(results) != len(leaves) else 0


if __name__ == '__main__':
    raise SystemExit(main())
