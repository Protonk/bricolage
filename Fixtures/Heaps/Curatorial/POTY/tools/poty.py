#!/usr/bin/env python3
"""POTY fixture intake and offline validation. No image-comparison operations."""
import argparse
from collections import Counter
import csv
import fcntl
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
from urllib.parse import quote, unquote

from PIL import Image, ImageDraw, ImageOps
from transport import Client, StopAcquisition, append, dump, safe, sha, utc

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = ('Arthropods', 'Constructions and buildings', 'People and human activity')
YEARS = (2023, 2024, 2025)
SEED = 'hazy-poty-round1-2023-2025-v1'
IMAGE_FIELDS = 'file batch family_id scene_id parents transformation relation_kind origin_count width height exif_orientation format byte_sha256 pixels_rgb_sha256'.split()
SOURCE_FIELDS = 'family_id source_filename scene_id subject credit_status source_sha256 width height exif_orientation source_url preprocessing view exposure_id original_path'.split()
EXT = {'JPEG': 'jpg', 'PNG': 'png', 'WEBP': 'webp', 'TIFF': 'tif'}


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def slug(category):
    return category.replace(' ', '-')


def text(value):
    return html.unescape(re.sub('<[^>]*>', '', value or '')).strip() or None


def norm(value):
    return ' '.join(unquote(value).replace('_', ' ').split()).casefold()


def page_content(page):
    return page['revisions'][0]['slots']['main']['content']


def gallery(year, category):
    return f'Commons:Picture of the Year/{year}/Gallery/{category}'


def wiki(title):
    return 'https://commons.wikimedia.org/wiki/' + quote(title.replace(' ', '_'), safe=':/')


def inventory(root, category):
    """Reconstruct every entry from actual published category-page revision bytes."""
    rows = []
    for year in YEARS:
        path = root / f'provenance/api/population-{year}.json'
        if not path.exists():
            continue
        pages = {p['title']: p for p in read(path)['query']['pages']}
        title = gallery(year, category) + '/data.json'
        page = pages[title]
        all_rows = json.loads(page_content(pages[gallery(year, 'All') + '/data.json']))
        all_titles = {norm(r['title']) for r in all_rows}
        for index, item in enumerate(json.loads(page_content(page))):
            file_title = 'File:' + item['title'].strip().replace('_', ' ')
            key = f'{year}\n{category}\n{file_title}'
            cid = hashlib.sha256(key.encode()).hexdigest()[:20]
            rows.append(dict(candidate_id=cid, year=year, official_category=category,
                             commons_title=file_title, published=item, published_index=index,
                             in_all_gallery=norm(item['title']) in all_titles,
                             gallery_url=wiki(gallery(year, category)), data_page=title,
                             data_revision=page['revisions'][0]['revid'],
                             data_url=wiki(title), metadata_path=str(path.relative_to(root)),
                             metadata_sha256=sha(path)))
    require(len({r['candidate_id'] for r in rows}) == len(rows), 'Repeated population entry')
    return rows


def ordering(rows, category):
    return sorted((r['candidate_id'] for r in rows),
                  key=lambda cid: (hashlib.sha256(f'{SEED}\n{category}\n{cid}'.encode()).hexdigest(), cid))


def initialize():
    first = ROOT / 'Arthropods'
    client = Client(first)
    for year in YEARS:
        client.api(f'population-{year}', prop='revisions', rvprop='ids|timestamp|content', rvslots='main',
                   titles='|'.join(gallery(year, cat) + '/data.json' for cat in ('All', *CATEGORIES)))
    for category in CATEGORIES:
        root = ROOT / slug(category)
        for year in YEARS:
            for suffix in ('.json', '.receipt.json'):
                relative = f'provenance/api/population-{year}{suffix}'
                dest = safe(root, relative)
                dest.parent.mkdir(parents=True, exist_ok=True)
                if root != first:
                    if dest.exists():
                        require(sha(dest) == sha(first / relative), 'Population cache differs')
                    else:
                        shutil.copyfile(first / relative, dest)
        rows = inventory(root, category)
        value = dict(official_category=category, years=list(YEARS), complete=True, candidates=rows,
                     basis='Complete category data.json pages used by the published Round 1 gallery; raw records preserved.')
        if (root / 'provenance/intake/inventory.json').exists():
            require(read(root / 'provenance/intake/inventory.json') == value, 'Existing inventory changed')
        dump(root / 'provenance/intake/inventory.json', value)
        dump(root / 'provenance/intake/ordering.json', dict(seed=SEED, algorithm='Ascending SHA-256 of UTF-8 seed + LF + official category + LF + candidate_id; ID tie break.',
                                          candidate_ids=ordering(rows, category)))
        print(category, len(rows), Counter(r['year'] for r in rows), flush=True)


