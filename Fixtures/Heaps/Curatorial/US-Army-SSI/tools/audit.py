#!/usr/bin/env python3
"""Offline exact-identity audit against the other integrated fixture leaves."""
import csv
import hashlib
import json
from urllib.parse import parse_qs, unquote, urlsplit

import ssi
from transport import dump, sha


def normalized(value):
    return unquote(value).removeprefix('File:').replace('_', ' ').casefold().strip()


def audit(fixture_names=None):
    root = ssi.ROOT
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
        if fixture_names is not None and name not in fixture_names:
            continue
        manifest = ssi.read(path)
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
            for row in ssi.read(mapping):
                where = name + '/' + row['final_file']
                for key in ('canonical_title', 'commons_api_title', 'commons_title', 'frozen_title'):
                    add('title', row.get(key), where)
                add('pageid', row.get('pageid') or row.get('commons_pageid'), where)
                add('original_sha1', row.get('original_sha1'), where)
        if leaf.name == 'Variants':
            source_manifest = leaf / 'source-manifest.json'
            record['source_manifest_sha256'] = sha(source_manifest)
            for row in ssi.read(source_manifest)['sources']:
                add('title', row['upstream_title'], name + '/' + row['file'])
                add('original_sha1', hashlib.sha1((leaf / row['file']).read_bytes()).hexdigest(), name + '/' + row['file'])
        inventories.append(record)

    if fixture_names is not None:
        ssi.require({r['fixture'] for r in inventories} == set(fixture_names), 'Recorded audit fixture is missing')

    selected = set(ssi.selection()['selected'])
    collisions = []
    checked = []
    evidence = ssi.evidence()
    for cid, candidate in ssi.candidates().items():
        values = dict(title={candidate['frozen_title']}, pageid={str(candidate['petscan_pageid'])}, original_sha1=set(), byte_sha256=set())
        if cid in evidence:
            page = evidence[cid]['page']
            values['title'].add(page['title'])
            values['pageid'].add(str(page['pageid']))
            if page.get('imageinfo'):
                values['original_sha1'].add(page['imageinfo'][0]['sha1'])
        receipt = root / f'provenance/source-receipts/{cid}.json'
        if receipt.exists():
            values['byte_sha256'].add(ssi.read(receipt)['sha256'])
        checked.append(dict(candidate_id=cid, identities={k: sorted(v) for k, v in values.items()}))
        for kind, entries in values.items():
            for entry in entries:
                key = normalized(entry) if kind == 'title' else entry
                if key in previous[kind]:
                    collisions.append(dict(candidate_id=cid, selected=cid in selected, identity=kind,
                                           value=entry, previous=sorted(previous[kind][key])))
    blockers = [r for r in collisions if r['selected']]
    return dict(status='failed' if blockers else 'passed', inventories=inventories,
                previous_inputs=sum(r['inputs'] for r in inventories),
                available_previous_identities={k: len(v) for k, v in previous.items()},
                checked=checked, collisions_with_previous=collisions, blocking_collisions=blockers,
                limitations='Exact identities only; title matching is conservative and case-folded. Original SHA-1/page IDs are compared where locally available. No exact match does not establish distinct designs, independent origins, or complete prior upstream coverage.')


if __name__ == '__main__':
    result = audit()
    dump(ssi.ROOT / 'provenance/identity-audit.json', result)
    print(json.dumps({k: v for k, v in result.items() if k != 'checked'}, indent=2))
    if result['blocking_collisions']:
        raise SystemExit(1)
