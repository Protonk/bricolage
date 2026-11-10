"""An authorized neighboring agent can remove an exact image and leave a checked commit."""
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest.mock import patch

import collection
import collection_removal as removal
import collection_totals
import fixture_history as history
import fixture_layout as layout
import test_collection as mechanics


class RemovalTests(unittest.TestCase):
    def setUp(self):
        mechanics.CollectionTests.setUp(self)
        self.repo = self.fixtures.parent
        self.image_id = 'sha256:' + self.rows[0]['byte_sha256']

    def setup_git(self):
        self.git = mechanics.CollectionTests.setup_git(self)
        self.original_commit = self.git('rev-parse', 'HEAD')

    def install_launchers(self):
        # Install real launchers and code in the disposable checkout.
        (self.fixtures / 'tools').mkdir()
        (self.fixtures / 'Sampler').mkdir()
        for script in (layout.FIXTURES / 'tools').glob('*.py'):
            shutil.copy2(script, self.fixtures / 'tools' / script.name)
        for script in ('sampler.py', 'sample_without.py'):
            shutil.copy2(layout.FIXTURES / 'Sampler' / script, self.fixtures / 'Sampler' / script)
        for executable in ('sample', 'sampleWithout', 'collection'):
            shutil.copy2(layout.FIXTURES / executable, self.fixtures / executable)
        (self.fixtures / '.venv').symlink_to(layout.FIXTURES / '.venv', target_is_directory=True)

    def run_remove(self, *extra, selector=None, reason='Remove unsuitable fixture'):
        stdout, stderr = io.StringIO(), io.StringIO()
        status = 0
        with patch('sys.argv', ['collection', 'remove', selector or self.image_id, '--reason', reason, *extra]), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                collection.main(self.fixtures)
            except SystemExit as error:
                status = error.code
        return status, json.loads(stdout.getvalue())

    def other_alias_leaf(self):
        other = self.fixtures / 'Heaps/Other'
        shutil.copytree(self.root, other)
        catalogs = history.catalogs(other)
        for row in self.rows[1:]:
            catalogs = history.project_removal(catalogs, row)
            (other / row['file']).unlink()
        for name, raw in catalogs.items():
            (other / name).write_bytes(raw)
        manifest = json.loads((other / 'manifest.json').read_text())
        manifest['fixture_id'] = 'another-v1'
        (other / 'manifest.json').write_bytes(history.encode(manifest))
        return other

    def test_neighbor_samples_removes_every_alias_and_commits_only_its_files(self):
        other = self.other_alias_leaf()
        # A second path within the same leaf must also disappear.
        alias = dict(self.rows[0], file='images/alias.png')
        shutil.copyfile(self.root / self.rows[0]['file'], self.root / alias['file'])
        manifest = json.loads((self.root / 'manifest.json').read_text())
        manifest['images'].append(alias)
        (self.root / 'manifest.json').write_bytes(history.encode(manifest))
        (self.root / 'manifest.csv').write_bytes(history.csv_bytes(self.before['manifest.csv'], manifest['images']))
        with (self.root / 'SHA256SUMS.txt').open('a') as stream:
            stream.write(f'{alias["byte_sha256"]}  {alias["file"]}\n')
        with (self.root / 'batches/batch-1.txt').open('a') as stream:
            stream.write(alias['file'] + '\n')
        self.install_launchers()
        for name in ('staged.txt', 'unstaged.txt'):
            (self.repo / name).write_text('original\n')
        self.setup_git()
        (self.repo / 'staged.txt').write_text('staged work\n')
        self.git('add', 'staged.txt')
        (self.repo / 'staged.txt').write_text('further unstaged work\n')
        (self.repo / 'unstaged.txt').write_text('unrelated work\n')
        staged = self.git('show', ':staged.txt')
        consumer = Path(self.temp.name) / 'neighbor with spaces'
        consumer.mkdir()

        def run(tool, *args):
            return subprocess.run([f'../bricolage/Fixtures/{tool}', *args], cwd=consumer,
                                  capture_output=True, text=True)

        sample = run('sample', '3')
        self.assertEqual(sample.returncode, 0, sample.stderr)
        world = Path(json.loads(sample.stdout)['output']['directory'])
        world_before = {p.name: p.read_bytes() for p in world.iterdir()}
        manifest = json.loads(world_before['world.json'])
        self.assertIn(self.image_id, [entry['id'] for entry in manifest['images']])
        source_before = (self.root / 'sources/0.png').read_bytes()
        result = run('collection', 'remove', self.image_id, '--reason', 'Remove unsuitable fixture',
                     '--commit-message', 'Remove exact sampled image')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertTrue(report['complete'])
        self.assertTrue(report['checks']['excluded_from_sampling'])
        self.assertEqual(len(report['receipts']), 3)
        self.assertEqual(report['commit'], self.git('rev-parse', 'HEAD'))
        self.assertEqual(self.git('log', '-1', '--format=%s'), 'Remove exact sampled image')
        committed = set(self.git('diff-tree', '--no-commit-id', '--name-only', '-r', report['commit']).splitlines())
        self.assertEqual(committed, set(report['changed_files']))
        self.assertFalse(any('/images/' in name or '/sources/' in name or '/previews/' in name for name in committed))
        self.assertEqual(self.git('show', ':staged.txt'), staged)
        self.assertEqual(self.git('show', 'HEAD:staged.txt'), 'original')
        self.assertEqual((self.repo / 'staged.txt').read_text(), 'further unstaged work\n')
        self.assertEqual((self.repo / 'unstaged.txt').read_text(), 'unrelated work\n')
        self.assertEqual(layout.check_layout(other)['images'], 0)
        self.assertEqual(layout.check_layout(self.root)['images'], 2)
        self.assertEqual((self.root / 'sources/0.png').read_bytes(), source_before)
        self.assertEqual({p.name: p.read_bytes() for p in world.iterdir()}, world_before)
        fresh = run('sample', '2')
        self.assertEqual(fresh.returncode, 0, fresh.stderr)
        self.assertNotIn(self.image_id, json.loads(fresh.stdout)['draw']['image_ids'])
        again = run('collection', 'remove', self.image_id, '--reason', 'Remove unsuitable fixture')
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(json.loads(again.stdout)['status'], 'already_removed')
        self.assertEqual(json.loads(again.stdout)['commit'], report['commit'])
        self.assertEqual(self.git('rev-list', '--count', 'HEAD'), '2')
        self.assertEqual(list(consumer.iterdir()), [])

    def test_neighbor_samples_without_an_old_world_after_removing_one_of_its_images(self):
        self.install_launchers()
        self.setup_git()
        consumer = Path(self.temp.name) / 'neighbor with spaces'
        consumer.mkdir()

        def run(tool, *args):
            return subprocess.run([f'../bricolage/Fixtures/{tool}', *args], cwd=consumer,
                                  capture_output=True, text=True)

        sampled = run('sample', '2')
        self.assertEqual(sampled.returncode, 0, sampled.stderr)
        original = json.loads(sampled.stdout)
        world = Path(original['output']['directory'])
        before = {p.name: p.read_bytes() for p in world.iterdir()}
        removed_id = original['draw']['image_ids'][0]
        removed = run('collection', 'remove', removed_id, '--reason', 'Remove sampled image')
        self.assertEqual(removed.returncode, 0, removed.stderr + removed.stdout)
        self.assertTrue(json.loads(removed.stdout)['complete'])

        result = run('sampleWithout', str(world), '1')
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        report = json.loads(result.stdout)
        self.assertTrue(report['output']['published'])
        self.assertTrue(report['output']['receipt_recorded'])
        self.assertEqual(report['output']['image_count'], 1)
        self.assertEqual(report['exclusion']['requested_count'], 2)
        self.assertEqual(report['exclusion']['matched_count'], 1)
        self.assertEqual(report['exclusion']['remaining_eligible'], 1)
        self.assertEqual(report['exclusion']['unmatched_image_ids'], [removed_id])
        self.assertEqual([warning['image_id'] for warning in report['warnings']], [removed_id])
        expected = {'sha256:' + row['byte_sha256'] for row in self.rows} - set(original['draw']['image_ids'])
        self.assertEqual(set(report['draw']['image_ids']), expected)
        self.assertEqual(report['problems'], [])
        self.assertEqual({p.name: p.read_bytes() for p in world.iterdir()}, before)
        self.assertEqual(run('sample', 'verify', report['draw']['sample_id']).returncode, 0)
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual(list(consumer.iterdir()), [])

    def test_dry_run_does_not_create_receipts_or_commit(self):
        self.setup_git()
        status, report = self.run_remove('--dry-run')
        self.assertEqual(status, 0, report)
        self.assertEqual(report['status'], 'planned')
        self.assertIsNone(report['commit'])
        self.assertFalse(Path(report['operation']).exists())
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual(history.catalogs(self.root), self.before)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.original_commit)

    def test_existing_staged_or_unstaged_target_edits_stop_before_removal(self):
        self.setup_git()
        for target in (self.root / 'README.md', self.root / 'sources.csv'):
            original = target.read_bytes()
            for staged in (False, True):
                with self.subTest(file=target.name, staged=staged):
                    target.write_bytes(original + b'\n')
                    if staged:
                        self.git('add', str(target))
                    status, report = self.run_remove()
                    self.assertEqual(status, 1)
                    self.assertIn(target.name, report['error'])
                    self.assertFalse((self.fixtures / removal.OPERATIONS).exists())
                    self.assertEqual((self.root / 'manifest.json').read_bytes(), self.before['manifest.json'])
                    self.assertEqual(target.read_bytes(), original + b'\n')
                    target.write_bytes(original)
                    self.git('add', str(target))

    def test_commit_failure_retry_preserves_reason_and_does_not_duplicate_receipts(self):
        self.setup_git()
        hook = self.repo / '.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\necho "injected commit refusal" >&2\nexit 1\n')
        hook.chmod(0o755)
        status, report = self.run_remove()
        self.assertEqual(status, 1)
        self.assertEqual(report['status'], 'incomplete')
        self.assertIn('injected commit refusal', report['error'])
        self.assertIsNone(report['commit'])
        self.assertTrue(report['checks']['excluded_from_sampling'])
        self.assertEqual(len(history.history(self.root)), 1)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.original_commit)
        status, changed = self.run_remove(reason='A different reason')
        self.assertEqual(status, 1)
        self.assertIn('original reason', changed['error'])
        hook.unlink()
        status, completed = self.run_remove()
        self.assertEqual(status, 0, completed)
        self.assertTrue(completed['complete'])
        self.assertEqual(len(history.history(self.root)), 1)
        self.assertEqual(self.git('status', '--porcelain'), '')
        self.assertEqual(self.git('log', '-1', '--format=%s'), 'Remove unsuitable fixture')

    def test_totals_partial_write_is_resumed_without_another_receipt(self):
        self.setup_git()
        original_write = history.atomic_write
        def fail_index(path, raw):
            if path == self.fixtures / 'INDEX.csv':
                raise OSError('injected index write failure')
            original_write(path, raw)
        with patch.object(history, 'atomic_write', side_effect=fail_index):
            status, report = self.run_remove()
        self.assertEqual(status, 1)
        self.assertIn('injected index write failure', report['error'])
        self.assertEqual(len(history.history(self.root)), 1)
        self.assertIsNone(report['commit'])
        status, completed = self.run_remove()
        self.assertEqual(status, 0, completed)
        self.assertTrue(completed['complete'])
        self.assertEqual(len(history.history(self.root)), 1)
        collection_totals.update(self.fixtures, check=True)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_validation_failure_is_retried_and_a_different_pending_removal_is_refused(self):
        self.setup_git()
        with patch.object(removal, 'validate_removal', side_effect=ValueError('injected validation failure')):
            status, report = self.run_remove()
        self.assertEqual(status, 1)
        self.assertIn('injected validation failure', report['error'])
        status, other = self.run_remove(selector=self.rows[1]['byte_sha256'])
        self.assertEqual(status, 1)
        self.assertIn('pending removal', other['error'])
        self.assertEqual(len(history.history(self.root)), 1)
        status, completed = self.run_remove()
        self.assertEqual(status, 0, completed)
        self.assertTrue(completed['complete'])

    def test_partial_alias_removal_is_resumed(self):
        other = self.other_alias_leaf()
        self.setup_git()
        original_remove = history.remove
        def fail_second(root, row, reason, **kwargs):
            if root == self.root and not kwargs.get('dry_run'):
                raise OSError('injected second leaf failure')
            return original_remove(root, row, reason, **kwargs)
        with patch.object(history, 'remove', side_effect=fail_second):
            status, report = self.run_remove()
        self.assertEqual(status, 1)
        self.assertEqual(len(history.history(other)), 1)
        self.assertEqual(len(history.history(self.root)), 0)
        status, completed = self.run_remove()
        self.assertEqual(status, 0, completed)
        self.assertEqual(len(history.history(other)), 1)
        self.assertEqual(len(history.history(self.root)), 1)
        self.assertTrue(completed['checks']['excluded_from_sampling'])

    def test_missing_alias_is_named_before_any_alias_is_removed(self):
        other = self.other_alias_leaf()
        self.setup_git()
        missing = other / 'images/0.png'
        missing.unlink()
        status, report = self.run_remove()
        self.assertEqual(status, 1)
        self.assertFalse(report['complete'])
        self.assertIn('images/0.png', report['error'])
        self.assertFalse((self.fixtures / removal.OPERATIONS).exists())
        self.assertEqual(history.history(self.root), [])
        self.assertEqual(history.history(other), [])

    def test_last_image_removal_allows_a_completely_empty_sampler_population(self):
        only = self.other_alias_leaf()
        shutil.rmtree(self.root)  # Fixture construction, before the disposable repo is initialized.
        self.setup_git()
        status, report = self.run_remove()
        self.assertEqual(status, 0, report)
        self.assertTrue(report['checks']['excluded_from_sampling'])
        self.assertEqual(layout.check_layout(only)['images'], 0)
        import sampler
        inventory = sampler.build_inventory(self.repo)
        self.assertEqual(inventory['population']['counts']['eligible'], 0)
        self.assertEqual(inventory['population']['counts']['excluded_leaves'], 0)
        self.assertEqual(self.git('status', '--porcelain'), '')

    def test_path_removal_has_explicit_scope_and_leaves_other_aliases_active(self):
        self.other_alias_leaf()
        self.setup_git()
        status, report = self.run_remove(selector=str(self.root / 'images/0.png'))
        self.assertEqual(status, 0, report)
        self.assertFalse(report['checks']['excluded_from_sampling'])
        self.assertEqual(report['checks']['remaining_aliases'], 1)
        status, report = self.run_remove()
        self.assertEqual(status, 0, report)
        self.assertTrue(report['checks']['excluded_from_sampling'])

    def test_damaged_pending_operation_is_named_and_left_intact(self):
        self.setup_git()
        with patch.object(removal.Git, 'commit', side_effect=ValueError('injected commit failure')):
            _, report = self.run_remove()
        path = Path(report['operation'])
        raw = path.read_text().replace('Remove unsuitable fixture', 'Changed reason')
        path.write_text(raw)
        status, report = self.run_remove()
        self.assertEqual(status, 1)
        self.assertIn(str(path), report['error'])
        self.assertEqual(path.read_text(), raw)

    def test_pending_operation_refuses_unexpected_generated_or_staged_edits(self):
        self.setup_git()
        with patch.object(removal.Git, 'commit', side_effect=ValueError('injected commit failure')):
            self.assertEqual(self.run_remove()[0], 1)
        for target in (self.fixtures / 'INDEX.csv', self.root / 'README.md'):
            with self.subTest(file=target.name):
                expected = target.read_bytes()
                target.write_bytes(expected + b'Unrelated edit\n')
                status, report = self.run_remove()
                self.assertEqual(status, 1)
                self.assertIn('Unexpected edits', report['error'])
                self.assertIn(target.name, report['error'])
                self.git('add', str(target))
                target.write_bytes(expected)
                status, report = self.run_remove()
                self.assertEqual(status, 1)
                self.assertIn('Unexpected staged edits', report['error'])
                self.git('add', str(target))
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.original_commit)

    def test_retry_does_not_fold_unrelated_source_changes_into_the_index(self):
        other = self.other_alias_leaf()
        self.setup_git()
        selector = str(self.root / 'images/0.png')
        with patch.object(removal.Git, 'commit', side_effect=ValueError('injected commit failure')):
            self.assertEqual(self.run_remove(selector=selector)[0], 1)
        index_before = (self.fixtures / 'INDEX.csv').read_bytes()
        catalog = other / 'sources.csv'
        catalog.write_text(catalog.read_text().replace('nobody; test', 'Unrelated credit edit'))
        status, report = self.run_remove(selector=selector)
        self.assertEqual(status, 1)
        self.assertIn('Generated output changed outside the removal plan: Fixtures/INDEX.csv', report['error'])
        self.assertEqual((self.fixtures / 'INDEX.csv').read_bytes(), index_before)
        self.assertEqual(self.git('rev-parse', 'HEAD'), self.original_commit)


if __name__ == '__main__':
    unittest.main()
