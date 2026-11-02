"""A visual fit excluded on rights/provenance must never reach source requests."""
import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import acquire


class SourceEligibilityTests(unittest.TestCase):
    def test_rights_exclusion_preserves_visual_fit_without_request(self):
        rejected = dict(candidate_id='bsp-0080', visually_accepted=True,
                        screening_status='reject')
        accepted = dict(candidate_id='bsp-0001', visually_accepted=True,
                        screening_status='accept')
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(acquire, 'ROOT', Path(directory)), \
                 patch.object(acquire, 'load_records', return_value=[rejected, accepted]), \
                 patch.object(acquire, 'save_records'), patch.object(acquire, 'Client'), \
                 patch.object(acquire, 'metadata', return_value=None) as metadata, \
                 patch('sys.argv', ['acquire.py', '--stage', 'source', '--user-agent', 'offline-test']), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(acquire.main(), 0)
            self.assertEqual(metadata.call_count, 1)
            self.assertIs(metadata.call_args.args[1], accepted)
            self.assertTrue(rejected['visually_accepted'])
            self.assertNotIn('source_acquisition_status', rejected)


if __name__ == '__main__':
    unittest.main()
