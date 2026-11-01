#!/usr/bin/env python3
"""Build and check each POTY leaf from preserved evidence; entirely offline."""
import argparse
from collections import Counter
import csv
import fcntl
import json
import math
from pathlib import Path
import shutil

from PIL import Image, ImageDraw, ImageOps
from poty import (ROOT, CATEGORIES, YEARS, SEED, IMAGE_FIELDS, SOURCE_FIELDS, choose,
                  csv_write, dimensions, inventory, metadata_records, norm, ordering,
                  read, require, review_rows, slug, wiki)
from transport import dump, safe, sha
from review import derive


def read_csv(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def imports(root):
    inv = {r['candidate_id']: r for r in read(root / 'provenance/intake/inventory.json')['candidates']}
    ev = {r['candidate_id']: r for r in review_rows(root)}
    review = read(root / 'provenance/provenance-review.json')
    result = []
    for cid in choose(root)['selected']:
        path = root / f'provenance/downloads/{cid}.json'
        if path.exists():
            receipt = read(path)
            result.append(dict(**receipt, final_file='images/' + Path(receipt['source_path']).name,
                               family_id='poty-' + cid, year=inv[cid]['year'],
                               official_category=inv[cid]['official_category'],
                               gallery_url=inv[cid]['gallery_url'], data_revision=inv[cid]['data_revision'],
                               canonical_title=ev[cid]['canonical_title'], source_url=wiki(ev[cid]['canonical_title']),
                               file_timestamp=ev[cid]['file_timestamp'], file_page_revision=ev[cid]['file_page_revision'],
                               creator=ev[cid]['creator'], license=ev[cid]['license'], license_url=ev[cid]['license_url'],
                               published_uploader=ev[cid]['published_uploader'], latest_revision_uploader=ev[cid]['latest_revision_uploader'],
                               credit=ev[cid]['credit'], usage_terms=ev[cid]['usage_terms'], restrictions=ev[cid]['restrictions'],
                               original_creator_keys=review[cid]['creator_keys'],
                               original_creator_unknown=review[cid]['creator_unknown'],
                               original_creator_basis=review[cid]['creator_basis'],
                               source_independence_confirmed=None))
    return result


def records(imported):
    images, sources = [], []
    for item in imported:
        images.append(dict(file=item['final_file'], batch='batch-1', family_id=item['family_id'],
                           scene_id='', parents=item['family_id'], transformation='source',
                           relation_kind='curatorial_selected', origin_count=1,
                           **{key: item[key] for key in ('width', 'height', 'exif_orientation', 'format')},
                           byte_sha256=item['sha256'], pixels_rgb_sha256=''))
        sources.append(dict(family_id=item['family_id'], source_filename=Path(item['source_path']).name,
                            scene_id='', subject=item['canonical_title'],
                            credit_status=f"{item['creator'] or 'unknown creator'}; {item['license']}",
                            source_sha256=item['sha256'], width=item['width'], height=item['height'],
                            exif_orientation=item['exif_orientation'], source_url=item['source_url'],
                            preprocessing=f"API rendition requested at 1600px; returned {item['width']}x{item['height']}; local byte copy only.",
                            view='', exposure_id='', original_path=item['canonical_title']))
    return images, sources


def summary(root):
    selection = choose(root)
    inv = read(root / 'provenance/intake/inventory.json')
    acquired = imports(root)
    ev = {r['candidate_id']: r for r in review_rows(root)}
    selected = selection['selected']
    pending_review = selection['counts'].get('pending', 0)
    pending_media = len(selected) - len(acquired)
    # A documented creator-limited shortfall is a completed selection, not a pending image.
    status = 'partial' if pending_review or pending_media else 'complete'
    if (root / 'provenance/last_transport_error.json').exists():
        status = 'stopped'
    log = root / 'provenance/http_log.jsonl'
    events = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
    transfers = [e for e in events if e.get('kind') in ('api', 'source')]
    return dict(status=status, official_category=inv['official_category'], eligible=len(inv['candidates']),
                by_year={str(y): sum(r['year'] == y for r in inv['candidates']) for y in YEARS},
                selected=len(selected), acquired=len(acquired), excluded=selection['counts'].get('excluded', 0),
                pending_review=pending_review, pending_acquisition=pending_media,
                reserve=selection['counts'].get('reserve', 0), target=50,
                completed_http_responses=sum(e['response_complete'] for e in transfers),
                failed_http_transfers=sum(not e['response_complete'] for e in transfers),
                post_transfer_validation_stops=sum(e.get('kind') not in ('api', 'source') and bool(e.get('error')) for e in events),
                automatic_retries=0,
                shortfall=50 - len(selected) if not pending_review and len(selected) < 50 else 0,
                selected_unknown_creators=sum(read(root / 'provenance/provenance-review.json')[cid]['creator_unknown'] for cid in selected),
                published_uploader_counts=dict(Counter(ev[cid]['published_uploader'] or 'unknown' for cid in selected)),
                latest_revision_uploader_counts=dict(Counter(ev[cid]['latest_revision_uploader'] or 'unknown' for cid in selected)),
                pending_candidate_ids=[cid for cid in selected if cid not in {r['candidate_id'] for r in acquired}])


def sheets(root, imported):
    receipts = []
    for offset in range(0, len(imported), 20):
        group = imported[offset:offset + 20]
        canvas = Image.new('RGB', (1280, math.ceil(len(group) / 4) * 280), '#eeeeee')
        draw = ImageDraw.Draw(canvas)
        for i, record in enumerate(group):
            with Image.open(safe(root, record['final_file'])) as im:
                tile = ImageOps.exif_transpose(im).convert('RGB')
                tile.thumbnail((304, 240), Image.Resampling.LANCZOS)
                x, y = i % 4 * 320, i // 4 * 280
                canvas.paste(tile, (x + (320 - tile.width) // 2, y + (240 - tile.height) // 2))
                draw.text((x + 8, y + 250), record['candidate_id'] + ' / ' + str(record['year']), fill='black')
        path = root / f'previews/selected-{offset // 20 + 1:02d}.jpg'
        path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(path, quality=92)
        receipts.append(dict(path=str(path.relative_to(root)), sha256=sha(path), width=canvas.width,
                             height=canvas.height, candidate_ids=[r['candidate_id'] for r in group]))
    dump(root / 'provenance/contact-sheets.json', receipts)


def build(root):
    require_unremoved(root)
    require(read(root / 'provenance/intake/selection.json') == choose(root), 'Selection changed; explicitly select first')
    imported = imports(root)
    rows, sources = records(imported)
    for item in imported:
        source = safe(root, item['source_path'])
        require(sha(source) == item['sha256'], 'Source changed')
        dest = safe(root, item['final_file'])
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            require(sha(dest) == sha(source), 'Existing input changed; refusing overwrite')
        else:
            shutil.copyfile(source, dest)
    for directory in ('images', 'sources', 'batches'):
        (root / directory).mkdir(exist_ok=True)
    category = read(root / 'provenance/intake/inventory.json')['official_category']
    dump(root / 'manifest.json', dict(schema_version=1, fixture_id='hazy-poty-' + slug(category).lower() + '-v1',
                                     kind='curatorial_heap', description=f'POTY Round 1 {category}, 2023–2025; seeded selection, no expected matches.', images=rows))
    csv_write(root / 'manifest.csv', rows, IMAGE_FIELDS)
    csv_write(root / 'sources.csv', sources, SOURCE_FIELDS)
    dump(root / 'provenance/import-map.json', imported)
    dump(root / 'provenance/acquisition.json', summary(root))
    dump(root / 'selections.json', dict(description='No expected pairs, similarity labels or matching ground truth.', pairs=[], known_shift_families=[]))
    csv_write(root / 'probes.csv', [], 'file_a file_b relation interpretation'.split())
    for name, subset in [('batch-1', rows), ('smoke', rows[:5]), ('medium', rows[:20])]:
        (root / f'batches/{name}.txt').write_text(''.join(r['file'] + '\n' for r in subset))
    files = sorted([r['final_file'] for r in imported] + [r['source_path'] for r in imported])
    (root / 'SHA256SUMS.txt').write_text(''.join(sha(root / name) + '  ' + name + '\n' for name in files))
    credit = ['# Acquired POTY sources', '', 'File-specific Commons rights evidence; no new license is assigned. Downloaded rendition bytes are unchanged. Creator and uploader are separate fields in the source evidence. Unknown fields remain null.', '']
    for row in imported:
        credit.extend([f"## {row['candidate_id']} — {row['canonical_title']}", '',
                       f"- POTY {row['year']}, {row['official_category']}; [gallery]({row['gallery_url']}).",
                       f"- Creator: {row['creator'] or 'unknown'}. Credit: {row['credit'] or 'unknown'}.",
                       f"- Original creator evidence: {row['original_creator_basis']}",
                       f"- License: {row['license']}; terms: {row['license_url'] or 'see preserved Commons metadata'}.",
                       f"- Usage terms: {row['usage_terms'] or 'not supplied'}; restrictions: {row['restrictions'] or 'not supplied'}.",
                       f"- [File page]({row['source_url']}); [exact downloaded rendition]({row['url']}).",
                       f"- Input: `{row['final_file']}`; source: `{row['source_path']}`; {row['width']} × {row['height']}; {row['format']}.",
                       f"- SHA-256: `{row['sha256']}`. Metadata: `{row['metadata_path']}`.", ''])
    (root / 'SOURCES.md').write_text('\n'.join(credit).rstrip() + '\n')
    sheets(root, imported)
    result = check(root)
    dump(root / 'provenance/validation.json', result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


def check_api(root, relative):
    path = safe(root, relative)
    receipt = read(path.with_suffix('.receipt.json'))
    require(receipt['response_complete'] is True and receipt['status'] == 200, 'Incomplete API receipt')
    require(receipt['sha256'] == sha(path) and receipt['bytes_received'] == path.stat().st_size, 'API bytes/receipt differ')
    require(receipt['url'].startswith('https://commons.wikimedia.org/w/api.php?'), 'Non-Commons API evidence')
    data = read(path)
    require('error' not in data and 'warnings' not in data and 'continue' not in data, 'API data incomplete')
    return receipt



# Active catalogs are checked separately from the preserved publication.
from pathlib import Path as _RemovalPath
import sys as _removal_sys
_removal_tools = next(p / 'tools' for p in _RemovalPath(__file__).resolve().parents if (p / 'tools/fixture_layout.py').is_file())
_removal_sys.path.insert(0, str(_removal_tools))
from fixture_removal import publication_check, require_unremoved

@publication_check
def check(root):
    inv = read(root / 'provenance/intake/inventory.json')
    category = inv['official_category']
    require(category in CATEGORIES and inv['years'] == list(YEARS) and inv['complete'], 'Invalid population scope')
    require(inv['candidates'] == inventory(root, category), 'Inventory differs from category data')
    require(len(inv['candidates']) > 0, 'Empty eligible population')
    require(all(r['in_all_gallery'] for r in inv['candidates']), 'Category candidate missing from Round 1 All data')
    require(all((root / f'provenance/api/population-{year}.json').exists() for year in YEARS), 'Incomplete years')
    used_api = {r['metadata_path'] for r in inv['candidates']}
    ev = review_rows(root)
    require(read(root / 'provenance/source-evidence.json') == ev, 'Source evidence differs from raw metadata')
    used_api.update(r['metadata_path'] for r in ev)
    for relative in used_api:
        check_api(root, relative)
    require(read(root / 'provenance/intake/ordering.json')['seed'] == SEED, 'Seed changed')
    require(read(root / 'provenance/intake/ordering.json')['candidate_ids'] == ordering(inv['candidates'], category), 'Ordering changed')
    chosen = choose(root)
    require(read(root / 'provenance/intake/selection.json') == chosen, 'Selection does not replay')
    review = read(root / 'provenance/provenance-review.json')
    require(review == derive(root), 'Provenance decisions do not reproduce from source evidence and explicit overrides')
    aliases = read(root / 'provenance/creator-aliases.json')
    alias_evidence = read(root / 'provenance/creator-alias-evidence.json')
    require(set(aliases) == set(alias_evidence), 'Creator alias evidence coverage differs')
    for key, value in aliases.items():
        evidence = alias_evidence[key]
        require(evidence['canonical_key'] == value and evidence['basis'] and evidence['source_evidence'], 'Missing creator alias basis')
        for record in evidence['source_evidence']:
            require(record['metadata_sha256'] == sha(safe(root, record['metadata_path'])), 'Creator alias evidence changed')
        if evidence.get('additional_metadata_path'):
            check_api(root, evidence['additional_metadata_path'])
            require(evidence['additional_metadata_sha256'] == sha(root / evidence['additional_metadata_path']), 'Additional creator evidence changed')
    by_id = {r['candidate_id']: r for r in ev}
    require(set(review) <= set(by_id), 'Review has unknown candidates')
    for cid, decision in review.items():
        require(decision['metadata_sha256'] == by_id[cid]['metadata_sha256'], 'Reviewed evidence changed')
        require(decision['creator_basis'] and decision['license_basis'] and decision['relationship_basis'], 'Missing review basis')
        require(isinstance(decision['creator_keys'], list) and isinstance(decision['relationship_keys'], list), 'Invalid review keys')
    creators = [key for cid in chosen['selected'] for key in review[cid]['creator_keys']]
    require(len(creators) == len(set(creators)), 'Repeated identified creator')
    imported = imports(root)
    require({p.stem for p in (root / 'provenance/downloads').glob('*.json')} == {r['candidate_id'] for r in imported}, 'Download receipt coverage differs')
    require(read(root / 'provenance/import-map.json') == imported, 'Import snapshot differs')
    require(read(root / 'provenance/acquisition.json') == summary(root), 'Acquisition counts differ')
    rows, sources = records(imported)
    manifest = read(root / 'manifest.json')
    require(manifest['schema_version'] == 1 and manifest['kind'] == 'curatorial_heap', 'Kind/schema differ')
    require(not (root / 'prompt.json').exists() and not (root / 'provenance/intake/prompt.json').exists(), 'Curatorial selection must not acquire a visual prompt')
    require(manifest['images'] == rows, 'Manifest/import mismatch')
    require(read_csv(root / 'manifest.csv') == [{k: str(v) for k, v in row.items()} for row in rows], 'Manifest CSV differs')
    require(read_csv(root / 'sources.csv') == [{k: str(v) for k, v in row.items()} for row in sources], 'Source CSV differs')
    expected_paths = {r['final_file'] for r in imported} | {r['source_path'] for r in imported}
    actual_paths = {str(p.relative_to(root)) for directory in ('images', 'sources') for p in (root / directory).rglob('*') if p.is_file()}
    require(actual_paths == expected_paths, 'Asset coverage differs')
    sums = {}
    for line in (root / 'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        require(name not in sums, 'Duplicate checksum')
        require(sha(safe(root, name)) == digest, f'Changed bytes: {name}')
        sums[name] = digest
    require(set(sums) == expected_paths, 'Checksum coverage differs')
    hashes = set()
    for row in imported:
        source, image = safe(root, row['source_path']), safe(root, row['final_file'])
        require(source.read_bytes() == image.read_bytes(), 'Source/input bytes differ')
        require(sha(source) == row['sha256'] and source.stat().st_size == row['bytes'], 'Download receipt differs')
        require(row['sha256'] not in hashes, 'Duplicate acquired bytes')
        hashes.add(row['sha256'])
        require(all(row[k] == value for k, value in dimensions(source).items()), 'Decoded metadata differs')
        response = row['response']
        require(response['response_complete'] and response['status'] == 200 and response['sha256'] == row['sha256'], 'Incomplete source transfer')
        require(response['url'] == row['url'] and response['bytes_received'] == row['bytes'], 'Transport receipt mismatch')
        pages = read(root / row['metadata_path'])['query']['pages']
        page = next(p for p in pages if p.get('pageid') == row['pageid'])
        info = page['imageinfo'][0]
        require(row['original_sha1'] == info['sha1'], 'Upstream identity differs')
        require(row['url'] in (info.get('thumburl'), info.get('url')), 'Media URL was not API-returned')
        require((row['api_reported_width'], row['api_reported_height']) == (info.get('thumbwidth', info['width']), info.get('thumbheight', info['height'])), 'API-reported dimensions differ')
        require(max(row['width'], row['height']) <= row['requested_edge'] * 1.5, 'Decoded rendition exceeds bound')
        require(row['source_independence_confirmed'] is None, 'Unsupported independence assertion')
    for name, subset in [('batch-1', rows), ('smoke', rows[:5]), ('medium', rows[:20])]:
        require((root / f'batches/{name}.txt').read_text().splitlines() == [r['file'] for r in subset], 'Batch differs')
    require({p.name for p in (root / 'batches').iterdir()} == {'batch-1.txt', 'smoke.txt', 'medium.txt'}, 'Unexpected batch lists')
    selection = read(root / 'selections.json')
    require(selection['pairs'] == [] and selection['known_shift_families'] == [] and read_csv(root / 'probes.csv') == [], 'Unexpected pair expectations')
    sheets = read(root / 'provenance/contact-sheets.json')
    require([cid for sheet in sheets for cid in sheet['candidate_ids']] == [r['candidate_id'] for r in imported], 'Contact-sheet input coverage differs')
    require({sheet['path'] for sheet in sheets} == {str(p.relative_to(root)) for p in (root / 'previews').glob('selected-*.jpg')}, 'Contact-sheet coverage differs')
    for sheet in sheets:
        require(sha(safe(root, sheet['path'])) == sheet['sha256'], 'Contact sheet changed')
        size = dimensions(root / sheet['path'])
        require(size['width'] == sheet['width'] and size['height'] == sheet['height'], 'Contact-sheet dimensions differ')
    return dict(validation='passed', kind='curatorial_heap', pairs=0, **summary(root))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'check', 'list'])
    parser.add_argument('--category', choices=CATEGORIES)
    args = parser.parse_args()
    lock = ROOT / 'Arthropods/previews/poty-intake.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for category in CATEGORIES:
            if args.category and args.category != category:
                continue
            root = ROOT / slug(category)
            if args.command == 'build': build(root)
            elif args.command == 'check': print(json.dumps(check(root), ensure_ascii=False))
            else: print(root.relative_to(ROOT), read(root / 'manifest.json')['kind'])


if __name__ == '__main__':
    main()
