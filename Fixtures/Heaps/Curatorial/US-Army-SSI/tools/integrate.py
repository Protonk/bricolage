#!/usr/bin/env python3
"""Build a fresh SSI publication stage, validate offline, then publish once."""
import argparse
from collections import Counter
import csv
import fcntl
import json
import math
from pathlib import Path
import shutil
import tempfile
from urllib.parse import parse_qs, quote, urlsplit

from PIL import Image, ImageDraw, ImageOps
import audit
import population
import ssi
from transport import dump, safe, sha

IMAGE_FIELDS = 'file batch family_id scene_id parents transformation relation_kind origin_count width height exif_orientation format byte_sha256 pixels_rgb_sha256'.split()
SOURCE_FIELDS = 'family_id source_filename scene_id subject credit_status source_sha256 width height exif_orientation source_url preprocessing view exposure_id original_path'.split()
PROBE_FIELDS = 'file_a file_b relation interpretation'.split()
require = ssi.require
read = ssi.read


def csv_write(path, rows, fields):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def csv_read(path):
    with path.open(newline='') as stream:
        return list(csv.DictReader(stream))


def imports():
    root = ssi.ROOT
    inventory = ssi.candidates()
    reviews = read(root / 'provenance/design-review.json')
    evidence = ssi.evidence()
    rows = []
    for cid in ssi.selection()['selected']:
        path = root / f'provenance/source-receipts/{cid}.json'
        if not path.exists():
            continue
        receipt = read(path)
        page = evidence[cid]['page']
        info = page['imageinfo'][0]
        review = reviews[cid]
        rows.append(dict(**receipt, source_path=receipt['path'],
                         final_file='images/' + Path(receipt['path']).name,
                         family_id='ssi-' + cid, frozen_title=inventory[cid]['frozen_title'],
                         petscan_pageid=inventory[cid]['petscan_pageid'],
                         source_url='https://commons.wikimedia.org/wiki/' + quote(page['title'].replace(' ', '_'), safe=':/'),
                         file_timestamp=info['timestamp'], file_page_revision=page['revisions'][0]['revid'],
                         design_key=review['design_key'], design_basis=review['design_basis'],
                         review_metadata_path=review['metadata_path'],
                         review_metadata_sha256=review['metadata_sha256'],
                         source_independence_confirmed=None,
                         **{k: review[k] for k in ('reported_artist', 'original_creator', 'designer', 'digital_renderer',
                                                  'creator_basis', 'uploader_current_file_revision', 'credit',
                                                  'license', 'license_url', 'rights_basis', 'restrictions')}))
    return rows


def records(imported):
    images, sources = [], []
    for item in imported:
        images.append(dict(file=item['final_file'], batch='batch-1', family_id=item['family_id'],
                           scene_id='', parents=item['family_id'], transformation='source',
                           relation_kind='curatorial_selected', origin_count=1,
                           **{k: item[k] for k in ('width', 'height', 'exif_orientation', 'format')},
                           byte_sha256=item['sha256'], pixels_rgb_sha256=''))
        sources.append(dict(family_id=item['family_id'], source_filename=Path(item['source_path']).name,
                            scene_id='', subject=item['canonical_title'],
                            credit_status=f"{item['reported_artist'] or 'unknown artist'}; {item['license']}",
                            source_sha256=item['sha256'], width=item['width'], height=item['height'],
                            exif_orientation=item['exif_orientation'], source_url=item['source_url'],
                            preprocessing=f"API request {item['requested_edge']}px; {item['rendition']}; decoded {item['width']}x{item['height']} {item['format']}; local byte copy only.",
                            view='', exposure_id='', original_path=item['frozen_title']))
    return images, sources


