#!/usr/bin/env python3
"""Create an unpublished leaf from the single fixture template; never acquires images."""
import argparse
import json
from pathlib import Path
import re
from fixture_layout import FIXTURES, require


def create(destination, fixture_id, kind, fixtures=FIXTURES):
    destination = Path(destination).resolve()
    fixtures = Path(fixtures).resolve()
    require(kind in {'derivatives', 'multiview', 'prompt_heap', 'curatorial_heap'}, 'Unknown fixture kind')
    require(re.fullmatch(r'[a-zA-Z0-9_-]+', fixture_id), 'Use a simple stable fixture ID')
    area = fixtures / ('Heaps' if kind.endswith('_heap') else 'Relationships')
    require(destination.is_relative_to(area) and destination != area, 'Destination must be a leaf below ' + str(area))
    require(not destination.exists(), 'Destination already exists')
    for manifest in fixtures.glob('**/manifest.json'):
        if set(manifest.relative_to(fixtures).parts) & {'provenance', 'images', 'sources', 'previews'}:
            continue
        require(json.loads(manifest.read_text()).get('fixture_id') != fixture_id, 'Fixture ID already exists')
    template = FIXTURES / 'Template/leaf'
    destination.mkdir(parents=True)
    for source in sorted(template.rglob('*.in')):
        relative = source.relative_to(template).with_suffix('')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text().replace('{{FIXTURE_ID}}', fixture_id).replace('{{KIND}}', kind)
        target.write_text(text)
    for directory in ('images', 'sources', 'previews', 'batches'):
        (destination / directory).mkdir(exist_ok=True)
    return dict(path=str(destination), fixture_id=fixture_id, kind=kind, status='unpublished; evidence and inputs required')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--id', required=True)
    parser.add_argument('--kind', required=True, choices=['derivatives', 'multiview', 'prompt_heap', 'curatorial_heap'])
    args = parser.parse_args()
    try:
        print(json.dumps(create(args.destination, args.id, args.kind), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error) + '\n')
