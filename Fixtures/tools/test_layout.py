import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import fixture_layout as layout
from new_fixture import create


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixtures = Path(self.temp.name) / 'Fixtures'

    def leaf(self, kind='derivatives'):
        area = 'Heaps/Nested/Collection' if kind.endswith('_heap') else 'Relationships'
        root = self.fixtures / area / kind
        create(root, kind + '-v1', kind, self.fixtures)
        return root

    def test_single_template_all_kinds_and_nesting(self):
        for kind in ('derivatives', 'multiview', 'prompt_heap', 'curatorial_heap'):
            leaf = self.leaf(kind)
            self.assertEqual(json.loads((leaf/'manifest.json').read_text())['kind'], kind)
            self.assertTrue((leaf/'tools/check.py').is_file())
        with patch.object(layout, 'FIXTURES', self.fixtures):
            self.assertEqual(len(layout.discover()), 4)

    def test_scaffold_never_fabricates_selection_evidence_or_valid_acquired_images(self):
        leaf = self.leaf('curatorial_heap')
        self.assertFalse((leaf/'provenance/intake').exists())
        with self.assertRaisesRegex(ValueError, 'Missing intake'):
            layout.check_layout(leaf, assets=False)
        leaf = self.leaf()
        self.assertEqual(layout.check_layout(leaf, assets=False)['images'], 0)
        with self.assertRaisesRegex(ValueError, 'Empty fixture'):
            layout.check_layout(leaf)

    def test_existing_destination_duplicate_identity_and_wrong_area_rejected(self):
        leaf = self.leaf()
        with self.assertRaisesRegex(ValueError, 'already exists'):
            create(leaf, 'again', 'derivatives', self.fixtures)
        with self.assertRaisesRegex(ValueError, 'ID already exists'):
            create(self.fixtures/'Relationships/Other', 'derivatives-v1', 'derivatives', self.fixtures)
        with self.assertRaisesRegex(ValueError, 'Destination must'):
            create(self.fixtures/'Heaps/Other', 'other', 'multiview', self.fixtures)

    def test_unexpected_root_entries_and_bad_catalogs_rejected(self):
        leaf = self.leaf()
        (leaf/'obsolete').write_text('')
        with self.assertRaisesRegex(ValueError, 'Unexpected leaf-root'):
            layout.check_layout(leaf, assets=False)
        (leaf/'obsolete').unlink()
        (leaf/'manifest.csv').write_text('wrong,columns\n')
        with self.assertRaisesRegex(ValueError, 'image columns'):
            layout.check_layout(leaf, assets=False)

    def test_historical_evidence_location_is_explicit_and_unambiguous(self):
        leaf = self.leaf('prompt_heap')
        old = leaf/'prompt.json'; old.write_text('historical bytes')
        self.assertEqual(layout.evidence_path(leaf,'prompt.json'), old)
        new = leaf/'provenance/intake/prompt.json'; new.parent.mkdir()
        old.rename(new)
        self.assertEqual(layout.evidence_path(leaf,'prompt.json'), new)
        old.write_text('duplicate')
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            layout.evidence_path(leaf,'prompt.json')

    def test_template_and_archived_manifests_are_not_discovered(self):
        leaf = self.leaf()
        for where in (leaf/'provenance/supplied', self.fixtures/'Template', leaf/'previews/stage'):
            where.mkdir(parents=True, exist_ok=True)
            (where/'manifest.json').write_text('{}')
        with patch.object(layout, 'FIXTURES', self.fixtures):
            self.assertEqual(layout.discover(), [leaf])

    def test_dependency_pin_accepts_only_exact_recorded_tool_change(self):
        script = self.fixtures/'tool.py'; script.parent.mkdir(parents=True)
        old = b'old'; new = b'new'; script.write_bytes(new)
        pin = hashlib.sha1(b'blob 3\0'+old).hexdigest()
        receipt = self.fixtures/'migration'; receipt.mkdir()
        (receipt/'tool-changes.json').write_text(json.dumps({'files': {'tool.py': {
            'before_git_blob_sha1': pin, 'before_sha256': hashlib.sha256(old).hexdigest(),
            'after_sha256': hashlib.sha256(new).hexdigest()}}}))
        with patch.object(layout,'MIGRATION',receipt), patch.object(layout,'REPO',self.fixtures.resolve()):
            self.assertTrue(layout.matches_tool_revision(script,blob=pin))
            script.write_bytes(b'unrecorded change')
            self.assertFalse(layout.matches_tool_revision(script,blob=pin))

    def test_live_candidate_writers_use_intake_directory(self):
        # Exercise actual publication helpers against fresh scratch roots: they
        # must create nested metadata paths without restoring old root files.
        for slug in ('PS01', 'CR01', 'TG01', 'BSP01'):
            path = layout.FIXTURES/'Heaps/Similarity'/slug/'tools/common.py'
            spec = importlib.util.spec_from_file_location('writer_' + slug, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            root = Path(self.temp.name)/slug
            root.mkdir()
            rows = [dict(candidate_id='example', screening_status='defer')]
            with patch.multiple(module, ROOT=root.resolve(),
                                CANON=root.resolve()/'provenance/intake/candidates.jsonl'):
                module.save_records(rows)
                self.assertEqual(module.load_records(), rows)
            self.assertTrue((root/'provenance/intake/candidates.csv').is_file())
            self.assertFalse((root/'candidates.jsonl').exists())


if __name__ == '__main__':
    unittest.main()