def metadata(root):
    rows = read(root / 'provenance/intake/inventory.json')['candidates']
    client = Client(root)
    # Fixed small batches preserve query identity across resumes and avoid URL-size limits.
    for offset in range(0, len(rows), 10):
        group = rows[offset:offset + 10]
        key = f'files-{offset // 10:03d}'
        data = client.api(key, prop='imageinfo|revisions', titles='|'.join(r['commons_title'] for r in group),
                          redirects=1, iiprop='url|size|mime|sha1|extmetadata|timestamp|user',
                          iiurlwidth=1600, iiurlheight=1600, rvprop='ids|timestamp|content', rvslots='main')
        require('continue' not in data, 'Unexpected incomplete metadata batch')
        print(root.name, key, 'cached', flush=True)


def metadata_records(root):
    result = {}
    for path in sorted((root / 'provenance/api').glob('files-*.json')):
        if path.name.endswith('.receipt.json'):
            continue
        data = read(path)
        aliases = {}
        for field in ('normalized', 'redirects'):
            for item in data.get('query', {}).get(field, []):
                aliases[item['from']] = item['to']
        pages = {p['title']: p for p in data['query']['pages']}
        for title in set(pages) | set(aliases):
            canonical = title
            seen = set()
            while canonical in aliases:
                require(canonical not in seen, 'Redirect loop')
                seen.add(canonical)
                canonical = aliases[canonical]
            if canonical in pages:
                result[norm(title)] = (pages[canonical], str(path.relative_to(root)))
    return result


def review_rows(root):
    """Extract evidence only. Creator attribution decisions are supplied separately."""
    metas = metadata_records(root)
    result = []
    for row in read(root / 'provenance/intake/inventory.json')['candidates']:
        found = metas.get(norm(row['commons_title']))
        if not found:
            continue
        page, path = found
        info = (page.get('imageinfo') or [{}])[0]
        ext = info.get('extmetadata', {})
        def value(key):
            return ext.get(key, {}).get('value')
        result.append(dict(candidate_id=row['candidate_id'], commons_title=row['commons_title'],
                           canonical_title=page['title'], pageid=page.get('pageid'),
                           original_sha1=info.get('sha1'), original_url=info.get('url'),
                           file_timestamp=info.get('timestamp'), original_size=info.get('size'),
                           original_width=info.get('width'), original_height=info.get('height'),
                           mime=info.get('mime'), artist_html=value('Artist'), creator=text(value('Artist')),
                           credit=text(value('Credit')), license=text(value('LicenseShortName')),
                           license_url=text(value('LicenseUrl')), usage_terms=text(value('UsageTerms')),
                           copyrighted=text(value('Copyrighted')), restrictions=text(value('Restrictions')),
                           published_uploader=row['published'].get('uploader') or None,
                           latest_revision_uploader=info.get('user'),
                           metadata_path=path, metadata_sha256=sha(root / path),
                           description=text(value('ImageDescription')),
                           file_page_revision=page.get('revisions', [{}])[0].get('revid')))
    return result


def export_review(root):
    dump(root / 'provenance/source-evidence.json', review_rows(root))


def choose(root):
    inv = read(root / 'provenance/intake/inventory.json')
    rows = inv['candidates']
    ordered = ordering(rows, inv['official_category'])
    evidence = {r['candidate_id']: r for r in review_rows(root)}
    decisions = read(root / 'provenance/provenance-review.json') if (root / 'provenance/provenance-review.json').exists() else {}
    accepted, output, creators, identities, relationships = [], [], {}, {}, {}
    blocked = False
    for cid in ordered:
        ev, decision = evidence.get(cid), decisions.get(cid)
        state, reason, conflicting = 'pending', 'metadata_or_provenance_review_pending', []
        if blocked:
            reason = 'earlier_candidate_pending'
        elif len(accepted) >= 50:
            state, reason = 'reserve', 'target_reached'
        elif not ev or not decision:
            blocked = True
        elif decision['exclude_reason']:
            state, reason = 'excluded', decision['exclude_reason']
        else:
            ids = [('pageid', ev['pageid']), ('original_sha1', ev['original_sha1'])]
            duplicate = [identities[k, v] for k, v in ids if v is not None and (k, v) in identities]
            repeated = [creators[c] for c in decision['creator_keys'] if c in creators]
            related = [relationships[g] for g in decision['relationship_keys'] if g in relationships]
            if duplicate:
                state, reason, conflicting = 'excluded', 'duplicate_asset', duplicate
            elif related:
                state, reason, conflicting = 'excluded', 'known_related_capture_or_crop', related
            elif repeated:
                state, reason, conflicting = 'excluded', 'creator_already_selected', repeated
            else:
                require(ev['pageid'] and ev['original_sha1'] and ev['license'], 'Acceptance without source/license')
                state, reason = 'selected', 'first_eligible_in_seeded_order'
                accepted.append(cid)
                for creator in decision['creator_keys']:
                    creators[creator] = cid
                for group in decision['relationship_keys']:
                    relationships[group] = cid
                for key, value in ids:
                    identities[key, value] = cid
        output.append(dict(candidate_id=cid, rank=len(output) + 1, decision=state, reason=reason,
                           conflicts_with=sorted(set(conflicting))))
    return dict(seed=SEED, target=50, official_category=inv['official_category'], decisions=output,
                selected=accepted, counts=dict(Counter(r['decision'] for r in output)))


def select(root):
    dump(root / 'provenance/intake/selection.json', choose(root))


