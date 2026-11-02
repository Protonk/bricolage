"""BSP01's explicit larger preview request preserves the prior evidence and bounds."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from PIL import Image
import acquire
import common

class PreviewSizeTests(unittest.TestCase):
    def test_explicit_size_has_separate_metadata_cache(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve()
            folder=root/'provenance/api';folder.mkdir(parents=True)
            old=folder/'bsp-0023-preview.json';old.write_text('{"error":{"code":"old-evidence"}}')
            ii={'url':'https://upload.wikimedia.org/a.jpg','thumburl':'https://thumb.wikimedia.org/330-a.jpg','width':1816,'height':4032,'sha1':'abc'}
            larger=folder/'bsp-0023-preview-640.json'
            larger.write_text(json.dumps({'query':{'pages':[{'pageid':42,'title':'File:A.jpg','imageinfo':[ii]}]}}))
            row={'candidate_id':'bsp-0023','commons_title':'File:A.jpg'};client=Mock()
            with patch.object(acquire,'ROOT',root),patch.object(common,'ROOT',root):
                acquire.metadata(client,row,'preview',640)
            self.assertEqual(row['api_preview_metadata_path'],'provenance/api/bsp-0023-preview-640.json')
            self.assertEqual(row['preview_requested_max_edge'],640)
            self.assertEqual(old.read_text(),'{"error":{"code":"old-evidence"}}')
            client.fetch.assert_not_called()

    def test_decode_size_guard_remains(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'preview.jpg';Image.new('RGB',(250,555)).save(p)
            with self.assertRaises(acquire.StopAcquisition):acquire.validate_media(p,320)
            self.assertEqual(acquire.validate_media(p,640)[:2],(250,555))
            Image.new('RGB',(250,961)).save(p)
            with self.assertRaises(acquire.StopAcquisition):acquire.validate_media(p,640)

if __name__=='__main__':unittest.main()