def summary():
    root = ssi.ROOT
    chosen = ssi.selection()
    imported = imports()
    reviews = read(root / 'provenance/design-review.json')
    acquired = {r['candidate_id'] for r in imported}
    pending = [cid for cid in chosen['selected'] if cid not in acquired]
    events = [json.loads(line) for line in (root / 'provenance/http_log.jsonl').read_text().splitlines()]
    status = 'partial' if chosen['counts']['pending'] or pending else 'complete'
    if len(acquired) == ssi.TARGET and not pending:
        status = 'provisional' if chosen['unresolved_prior_candidates'] else 'complete'
    if (root / 'provenance/last_transport_error.json').exists():
        status = 'stopped'
    counts = chosen['counts']
    return dict(status=status, target=ssi.TARGET, raw_listings=len(ssi.order()), unique_file_identities=len(ssi.order()),
                target_acquired=len(acquired) == ssi.TARGET,
                provisional_selected=len(chosen['provisional_selected']),
                reviewed_entries=len(reviews), selected=len(chosen['selected']), acquired=len(acquired),
                excluded=counts['excluded'], reserve=counts['reserve'], pending_selection=counts['pending'],
                unreviewed_entries=len(ssi.order())-len(reviews),
                reviewed_decisions=dict(Counter(r['decision'] for r in reviews.values())),
                pending_acquisition=len(pending), pending_acquisition_ids=pending,
                exclusions_by_reason=dict(Counter(r['reason'] for r in chosen['decisions'] if r['decision'] == 'excluded')),
                unresolved_review_ids=[cid for cid, r in reviews.items() if r['decision'] == 'pending'],
                exhausted_population_shortfall=ssi.TARGET-len(chosen['selected']) if not counts['pending'] and not counts['reserve'] else None,
                transport_failures=sum(bool(r.get('error')) and r.get('kind') in ('population', 'api', 'preview', 'source') for r in events),
                post_transfer_validation_stops=sum(bool(r.get('error')) and r.get('kind') == 'decode' for r in events),
                automatic_retries=0,
                concentration={role: dict(Counter(reviews[cid][role] or 'unknown' for cid in chosen['selected']))
                               for role in ('original_creator', 'designer', 'digital_renderer', 'uploader_current_file_revision')})


def credits(imported):
    text = ['# Acquired SSI sources', '',
            'File-specific Commons claims and credits are retained below and in raw API/file-page evidence. No blanket collection license or independent authentication is claimed. Unknown roles remain unknown. Downloaded bytes, including alpha, are unchanged.', '']
    for row in imported:
        text.extend([f"## {row['candidate_id']} — {row['canonical_title']}", '',
                     f"- [File page]({row['source_url']}); [exact rendition]({row['url']}).",
                     f"- Reported Artist: {row['reported_artist'] or 'unknown'}. Credit: {row['credit'] or 'unknown'}.",
                     f"- Original creator: {row['original_creator'] or 'unknown'}; designer: {row['designer'] or 'unknown'}; digital renderer: {row['digital_renderer'] or 'unknown'}.",
                     f"- Role evidence: {row['creator_basis']} Current file-version uploader: {row['uploader_current_file_revision'] or 'unknown'}.",
                     f"- License: {row['license']}; terms: {row['license_url'] or 'no URL supplied; see retained public-domain templates'}. Restrictions: {row['restrictions'] or 'none supplied'}.",
                     f"- Original: {row['original_mime']}, SHA-1 `{row['original_sha1']}`. Acquired: {row['format']}, {row['width']} × {row['height']}, mode {row['mode']}, alpha {row['has_alpha']}.",
                     f"- Source `{row['source_path']}`; input `{row['final_file']}`; SHA-256 `{row['sha256']}`.",
                     f"- Rights evidence `{row['review_metadata_path']}`; rendition evidence `{row['metadata_path']}`.", ''])
    return '\n'.join(text).rstrip() + '\n'