def dimensions(path):
    with Image.open(path) as im:
        require(getattr(im, 'n_frames', 1) == 1, 'Multiple frames unsupported')
        require(im.format in EXT, 'Unsupported format')
        im.load()
        return dict(width=im.width, height=im.height, format=im.format,
                    exif_orientation=im.getexif().get(274, 1))


def acquire(root, limit, reuse_complete_body=False):
    require(read(root / 'provenance/intake/selection.json') == choose(root), 'Stale selection')
    selected = read(root / 'provenance/intake/selection.json')['selected']
    evidence = {r['candidate_id']: r for r in review_rows(root)}
    metas = metadata_records(root)
    client = Client(root)
    completed = 0
    for cid in selected:
        dest_receipt = root / f'provenance/downloads/{cid}.json'
        if dest_receipt.exists():
            receipt = read(dest_receipt)
            require(sha(safe(root, receipt['source_path'])) == receipt['sha256'], 'Cached media changed')
            continue
        if completed >= limit:
            break
        ev = evidence[cid]
        page, path = metas[norm(ev['commons_title'])]
        info = page['imageinfo'][0]
        url = info.get('thumburl')
        if not url and max(info['width'], info['height']) <= 1600:
            url = info['url']
        require(url, 'No bounded API rendition; explicit exclusion required')
        from urllib.parse import urlparse
        unscaled = urlparse(url).path == urlparse(info['url']).path
        require(not unscaled or max(info['width'], info['height']) <= 1600, 'Oversized original; explicit smaller request or exclusion required')
        part = root / f'previews/partials/{cid}.part'
        reused = False
        if part.exists() and reuse_complete_body:
            events = [json.loads(line) for line in (root / 'provenance/http_log.jsonl').read_text().splitlines()]
            matching = [e for e in events if e.get('key') == cid and e.get('kind') == 'source'
                        and e.get('response_complete') and e.get('status') == 200
                        and e.get('url') == url and e.get('sha256') == sha(part)
                        and e.get('bytes_received') == part.stat().st_size]
            require(len(matching) == 1, 'No unique complete transfer receipt for retained body')
            event, reused = matching[0], True
        else:
            part, event = client.fetch(url, 'source', cid, f'previews/partials/{cid}.part')
        try:
            measured = dimensions(part)
            require(max(measured['width'], measured['height']) <= 2400, 'Rendition exceeds nominal edge by over 50%')
        except Exception as error:
            client.stop(dict(utc=utc(), key=cid, kind='decode', status=200, response_complete=True,
                             partial_path=str(part.relative_to(root)), sha256=sha(part), error=str(error)))
        source = f'sources/{cid}.{EXT[measured["format"]]}'
        destination = safe(root, source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        require(not destination.exists(), 'Unreceipted source exists')
        if reused:
            shutil.copyfile(part, destination)  # Retain the diagnosed stop's complete body.
        else:
            part.replace(destination)
        dump(dest_receipt, dict(candidate_id=cid, source_path=source, sha256=sha(destination),
                               bytes=destination.stat().st_size, url=url, requested_edge=1600,
                               rendition='api_reported_unscaled_original' if unscaled else 'api_returned_rendition',
                               metadata_path=path, metadata_sha256=sha(root / path),
                               original_sha1=ev['original_sha1'], pageid=ev['pageid'],
                               api_reported_width=info['width'] if unscaled else info['thumbwidth'],
                               api_reported_height=info['height'] if unscaled else info['thumbheight'],
                               reused_complete_body_after_acknowledgement=reused,
                               response=event, **measured))
        completed += 1
        print(root.name, cid, measured['width'], measured['height'], 'acquired', flush=True)


def csv_write(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['initialize', 'metadata', 'evidence', 'select', 'acquire'])
    parser.add_argument('--category', choices=CATEGORIES)
    parser.add_argument('--limit', type=int, default=1)
    parser.add_argument('--acknowledge-error', help='Explicit diagnosis and resumption reason; never automatic')
    parser.add_argument('--reuse-complete-body', action='store_true', help='Explicitly reuse a retained body only with a matching complete transfer receipt')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit must be a positive bounded chunk size')
    roots = [ROOT / slug(c) for c in CATEGORIES if not args.category or c == args.category]
    lock = ROOT / 'Arthropods/previews/poty-intake.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.command in ('initialize', 'metadata', 'acquire'):
            for category in CATEGORIES:
                root = ROOT / slug(category)
                latch = root / 'provenance/last_transport_error.json'
                if latch.exists():
                    if not args.acknowledge_error:
                        raise StopAcquisition(f'Inspect {latch}; explicit acknowledgement required')
                    append(root / 'provenance/error_acknowledgements.jsonl',
                           dict(utc=utc(), reason=args.acknowledge_error, failure=read(latch)))
                    latch.unlink()
        if args.command == 'initialize':
            initialize()
        else:
            for root in roots:
                if args.command == 'metadata': metadata(root)
                elif args.command == 'evidence': export_review(root)
                elif args.command == 'select': select(root)
                elif args.command == 'acquire': acquire(root, args.limit, args.reuse_complete_body)


if __name__ == '__main__':
    main()
