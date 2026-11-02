"""The full fixture validator enforces BSP01's floor independently of the count report."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import integrate


class PublicationFloorTests(unittest.TestCase):
    def test_manifest_with_twenty_nine_inputs_is_not_publishable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manifest = dict(schema_version=1, kind='prompt_heap',
                            images=[{'file': f'images/{i}.jpg'} for i in range(29)])
            (root / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'at least 30'):
                integrate.check(root)

    def test_build_refuses_subfloor_before_creating_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            rows = [dict(candidate_id=f'bsp-{i:04d}', screening_status='accept', image_downloaded=True)
                    for i in range(29)]
            (root / 'provenance/intake').mkdir(parents=True)
            (root / 'provenance/intake/candidates.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in rows))
            (root / 'previews').mkdir()
            with patch.object(integrate, 'ROOT', root), patch.object(integrate, 'local', side_effect=lambda p: root / p), patch.object(integrate, 'check_evidence'):
                with self.assertRaisesRegex(ValueError, 'below 30'):
                    integrate.build('floor-test')
            self.assertFalse((root / 'previews/integration-floor-test/images').exists())
            self.assertTrue((root / 'previews/integration-floor-test/FAILED.json').exists())

    def test_abandoned_review_cannot_hide_published_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();(root/'provenance').mkdir()
            (root/'provenance/acquisition.json').write_text(json.dumps({'status':'abandoned_below_floor'}))
            (root/'images').mkdir()
            with self.assertRaisesRegex(ValueError,'published outputs'):
                integrate.check_state(root)

    def test_abandoned_state_still_checks_full_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();(root/'provenance').mkdir()
            (root/'provenance/acquisition.json').write_text(json.dumps({'status':'abandoned_below_floor'}))
            with patch.object(integrate,'check_evidence',side_effect=ValueError('changed evidence')):
                with self.assertRaisesRegex(ValueError,'changed evidence'):
                    integrate.check_state(root)


if __name__ == '__main__':
    unittest.main()
