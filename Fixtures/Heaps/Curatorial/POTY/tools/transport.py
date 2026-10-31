"""POTY's serial Commons transport, adapted from PS01; never retries or redirects."""
import hashlib
import json
import time
from datetime import datetime, timezone
from http.client import IncompleteRead
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler

API = 'https://commons.wikimedia.org/w/api.php'
AGENT = 'HazyFixtureBot/0.1 (https://github.com/Protonk/hazy) Python-urllib'
HEADERS = {'content-type', 'content-length', 'retry-after', 'x-request-id', 'x-cache',
           'server', 'etag', 'last-modified', 'cache-control', 'date'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root, name):
    path = root / name
    if Path(name).is_absolute() or '..' in Path(name).parts or root.resolve() not in path.resolve().parents:
        raise ValueError(f'Outside fixture: {name}')
    if any(p.is_symlink() for p in [path, *path.parents]):
        raise ValueError(f'Symlink: {name}')
    return path


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    tmp.replace(path)


def append(path, event):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a') as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + '\n')


class StopAcquisition(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    # Shared across leaf clients: at least three seconds after every response.
    last = 0

    def __init__(self, root, pace=3, timeout=40):
        if pace < 3:
            raise ValueError('Pace must be at least three seconds')
        self.root, self.pace, self.timeout = root, pace, timeout
        self.opener = build_opener(NoRedirect)

    def stop(self, event):
        append(self.root / 'provenance/http_log.jsonl', event)
        dump(self.root / 'provenance/last_transport_error.json', event)
        raise StopAcquisition(event['error'])

    def fetch(self, url, kind, key, partial):
        if (self.root / 'provenance/last_transport_error.json').exists():
            raise StopAcquisition('Unacknowledged failure; no request made')
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname not in ('commons.wikimedia.org', 'upload.wikimedia.org', 'thumb.wikimedia.org'):
            raise StopAcquisition('Unexpected Wikimedia URL')
        path = safe(self.root, partial)
        if path.exists():
            raise StopAcquisition('Partial exists; preserve and diagnose before resumption')
        path.parent.mkdir(parents=True, exist_ok=True)
        time.sleep(max(0, self.pace - (time.monotonic() - Client.last)))
        event = dict(utc=utc(), key=key, kind=kind, url=url, user_agent=AGENT,
                     status=None, response_complete=False, bytes_received=0, headers={})
        limit = 8_000_000 if kind == 'api' else 20_000_000
        try:
            request = Request(url, headers={'User-Agent': AGENT, 'Accept': 'application/json' if kind == 'api' else 'image/*'})
            with self.opener.open(request, timeout=self.timeout) as response:
                event['status'] = response.status
                event['headers'] = {k.lower(): v for k, v in response.headers.items() if k.lower() in HEADERS}
                content_type = response.headers.get_content_type()
                if (kind == 'api' and content_type != 'application/json') or (kind != 'api' and not content_type.startswith('image/')):
                    raise StopAcquisition(f'Unexpected content type: {content_type}')
                declared = int(response.headers.get('Content-Length', '0'))
                if declared > limit:
                    raise StopAcquisition('Body exceeds size bound')
                with path.open('wb') as stream:
                    while True:
                        try:
                            chunk = response.read(65536)
                        except IncompleteRead as error:
                            if error.partial:
                                stream.write(error.partial)
                            raise
                        if not chunk:
                            break
                        stream.write(chunk)
                        if stream.tell() > limit:
                            raise StopAcquisition('Body exceeds size bound')
                if declared and declared != path.stat().st_size:
                    raise StopAcquisition('Incomplete HTTP body')
                event.update(response_complete=True, bytes_received=path.stat().st_size, sha256=sha(path))
                append(self.root / 'provenance/http_log.jsonl', event)
                return path, event
        except Exception as error:
            if isinstance(error, HTTPError):
                event['status'] = error.code
                event['headers'] = {k.lower(): v for k, v in error.headers.items() if k.lower() in HEADERS}
                try:
                    event['body_excerpt'] = error.read(2048).decode('utf-8', 'replace')
                except Exception as body_error:
                    event['body_error'] = str(body_error)
            if path.exists():
                event.update(partial_path=partial, bytes_received=path.stat().st_size, partial_sha256=sha(path))
            event['error'] = f'{type(error).__name__}: {error}'
            self.stop(event)
        finally:
            Client.last = time.monotonic()

    def api(self, key, **query):
        path = safe(self.root, f'provenance/api/{key}.json')
        url = API + '?' + urlencode(dict(action='query', format='json', formatversion=2, maxlag=5, **query))
        receipt = path.with_suffix('.receipt.json')
        if path.exists():
            evidence = json.loads(receipt.read_text())
            if evidence['url'] != url or evidence['sha256'] != sha(path):
                raise StopAcquisition('Cached API bytes or query changed')
        else:
            partial, event = self.fetch(url, 'api', key, f'provenance/partials/{key}.part')
            path.parent.mkdir(parents=True, exist_ok=True)
            partial.replace(path)
            dump(receipt, event)
        try:
            data = json.loads(path.read_bytes())
            if 'error' in data or 'warnings' in data:
                raise ValueError('API error/warning: ' + json.dumps(data))
        except (ValueError, UnicodeDecodeError) as error:
            self.stop(dict(utc=utc(), key=key, kind='api-validation', error=str(error), metadata_path=str(path.relative_to(self.root))))
        return data
