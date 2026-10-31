"""SSI-specific offline population, selection, rendition and diagnostic checks."""
import contextlib,copy,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
from email.message import Message
from urllib.error import HTTPError
from PIL import Image
import population,ssi,transport

class PopulationTests(unittest.TestCase):
 def data(self):return {'n':'result','*':[{'a':{'*':[dict(id=1,title='A_B.svg',namespace=6,nstext='File',extra='retained')]}}]}
 def test_raw_fields_and_frozen_title_preserved(self):
  data=self.data();rows=population.rows_from_export(data);c=population.candidates(rows)[0]
  self.assertEqual(c['raw_row'],rows[0]);self.assertEqual(c['frozen_title'],'File:A_B.svg')
  self.assertNotEqual(c['candidate_id'],population.candidates([dict(rows[0],title='A B.svg')])[0]['candidate_id'])
 def test_duplicates_and_nonfile_namespace_refused(self):
  data=self.data();data['*'][0]['a']['*']*=2
  with self.assertRaisesRegex(ValueError,'Repeated'):population.rows_from_export(data)
  data=self.data();data['*'][0]['a']['*'][0]['namespace']=14
  with self.assertRaisesRegex(ValueError,'File namespace'):population.rows_from_export(data)
 def test_order_independent_of_export_sequence(self):
  rows=population.candidates([dict(id=i,title=f'File{i}',namespace=6,nstext='File') for i in range(10)])
  self.assertEqual(population.ordering(rows),population.ordering(list(reversed(rows))))

class SelectionTests(unittest.TestCase):
 def run_selection(self,reviews):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);(root/'provenance').mkdir();transport.dump(root/'provenance/design-review.json',reviews);transport.dump(root/'ordering.json',{'seed':'test'});transport.dump(root/'inventory.json',{'snapshot_sha256':'test'})
   ev={c:dict(page=dict(pageid=n,imageinfo=[{'sha1':c}])) for n,c in enumerate(['a','b','c'],1)}
   with patch.object(ssi,'ROOT',root),patch.object(ssi,'order',return_value=['a','b','c']),patch.object(ssi,'evidence',return_value=ev):return ssi.selection()
 def eligible(self,key):return dict(decision='eligible',design_key=key,design_basis='reviewed design',rights_basis='file-specific review',original_creator='US Army')
 def test_design_repeat_excluded_but_shared_creator_allowed(self):
  result=self.run_selection({'a':self.eligible('one'),'b':self.eligible('one'),'c':self.eligible('two')})
  self.assertEqual(result['selected'],['a','c']);self.assertEqual(result['decisions'][1]['reason'],'design_already_selected');self.assertEqual(result['decisions'][1]['conflicts_with'],['a'])
 def test_unresolved_earlier_rank_blocks_later_acceptance(self):
  result=self.run_selection({'a':self.eligible('one'),'c':self.eligible('two')})
  self.assertEqual(result['selected'],['a']);self.assertEqual(result['decisions'][2]['reason'],'earlier_candidate_pending')

class RenditionTests(unittest.TestCase):
 def rendition(self,original_mime):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);part=root/'previews/partials/pilot.part';part.parent.mkdir(parents=True)
   Image.new('RGBA',(16,12),(20,30,40,90)).save(part,format='PNG');original_bytes=part.read_bytes();original_url='https://upload.wikimedia.org/original.'+('svg' if original_mime=='image/svg+xml' else 'png');url='https://thumb.wikimedia.org/api-returned.png' if original_mime=='image/svg+xml' else original_url
   ii=dict(mime=original_mime,url=original_url,thumburl=url,width=16,height=12,thumbwidth=16,thumbheight=12,sha1='upstream-sha1');ev={'a':dict(page=dict(pageid=42,title='File:Original',imageinfo=[ii]),metadata_path='provenance/api/pilot.json',metadata_sha256='metadata-hash')}
   client=Mock();client.fetch.return_value=(part,{'headers':{'content-type':'image/png'}})
   with patch.object(ssi,'ROOT',root),patch.object(ssi,'order',return_value=['a']),patch.object(ssi,'evidence',return_value=ev),patch.object(ssi,'Client',return_value=client),contextlib.redirect_stdout(io.StringIO()):ssi.media('preview',1,1,480,1)
   rec=ssi.read(root/'provenance/preview-receipts/a.json');self.assertEqual(rec['original_mime'],original_mime);self.assertEqual(rec['original_sha1'],'upstream-sha1');self.assertEqual(rec['format'],'PNG');self.assertTrue(rec['has_alpha']);self.assertEqual((root/rec['path']).read_bytes(),original_bytes)
   return rec
 def test_svg_original_uses_api_png_and_preserves_alpha(self):self.assertEqual(self.rendition('image/svg+xml')['rendition'],'api_returned_rendition')
 def test_bounded_raster_original_remains_original(self):self.assertEqual(self.rendition('image/png')['rendition'],'api_reported_unscaled_original')
 def test_animated_and_oversize_inputs_refused(self):
  with tempfile.TemporaryDirectory() as temp:
   p=Path(temp)/'x.png';Image.new('RGB',(500,721)).save(p)
   with self.assertRaisesRegex(ValueError,'nominal edge'):ssi.dimensions(p,480)
   self.assertEqual(ssi.dimensions(p,640)['height'],721)
   p=Path(temp)/'x.gif';Image.new('RGB',(2,2),'red').save(p,save_all=True,append_images=[Image.new('RGB',(2,2),'blue')])
   with self.assertRaisesRegex(ValueError,'Animated'):ssi.dimensions(p,640)

class DiagnosticTests(unittest.TestCase):
 def test_redirect_is_recorded_with_location_and_no_follow(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp).resolve();client=transport.Client(root);client.opener=Mock();headers=Message();headers['Location']='https://petscan.toolforge.org/'
   client.opener.open.side_effect=HTTPError('https://petscan.wmcloud.org/',301,'Moved',headers,io.BytesIO(b'moved'))
   with patch.object(transport.time,'sleep'),self.assertRaises(transport.StopAcquisition):client.fetch('https://petscan.wmcloud.org/','population','test','provenance/partials/test.part')
   self.assertEqual(client.opener.open.call_count,1);self.assertEqual(population.read(root/'provenance/last_transport_error.json')['headers']['location'],'https://petscan.toolforge.org/')
 def test_size_specific_metadata_keys_keep_both_responses(self):
  self.assertNotEqual(ssi.metadata_path('preview',480,1,10),ssi.metadata_path('preview',640,1,10))
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);a=root/ssi.metadata_path('preview',480,1,10);b=root/ssi.metadata_path('preview',640,1,10);transport.dump(a,{'query':{'pages':[]}});transport.dump(b,{'query':{'pages':[]}})
   with patch.object(ssi,'ROOT',root),patch.object(ssi,'candidates',return_value={}),patch.object(ssi,'order',return_value=[]):
    transport.dump(a.with_suffix('.receipt.json'),{'receipt':'not an API reply'});self.assertEqual(ssi.evidence(),{})
   self.assertTrue(a.exists() and b.exists())

if __name__=='__main__':unittest.main()
