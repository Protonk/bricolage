#!/usr/bin/env python3
"""Offline exact-identity audit against the other integrated fixture leaves."""

# Resolve relocated evidence while preserving historical audit identifiers.
from pathlib import Path as _LayoutPath
import sys as _layout_sys
_layout_root = next(p for p in _LayoutPath(__file__).resolve().parents if (p/'tools/fixture_layout.py').is_file())
_layout_sys.path.insert(0, str(_layout_root/'tools'))
from fixture_layout import evidence_path

import csv
import hashlib
import json
from urllib.parse import parse_qs, unquote, urlsplit

import three_category as e
from transport import dump, sha


def normalized(value):
    return unquote(value).removeprefix('File:').replace('_', ' ').casefold().strip()


def audit():
    root = e.ROOT
    fixtures = root.parents[2]
    previous = {k: {} for k in ('title', 'pageid', 'original_sha1', 'byte_sha256')}
    inventories = []

    def add(kind, value, location):
        if value is not None and str(value).strip():
            key = normalized(value) if kind == 'title' else str(value)
            previous[kind].setdefault(key, set()).add(location)

    # A manifest beside sources.csv defines an integrated leaf, at any depth.
    for path in sorted(fixtures.rglob('manifest.json')):
        leaf = path.parent
        if leaf == root or any(p in ('provenance', 'previews', 'sources', 'images') for p in leaf.relative_to(fixtures).parts):
            continue
        if not (leaf / 'sources.csv').is_file():
            continue
        name = str(leaf.relative_to(fixtures))
        manifest = e.read(path)
        with (leaf / 'sources.csv').open(newline='') as stream:
            sources = list(csv.DictReader(stream))
        record = dict(fixture=name, inputs=len(manifest['images']), sources=len(sources),
                      manifest_sha256=sha(path), source_catalog_sha256=sha(leaf / 'sources.csv'))
        for row in manifest['images']:
            add('byte_sha256', row['byte_sha256'], name + '/' + row['file'])
        for row in sources:
            where = name + '/sources/' + row['source_filename']
            add('byte_sha256', row['source_sha256'], where)
            for field in ('subject', 'original_path'):
                if row[field].startswith('File:'):
                    add('title', row[field], where)
            url = row['source_url']
            if urlsplit(url).hostname == 'commons.wikimedia.org':
                if '/wiki/File:' in url:
                    add('title', url.split('/wiki/', 1)[1], where)
                for value in parse_qs(urlsplit(url).query).get('curid', []):
                    add('pageid', value, where)
        mapping = leaf / 'provenance/import-map.json'
        if mapping.exists():
            record['import_map_sha256'] = sha(mapping)
            for row in e.read(mapping):
                where = name + '/' + row['final_file']
                for key in ('canonical_title', 'commons_api_title', 'commons_title', 'frozen_title'):
                    add('title', row.get(key), where)
                add('pageid', row.get('pageid') or row.get('commons_pageid'), where)
                add('original_sha1', row.get('original_sha1'), where)
        candidate_catalog = evidence_path(leaf, 'candidates.jsonl')
        if candidate_catalog.exists():
            candidate_rows = [json.loads(line) for line in candidate_catalog.read_text().splitlines()]
            record['candidate_catalog_sha256'] = sha(candidate_catalog)
            record['candidate_catalog_entries'] = len(candidate_rows)
            for row in candidate_rows:
                where = name + '/candidates.jsonl#' + row['candidate_id']
                for field in ('commons_title', 'commons_api_title', 'canonical_title'):
                    add('title', row.get(field), where)
                add('pageid', row.get('commons_pageid') or row.get('pageid'), where)
                add('original_sha1', row.get('original_sha1'), where)
                add('byte_sha256', row.get('acquired_sha256'), where)
        frozen_inventory = evidence_path(leaf, 'inventory.json')
        if frozen_inventory.exists():
            frozen_rows = e.read(frozen_inventory)['candidates']
            record['candidate_inventory_sha256'] = sha(frozen_inventory)
            record['candidate_inventory_entries'] = len(frozen_rows)
            for row in frozen_rows:
                where = name + '/inventory.json#' + row['candidate_id']
                for field in ('frozen_title', 'commons_title', 'canonical_title'):
                    add('title', row.get(field), where)
                for field in ('category_pageid', 'petscan_pageid', 'pageid'):
                    add('pageid', row.get(field), where)
                add('original_sha1', row.get('original_sha1'), where)
        if leaf.name == 'Variants':
            source_manifest = evidence_path(leaf, 'source-manifest.json')
            record['source_manifest_sha256'] = sha(source_manifest)
            for row in e.read(source_manifest)['sources']:
                add('title', row['upstream_title'], name + '/' + row['file'])
                add('original_sha1', hashlib.sha1((leaf / row['file']).read_bytes()).hexdigest(), name + '/' + row['file'])
        inventories.append(record)

    included = set(e.selection()['selected'])
    collisions = []
    checked = []
    evidence = e.evidence()
    for cid, candidate in e.candidates().items():
        values = dict(title={candidate['frozen_title']}, pageid={str(candidate['category_pageid'])}, original_sha1=set(), byte_sha256=set())
        if cid in evidence:
            page = evidence[cid]['page']
            values['title'].add(page['title'])
            values['pageid'].add(str(page['pageid']))
            if page.get('imageinfo'):
                values['original_sha1'].add(page['imageinfo'][0]['sha1'])
        receipt = root / f'provenance/source-receipts/{cid}.json'
        if receipt.exists():
            values['byte_sha256'].add(e.read(receipt)['sha256'])
        checked.append(dict(candidate_id=cid, identities={k: sorted(v) for k, v in values.items()}))
        for kind, entries in values.items():
            for entry in entries:
                key = normalized(entry) if kind == 'title' else entry
                if key in previous[kind]:
                    collisions.append(dict(candidate_id=cid, included=cid in included, identity=kind,
                                           value=entry, previous=sorted(previous[kind][key])))
    included_overlaps = [r for r in collisions if r['included']]
    return dict(status='reported', inventories=inventories,
                previous_inputs=sum(r['inputs'] for r in inventories),
                previous_frozen_candidates=sum(r.get('candidate_inventory_entries', 0) + r.get('candidate_catalog_entries', 0) for r in inventories),
                available_previous_identities={k: len(v) for k, v in previous.items()},
                checked=checked, collisions_with_previous=collisions, included_overlaps=included_overlaps,
                policy='Retain otherwise eligible selections despite prior fixture reuse; exact overlaps are recorded, not automatic exclusions. Within-leaf repeats are handled by the separate ordered selection. Inventory-only matches are identified by inventory.json or candidates.jsonl locations and do not claim acquired reuse.',
                limitations='Exact identities only; title matching is conservative and case-folded. Original SHA-1/page IDs are compared where locally available. No exact match does not establish distinct works, independent origins, or complete prior upstream coverage.')


if __name__ == '__main__':
    result = audit()
    dump(e.ROOT / 'provenance/identity-audit.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'checked'}, indent=2))
    # Overlaps are evidence, not acquisition exclusions.
