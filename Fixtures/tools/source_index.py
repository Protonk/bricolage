"""Generate the flat source index: one row per active input across every leaf.

The index is derived from active manifests, source catalogs and import maps.
It records where an input lives, what bytes it is, and the upstream identity a
fresh agent would need to fetch it again. It is a membership table and a
recovery contract, not a category structure: a sub-heap is only a longer leaf
path. Rows are data; nothing here fetches, repairs or judges.
"""
import csv
import io
import json
from pathlib import Path
from urllib.parse import urlsplit

from fixture_layout import FIXTURES, discover, check_layout, require

COLUMNS = ('leaf fixture_id kind file byte_sha256 width height format transformation family_id '
           'source_filename origin source_url title page_id original_sha1 acquired_url requested_edge '
           'rendition_kind license license_url credit recovery recovery_note shared_with').split()

ORIGINS = {'commons.wikimedia.org': 'commons', 'upload.wikimedia.org': 'commons',
           'scikit-image.org': 'scikit-image', 'vision.middlebury.edu': 'middlebury'}
COPIES = {'source', 'byte_copy', 'singleton'}


def first(record, *keys):
    for key in keys:
        value = record.get(key)
        if value not in (None, ''):
            return str(value)
    return ''


def read_csv(path):
    with Path(path).open(newline='', encoding='utf-8') as stream:
        return list(csv.DictReader(stream))


def import_records(leaf):
    """Import-map rows by input path, read through one adapter for the known spellings."""
    path = leaf / 'provenance/import-map.json'
    if not path.exists():
        return {}
    records = json.loads(path.read_text())
    if not isinstance(records, list):
        return {}
    mapped = {}
    for record in records:
        if isinstance(record, dict) and record.get('final_file'):
            mapped[record['final_file']] = dict(
                title=first(record, 'canonical_title', 'commons_api_title', 'commons_title', 'frozen_title'),
                page_id=first(record, 'pageid', 'commons_pageid'),
                original_sha1=first(record, 'original_sha1'),
                acquired_url=first(record, 'acquired_url', 'url'),
                requested_edge=first(record, 'requested_edge', 'requested_max_edge', 'source_requested_max_edge'),
                rendition_kind=first(record, 'rendition', 'acquired_rendition_kind'),
                license=first(record, 'license'), license_url=first(record, 'license_url'))
    return mapped


def construction_sources(leaf):
    """Supplied source identities from a construction source manifest, by sources/ path."""
    path = leaf / 'provenance/construction/source-manifest.json'
    if not path.exists():
        return {}
    mapped = {}
    for record in json.loads(path.read_text()).get('sources', []):
        mapped[record['file']] = dict(
            title=first(record, 'upstream_title'), acquired_url=first(record, 'download_url'),
            rendition_kind=first(record, 'download_kind'), license=first(record, 'license'),
            license_url=first(record, 'license_url'), page_id='', original_sha1='', requested_edge='')
    return mapped


def origin_of(url):
    host = urlsplit(url).hostname or ''
    if not url:
        return 'unknown'
    return ORIGINS.get(host, 'url')


def leaf_rows(leaf, fixtures=FIXTURES):
    leaf = Path(leaf)
    check_layout(leaf, assets=False)
    manifest = json.loads((leaf / 'manifest.json').read_text())
    sources = {row['family_id']: row for row in read_csv(leaf / 'sources.csv')}
    imports = import_records(leaf)
    construction = construction_sources(leaf)
    relative = leaf.relative_to(fixtures).as_posix()
    rows = []
    for image in manifest['images']:
        family = image['family_id'] or image['parents'].split('|')[0]
        source = sources.get(family, {})
        source_url = source.get('source_url', '')
        origin = origin_of(source_url)
        identity = imports.get(image['file']) or construction.get('sources/' + source.get('source_filename', '')) or {}
        derived = image['transformation'] not in COPIES
        if derived:
            recovery, note = 'regenerate', 'Derived input; rebuild from its family source with the leaf tools.'
        elif identity.get('page_id') and identity.get('original_sha1') and identity.get('acquired_url'):
            recovery, note = 'commons-api', ''
        elif identity.get('acquired_url'):
            recovery, note = 'source-url', 'Fetch URL recorded without a page ID or upstream hash.'
        elif source_url.startswith('http'):
            recovery, note = 'source-url', 'Only the source page or dataset URL is recorded; see sources.csv and SOURCES.md.'
        else:
            recovery, note = 'none', 'No upstream location recorded; the preserved bytes are the only copy.'
        rows.append(dict(
            leaf=relative, fixture_id=manifest['fixture_id'], kind=manifest['kind'], file=image['file'],
            byte_sha256=image['byte_sha256'], width=image['width'], height=image['height'], format=image['format'],
            transformation=image['transformation'], family_id=family, source_filename=source.get('source_filename', ''),
            origin=origin, source_url=source_url, title=identity.get('title', ''), page_id=identity.get('page_id', ''),
            original_sha1=identity.get('original_sha1', ''), acquired_url=identity.get('acquired_url', ''),
            requested_edge=identity.get('requested_edge', ''), rendition_kind=identity.get('rendition_kind', ''),
            license=identity.get('license', ''), license_url=identity.get('license_url', ''),
            credit=source.get('credit_status', ''), recovery=recovery, recovery_note=note, shared_with=''))
    return rows


def render(fixtures=FIXTURES, leaves=None):
    fixtures = Path(fixtures)
    leaves = discover(fixtures) if leaves is None else sorted(leaves)
    rows = [row for leaf in leaves for row in leaf_rows(leaf, fixtures)]
    by_hash, by_upstream = {}, {}
    for row in rows:
        by_hash.setdefault(row['byte_sha256'], []).append(row)
        if row['original_sha1'] and row['transformation'] in COPIES:
            by_upstream.setdefault(row['original_sha1'], []).append(row)
    for row in rows:
        others = {f"{r['leaf']}:{r['file']}" for r in by_hash[row['byte_sha256']] if r['leaf'] != row['leaf']}
        if row['original_sha1']:
            others |= {f"{r['leaf']}:{r['file']}" for r in by_upstream.get(row['original_sha1'], []) if r['leaf'] != row['leaf']}
        row['shared_with'] = ';'.join(sorted(others))
    rows.sort(key=lambda r: (r['leaf'], r['file']))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def summary(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    return dict(inputs=len(rows), leaves=len({r['leaf'] for r in rows}),
                recovery={k: sum(r['recovery'] == k for r in rows) for k in ('commons-api', 'source-url', 'regenerate', 'none')},
                shared=sum(bool(r['shared_with']) for r in rows))


def update(fixtures=FIXTURES, *, check=False):
    fixtures = Path(fixtures)
    path = fixtures / 'INDEX.csv'
    text = render(fixtures)
    stale = not path.exists() or path.read_text() != text
    if check:
        require(not stale, 'Stale source index; run Fixtures/collection index: ' + str(path))
    elif stale:
        from fixture_removal import atomic_write
        atomic_write(path, text.encode())
    return dict(status='current' if check else 'generated', changed=[str(path)] if stale and not check else [], **summary(text))