def sheets(stage, imported):
    receipts = []
    (stage / 'previews').mkdir(exist_ok=True)
    for start in range(0, len(imported), 20):
        group = imported[start:start+20]
        canvas = Image.new('RGB', (1280, math.ceil(len(group)/4)*280), '#eeeeee')
        draw = ImageDraw.Draw(canvas)
        for i, row in enumerate(group):
            with Image.open(stage / row['final_file']) as im:
                tile = ImageOps.exif_transpose(im).convert('RGBA')
                tile.thumbnail((304, 240), Image.Resampling.LANCZOS)
                x, y = i % 4 * 320, i // 4 * 280
                canvas.paste(tile, (x+(320-tile.width)//2, y+(240-tile.height)//2), tile)
                draw.text((x+8, y+250), row['candidate_id'], fill='black')
        relative = f'previews/selected-{start//20+1:02d}.jpg'
        canvas.save(stage / relative, quality=92)
        receipts.append(dict(path=relative, sha256=sha(stage / relative), width=canvas.width,
                             height=canvas.height, candidate_ids=[r['candidate_id'] for r in group]))
    dump(stage / 'provenance/contact-sheets.json', receipts)


def check_api(relative):
    path = safe(ssi.ROOT, relative)
    receipt = read(path.with_suffix('.receipt.json'))
    require(receipt['status'] == 200 and receipt['response_complete'], 'Incomplete API receipt')
    require(receipt['sha256'] == sha(path) and receipt['bytes_received'] == path.stat().st_size, 'Changed API body')
    parsed = urlsplit(receipt['url'])
    require(parsed.scheme == 'https' and parsed.netloc == 'commons.wikimedia.org' and parsed.path == '/w/api.php', 'Wrong API URL')
    params = parse_qs(parsed.query)
    require(params['maxlag'] == ['5'], 'Missing maxlag')
    data = read(path)
    require(not any(k in data for k in ('error', 'warnings', 'continue')), 'Incomplete/failed metadata reply')
    return params



# Active catalogs are checked separately from the preserved publication.
from pathlib import Path as _RemovalPath
import sys as _removal_sys
_removal_tools = next(p / 'tools' for p in _RemovalPath(__file__).resolve().parents if (p / 'tools/fixture_layout.py').is_file())
_removal_sys.path.insert(0, str(_removal_tools))
from fixture_removal import publication_artifacts, require_unremoved

@publication_artifacts(lambda: ssi.ROOT)
def check(artifacts=None):
    root = ssi.ROOT
    output = artifacts or root
    require(root.name == 'US-Army-SSI' and root.parent.name == 'Curatorial', 'Wrong leaf placement')
    require(not [p for p in root.glob('*/manifest.json') if p.parent.name not in ('provenance', 'previews')], 'Unexpected child fixture')
    require(not (root / 'prompt.json').exists() and not (root / 'provenance/intake/prompt.json').exists(), 'Curatorial leaf must not have a visual prompt')
    population.check(root)
    chosen = ssi.selection()
    require(read(root / 'provenance/intake/selection.json') == chosen, 'Selection does not replay')
    reviews = read(root / 'provenance/design-review.json')
    evidence = ssi.evidence()
    for path in (root / 'provenance/api').glob('*.json'):
        if not path.name.endswith('.receipt.json'):
            check_api(str(path.relative_to(root)))
    for cid, review in reviews.items():
        require(cid in evidence and review['rank'] == ssi.order().index(cid)+1, 'Review identity/rank differs')
        require(review['metadata_sha256'] == sha(safe(root, review['metadata_path'])), 'Reviewed metadata changed')
        require(review['metadata_path'] == evidence[cid]['metadata_path'], 'Wrong reviewed API response')
        require(review['design_basis'] and review['creator_basis'], 'Missing decision evidence')
        meta = evidence[cid]['page']['imageinfo'][0]['extmetadata']
        require(review['reported_artist'] == ssi.clean(meta.get('Artist', {}).get('value')), 'Artist evidence differs')
        require(review['license'] == ssi.clean(meta.get('LicenseShortName', {}).get('value')), 'License evidence differs')
        require(review['license_url'] == ssi.clean(meta.get('LicenseUrl', {}).get('value')), 'License URL differs')
        require(review['credit'] == ssi.clean(meta.get('Credit', {}).get('value')), 'Credit evidence differs')
        require(review['restrictions'] == ssi.clean(meta.get('Restrictions', {}).get('value')), 'Restrictions differ')
        require(review['uploader_current_file_revision'] == evidence[cid]['page']['imageinfo'][0]['user'], 'Uploader evidence differs')
        require(all(k in review for k in ('original_creator', 'designer', 'digital_renderer')), 'Missing explicit role fields')
        if review.get('inspection_evidence'):
            require(sha(safe(root, review['inspection_evidence'])) == review['inspection_sha256'], 'Inspection evidence changed')
    keys = [reviews[cid]['design_key'] for cid in chosen['selected']]
    require(len(keys) == len(set(keys)), 'Repeated selected design')
    imported = imports()
    require({p.stem for p in (root / 'provenance/source-receipts').glob('*.json')} == {r['candidate_id'] for r in imported}, 'Source receipt coverage differs')
    require(read(output / 'provenance/import-map.json') == imported, 'Import snapshot differs')
    require(read(output / 'provenance/acquisition.json') == summary(), 'Acquisition summary differs')
    recorded_audit = read(output / 'provenance/identity-audit.json')
    identity_audit = audit.audit(fixture_names=[r['fixture'] for r in recorded_audit['inventories']], recorded_inventories=recorded_audit['inventories'])
    require(identity_audit['status'] == 'passed', 'Prior identity collision unresolved')
    require(read(output / 'provenance/identity-audit.json') == identity_audit, 'Cross-fixture audit differs')
    rows, sources = records(imported)
    manifest = read(output / 'manifest.json')
    require(manifest['schema_version'] == 1 and manifest['kind'] == 'curatorial_heap' and manifest['fixture_id'] == 'hazy-us-army-ssi-v1', 'Manifest kind/identity differs')
    require(manifest['images'] == rows, 'Manifest records differ')
    require(csv_read(output / 'manifest.csv') == [{k: str(v) for k, v in r.items()} for r in rows], 'Manifest CSV differs')
    require(csv_read(output / 'sources.csv') == [{k: str(v) for k, v in r.items()} for r in sources], 'Sources CSV differs')
    require((output / 'SOURCES.md').read_text() == credits(imported), 'Readable credits differ')
    source_paths = {r['source_path'] for r in imported}
    input_paths = {r['final_file'] for r in imported}
    require({str(p.relative_to(root)) for p in (root / 'sources').rglob('*') if p.is_file()} == source_paths, 'Source directory coverage differs')
    require({str(p.relative_to(output)) for p in (output / 'images').rglob('*') if p.is_file()} == input_paths, 'Input directory coverage differs')
    sums = {}
    for line in (output / 'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        require(name not in sums, 'Repeated checksum')
        sums[name] = digest
    require(set(sums) == source_paths | input_paths, 'Checksum coverage differs')
    acquired_hashes = set()
    for row in imported:
        source, image = safe(root, row['source_path']), safe(output, row['final_file'])
        require(source.read_bytes() == image.read_bytes(), 'Source/input bytes differ')
        require(sha(source) == row['sha256'] == sums[row['source_path']] == sums[row['final_file']], 'Source hash differs')
        require(row['sha256'] not in acquired_hashes, 'Duplicate acquired bytes')
        acquired_hashes.add(row['sha256'])
        require(source.stat().st_size == row['bytes'], 'Source size differs')
        require(all(row[k] == v for k, v in ssi.dimensions(source, row['requested_edge']).items()), 'Decoded attributes differ')
        require(row['source_independence_confirmed'] is None, 'Unsupported independence claim')
        response = row['response']
        require(response['status'] == 200 and response['response_complete'] and response['url'] == row['url'], 'Incomplete source transfer')
        require(response['sha256'] == row['sha256'] and response['bytes_received'] == row['bytes'], 'Transport receipt differs')
        require(row['metadata_sha256'] == sha(root / row['metadata_path']), 'Rendition metadata changed')
        params = check_api(row['metadata_path'])
        require(params['iiurlwidth'] == params['iiurlheight'] == [str(row['requested_edge'])], 'Requested size differs')
        page = next(p for p in read(root / row['metadata_path'])['query']['pages'] if p.get('pageid') == row['pageid'])
        info = page['imageinfo'][0]
        require(row['canonical_title'] == page['title'] and row['original_sha1'] == info['sha1'] and row['original_mime'] == info['mime'], 'Upstream identity differs')
        reviewed_page = evidence[row['candidate_id']]['page']
        reviewed_info = reviewed_page['imageinfo'][0]
        require(page['pageid'] == reviewed_page['pageid'] and info['sha1'] == reviewed_info['sha1'], 'Acquired original differs from reviewed identity')
        require(info['extmetadata'] == reviewed_info['extmetadata'], 'Acquired rights/description differs from review')
        require(row['url'] in (info.get('thumburl'), info['url']), 'URL not API-returned')
        original = row['rendition'] == 'api_reported_unscaled_original'
        require((row['api_reported_width'], row['api_reported_height']) == ((info['width'], info['height']) if original else (info['thumbwidth'], info['thumbheight'])), 'API display dimensions differ')
        if original:
            require(info['mime'] != 'image/svg+xml' and max(info['width'], info['height']) <= row['requested_edge'], 'Unsupported/oversized original')
        if info['mime'] == 'image/svg+xml':
            require(not original and row['format'] == 'PNG', 'SVG was not an API PNG rendition')
    for name, subset in [('batch-1', rows), ('smoke', rows[:5]), ('medium', rows[:20])]:
        require((output / f'batches/{name}.txt').read_text().splitlines() == [r['file'] for r in subset], 'Batch coverage differs')
    require({p.name for p in (output / 'batches').iterdir()} == {'batch-1.txt', 'smoke.txt', 'medium.txt'}, 'Unexpected batches')
    pairs = read(output / 'selections.json')
    require(pairs['pairs'] == [] and pairs['known_shift_families'] == [] and not csv_read(output / 'probes.csv'), 'Unexpected pair expectations')
    contacts = read(output / 'provenance/contact-sheets.json')
    require([cid for r in contacts for cid in r['candidate_ids']] == [r['candidate_id'] for r in imported], 'Contact coverage differs')
    for record in contacts:
        require(sha(safe(output, record['path'])) == record['sha256'], 'Contact sheet changed')
        with Image.open(output / record['path']) as im:
            im.load()
            require(im.size == (record['width'], record['height']), 'Contact dimensions differ')
    return dict(validation='passed', kind='curatorial_heap', pairs=0, **summary())


def replacement_snapshot(expected_sha, preserved):
    root = ssi.ROOT
    require_unremoved(root)
    require(expected_sha and preserved, 'Published set already exists; explicit manifest hash and preserved publication required')
    require(sha(root / 'manifest.json') == expected_sha, 'Published manifest changed')
    backup = safe(root, preserved)
    snapshot = read(backup / 'snapshot.json')
    require(sha(backup / 'manifest.json') == expected_sha == snapshot['files']['manifest.json'], 'Preserved manifest differs')
    expected = dict(snapshot['files'])
    for name, digest in snapshot['files'].items():
        require(sha(safe(backup, name)) == digest, 'Preserved publication changed: '+name)
    for row in read(root / 'manifest.json')['images']:
        require(sha(safe(root, row['file'])) == row['byte_sha256'], 'Existing input changed')
        expected[row['file']] = row['byte_sha256']
    for row in snapshot['contact_sheets']:
        require(sha(safe(root, row['preserved_path'])) == row['sha256'], 'Preserved contact sheet changed')
        expected[row['original_path']] = row['sha256']
    return expected


def build(replace_manifest_sha=None, preserved_publication=None):
    root = ssi.ROOT
    replacing = (root / 'manifest.json').exists()
    expected = replacement_snapshot(replace_manifest_sha, preserved_publication) if replacing else {}
    require(read(root / 'provenance/intake/selection.json') == ssi.selection(), 'Explicitly record selection before building')
    stage = Path(tempfile.mkdtemp(prefix='integration-stage-', dir=root / 'previews'))
    imported = imports()
    rows, sources = records(imported)
    for name in ('images', 'batches', 'provenance'):
        (stage / name).mkdir()
    for row in imported:
        require(sha(root / row['source_path']) == row['sha256'], 'Source changed')
        shutil.copyfile(root / row['source_path'], stage / row['final_file'])
    dump(stage / 'manifest.json', dict(schema_version=1, fixture_id='hazy-us-army-ssi-v1', kind='curatorial_heap',
                                      description='Distinct US Army shoulder-sleeve insignia designs from a frozen Commons PetScan category population; seeded file ordering and documented exclusions; no expected matches.', images=rows))
    csv_write(stage / 'manifest.csv', rows, IMAGE_FIELDS)
    csv_write(stage / 'sources.csv', sources, SOURCE_FIELDS)
    csv_write(stage / 'probes.csv', [], PROBE_FIELDS)
    dump(stage / 'selections.json', dict(description='No expected pairs, matching ground truth or similarity labels.', pairs=[], known_shift_families=[]))
    dump(stage / 'provenance/import-map.json', imported)
    dump(stage / 'provenance/acquisition.json', summary())
    dump(stage / 'provenance/identity-audit.json', audit.audit())
    for name, subset in [('batch-1', rows), ('smoke', rows[:5]), ('medium', rows[:20])]:
        (stage / f'batches/{name}.txt').write_text(''.join(r['file']+'\n' for r in subset))
    (stage / 'SHA256SUMS.txt').write_text(''.join(digest+'  '+name+'\n' for name, digest in sorted((name, r['sha256']) for r in imported for name in (r['source_path'], r['final_file']))))
    (stage / 'SOURCES.md').write_text(credits(imported))
    sheets(stage, imported)
    result = check(stage)
    dump(stage / 'provenance/validation.json', result)
    # Check every destination before publishing. A failed stage stays local for diagnosis.
    generated = [p for p in stage.rglob('*') if p.is_file()]
    if replacing:
        old_inputs = {r['file'] for r in read(root / 'manifest.json')['images']}
        require(old_inputs <= {r['file'] for r in rows}, 'Replacement would remove published inputs; reconcile explicitly first')
    for path in generated:
        dest = root / path.relative_to(stage)
        if dest.exists():
            relative = str(path.relative_to(stage))
            require((replacing and relative in expected and sha(dest) == expected[relative]) or
                    (not replacing and dest.name == 'identity-audit.json' and dest.read_bytes() == path.read_bytes()),
                    'Existing published artifact changed or unpreserved: '+str(dest))
    for path in generated:
        dest = root / path.relative_to(stage)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if replacing or not dest.exists():
            path.replace(dest)
    shutil.rmtree(stage)
    result = check()
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['build', 'check', 'list'])
    parser.add_argument('--replace-manifest-sha')
    parser.add_argument('--preserved-publication')
    args = parser.parse_args()
    lock = ssi.ROOT / 'previews/intake.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.command == 'build':
            build(args.replace_manifest_sha, args.preserved_publication)
        elif args.command == 'check':
            print(json.dumps(check(), indent=2))
        else:
            print('US-Army-SSI', read(ssi.ROOT / 'manifest.json')['kind'])


if __name__ == '__main__':
    main()
