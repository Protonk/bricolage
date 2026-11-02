"""Offline checks for the downloader's failure and cache boundaries."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch
import urllib.error
from email.message import Message

spec=importlib.util.spec_from_file_location('commons',Path(__file__).with_name('commons.py'))
commons=importlib.util.module_from_spec(spec); spec.loader.exec_module(commons)


class CommonsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name).resolve()
        self.patch=patch.object(commons,'ROOT',self.root); self.patch.start()
        self.addCleanup(self.patch.stop); self.addCleanup(self.temp.cleanup)

    def test_rate_limit_is_one_attempt_and_persistent_stop(self):
        client=commons.Client(); headers=Message(); headers['Retry-After']='120'
        client.opener=Mock(); client.opener.open.side_effect=urllib.error.HTTPError(commons.API,429,'limited',headers,io.BytesIO(b'busy'))
        with self.assertRaisesRegex(RuntimeError,'no automatic retries'):
            client.get(commons.API,'application/json')
        self.assertEqual(client.opener.open.call_count,1)
        failure=json.loads((self.root/'provenance/STOP.json').read_text())
        self.assertEqual(failure['retry_after'],'120'); self.assertEqual(failure['status'],429)
        with self.assertRaisesRegex(ValueError,'Acquisition stopped'): commons.Client()

    def test_cached_metadata_does_not_make_request(self):
        candidate={'candidate_id':'rg-0001','commons_title':'File:example.jpg'}
        commons.save('provenance/commons/rg-0001-320.json',{'response':{'query':{}}})
        client=Mock(); result=commons.metadata(client,candidate,320)
        client.get.assert_not_called(); self.assertIn('query',result['response'])

    def test_outside_urls_and_paths_rejected(self):
        with self.assertRaises(ValueError): commons.path('../escape')
        with self.assertRaises(ValueError): commons.Client().get('https://example.com/x','image/*')
        (self.root/'linked').symlink_to(self.root.parent,target_is_directory=True)
        with self.assertRaises(ValueError): commons.path('linked/elsewhere')

    def test_oversized_original_never_downloaded(self):
        candidate={'candidate_id':'rg-0001','commons_title':'File:example.jpg'}
        info={'url':'https://upload.wikimedia.org/original.jpg','width':10000,'height':10000,'size':1000,'mime':'image/jpeg','mediatype':'BITMAP','extmetadata':{'Artist':{'value':'Creator'},'LicenseShortName':{'value':'CC0'}}}
        with patch.object(commons,'metadata',return_value={'response':{'query':{'pages':[{'imageinfo':[info]}]}}}):
            client=Mock(); result=commons.acquire(client,candidate,320,True)
            self.assertEqual(result['status'],'no_bounded_rendition'); client.get.assert_not_called()

    def test_api_error_stops_without_retry(self):
        client=commons.Client(); response=Mock(); response.status=200; response.url=commons.API
        headers=Message(); headers['Content-Type']='application/json'; response.headers=headers
        response.read.return_value=b'{"error":{"code":"maxlag"}}'
        client.opener=MagicMock(); client.opener.open.return_value.__enter__.return_value=response
        with self.assertRaises(RuntimeError):client.get(commons.API,'application/json')
        self.assertEqual(client.opener.open.call_count,1)
        self.assertTrue((self.root/'provenance/STOP.json').is_file())


if __name__=='__main__':unittest.main()
