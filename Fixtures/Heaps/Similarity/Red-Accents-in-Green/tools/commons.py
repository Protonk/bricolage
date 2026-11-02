#!/usr/bin/env python3
"""Bounded, serial Commons acquisition for the supplied RG01 leads only.

No search, retries, credentials, URL guessing, or automatic acceptance.
"""
import argparse
import fcntl
import hashlib
import io
import json
from pathlib import Path
import time
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
UA = 'HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib'
API = 'https://commons.wikimedia.org/w/api.php'
PAUSE = 3.0
MAX_BYTES = 12 * 1024 * 1024


def path(name):
    p = ROOT / name
    if p.is_absolute() and (p == ROOT or ROOT not in p.resolve().parents):
        raise ValueError(f'Path outside set: {name}')
    if any(x.is_symlink() for x in [p, *p.parents] if x != ROOT.parent):
        raise ValueError(f'Symlink not allowed: {name}')
    return p


def save(name, value):
    p = path(name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


class Client:
    def __init__(self):
        self.last = 0
        if path('provenance/STOP.json').exists():
            raise ValueError('Acquisition stopped; diagnose provenance/STOP.json before any resumption.')
        self.opener = urllib.request.build_opener(NoRedirect)

    def get(self, url, accept):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname not in ('commons.wikimedia.org', 'upload.wikimedia.org', 'thumb.wikimedia.org'):
            raise ValueError('Unexpected Commons URL')
        time.sleep(max(0, self.last + PAUSE - time.monotonic()))
        event = dict(time_utc=now(), url=url, user_agent=UA)
        try:
            request = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': accept})
            with self.opener.open(request, timeout=40) as response:
                event.update(status=response.status, headers=dict(response.headers), final_url=response.url)
                data = response.read(MAX_BYTES + 1)
                if len(data) > MAX_BYTES:
                    raise ValueError('Response exceeded 12 MiB limit')
                event.update(size_bytes=len(data), sha256=sha(data))
                content_type = response.headers.get_content_type()
                if accept == 'application/json':
                    if content_type != 'application/json':
                        raise ValueError(f'Unexpected API content type: {content_type}')
                    result = json.loads(data)
                    if 'error' in result or 'warnings' in result:
                        event['api_response'] = result
                        raise ValueError('API error/warning; inspect STOP.json')
                elif not content_type.startswith('image/'):
                    raise ValueError(f'Unexpected media content type: {content_type}')
            self.log(event)
            return data
        except Exception as error:
            if isinstance(error, urllib.error.HTTPError):
                event.update(status=error.code, headers=dict(error.headers),
                             retry_after=error.headers.get('Retry-After'),
                             response_excerpt=error.read(4096).decode('utf-8', errors='replace'))
            event['error'] = str(error)
            self.log(event)
            save('provenance/STOP.json', event)
            raise RuntimeError('Stopped after one failed request; no automatic retries.') from error
        finally:
            self.last = time.monotonic()

    def log(self, event):
        p = path('provenance/requests.jsonl')
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open('a') as f:
            f.write(json.dumps(event, ensure_ascii=False) + '\n')


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # API-returned media URLs should be direct. Diagnose redirects, never
        # blindly follow a redirect to an original or a different service.
        return None


def metadata(client, candidate, edge):
    name = f"provenance/commons/{candidate['candidate_id']}-{edge}.json"
    p = path(name)
    if p.exists():
        return json.loads(p.read_text())
    query = dict(action='query', format='json', formatversion=2, maxlag=5,
                 titles=candidate['commons_title'], redirects=1,
                 prop='imageinfo', iiprop='url|size|sha1|mime|mediatype|extmetadata',
                 iiurlwidth=edge, iiurlheight=edge, iiextmetadatalanguage='en')
    data = client.get(API + '?' + urllib.parse.urlencode(query), 'application/json')
    record = dict(candidate_id=candidate['candidate_id'], retrieved_utc=now(),
                  requested_title=candidate['commons_title'], response=json.loads(data))
    save(name, record)
    return record


def acquire(client, candidate, edge, preview):
    record = metadata(client, candidate, edge)
    pages = record['response']['query']['pages']
    if len(pages) != 1 or 'imageinfo' not in pages[0]:
        return dict(candidate_id=candidate['candidate_id'], status='missing_file', metadata=record)
    page = pages[0]
    info = page['imageinfo'][0]
    if info['mime'] not in ('image/jpeg', 'image/png') or info['mediatype'] != 'BITMAP':
        return dict(candidate_id=candidate['candidate_id'], status='unsupported_media', mime=info['mime'])
    ext = info.get('extmetadata', {})
    # Keep full upstream HTML as evidence, never execute it.
    license_name = ext.get('LicenseShortName', {}).get('value')
    creator = ext.get('Artist', {}).get('value')
    if not license_name or not creator:
        return dict(candidate_id=candidate['candidate_id'], status='missing_attribution_or_license')
    url = info.get('thumburl')
    if not url and max(info['width'], info['height']) <= edge and info['size'] <= MAX_BYTES:
        url = info['url']
    if not url or (url == info['url'] and max(info['width'], info['height']) > edge):
        return dict(candidate_id=candidate['candidate_id'], status='no_bounded_rendition')
    folder = 'previews/candidates' if preview else 'sources'
    name = f"{folder}/{candidate['candidate_id']}.{'png' if info.get('thumbmime',info['mime']) == 'image/png' else 'jpg'}"
    receipt = f"provenance/downloads/{candidate['candidate_id']}-{edge}.json"
    if path(receipt).exists():
        done = json.loads(path(receipt).read_text())
        if sha(path(done['file']).read_bytes()) != done['sha256']:
            raise ValueError('Cached media changed; not refetching automatically')
        return done
    if path(name).exists():
        raise ValueError(f'Unreceipted file exists: {name}')
    data = client.get(url, 'image/*')
    try:
        with Image.open(io.BytesIO(data)) as im:
            im.load()
            width, height = im.size
            if im.format not in ('PNG', 'JPEG') or getattr(im, 'n_frames', 1) != 1:
                raise ValueError('Unexpected image encoding/frame count')
            # Commons can round to cached thumbnail sizes. Record actual size;
            # reject unexpectedly large replies without another request.
            if max(width, height) > edge * 1.5:
                raise ValueError('Rendition exceeds requested edge by more than 50%')
            orientation = im.getexif().get(274, 1)
    except Exception as error:
        save('provenance/STOP.json', dict(time_utc=now(), url=url, error=str(error)))
        raise
    p = path(name); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    result = dict(candidate_id=candidate['candidate_id'], status='preview_downloaded' if preview else 'downloaded',
                  canonical_title=page['title'], pageid=page['pageid'], file=name,
                  url=url, sha256=sha(data), width=width, height=height, exif_orientation=orientation,
                  requested_max_edge=edge, original_width=info['width'], original_height=info['height'],
                  original_sha1=info['sha1'], creator=creator, license=license_name,
                  license_url=ext.get('LicenseUrl', {}).get('value'), retrieved_utc=now(),
                  visual_review='pending' if preview else 'see reviews.json',
                  source_independence='unverified' if preview else 'see reviews.json')
    save(receipt, result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['previews', 'acquire'])
    parser.add_argument('--limit', type=int, default=1, help='Maximum candidates this invocation; default single-request pilot')
    args = parser.parse_args()
    if not 1 <= args.limit <= 107:
        parser.error('limit must be 1..107')
    candidates = [json.loads(line) for line in path('provenance/intake/candidates.jsonl').read_text().splitlines()]
    if args.mode == 'acquire':
        reviews = json.loads(path('provenance/reviews.json').read_text())
        accepted = {r['candidate_id'] for r in reviews if r['decision'] == 'accept'
                    and r['visual_reason'] and r['provenance_review'] and r['license_review']}
        candidates = [c for c in candidates if c['candidate_id'] in accepted]
    client = Client()
    for candidate in candidates[:args.limit]:
        result = acquire(client, candidate, 320 if args.mode == 'previews' else 1600, args.mode == 'previews')
        save(f"provenance/status/{candidate['candidate_id']}-{args.mode}.json", result)
        print(candidate['candidate_id'], result['status'], flush=True)


if __name__ == '__main__':
    lock = path('previews/acquisition.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another acquisition is running; no request made.')
        main()
