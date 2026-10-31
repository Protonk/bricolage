"""Checks for botanical provenance failures and source-artwork relationships."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from PIL import Image
import botanical as b
import integrate
import relationships
import transport


class EvidenceTests(unittest.TestCase):
    def test_current_file_metadata_allows_only_older_upload_history_continuation(self):
        page = dict(imageinfo=[dict(timestamp='2020-01-02T00:00:00Z')],
                    revisions=[dict(slots=dict(main=dict(content='File-specific rights')))])
        reply = dict(query=dict(pages=[page]),
                     **{'continue': dict(iistart='2019-01-01T00:00:00Z', **{'continue': '||revisions'})})
        integrate.check_current_metadata(reply)
        reply['continue']['rvcontinue'] = 'unretrieved-page-evidence'
        with self.assertRaisesRegex(ValueError, 'Unresolved metadata continuation'):
            integrate.check_current_metadata(reply)
        del reply['continue']['rvcontinue']
        page['revisions'] = []
        with self.assertRaisesRegex(ValueError, 'Missing current'):
            integrate.check_current_metadata(reply)

    def test_incomplete_body_remains_evidence_after_explicit_acknowledgement(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            part = root / 'previews/partials/a.part'
            part.parent.mkdir(parents=True)
            part.write_bytes(b'incomplete')
            failure = dict(error='timeout', response_complete=False,
                           partial_path='previews/partials/a.part',
                           partial_sha256=transport.sha(part), bytes_received=10)
            transport.append(root / 'provenance/http_log.jsonl', failure)
            transport.append(root / 'provenance/error_acknowledgements.jsonl',
                             dict(failure=failure, diagnosis='Retain pending; no retry'))
            integrate.check_diagnostics(root)
            part.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'Diagnostic body changed'):
                integrate.check_diagnostics(root)

    def test_alternate_crop_links_preserve_identity_without_expected_pairs(self):
        refs, passages = relationships.links('|other_versions={{Image extracted|1=Plant (crop).jpg}}')
        self.assertEqual(refs, ['File:Plant (crop).jpg'])
        self.assertTrue(passages)
        with patch.object(relationships, 'evidence', return_value=[dict(candidate_id='a', linked_inventory_candidates=['b'])]):
            with self.assertRaisesRegex(ValueError, 'alternate-file'):
                relationships.check_selected(['a', 'b'])
            relationships.check_selected(['a'])

    def test_html_credit_cleanup_retains_text_and_not_styles(self):
        self.assertEqual(b.clean('<style>.x{color:red}</style><b>Library</b> &amp; author'), 'Library & author')
        self.assertIsNone(b.clean(None))

    def test_unknown_artist_not_replaced_by_repository_or_uploader(self):
        review = dict(work_key='one', work_basis='plate identity', metadata_path='evidence', metadata_sha256='evidencehash',
                      reported_artist='Digital library', original_artist=None, engraver_lithographer=None,
                      publisher=None, digitizer='Digital library', creator_basis='Library is digital source only',
                      uploader_current_file_revision='Uploader', credit='Library', license='Public domain',
                      license_url=None, restrictions=None, rights_basis='Retained file-specific public-domain claim')
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            transport.dump(root / 'provenance/work-review.json', {'a': review})
            transport.dump(root / 'provenance/source-receipts/a.json', {'path':'sources/a.png','candidate_id':'a'})
            ev = {'a': dict(page=dict(title='File:A', revisions=[{'revid':1}], imageinfo=[{'timestamp':'date'}]))}
            with patch.object(b, 'ROOT', root), patch.object(b, 'candidates', return_value={'a':dict(frozen_title='File:A',petscan_pageid=1)}), patch.object(b, 'evidence', return_value=ev), patch.object(b, 'selection', return_value={'selected':['a']}):
                row = integrate.imports()[0]
            self.assertIsNone(row['original_artist'])
            self.assertEqual(row['uploader_current_file_revision'], 'Uploader')
            self.assertEqual(row['digitizer'], 'Digital library')

    def test_multipage_document_is_not_rendered_as_an_arbitrary_plate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ev = {'a':dict(page=dict(title='File:Book.pdf',imageinfo=[dict(mime='application/pdf',url='https://upload.wikimedia.org/book.pdf')]),metadata_path='provenance/api/test.json')}
            client = Mock()
            with patch.object(b,'ROOT',root), patch.object(b,'order',return_value=['a']), patch.object(b,'evidence',return_value=ev), patch.object(b,'Client',return_value=client), contextlib.redirect_stdout(io.StringIO()):
                b.media('preview',1,1,480,1)
            client.fetch.assert_not_called()
            self.assertTrue((root/'provenance/unavailable/a-preview-480.json').exists())

    def test_failed_decode_keeps_complete_body_and_blocks_future_fetch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            part=root/'previews/partials/a.part';part.parent.mkdir(parents=True);part.write_bytes(b'not an image')
            ev={'a':dict(page=dict(title='File:A.png',imageinfo=[dict(mime='image/png',url='https://upload.wikimedia.org/a.png',width=2,height=2)]),metadata_path='evidence')}
            client=transport.Client(root);client.fetch=Mock(return_value=(part,{'headers':{'content-type':'image/png'}}))
            with patch.object(b,'ROOT',root),patch.object(b,'order',return_value=['a']),patch.object(b,'evidence',return_value=ev),patch.object(b,'Client',return_value=client),self.assertRaises(transport.StopAcquisition):
                b.media('preview',1,1,480,1)
            self.assertEqual(part.read_bytes(),b'not an image')
            stop=b.read(root/'provenance/last_transport_error.json')
            self.assertTrue(stop['response_complete'])
            with self.assertRaises(transport.StopAcquisition):
                transport.Client(root).fetch(transport.API,'source','b','previews/partials/b.part')

    def test_completed_media_is_not_redownloaded_and_changed_bytes_latch(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();p=root/'previews/tiles/a.png';p.parent.mkdir(parents=True);Image.new('RGBA',(2,2)).save(p)
            transport.dump(root/'provenance/preview-receipts/a.json',dict(path='previews/tiles/a.png',sha256=transport.sha(p)))
            client=transport.Client(root);client.fetch=Mock()
            with patch.object(b,'ROOT',root),patch.object(b,'order',return_value=['a']),patch.object(b,'evidence',return_value={}),patch.object(b,'Client',return_value=client):
                b.media('preview',1,1,480,1)
                client.fetch.assert_not_called()
                p.write_bytes(b'changed')
                with self.assertRaises(transport.StopAcquisition):b.media('preview',1,1,480,1)
            self.assertTrue((root/'provenance/last_transport_error.json').exists())


    def test_identical_api_url_reuses_validated_preview_bytes_for_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();path=root/'previews/tiles/a.png';path.parent.mkdir(parents=True)
            Image.new('RGBA',(16,12),(20,30,40,90)).save(path)
            url='https://upload.wikimedia.org/a.png';digest=transport.sha(path)
            event=dict(status=200,response_complete=True,sha256=digest,bytes_received=path.stat().st_size,url=url,headers={'content-type':'image/png'})
            transport.dump(root/'provenance/preview-receipts/a.json',dict(path='previews/tiles/a.png',url=url,sha256=digest,response=event))
            ii=dict(mime='image/png',url=url,thumburl=url,width=16,height=12,sha1='upstream',extmetadata={})
            ev={'a':dict(page=dict(pageid=1,title='File:A.png',imageinfo=[ii]),metadata_path='api',metadata_sha256='hash')}
            client=Mock()
            with patch.object(b,'ROOT',root),patch.object(b,'order',return_value=['a']),patch.object(b,'evidence',return_value=ev),patch.object(b,'selection',return_value={'selected':['a']}),patch.object(b,'Client',return_value=client),contextlib.redirect_stdout(io.StringIO()):
                b.media('source',1,1,1600,1)
            client.fetch.assert_not_called()
            self.assertEqual(path.read_bytes(),(root/'sources/a.png').read_bytes())
            receipt=b.read(root/'provenance/source-receipts/a.json')
            self.assertEqual(receipt['response'],event)
            self.assertEqual(receipt['reused_preview_receipt'],'provenance/preview-receipts/a.json')
            self.assertTrue(receipt['has_alpha'])


if __name__ == '__main__':
    unittest.main()
