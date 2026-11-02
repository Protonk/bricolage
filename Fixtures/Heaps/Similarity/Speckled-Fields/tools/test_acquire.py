"""Offline request-stop, cache, and asset boundary checks."""
import io
import json
from email.message import Message
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,MagicMock,patch
from urllib.error import HTTPError
import acquire

class AcquireTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name).resolve()
        self.patch=patch.object(acquire,'ROOT',self.root);self.patch.start()
        (self.root/'provenance').mkdir()
        self.addCleanup(self.patch.stop);self.addCleanup(self.temp.cleanup)
    def test_rate_limit_stops_once_and_latches(self):
        client=acquire.Client('test',3,40);headers=Message();headers['Retry-After']='120'
        client.opener=Mock();client.opener.open.side_effect=HTTPError(acquire.API,429,'limited',headers,io.BytesIO(b'busy'))
        with self.assertRaises(acquire.TransportError):client.request(acquire.API,'api','sf-0001')
        self.assertEqual(client.opener.open.call_count,1)
        record=json.loads((self.root/'provenance/last_transport_error.json').read_text())
        self.assertEqual(record['headers']['retry-after'],'120')
        with self.assertRaises(acquire.TransportError):acquire.Client('test',3,40)
    def test_api_maxlag_is_not_a_missing_file(self):
        client=acquire.Client('test',3,40);client.opener=MagicMock();response=Mock()
        response.status=200;response.headers=Message();response.headers['Content-Type']='application/json'
        response.read.return_value=b'{"error":{"code":"maxlag"}}'
        client.opener.open.return_value.__enter__.return_value=response
        with self.assertRaises(acquire.TransportError):client.request(acquire.API,'api','sf-0001')
        record=json.loads((self.root/'provenance/last_transport_error.json').read_text())
        self.assertEqual(record['status'],200)
        self.assertEqual(record['headers']['content-type'],'application/json')
    def test_metadata_cache_uses_no_network(self):
        p=self.root/'provenance/api/sf-0001-preview.json';p.parent.mkdir()
        p.write_text('{"query":{"pages":[{"pageid":1,"title":"File:X.jpg","imageinfo":[{"width":640,"height":480}]}]}}')
        client=Mock();row={'candidate_id':'sf-0001','commons_title':'File:X.jpg'}
        acquire.get_metadata(client,row,'preview',320);client.request.assert_not_called()
        self.assertEqual(row['commons_pageid'],1)
    def test_paths_and_hosts_restricted(self):
        with self.assertRaises(ValueError):acquire.local('../outside')
        (self.root/'link').symlink_to(self.root.parent,target_is_directory=True)
        with self.assertRaises(ValueError):acquire.local('link/file')
        with self.assertRaises(ValueError):acquire.Client('test',3,40).request('https://example.com/x','image','sf-0001')
    def test_unscaled_url_identity_ignores_tracking_query(self):
        original='https://upload.wikimedia.org/wikipedia/commons/a/ab/image.jpg?utm_content=original'
        unscaled='https://upload.wikimedia.org/wikipedia/commons/a/ab/image.jpg?utm_content=thumbnail_unscaled'
        thumb='https://thumb.wikimedia.org/wikipedia/commons/thumb/a/ab/image.jpg/1920px-image.jpg'
        self.assertTrue(acquire.same_media_url(original,unscaled))
        self.assertFalse(acquire.same_media_url(original,thumb))
    def test_catalog_csv_matches_union_of_fields(self):
        acquire.save_records([{'candidate_id':'sf-0001'},{'candidate_id':'sf-0002','license':'CC0'}])
        import csv
        with (self.root/'provenance/intake/candidates.csv').open() as f:rows=list(csv.DictReader(f))
        self.assertEqual(rows[0]['license'],'');self.assertEqual(rows[1]['license'],'CC0')

if __name__=='__main__':unittest.main()
