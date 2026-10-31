"""Historical audit coverage must survive new peer fixtures, but not lost evidence."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import audit
import botanical as ssi
from transport import dump


class AuditCoverageTests(unittest.TestCase):
    def test_frozen_coverage_ignores_new_leaf_and_rejects_missing_old_leaf(self):
        with tempfile.TemporaryDirectory() as temp:
            fixtures = Path(temp).resolve() / 'Fixtures'
            root = fixtures / 'Heaps/Curatorial/Botanical-Illustrations'
            root.mkdir(parents=True)

            def leaf(name):
                path = fixtures / name
                dump(path / 'manifest.json', {'images': []})
                (path / 'sources.csv').write_text('source_filename\n')
                return path

            old = leaf('Heaps/Curatorial/POTY/Arthropods')
            with patch.object(ssi, 'ROOT', root), patch.object(ssi, 'selection', return_value={'selected': []}), patch.object(ssi, 'candidates', return_value={}), patch.object(ssi, 'evidence', return_value={}):
                original = audit.audit()
                scope = [r['fixture'] for r in original['inventories']]
                leaf('Heaps/Curatorial/US-Army-SSI')
                self.assertEqual(audit.audit(fixture_names=scope), original)
                self.assertEqual(len(audit.audit()['inventories']), 2)
                (old / 'sources.csv').write_text('source_filename,changed\n')
                self.assertNotEqual(audit.audit(fixture_names=scope), original)
                (old / 'sources.csv').unlink()
                with self.assertRaisesRegex(ValueError, 'Recorded audit fixture is missing'):
                    audit.audit(fixture_names=scope)


if __name__ == '__main__':
    unittest.main()
