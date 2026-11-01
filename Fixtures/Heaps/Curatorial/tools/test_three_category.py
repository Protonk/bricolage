"""Focused checks for ordering, review gates and input preservation."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import three_category as t

class SelectionTests(unittest.TestCase):
 def setUp(self):
  temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)/'Rocks-in-Thin-Section';self.root.mkdir();(self.root/'provenance').mkdir();t.dump(self.root/'inventory.json',{'test':True})
  self.ids=['a','b','c'];self.reviews={cid:dict(visual_decision='accept',provenance_decision='accept',rights_decision='accept',reason='viewed in scope',work_key=None)for cid in self.ids}
  self.ev={cid:dict(page=dict(pageid=i,imageinfo=[dict(sha1=str(i))]))for i,cid in enumerate(self.ids)}
  for attr,value in [('ROOT',self.root),('TARGET',2)]:p=patch.object(t,attr,value);p.start();self.addCleanup(p.stop)
  for method,value in [('order',self.ids),('evidence',self.ev),('config',{'seed':'fixed'})]:p=patch.object(t,method,return_value=value);p.start();self.addCleanup(p.stop)
 def choose(self):t.dump(self.root/'provenance/work-review.json',self.reviews);return t.selection()
 def test_unviewed_gap_blocks_selection(self):
  del self.reviews['a'];self.assertEqual(self.choose()['selected'],[])
 def test_defer_is_not_rejection_and_later_selection_is_provisional(self):
  self.reviews['a']['rights_decision']='defer';r=self.choose();self.assertEqual(r['selected'],['b','c']);self.assertEqual(r['unresolved_prior_candidates'],['a']);self.assertEqual(r['provisional_selected'],['b','c'])
 def test_scope_rejection_does_not_become_pending_due_to_separate_rights_uncertainty(self):
  self.reviews['a'].update(visual_decision='reject',rights_decision='defer');r=self.choose();self.assertEqual(r['selected'],['b','c']);self.assertEqual(r['decisions'][0]['decision'],'excluded');self.assertEqual(r['provisional_selected'],[])
 def test_known_work_duplicate_is_skipped_in_order(self):
  self.reviews['a']['work_key']=self.reviews['b']['work_key']='same-specimen';r=self.choose();self.assertEqual(r['selected'],['a','c']);self.assertEqual(r['decisions'][1]['conflicts_with'],['a'])
 def test_unknown_work_is_not_assumed_repeated(self):self.assertEqual(self.choose()['selected'],['a','b'])
 def test_same_original_bytes_are_rejected(self):
  self.ev['b']['page']['imageinfo'][0]['sha1']='0';self.assertEqual(self.choose()['selected'],['a','c'])
 def test_download_absence_does_not_replace_selection(self):
  self.assertEqual(self.choose()['selected'],['a','b']);self.assertEqual(list(self.root.glob('sources/*')),[])

class OrderingAndMediaTests(unittest.TestCase):
 def test_exact_unicode_and_spelling_define_candidate_id(self):
  a=t.cid_for('Ex-Libris','File:Épreuve_one.jpg');self.assertEqual(a,hashlib.sha256('hazy-curatorial-triplet-v1\nEx-Libris\nFile:Épreuve_one.jpg'.encode()).hexdigest()[:20]);self.assertNotEqual(a,t.cid_for('Ex-Libris','File:Épreuve one.jpg'))
 def test_order_independent_of_enumeration(self):
  rows=[{'candidate_id':x}for x in ['d','c','b','a']];self.assertEqual(t.ordered(rows,'seed'),t.ordered(rows[::-1],'seed'));self.assertEqual(set(t.ordered(rows,'seed')),{'a','b','c','d'})
 def test_dimensions_reject_oversize_and_leave_bytes_unchanged(self):
  with tempfile.TemporaryDirectory()as temp:
   p=Path(temp)/'image.png';Image.new('RGB',(721,10)).save(p);before=p.read_bytes()
   with self.assertRaisesRegex(ValueError,'nominal edge'):t.dimensions(p,480)
   self.assertEqual(p.read_bytes(),before)
 def test_missing_current_metadata_and_unresolved_continuation_rejected(self):
  with self.assertRaises(ValueError):t.current_metadata({'query':{'pages':[]}})
  with self.assertRaises(ValueError):t.current_metadata({'query':{'pages':[{'title':'File:x'}]},'continue':{'rvcontinue':'x'}})
 def test_animation_is_not_silently_reduced_to_first_frame(self):
  with tempfile.TemporaryDirectory()as temp:
   p=Path(temp)/'animated.gif';Image.new('RGB',(5,5),'red').save(p,save_all=True,append_images=[Image.new('RGB',(5,5),'blue')]);before=p.read_bytes()
   with self.assertRaisesRegex(ValueError,'Animated media unsupported'):t.dimensions(p,480)
   self.assertEqual(p.read_bytes(),before)

if __name__=='__main__':unittest.main()
