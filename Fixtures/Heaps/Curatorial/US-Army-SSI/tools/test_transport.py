"""Offline tests of the SSI transport adapted from active POTY tests."""
import io
import json
from email.message import Message
from http.client import IncompleteRead
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import population
import transport


class TransportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve() / 'Fixtures/Heaps/Curatorial/US-Army-SSI'
        self.root.mkdir(parents=True)
        self.client = transport.Client(self.root)
        self.client.opener = Mock()
        sleeper = patch.object(transport.time, 'sleep')
        sleeper.start()
        self.addCleanup(sleeper.stop)

    def response(self, content_type='image/jpeg'):
        response = Mock(status=200)
        response.headers = Message()
        response.headers['Content-Type'] = content_type
        self.client.opener.open.return_value.__enter__ = Mock(return_value=response)
        self.client.opener.open.return_value.__exit__ = Mock(return_value=False)
        return response

    def test_timeout_after_headers_preserves_bytes_and_latches(self):
        response = self.response()
        response.read.side_effect = [b'partial body', TimeoutError('body timeout')]
        with self.assertRaises(transport.StopAcquisition):
            self.client.fetch(transport.API, 'source', 'abc', 'previews/partials/abc.part')
        event = population.read(self.root / 'provenance/last_transport_error.json')
        self.assertEqual(event['status'], 200)
        self.assertFalse(event['response_complete'])
        self.assertEqual(event['bytes_received'], 12)
        self.assertEqual((self.root / event['partial_path']).read_bytes(), b'partial body')
        with self.assertRaises(transport.StopAcquisition):
            self.client.fetch(transport.API, 'source', 'next', 'previews/partials/next.part')
        self.assertEqual(self.client.opener.open.call_count, 1)

    def test_incomplete_read_retains_exception_body(self):
        response = self.response()
        response.read.side_effect = [b'prefix', IncompleteRead(b'tail', 10)]
        with self.assertRaises(transport.StopAcquisition):
            self.client.fetch(transport.API, 'source', 'abc', 'previews/partials/abc.part')
        self.assertEqual((self.root / 'previews/partials/abc.part').read_bytes(), b'prefixtail')

    def test_rate_limit_has_no_retry(self):
        headers = Message()
        headers['Retry-After'] = '120'
        self.client.opener.open.side_effect = HTTPError(transport.API, 429, 'busy', headers, io.BytesIO(b'busy'))
        with self.assertRaises(transport.StopAcquisition):
            self.client.fetch(transport.API, 'api', 'abc', 'provenance/partials/abc.part')
        event = population.read(self.root / 'provenance/last_transport_error.json')
        self.assertEqual(event['headers']['retry-after'], '120')
        self.assertEqual(self.client.opener.open.call_count, 1)

    def test_api_error_is_a_stop_not_an_empty_population(self):
        response = self.response('application/json')
        response.read.side_effect = [b'{"error":{"code":"maxlag"}}', b'']
        with self.assertRaises(transport.StopAcquisition):
            self.client.api('bad', titles='Example')
        self.assertTrue((self.root / 'provenance/api/bad.json').exists())
        self.assertTrue((self.root / 'provenance/last_transport_error.json').exists())

    def test_cached_query_and_hash_are_bound(self):
        response = self.response('application/json')
        response.read.side_effect = [b'{"query":{"pages":[]}}', b'']
        expected = self.client.api('test', titles='Example')
        self.assertEqual(self.client.api('test', titles='Example'), expected)
        self.assertEqual(self.client.opener.open.call_count, 1)
        with self.assertRaises(transport.StopAcquisition):
            self.client.api('test', titles='Different')
        (self.root / 'provenance/api/test.json').write_text('{}')
        with self.assertRaises(transport.StopAcquisition):
            self.client.api('test', titles='Example')

    def test_paths_hosts_and_retained_partials_are_protected(self):
        with self.assertRaises(ValueError):
            transport.safe(self.root, '../escape')
        with self.assertRaises(transport.StopAcquisition):
            self.client.fetch('https://example.com/a', 'source', 'abc', 'previews/abc')
        partial = self.root / 'previews/partials/abc.part'
        partial.parent.mkdir(parents=True)
        partial.write_bytes(b'evidence')
        with self.assertRaises(transport.StopAcquisition):
            self.client.fetch(transport.API, 'source', 'abc', 'previews/partials/abc.part')
        self.client.opener.open.assert_not_called()

    def test_explicit_acknowledgement_preserves_failure_and_allows_new_request(self):
        response = self.response()
        response.read.side_effect = [b'partial', TimeoutError('interrupted')]
        with self.assertRaises(transport.StopAcquisition):
            self.client.fetch(transport.API, 'preview', 'a', 'previews/partials/a.part')
        with self.assertRaises(ValueError):
            self.client.acknowledge(' ')
        self.assertTrue((self.root / 'provenance/last_transport_error.json').exists())
        self.client.acknowledge('Inspected the preserved incomplete body; make a separate explicit request.')
        self.assertEqual((self.root / 'previews/partials/a.part').read_bytes(), b'partial')
        self.assertEqual(self.client.opener.open.call_count, 1)
        event = json.loads((self.root / 'provenance/error_acknowledgements.jsonl').read_text())
        self.assertEqual(event['failure']['bytes_received'], 7)
        response.read.side_effect = [b'complete', b'']
        path, receipt = self.client.fetch(transport.API, 'preview', 'b', 'previews/partials/b.part')
        self.assertEqual(path.read_bytes(), b'complete')
        self.assertTrue(receipt['response_complete'])
        self.assertEqual(self.client.opener.open.call_count, 2)
