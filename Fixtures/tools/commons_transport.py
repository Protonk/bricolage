"""Paced Commons HTTP requests with per-leaf receipts and partial-body evidence."""
from datetime import datetime, timezone
import hashlib
from http.client import IncompleteRead
import json
from pathlib import Path
import time
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

from fixture_history import atomic_write, safe


MAX_BYTES = {'api': 4_000_000, 'preview': 12_000_000, 'source': 12_000_000}
HEADERS = {'content-type', 'content-length', 'retry-after', 'x-request-id', 'x-cache',
           'server', 'etag', 'last-modified', 'cache-control', 'date'}
HOSTS = {'commons.wikimedia.org', 'upload.wikimedia.org', 'thumb.wikimedia.org'}


class StopAcquisition(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def recorded_headers(headers):
    return {name.lower(): value for name, value in headers.items() if name.lower() in HEADERS}


def read_body(response, kind, path):
    content_type = response.headers.get_content_type()
    expected_type = content_type == 'application/json' if kind == 'api' else content_type.startswith('image/')
    if not expected_type:
        raise StopAcquisition(f'Unexpected content type: {content_type}')
    try:
        declared = int(response.headers.get('Content-Length', '0'))
    except ValueError:
        declared = 0
    limit = MAX_BYTES[kind]
    if declared > limit:
        raise StopAcquisition(f'Content-Length {declared} exceeds conservative {kind} limit')
    digest = hashlib.sha256()
    received = 0
    with path.open('wb') as stream:
        while True:
            try:
                chunk = response.read(64 * 1024)
            except IncompleteRead as error:
                if error.partial:
                    stream.write(error.partial)
                raise
            if not chunk:
                break
            stream.write(chunk)
            digest.update(chunk)
            received += len(chunk)
            if received > limit:
                raise StopAcquisition(f'{kind} body exceeded conservative {limit} byte limit')
    if declared and declared != received:
        raise StopAcquisition(f'incomplete HTTP body: declared {declared}, received {received}')
    return received, digest.hexdigest()


class CommonsClient:
    def __init__(self, root, agent, pace, timeout):
        self.root = Path(root).resolve()
        self.agent = agent
        self.pace = pace
        self.timeout = timeout
        self.last = None
        self.opener = build_opener(NoRedirect)

    def fetch(self, url, kind, candidate_id, tmp_path):
        """Make one request. Success returns the partial-file path and recorded headers."""
        parsed = urlparse(url)
        if parsed.scheme != 'https' or parsed.hostname not in HOSTS:
            raise StopAcquisition('Unexpected Wikimedia URL')
        if kind not in MAX_BYTES:
            raise ValueError(f'Unknown Commons request kind: {kind}')
        tmp_path = safe(self.root, Path(tmp_path).relative_to(self.root))
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        if self.last is not None:
            time.sleep(max(0, self.pace - (time.monotonic() - self.last)))
        accept = 'application/json' if kind == 'api' else 'image/*'
        request = Request(url, headers={'User-Agent': self.agent, 'Accept': accept})
        event = dict(utc=datetime.now(timezone.utc).isoformat(), candidate_id=candidate_id,
                     kind=kind, url=url, status=None, response_complete=False,
                     bytes_received=0, headers=None, partial_path=None, user_agent=self.agent)
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                event.update(status=response.status, headers=recorded_headers(response.headers))
                received, sha256 = read_body(response, kind, tmp_path)
            event.update(response_complete=True, bytes_received=received, sha256=sha256)
        except HTTPError as error:
            event.update(status=error.code, headers=recorded_headers(error.headers), error=f'HTTP {error.code}')
            try:
                event['body_excerpt'] = error.read(2048).decode('utf-8', 'replace')
            except Exception as read_error:
                event['body_error'] = str(read_error)
            finally:
                error.close()
        except Exception as error:
            event['error'] = f'{type(error).__name__}: {error}'
        self.last = time.monotonic()
        if 'error' in event and tmp_path.exists():
            event.update(bytes_received=tmp_path.stat().st_size,
                         partial_path=str(tmp_path.relative_to(self.root)))
        log = safe(self.root, 'provenance/http_log.jsonl')
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + '\n')
        if 'error' in event:
            latch = safe(self.root, 'provenance/last_transport_error.json')
            atomic_write(latch, json.dumps(event, ensure_ascii=False, indent=2).encode('utf-8'))
            raise StopAcquisition(f"{candidate_id} {kind} stopped: {event['error']}; no retry")
        return tmp_path, event['headers']
