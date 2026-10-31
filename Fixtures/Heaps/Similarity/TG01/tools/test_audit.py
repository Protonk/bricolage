"""Duplicate identity checks must include nonadjacent accepted candidates."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import audit

class AuditTests(unittest.TestCase):
    def test_rejected_middle_duplicate_does_not_hide_accepted_pair(self):
        rows=[dict(candidate_id=f'tg-{n:04d}',commons_title='File:Same.jpg',screening_status=state) for n,state in [(1,'accept'),(2,'reject'),(3,'accept')]]
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);(root/'provenance').mkdir()
            with patch.object(audit,'ROOT',root),patch.object(audit,'SETS',{}),patch.object(audit,'load_records',return_value=rows),contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):audit.main()
            result=json.loads((root/'provenance/identity-audit.json').read_text())
            self.assertEqual(result['status'],'failed')
            self.assertIn(['tg-0001','tg-0003'],[r['candidate_ids'] for r in result['blocking_collisions']])

if __name__=='__main__':unittest.main()
