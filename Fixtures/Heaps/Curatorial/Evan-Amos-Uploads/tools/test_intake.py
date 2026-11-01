"""Offline checks of exhaustive membership, rights roles, transport promotion and publication."""
import contextlib
import io
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from urllib.parse import urlencode
from PIL import Image
import population as p
import evan as e
import review
import integrate
import audit
import relationships
import transport as t

REJECTS=['File:Reject A.jpg','File:Reject B.jpg','File:Reject C.jpg']


def member(n,title):return dict(pageid=n,ns=6,title=title,timestamp='2026-10-31T00:00:00Z')


class PopulationTests(unittest.TestCase):
    def test_exact_three_rejects_and_all_related_formats_are_included(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'provenance/intake').mkdir(parents=True);(root/'provenance/intake/EXCLUSIONS.txt').write_text('\n'.join(REJECTS)+'\n')
            rows=[member(i,t)for i,t in enumerate(REJECTS+['File:Device-FL.jpg','File:Device-FL.png','File:Device-FR.jpg','File:Reject A.jpg crop.png'],1)]
            with patch.object(p,'ROOT',root):result=p.selection(dict(candidates=p.candidates(rows)))
            self.assertEqual(result['counts'],{'included':4,'excluded_by_user':3})
            self.assertEqual(len(result['decisions']),7)
            self.assertEqual(result['absent_exclusion_titles'],[])
            self.assertNotIn('seed',result)

    def test_changed_population_and_absent_reject_are_reported_without_a_cap(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'provenance/intake').mkdir(parents=True);(root/'provenance/intake/EXCLUSIONS.txt').write_text('\n'.join(REJECTS)+'\n')
            rows=[member(i,f'File:New-{i}.jpg')for i in range(200)]
            with patch.object(p,'ROOT',root):result=p.selection(dict(candidates=p.candidates(rows)))
            self.assertEqual(len(result['included']),200)
            self.assertEqual(result['absent_exclusion_titles'],REJECTS)

    def test_nonfiles_and_duplicate_ids_fail_but_distinct_titles_survive(self):
        with self.assertRaisesRegex(ValueError,'File members'):p.candidates([dict(member(1,'Category:Child'),ns=14)])
        with self.assertRaisesRegex(ValueError,'Repeated category page ID'):p.candidates([member(1,'File:A'),member(1,'File:B')])
        rows=p.candidates([member(1,'File:A.jpg'),member(2,'File:A.png')])
        self.assertNotEqual(rows[0]['candidate_id'],rows[1]['candidate_id'])

    def test_short_category_page_still_requires_continuation_and_exact_query(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();token={'continue':'-||','cmcontinue':'file|B|2'}
            for n,(data,extra)in enumerate([(dict(query={'categorymembers':[member(1,'File:A')]},**{'continue':token}),{}),(dict(query={'categorymembers':[member(2,'File:B')]}),token)],1):
                path=root/f'provenance/api/category-{n:04d}.json';t.dump(path,data)
                url=t.API+'?'+urlencode(dict(action='query',format='json',formatversion=2,maxlag=5,**p.QUERY,**extra))
                t.dump(path.with_suffix('.receipt.json'),dict(status=200,response_complete=True,sha256=t.sha(path),bytes_received=path.stat().st_size,url=url,utc='test'))
            with patch.object(p,'ROOT',root):
                value=p.reconstruct();self.assertEqual(value['actual_count'],2);self.assertEqual(len(value['responses']),2)
                r=root/'provenance/api/category-0002.receipt.json';v=p.read(r);v['url']=v['url'].replace('cmtype=file','cmtype=subcat');t.dump(r,v)
                with self.assertRaisesRegex(ValueError,'API query differs'):p.reconstruct()


class EvidenceTests(unittest.TestCase):
    def test_wikilink_wrappers_do_not_create_invented_related_file_titles(self):
        refs,_=relationships.links('|other versions=[[:file:Device-FL.jpg|Original]]')
        self.assertEqual(refs,['File:Device-FL.jpg'])

    def page(self,artist='Evan-Amos',author='[[User:Evan-Amos|Evan-Amos]]'):
        return dict(pageid=1,title='File:A.jpg',revisions=[dict(slots=dict(main=dict(content='|Author='+author+'\n{{PD-self}}')))],imageinfo=[dict(user='Different uploader',mime='image/jpeg',extmetadata={k:dict(value=v)for k,v in dict(Artist=artist,LicenseShortName='Public domain',Copyrighted='False',Credit='Own work').items()})])

    def test_creator_and_modifier_come_from_author_not_uploader(self):
        page=self.page('Evan-Amos, modified by Gunnar.offel','[[User:Evan-Amos|Evan-Amos]], modified by [[User:Gunnar.offel|Gunnar.offel]]')
        evidence={'a':dict(page=page,metadata_path='metadata',metadata_sha256='hash',redirected=False)}
        with patch.object(e,'evidence',return_value=evidence),patch.object(e,'candidates',return_value={'a':dict(category_pageid=1,frozen_title='File:A.jpg')}):r=review.records()['a']
        self.assertEqual(r['status'],'ready');self.assertEqual(r['original_creator'],'Evan-Amos');self.assertEqual(r['digital_modifier'],'Gunnar.offel');self.assertEqual(r['uploader_current_file_revision'],'Different uploader');self.assertIsNone(r['copyright_holder']);self.assertIsNone(r['license_url'])

    def test_missing_rights_is_blocked_without_becoming_a_selection_exclusion(self):
        page=self.page('Unparsed attribution','Unparsed attribution');page['imageinfo'][0]['extmetadata'].pop('LicenseShortName')
        evidence={'a':dict(page=page,metadata_path='metadata',metadata_sha256='hash',redirected=False)}
        with patch.object(e,'evidence',return_value=evidence),patch.object(e,'candidates',return_value={'a':dict(category_pageid=1,frozen_title='File:A.jpg')}):r=review.records()['a']
        self.assertEqual(r['status'],'blocked');self.assertIsNone(r['original_creator']);self.assertNotIn('decision',r)

    def test_only_older_upload_history_continuation_is_permitted(self):
        page=self.page();page['imageinfo'][0]['timestamp']='2026-01-01T00:00:00Z'
        reply=dict(query=dict(pages=[page]),**{'continue':dict(iistart='2025-01-01T00:00:00Z',**{'continue':'||revisions'})})
        e.current_metadata(reply);reply['continue']['rvcontinue']='missing'
        with self.assertRaisesRegex(ValueError,'Unresolved metadata'):e.current_metadata(reply)

    def media_fixture(self,root,mime='image/svg+xml'):
        t.dump(root/'provenance/rights-review.json',{'a':{'status':'ready'}})
        ii=dict(mime=mime,url='https://upload.wikimedia.org/original.svg',thumburl='https://thumb.wikimedia.org/rendition.png',width=4000,height=3000,thumbwidth=1600,thumbheight=1200,sha1='original',extmetadata={})
        return {'a':dict(page=dict(pageid=1,title='File:A.svg',imageinfo=[ii]),metadata_path='metadata',metadata_sha256='hash')}

    def test_svg_png_alpha_bytes_are_promoted_unchanged_and_cache_is_not_refetched(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();ev=self.media_fixture(root);part=root/'previews/partials/a.part';part.parent.mkdir(parents=True);Image.new('RGBA',(12,8),(0,0,0,30)).save(part,format='PNG');body=part.read_bytes()
            client=Mock();client.fetch.return_value=(part,dict(headers={'content-type':'image/png'}))
            with patch.object(e,'ROOT',root),patch.object(e,'evidence',return_value=ev),patch.object(e,'candidates',return_value={}),patch.object(e,'order',return_value=['a']),patch.object(e,'selection',return_value={'included':['a']}),patch.object(e,'Client',return_value=client),contextlib.redirect_stdout(io.StringIO()):
                e.media(1,1,1600,1);e.media(1,1,1600,1)
            client.fetch.assert_called_once();self.assertEqual((root/'sources/a.png').read_bytes(),body);r=p.read(root/'provenance/source-receipts/a.json');self.assertTrue(r['has_alpha']);self.assertEqual(r['original_mime'],'image/svg+xml')

    def test_oversized_unscaled_original_is_pending_without_download(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();ev=self.media_fixture(root,'image/png');i=ev['a']['page']['imageinfo'][0];i['thumburl']=i['url'];client=Mock()
            with patch.object(e,'ROOT',root),patch.object(e,'evidence',return_value=ev),patch.object(e,'candidates',return_value={}),patch.object(e,'order',return_value=['a']),patch.object(e,'selection',return_value={'included':['a']}),patch.object(e,'Client',return_value=client),contextlib.redirect_stdout(io.StringIO()):e.media(1,1,1600,1)
            client.fetch.assert_not_called();self.assertTrue((root/'provenance/unavailable/a-1600.json').exists());self.assertFalse((root/'provenance/source-receipts/a.json').exists())

    def test_bounded_raster_original_must_match_api_original_sha1(self):
        for correct in (True,False):
            with self.subTest(correct=correct),tempfile.TemporaryDirectory()as temp:
                root=Path(temp).resolve();ev=self.media_fixture(root,'image/png');ii=ev['a']['page']['imageinfo'][0]
                part=root/'previews/partials/a.part';part.parent.mkdir(parents=True);Image.new('RGB',(12,8)).save(part,format='PNG')
                ii.update(width=12,height=8,url='https://upload.wikimedia.org/a.png',thumburl='https://upload.wikimedia.org/a.png',sha1=hashlib.sha1(part.read_bytes()).hexdigest()if correct else'wrong')
                client=t.Client(root);client.fetch=Mock(return_value=(part,dict(headers={'content-type':'image/png'})))
                with patch.object(e,'ROOT',root),patch.object(e,'evidence',return_value=ev),patch.object(e,'candidates',return_value={}),patch.object(e,'order',return_value=['a']),patch.object(e,'selection',return_value={'included':['a']}),patch.object(e,'Client',return_value=client),contextlib.redirect_stdout(io.StringIO()):
                    if correct:e.media(1,1,1600,1)
                    else:
                        with self.assertRaisesRegex(t.StopAcquisition,'SHA-1 differs'):e.media(1,1,1600,1)
                self.assertEqual((root/'provenance/source-receipts/a.json').exists(),correct)
                self.assertEqual(part.exists(),not correct)

    def test_failed_decode_retains_body_and_latches(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();ev=self.media_fixture(root);part=root/'previews/partials/a.part';part.parent.mkdir(parents=True);part.write_bytes(b'not-image');client=t.Client(root);client.fetch=Mock(return_value=(part,dict(headers={})))
            with patch.object(e,'ROOT',root),patch.object(e,'evidence',return_value=ev),patch.object(e,'candidates',return_value={}),patch.object(e,'order',return_value=['a']),patch.object(e,'selection',return_value={'included':['a']}),patch.object(e,'Client',return_value=client),self.assertRaises(t.StopAcquisition):e.media(1,1,1600,1)
            self.assertEqual(part.read_bytes(),b'not-image');self.assertTrue((root/'provenance/last_transport_error.json').exists())

    def test_excluded_identity_never_downloaded(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp).resolve();t.dump(root/'provenance/rights-review.json',{});client=Mock()
            with patch.object(e,'ROOT',root),patch.object(e,'evidence',return_value={}),patch.object(e,'candidates',return_value={}),patch.object(e,'order',return_value=['rejected']),patch.object(e,'selection',return_value={'included':[]}),patch.object(e,'Client',return_value=client):e.media(1,1,1600,1)
            client.fetch.assert_not_called()


class PublicationTests(unittest.TestCase):
    def test_same_hash_and_related_views_are_not_deduplicated_or_paired(self):
        base=dict(width=16,height=12,exif_orientation=1,format='PNG',sha256='same-bytes',canonical_title='File:Device',frozen_title='File:Device',reported_artist='Same creator',license='Public domain',source_url='url',requested_edge=1600,rendition='api_returned_rendition')
        rows,sources=integrate.records([dict(**base,final_file=f'images/{c}.png',source_path=f'sources/{c}.png',family_id=c)for c in('a','b')])
        self.assertEqual(len(rows),2);self.assertEqual(len(sources),2);self.assertTrue(all(r['scene_id']==''and r['relation_kind']=='curatorial_selected'for r in rows));self.assertNotEqual(rows[0]['family_id'],rows[1]['family_id'])

    def test_existing_publication_is_never_silently_replaced(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);(root/'manifest.json').write_text('old publication')
            with patch.object(e,'ROOT',root),self.assertRaisesRegex(ValueError,'Publication exists'):integrate.build()
            self.assertEqual((root/'manifest.json').read_text(),'old publication')

    def test_pending_transfer_prevents_complete_even_with_included_membership(self):
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);t.dump(root/'provenance/rights-review.json',{'a':dict(status='ready',original_creator=None,digital_modifier=None,copyright_holder=None,uploader_current_file_revision=None)})
            with patch.object(e,'ROOT',root),patch.object(e,'selection',return_value=dict(included=['a'],counts={'excluded_by_user':0},absent_exclusion_titles=[])),patch.object(e,'order',return_value=['a']),patch.object(e,'candidates',return_value={'a':dict(frozen_title='File:A',category_pageid=1)}),patch.object(e,'evidence',return_value={'a':dict(page={'pageid':1},redirected=False)}),patch.object(integrate,'imports',return_value=[]):result=integrate.summary()
            self.assertEqual(result['status'],'partial');self.assertEqual(result['included'],1);self.assertEqual(result['pending'],1)

    def test_prior_overlap_is_reported_and_kept(self):
        with tempfile.TemporaryDirectory()as temp:
            fixtures=Path(temp).resolve()/'Fixtures';root=fixtures/'Heaps/Curatorial/Evan-Amos-Uploads';root.mkdir(parents=True);prior=fixtures/'Heaps/Similarity/Test';t.dump(prior/'manifest.json',{'images':[dict(file='images/a.jpg',byte_sha256='hash')]});(prior/'sources.csv').write_text('source_filename,source_sha256,subject,original_path,source_url\na.jpg,hash,File:A.jpg,,\n')
            with patch.object(e,'ROOT',root),patch.object(e,'selection',return_value={'included':['a']}),patch.object(e,'candidates',return_value={'a':dict(frozen_title='File:A.jpg',category_pageid=1)}),patch.object(e,'evidence',return_value={}):result=audit.audit()
            self.assertEqual(result['status'],'reported');self.assertTrue(result['included_overlaps']);self.assertNotIn('blocking_collisions',result)


if __name__=='__main__':unittest.main()
