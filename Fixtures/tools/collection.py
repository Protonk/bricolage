#!/usr/bin/env python3
"""Maintain active fixture membership, generated collection totals and the source index."""
import argparse
import fcntl
import json
from pathlib import Path
import sys

from fixture_layout import FIXTURES, discover, require
from fixture_history import history, remove, repin
import collection_totals
import source_index


def resolve(selector, leaf=None, fixtures=FIXTURES):
    leaves = [p.resolve() for p in discover(fixtures)]
    if leaf is not None:
        leaf = Path(leaf).resolve()
        require(leaf in leaves, f'Not an active collection: {leaf}')
        leaves = [leaf]
    matches, removed = [], []
    digest = selector.removeprefix('sha256:')
    for root in leaves:
        def matches_row(row):
            return (digest == row['byte_sha256'] or selector == row['file']
                    or Path(selector).resolve() == root / row['file'])
        manifest = json.loads((root / 'manifest.json').read_text())
        matches.extend((root, row) for row in manifest['images'] if matches_row(row))
        removed.extend((root, record['receipt']['image']) for record in history(root)
                       if record['kind'] == 'removal' and matches_row(record['receipt']['image']))
    candidates = matches or removed
    require(candidates, f'No input matches: {selector}')
    require(len(candidates) == 1, 'Ambiguous input; use --leaf and an images/ path: ' + ', '.join(str(root / row['file']) for root, row in candidates))
    return *candidates[0], not matches


def main(fixtures=FIXTURES):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    removal = commands.add_parser('remove', help='Remove one active input by SHA-256 or path; retain publication evidence')
    removal.add_argument('input')
    removal.add_argument('--leaf', type=Path, help='Limit the match to this collection directory')
    removal.add_argument('--reason', required=True)
    removal.add_argument('--dry-run', action='store_true')
    pin = commands.add_parser('repin', help='Replace one active input with equivalent bytes and record why; no network')
    pin.add_argument('input')
    pin.add_argument('--from', dest='replacement', required=True, type=Path, help='Replacement file outside the leaf')
    pin.add_argument('--leaf', type=Path, help='Limit the match to this collection directory')
    pin.add_argument('--reason', required=True)
    pin.add_argument('--dry-run', action='store_true')
    totals = commands.add_parser('totals', help='Regenerate manifest totals and marked README sections')
    totals.add_argument('--check', action='store_true', help='Fail if generated totals are stale; write nothing')
    index = commands.add_parser('index', help='Regenerate the flat source index of every active input')
    index.add_argument('--check', action='store_true', help='Fail if the index is stale; write nothing')
    args = parser.parse_args()
    try:
        require(sys.version_info[:2] == (3, 14), 'Use the Python 3.14.x Fixtures/.venv')
        output = fixtures / 'output'
        output.mkdir(exist_ok=True)
        with (output / 'collection.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if args.command == 'totals':
                result = collection_totals.update(fixtures, check=args.check)
            elif args.command == 'index':
                result = source_index.update(fixtures, check=args.check)
            else:
                root, row, already = resolve(args.input, args.leaf, fixtures)
                # Check every generation target before mutating the collection.
                collection_totals.generated_files(fixtures)
                if args.command == 'repin':
                    require(not already, f'Not an active input: {row["file"]}')
                    result = repin(root, row, args.replacement, args.reason, dry_run=args.dry_run)
                else:
                    result = (dict(status='already_removed', fixture=str(root), file=row['file']) if already
                              else remove(root, row, args.reason, dry_run=args.dry_run))
                if not args.dry_run and result['status'] in ('removed', 'repinned'):
                    try:
                        result['totals'] = collection_totals.update(fixtures)
                    except (ValueError, OSError) as error:
                        raise ValueError(f'The change is recorded; totals generation failed: {error}. Run Fixtures/collection totals.') from error
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'collection: {error}\n')


if __name__ == '__main__':
    main()
