"""Removal behavior, retained evidence, and generated totals using disposable inputs."""
import csv
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import collection
import collection_totals
import source_index
import fixture_layout as layout
import fixture_removal as removal
from new_fixture import create


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixtures = Path(self.temp.name).resolve() / 'Fixtures'
        self.root = self.fixtures / 'Relationships/Example'
        create(self.root, 'test-v1', 'derivatives', self.fixtures)
        self.rows = []
        for number in range(3):
            raw = f'generated mechanics input {number}'.encode()
            name = f'{number}.png'
            (self.root / 'images' / name).write_bytes(raw)
            (self.root / 'sources' / name).write_bytes(raw)
            self.rows.append(dict(zip(layout.IMAGE_FIELDS, [
                'images/' + name, 'batch-1', str(number), '', str(number), 'source',
                'identity', 1, 1, 1, 1, 'PNG', hashlib.sha256(raw).hexdigest(), '',
            ])))
        manifest = json.loads((self.root / 'manifest.json').read_text())
        manifest['images'] = self.rows
        (self.root / 'manifest.json').write_bytes(removal.encode(manifest))
        (self.root / 'manifest.csv').write_bytes(removal.csv_bytes((self.root / 'manifest.csv').read_bytes(), self.rows))
        (self.root / 'SHA256SUMS.txt').write_text(''.join(
            f'{row["byte_sha256"]}  {area}/{Path(row["file"]).name}\n'
            for area in ('images', 'sources') for row in self.rows))
        for name in ('batch-1', 'smoke', 'medium'):
            (self.root / f'batches/{name}.txt').write_text(''.join(r['file'] + '\n' for r in self.rows))
        pairs = [dict(file_a=self.rows[0]['file'], file_b=self.rows[1]['file'], relation='diagnostic', interpretation='mechanics'),
                 dict(file_a=self.rows[1]['file'], file_b=self.rows[2]['file'], relation='diagnostic', interpretation='mechanics')]
        (self.root / 'probes.csv').write_bytes(removal.csv_bytes((self.root / 'probes.csv').read_bytes(), pairs))
        (self.root / 'selections.json').write_bytes(removal.encode(dict(description='mechanics', pairs=pairs, known_shift_families=['0', '1'])))
        self.before = removal.catalogs(self.root)
        self.evidence = self.root / 'provenance/untouched.json'
        self.evidence.write_bytes(b'{ "original": true }\n')
        self.source_hash = removal.sha(self.root / 'sources/0.png')

    def remove(self, index=0, **kwargs):
        return removal.remove(self.root, self.rows[index], 'test removal', **kwargs)

    def test_removal_updates_active_membership_and_keeps_historical_bytes(self):
        self.remove()
        self.assertFalse((self.root / 'images/0.png').exists())
        self.assertEqual(removal.sha(self.root / 'sources/0.png'), self.source_hash)
        self.assertEqual(self.evidence.read_bytes(), b'{ "original": true }\n')
        self.assertEqual(json.loads((self.root / 'manifest.json').read_text())['images'], self.rows[1:])
        self.assertEqual((self.root / 'batches/smoke.txt').read_text(), 'images/1.png\nimages/2.png\n')
        pairs = json.loads((self.root / 'selections.json').read_text())
        self.assertEqual(pairs['known_shift_families'], ['1'])
        self.assertEqual(len(pairs['pairs']), 1)
        self.assertEqual(len(list(csv.DictReader(io.StringIO((self.root / 'probes.csv').read_text())))), 1)
        record = removal.history(self.root, assets=True)[0]
        self.assertEqual(record[2], self.before)
        self.assertEqual(removal.historical_manifest(self.root, removal.digest(self.before['manifest.json'])).read_bytes(), self.before['manifest.json'])
        self.assertEqual(layout.check_layout(self.root)['removed_inputs'], 1)

    def test_second_removal_replays_chain_and_both_historical_manifest_pins(self):
        self.remove()
        first = (self.root / 'manifest.json').read_bytes()
        self.remove(1)
        self.assertEqual(len(removal.history(self.root, assets=True)), 2)
        for raw in (self.before['manifest.json'], first):
            self.assertEqual(removal.historical_manifest(self.root, removal.digest(raw)).read_bytes(), raw)
        with self.assertRaisesRegex(ValueError, 'last input'):
            self.remove(2)

    def test_original_publication_view_is_temporary_and_leaves_active_inputs_removed(self):
        self.remove()
        self.remove(1)
        with patch.object(removal, 'FIXTURES', self.fixtures), removal.publication_view(self.root) as view:
            self.assertEqual((view / 'manifest.json').read_bytes(), self.before['manifest.json'])
            self.assertEqual(len(list((view / 'images').iterdir())), 3)
            self.assertFalse((self.root / 'images/0.png').exists())
            self.assertFalse((view / 'provenance/removals').exists())
            self.assertEqual((view / 'provenance/untouched.json').read_bytes(), self.evidence.read_bytes())
        self.assertFalse(view.exists())
        self.assertEqual(len(list((self.root / 'images').iterdir())), 1)

    def test_changed_snapshot_and_unrecorded_catalog_edits_fail(self):
        self.remove()
        snapshot = self.root / 'provenance/removals/0001/before/manifest.json'
        original = snapshot.read_bytes()
        snapshot.write_bytes(original + b' ')
        with self.assertRaisesRegex(ValueError, 'Changed removal snapshot'):
            removal.history(self.root)
        snapshot.write_bytes(original)
        (self.root / 'batches/medium.txt').write_text('images/1.png\n')
        with self.assertRaisesRegex(ValueError, 'Active catalogs differ'):
            removal.historical_manifest(self.root, removal.digest(self.before['manifest.json']))

    def test_missing_preserved_media_is_reported_and_never_recreated(self):
        self.remove()
        archive = self.root / removal.history(self.root)[0][1]['preserved_image']
        archive.unlink()
        with self.assertRaisesRegex(FileNotFoundError, archive.name):
            layout.check_layout(self.root)
        self.assertEqual(layout.check_layout(self.root, assets=False)['images'], 2)
        self.assertFalse(archive.exists())

    def test_unrecorded_restoration_fails(self):
        self.remove()
        (self.root / 'images/0.png').write_bytes((self.root / 'sources/0.png').read_bytes())
        with self.assertRaisesRegex(ValueError, 'Removed input was restored'):
            removal.history(self.root, assets=True)

    def test_dry_run_changes_no_catalogs_or_media(self):
        self.assertEqual(self.remove(dry_run=True)['status'], 'planned')
        self.assertEqual(removal.catalogs(self.root), self.before)
        self.assertTrue((self.root / 'images/0.png').is_file())
        self.assertFalse((self.root / 'provenance/removals').exists())

    def test_write_failure_rolls_back_catalogs_and_media(self):
        original = removal.atomic_write
        calls = 0
        def fail_once(path, raw):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError('injected write failure')
            original(path, raw)
        with patch.object(removal, 'atomic_write', side_effect=fail_once), self.assertRaisesRegex(OSError, 'injected'):
            self.remove()
        self.assertEqual(removal.catalogs(self.root), self.before)
        self.assertEqual(removal.sha(self.root / 'images/0.png'), self.source_hash)
        self.assertFalse((self.root / 'provenance/removals').exists())

    def test_hash_path_ambiguity_and_repeated_removal_resolution(self):
        root, row, already = collection.resolve(self.rows[0]['byte_sha256'], fixtures=self.fixtures)
        self.assertEqual((root, row, already), (self.root, self.rows[0], False))
        self.remove()
        self.assertTrue(collection.resolve('sha256:' + row['byte_sha256'], fixtures=self.fixtures)[2])
        self.assertEqual(collection.resolve('images/1.png', self.root, self.fixtures)[1], self.rows[1])
        with self.assertRaisesRegex(ValueError, 'No input matches'):
            collection.resolve('missing', fixtures=self.fixtures)
        other = self.fixtures / 'Relationships/Other'
        create(other, 'other-v1', 'derivatives', self.fixtures)
        m = json.loads((other / 'manifest.json').read_text()); m['images'] = [self.rows[1]]
        (other / 'manifest.json').write_bytes(removal.encode(m))
        with self.assertRaisesRegex(ValueError, 'Ambiguous input'):
            collection.resolve(self.rows[1]['byte_sha256'], fixtures=self.fixtures)

    def test_symlink_and_changed_bytes_are_rejected_before_removal(self):
        image = self.root / 'images/0.png'
        image.unlink(); image.symlink_to(self.root / 'sources/0.png')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            self.remove()
        image.unlink(); image.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Input hash differs'):
            self.remove()
        self.assertEqual(removal.catalogs(self.root), self.before)

    def test_totals_detect_staleness_and_regenerate_from_manifests(self):
        collection_totals.update(self.fixtures)
        self.assertIn('3 active inputs', (self.fixtures / 'COLLECTIONS.md').read_text())
        self.remove()
        with self.assertRaisesRegex(ValueError, 'Stale collection totals'):
            collection_totals.update(self.fixtures, check=True)
        collection_totals.update(self.fixtures)
        self.assertIn('2 active inputs', (self.fixtures / 'COLLECTIONS.md').read_text())
        self.assertIn('**2 active inputs**', (self.root / 'README.md').read_text())
        self.assertEqual(collection_totals.update(self.fixtures, check=True)['changed'], [])
        # Snapshots under provenance are never extra collections or inputs.
        self.assertIn('1 collections', (self.fixtures / 'COLLECTIONS.md').read_text())

    def test_distinct_totals_deduplicate_hashes_across_collections(self):
        other = self.fixtures / 'Relationships/Other'
        create(other, 'other-v1', 'derivatives', self.fixtures)
        m = json.loads((other / 'manifest.json').read_text()); m['images'] = [self.rows[0]]
        (other / 'manifest.json').write_bytes(removal.encode(m))
        (other / 'manifest.csv').write_bytes(removal.csv_bytes((other / 'manifest.csv').read_bytes(), m['images']))
        text = collection_totals.render(self.fixtures)
        self.assertIn('4 active inputs · 2 collections · 3 distinct byte hashes', text)

    def test_index_lists_every_input_with_recovery_and_cross_leaf_sharing(self):
        other = self.fixtures / 'Heaps/Other'
        create(other, 'other-v1', 'prompt_heap', self.fixtures)
        (other / 'provenance/intake').mkdir()
        for name in ('prompt.json', 'candidates.jsonl', 'candidates.csv'):
            (other / 'provenance/intake' / name).write_text('{}' if name.endswith('.json') else '')
        m = json.loads((other / 'manifest.json').read_text()); m['images'] = [self.rows[1]]
        (other / 'manifest.json').write_bytes(removal.encode(m))
        (other / 'manifest.csv').write_bytes(removal.csv_bytes((other / 'manifest.csv').read_bytes(), m['images']))
        (other / 'sources.csv').write_text((other / 'sources.csv').read_text()
            + '1,1.png,,File:One.jpg,Someone; CC0,%s,1,1,1,https://commons.wikimedia.org/?curid=7,,,,One.jpg\n' % self.rows[1]['byte_sha256'])
        (other / 'provenance/import-map.json').write_text(json.dumps([dict(
            final_file='images/1.png', commons_pageid=7, original_sha1='abc', acquired_url='https://upload.wikimedia.org/x.png',
            source_requested_max_edge=1600, acquired_rendition_kind='api_returned_rendition', license='CC0', license_url='u',
            commons_title='File:One.jpg')]))
        rows = list(csv.DictReader(io.StringIO(source_index.render(self.fixtures))))
        self.assertEqual([r['leaf'] for r in rows], ['Heaps/Other'] + ['Relationships/Example'] * 3)
        commons = rows[0]
        self.assertEqual((commons['origin'], commons['recovery'], commons['page_id'], commons['original_sha1'], commons['requested_edge']),
                         ('commons', 'commons-api', '7', 'abc', '1600'))
        self.assertEqual(commons['shared_with'], 'Relationships/Example:images/1.png')
        example = {r['file']: r for r in rows[1:]}
        self.assertEqual(example['images/1.png']['shared_with'], 'Heaps/Other:images/1.png')
        self.assertEqual(example['images/0.png']['shared_with'], '')
        self.assertEqual((example['images/0.png']['origin'], example['images/0.png']['recovery']), ('unknown', 'none'))
        self.assertEqual(list(rows[0]), source_index.COLUMNS)
        result = source_index.update(self.fixtures)
        self.assertEqual((result['inputs'], result['leaves'], result['shared']), (4, 2, 2))
        self.assertEqual(source_index.update(self.fixtures, check=True)['changed'], [])
        self.remove()
        with self.assertRaisesRegex(ValueError, 'Stale source index'):
            source_index.update(self.fixtures, check=True)
        # Totals regenerate the index too, so one command and one check cover both.
        collection_totals.update(self.fixtures)
        self.assertEqual(source_index.update(self.fixtures, check=True)['inputs'], 3)

    def test_unknown_audit_pin_and_rebuild_are_rejected(self):
        self.remove()
        with self.assertRaisesRegex(ValueError, 'No preserved manifest matching'):
            removal.historical_manifest(self.root, '0' * 64)
        with self.assertRaisesRegex(ValueError, 'Rebuilding a publication after removals is unsupported'):
            removal.require_unremoved(self.root)

    def test_artifact_adapter_preserves_explicit_stage_and_keyword_calls(self):
        self.remove()
        @removal.publication_artifacts(lambda: self.root)
        def check(output=None):
            return (output / 'manifest.json').read_bytes()
        with patch.object(removal, 'FIXTURES', self.fixtures):
            self.assertEqual(check(), self.before['manifest.json'])
            self.assertEqual(check(output=None), self.before['manifest.json'])
            self.assertEqual(check(output=self.root), (self.root / 'manifest.json').read_bytes())

    def test_cli_removes_regenerates_totals_and_repeats_without_another_record(self):
        arguments = ['collection', 'remove', self.rows[0]['byte_sha256'], '--reason', 'CLI regression']
        for expected in ('removed', 'already_removed'):
            output = io.StringIO()
            with patch('sys.argv', arguments), redirect_stdout(output):
                collection.main(self.fixtures)
            self.assertEqual(json.loads(output.getvalue())['status'], expected)
            collection_totals.update(self.fixtures, check=True)
            self.assertEqual(len(removal.history(self.root)), 1)


if __name__ == '__main__':
    unittest.main()
