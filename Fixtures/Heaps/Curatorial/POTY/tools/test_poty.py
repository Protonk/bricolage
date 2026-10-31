"""Offline mechanics: transport stops, provenance roles, replay and nested leaves."""
import io
import json
from email.message import Message
from http.client import IncompleteRead
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

import poty
import review
import transport


class TransportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve() / 'Fixtures/Heaps/Curatorial/POTY/Arthropods'
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
        event = poty.read(self.root / 'provenance/last_transport_error.json')
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
        event = poty.read(self.root / 'provenance/last_transport_error.json')
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


class SelectionTests(unittest.TestCase):
    def test_creator_is_original_not_linked_editor(self):
        artist = '<ul><li><b>Original: </b> Anton Gutmann</li>\n<li><b>Derivative work: </b><a href="//commons.wikimedia.org/wiki/User:Radomianin">Radomianin</a></li></ul>'
        self.assertEqual(review.creator_identity(artist)[0], ['name:anton gutmann'])
        self.assertEqual(review.creator_identity('Unknown author')[0], [])

    def test_known_other_versions_are_exclusion_links(self):
        keys, passages = review.relationships('|other versions=<gallery>\nRelated.jpg|Other capture\n</gallery>\n}}', 'File:Original.jpg')
        self.assertIn('asset:related.jpg', keys)
        self.assertIn('asset:original.jpg', keys)
        self.assertTrue(passages)

    def test_order_does_not_depend_on_inventory_iteration(self):
        rows = [{'candidate_id': cid} for cid in ('a', 'b', 'c')]
        self.assertEqual(poty.ordering(rows, 'Arthropods'), poty.ordering(list(reversed(rows)), 'Arthropods'))
        self.assertEqual(set(poty.ordering(rows, 'Arthropods')), {'a', 'b', 'c'})

    def test_replacements_creator_cap_duplicates_relationships_and_unknowns(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            ids = ['a', 'b', 'c', 'd', 'e', 'f', 'g']
            transport.dump(root / 'inventory.json', dict(official_category='Arthropods', candidates=[dict(candidate_id=cid) for cid in ids]))
            ev = [dict(candidate_id=cid, pageid=i + 1, original_sha1=f'hash{i}', license='CC0', published_uploader='Same uploader') for i, cid in enumerate(ids)]
            ev[2]['original_sha1'] = ev[0]['original_sha1']
            decisions = {cid: dict(creator_keys=[], relationship_keys=[], exclude_reason=None) for cid in ids}
            decisions['a']['creator_keys'] = ['original photographer']
            decisions['b']['creator_keys'] = ['original photographer']
            decisions['a']['relationship_keys'] = ['known sequence']
            decisions['d']['relationship_keys'] = ['known sequence']
            decisions['e']['exclude_reason'] = 'unsupported_media_type'
            transport.dump(root / 'provenance/provenance-review.json', decisions)
            with patch.object(poty, 'ordering', return_value=ids), patch.object(poty, 'review_rows', return_value=ev):
                result = poty.choose(root)
            self.assertEqual(result['selected'], ['a', 'f', 'g'])
            reasons = {r['candidate_id']: r['reason'] for r in result['decisions']}
            self.assertEqual(reasons['b'], 'creator_already_selected')
            self.assertEqual(reasons['c'], 'duplicate_asset')
            self.assertEqual(reasons['d'], 'known_related_capture_or_crop')
            # Unknown creators remain separate; the shared uploader is never a creator key.
            self.assertEqual(result['counts'], {'selected': 3, 'excluded': 4})


if __name__ == '__main__':
    unittest.main()
