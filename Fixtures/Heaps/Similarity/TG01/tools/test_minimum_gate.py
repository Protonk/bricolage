"""Offline checks for the 30-image floor and acquisition/visual separation."""
import hashlib,tempfile,unittest
from pathlib import Path
from minimum_gate import classify
class MinimumGateTests(unittest.TestCase):
    def rec(self,i,s):return dict(candidate_id=f'tg-{i:04d}',screening_status=s,image_downloaded=False,acquired_path=None,acquired_sha256=None)
    def test_unviewed_not_abandoned(self):
        rs=[self.rec(i,'reject') for i in range(1,30)]+[self.rec(30,'pending_visual_review')]
        self.assertEqual(classify(rs,Path('/tmp'))['status'],'pending_visual_review')
    def test_fewer_than_thirty_abandoned(self):
        rs=[self.rec(i,'accept' if i<=29 else 'reject') for i in range(1,51)]
        self.assertEqual(classify(rs,Path('/tmp'))['status'],'abandon_below_floor')
    def test_transport_failure_is_incomplete(self):
        rs=[self.rec(i,'accept') for i in range(1,31)]
        self.assertEqual(classify(rs,Path('/tmp'))['status'],'acquisition_incomplete')
    def test_thirty_verified_acquisitions(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'sources').mkdir()
            rs=[self.rec(i,'accept') for i in range(1,31)]
            for r in rs:
                name=f"sources/{r['candidate_id']}.jpg";data=r['candidate_id'].encode()
                (root/name).write_bytes(data)
                r.update(image_downloaded=True,acquired_path=name,acquired_sha256=hashlib.sha256(data).hexdigest())
            self.assertEqual(classify(rs,root)['status'],'count_gate_met_full_review_still_required')
            (root/rs[0]['acquired_path']).write_bytes(b'changed')
            self.assertEqual(classify(rs,root)['status'],'acquisition_incomplete')
if __name__=='__main__':unittest.main()
