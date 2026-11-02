import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import check_layout
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
        writers = [leaf for leaf in layout.discover() if (leaf/'tools/common.py').is_file()
                   and 'def save_records' in (leaf/'tools/common.py').read_text()]
        self.assertGreaterEqual(len(writers), 1, 'No leaf ships the candidate writer')
        for leaf in writers:
            slug = leaf.name
            path = leaf/'tools/common.py'
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

    def test_recorded_leaf_rename_resolves_tool_pins_and_sampler_locations(self):
        # A leaf renamed with a relocation record stays reachable from records that
        # name its old path: migration tool pins and sampler snapshots.
        repo = Path(self.temp.name)
        old = self.leaf()
        (old/'images').mkdir(exist_ok=True)
        (old/'images/a.jpg').write_bytes(b'picture')
        digest = hashlib.sha256(b'picture').hexdigest()
        (old/'tools/common.py').write_bytes(b'adapted')
        new = old.with_name('Renamed-Leaf')
        old.rename(new)
        tool = new/'tools/common.py'
        record = self.fixtures/'provenance/rename/relocations.json'
        record.parent.mkdir(parents=True)
        record.write_text(json.dumps({'moves': [{'old': 'Fixtures/Relationships/derivatives',
                                                 'new': 'Fixtures/Relationships/Renamed-Leaf',
                                                 'purpose': 'leaf-rename'}]}))
        status = layout.sampler.location_status(repo, 'Fixtures/Relationships/derivatives/images/a.jpg', digest)
        self.assertEqual(status, dict(status='ok', observed_sha256=digest,
                                      current_path='Fixtures/Relationships/Renamed-Leaf/images/a.jpg'))
        self.assertEqual(layout.sampler.location_status(
            repo, 'Fixtures/Relationships/derivatives/images/a.jpg', 'other')['status'], 'changed')
        self.assertEqual(layout.sampler.location_status(
            repo, 'Fixtures/Relationships/derivatives/images/b.jpg', digest)['status'], 'missing')
        self.assertEqual(layout.sampler.location_status(
            repo, 'Fixtures/Relationships/Renamed-Leaf/images/a.jpg', digest),
            dict(status='ok', observed_sha256=digest))
        receipt = self.fixtures/'migration'
        receipt.mkdir()
        (receipt/'tool-changes.json').write_text(json.dumps({'files': {
            'Fixtures/Relationships/derivatives/tools/common.py': {
                'before_git_blob_sha1': 'pin', 'before_sha256': 'before',
                'after_sha256': hashlib.sha256(b'adapted').hexdigest()}}}))
        with patch.object(layout, 'MIGRATION', receipt), patch.object(layout, 'REPO', repo.resolve()):
            self.assertTrue(layout.matches_tool_revision(tool, blob='pin'))
            tool.write_bytes(b'unrecorded change')
            self.assertFalse(layout.matches_tool_revision(tool, blob='pin'))

    def test_live_files_reference_only_existing_fixture_paths(self):
        # Guides, tools and catalogs outside the historical records must not name a
        # leaf path that no longer exists; provenance and media keep their old strings.
        pattern = re.compile(r'(?<![\w/.-])(?:Fixtures/)?(?:Heaps|Relationships)/[\w.-]+(?:/[\w.-]+)*')
        # Tests build scratch trees and the template shows example paths; both are skipped.
        skip = {'provenance', 'previews', 'images', 'sources', 'output', 'records', 'Template',
                '__pycache__', '.venv', '.git'}
        suffixes = {'.md', '.py', '.json', '.txt', '.csv', '.cfg', '.toml', ''}
        files = [layout.REPO/name for name in ('README.md', 'AGENTS.md', 'CONTRIBUTING.md', 'WORLD.md')]
        files += [p for p in layout.FIXTURES.rglob('*') if p.is_file() and p.suffix in suffixes
                  and not p.name.startswith('test_')
                  and not skip & set(p.relative_to(layout.FIXTURES).parts[:-1])]
        stale = []
        for file in files:
            try:
                text = file.read_text(encoding='utf-8')
            except (OSError, UnicodeDecodeError):
                continue
            for match in pattern.findall(text):
                target = match.rstrip('.')
                if '{' in target or '<' in target:
                    continue
                base = layout.REPO if target.startswith('Fixtures/') else layout.FIXTURES
                if not (base/target).exists():
                    stale.append(f'{file.relative_to(layout.REPO)}: {target}')
        self.assertEqual(stale, [])

    def test_check_layout_script_reports_every_discovered_leaf_and_failures(self):
        self.leaf()
        self.leaf('multiview')
        out = io.StringIO()
        code = check_layout.main(['--metadata-only'], fixtures=self.fixtures, stdout=out)
        report = json.loads(out.getvalue())
        self.assertEqual((code, report['leaves'], report['passed'], report['failed']), (0, 2, 2, []))
        self.assertEqual(len(report['results']), 2)
        (self.fixtures/'Relationships/derivatives/stray.txt').write_text('x')
        out = io.StringIO()
        code = check_layout.main(['--metadata-only'], fixtures=self.fixtures, stdout=out)
        report = json.loads(out.getvalue())
        self.assertEqual((code, report['leaves'], report['passed']), (1, 2, 1))
        self.assertEqual(report['failed'], [str(self.fixtures/'Relationships/derivatives')])
        self.assertEqual(len(report['results']), 2)


if __name__ == '__main__':
    unittest.main()
