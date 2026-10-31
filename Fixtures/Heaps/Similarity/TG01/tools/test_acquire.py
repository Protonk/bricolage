"""Offline checks for transport stops, partial evidence, API errors and caching."""
import io,json,tempfile,unittest
from pathlib import Path
from email.message import Message
from unittest.mock import MagicMock,Mock,patch
from urllib.error import HTTPError
import acquire,common

class AcquisitionTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name).resolve()
        for module in (acquire,common):
            p=patch.object(module,'ROOT',self.root);p.start();self.addCleanup(p.stop)
    def client(self):
        c=acquire.Client('test',3,40);c.opener=MagicMock();return c
    def response(self):
        r=Mock();r.status=200;r.headers=Message();r.headers['Content-Type']='image/jpeg';return r
    def test_body_timeout_keeps_status_and_partial(self):
        c=self.client();r=self.response();r.read.side_effect=[b'known bytes',TimeoutError('read timed out')]
        c.opener.open.return_value.__enter__.return_value=r
        p=self.root/'previews/partials/test.part'
        with self.assertRaises(acquire.StopAcquisition):c.fetch(acquire.API,'preview','ps-0001',p)
        event=json.loads((self.root/'provenance/last_transport_error.json').read_text())
        self.assertEqual(event['status'],200);self.assertFalse(event['response_complete'])
        self.assertEqual(event['bytes_received'],11);self.assertEqual(p.read_bytes(),b'known bytes')
        self.assertEqual(c.opener.open.call_count,1)
    def test_rate_limit_does_not_retry(self):
        c=self.client();headers=Message();headers['Retry-After']='120'
        c.opener.open.side_effect=HTTPError(acquire.API,429,'limited',headers,io.BytesIO(b'busy'))
        with self.assertRaises(acquire.StopAcquisition):c.fetch(acquire.API,'api','ps-0001',self.root/'provenance/partials/test.part')
        event=json.loads((self.root/'provenance/last_transport_error.json').read_text())
        self.assertEqual(event['status'],429);self.assertEqual(event['headers']['retry-after'],'120')
        self.assertEqual(c.opener.open.call_count,1)
    def test_api_error_is_not_missing_image(self):
        p=self.root/'provenance/api/ps-0001-preview.json';p.parent.mkdir(parents=True);p.write_text('{"error":{"code":"maxlag"}}')
        c=Mock()
        with self.assertRaises(acquire.StopAcquisition):acquire.metadata(c,{'candidate_id':'ps-0001'},'preview',320)
        c.fetch.assert_not_called()
    def test_cached_metadata_and_unscaled_identity(self):
        p=self.root/'provenance/api/ps-0001-preview.json';p.parent.mkdir(parents=True)
        ii=dict(url='https://upload.wikimedia.org/a.jpg?utm_content=original',thumburl='https://upload.wikimedia.org/a.jpg?utm_content=thumbnail_unscaled',width=300,height=200,sha1='abc')
        p.write_text(json.dumps({'query':{'pages':[{'pageid':42,'title':'File:A.jpg','imageinfo':[ii]}]}}))
        c=Mock();r={'candidate_id':'ps-0001','commons_title':'File:A.jpg'}
        result=acquire.metadata(c,r,'preview',320)
        c.fetch.assert_not_called();self.assertEqual(result[1],'api_reported_unscaled_original');self.assertEqual(r['commons_pageid'],42)
    def test_smaller_source_request_uses_distinct_cache(self):
        folder=self.root/'provenance/api';folder.mkdir(parents=True)
        original='https://upload.wikimedia.org/a.jpg?utm_content=original'
        base=dict(width=1601,height=1060,url=original,thumburl=original,sha1='abc')
        def write(name,info):
            (folder/name).write_text(json.dumps({'query':{'pages':[{'pageid':42,'title':'File:A.jpg','imageinfo':[info]}]}}))
        write('ps-0001-source.json',base)
        write('ps-0001-source-1280.json',dict(base,thumburl='https://thumb.wikimedia.org/1280-a.jpg',thumbwidth=1280,thumbheight=847))
        c=Mock();r={'candidate_id':'ps-0001','commons_title':'File:A.jpg'}
        self.assertIsNone(acquire.metadata(c,r,'source',1600))
        self.assertEqual(acquire.metadata(c,r,'source',1280)[1],'api_returned_rendition')
        self.assertEqual(r['source_requested_max_edge'],1280);c.fetch.assert_not_called()
    def test_paths_and_hosts_restricted(self):
        with self.assertRaises(ValueError):common.local('../out')
        c=self.client()
        with self.assertRaises(acquire.StopAcquisition):c.fetch('https://example.com','source','ps-0001',self.root/'previews/x')
        c.opener.open.assert_not_called()

if __name__=='__main__':unittest.main()
