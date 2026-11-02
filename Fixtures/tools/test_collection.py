"""Removal and re-pin behavior, retained evidence, and generated outputs using disposable inputs."""
import csv
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import zlib

import collection
import collection_totals
import source_index
import fixture_layout as layout
import fixture_history as history
from new_fixture import create


def png(seed, width=1, height=1):
    """A real PNG with deterministic pixels, so a replacement decodes to known attributes."""
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    pixel = bytes([seed % 256, (seed * 7) % 256, (seed * 13) % 256])
    raw = b''.join(b'\x00' + pixel * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b''))


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.fixtures = Path(self.temp.name).resolve() / 'Fixtures'
        self.root = self.fixtures / 'Relationships/Example'
        create(self.root, 'test-v1', 'derivatives', self.fixtures)
        self.rows, sources = [], []
        for number in range(3):
            raw = png(number + 1)
            name = f'{number}.png'
            (self.root / 'images' / name).write_bytes(raw)
            (self.root / 'sources' / name).write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            self.rows.append(dict(zip(layout.IMAGE_FIELDS, [
                'images/' + name, 'batch-1', str(number), '', str(number), 'source',
                'identity', 1, 1, 1, 1, 'PNG', digest, 'pixels-' + str(number),
            ])))
            sources.append(dict(zip(layout.SOURCE_FIELDS, [
                str(number), name, '', 'mechanics', 'nobody; test', digest, 1, 1, 1, '', 'none', '', '', name])))
        manifest = json.loads((self.root / 'manifest.json').read_text())
        manifest['images'] = self.rows
        (self.root / 'manifest.json').write_bytes(history.encode(manifest))
        (self.root / 'manifest.csv').write_bytes(history.csv_bytes((self.root / 'manifest.csv').read_bytes(), self.rows))
        (self.root / 'sources.csv').write_bytes(history.csv_bytes((self.root / 'sources.csv').read_bytes(), sources))
        (self.root / 'SHA256SUMS.txt').write_text(''.join(
            f'{row["byte_sha256"]}  {area}/{Path(row["file"]).name}\n'
            for area in ('images', 'sources') for row in self.rows))
        for name in ('batch-1', 'smoke', 'medium'):
            (self.root / f'batches/{name}.txt').write_text(''.join(r['file'] + '\n' for r in self.rows))
        pairs = [dict(file_a=self.rows[0]['file'], file_b=self.rows[1]['file'], relation='diagnostic', interpretation='mechanics'),
                 dict(file_a=self.rows[1]['file'], file_b=self.rows[2]['file'], relation='diagnostic', interpretation='mechanics')]
        (self.root / 'probes.csv').write_bytes(history.csv_bytes((self.root / 'probes.csv').read_bytes(), pairs))
        (self.root / 'selections.json').write_bytes(history.encode(dict(description='mechanics', pairs=pairs, known_shift_families=['0', '1'])))
        self.before = history.catalogs(self.root)
        self.evidence = self.root / 'provenance/untouched.json'
        self.evidence.write_bytes(b'{ "original": true }\n')
        self.source_hash = history.sha(self.root / 'sources/0.png')
        self.replacement = Path(self.temp.name) / 'replacement.png'
        self.replacement.write_bytes(png(99))
        self.replacement_hash = hashlib.sha256(png(99)).hexdigest()

    def remove(self, index=0, **kwargs):
        return history.remove(self.root, self.rows[index], 'test removal', **kwargs)

    def repin(self, index=0, replacement=None, **kwargs):
        return history.repin(self.root, self.rows[index], replacement or self.replacement, 'test re-pin', **kwargs)

    def sums(self):
        return dict(line.split('  ', 1)[::-1] for line in (self.root / 'SHA256SUMS.txt').read_text().splitlines())

    def test_removal_updates_active_membership_and_keeps_historical_bytes(self):
        self.remove()
        self.assertFalse((self.root / 'images/0.png').exists())
        self.assertEqual(history.sha(self.root / 'sources/0.png'), self.source_hash)
        self.assertEqual(self.evidence.read_bytes(), b'{ "original": true }\n')
        self.assertEqual(json.loads((self.root / 'manifest.json').read_text())['images'], self.rows[1:])
        self.assertEqual((self.root / 'batches/smoke.txt').read_text(), 'images/1.png\nimages/2.png\n')
        pairs = json.loads((self.root / 'selections.json').read_text())
        self.assertEqual(pairs['known_shift_families'], ['1'])
        self.assertEqual(len(pairs['pairs']), 1)
        self.assertEqual(len(list(csv.DictReader(io.StringIO((self.root / 'probes.csv').read_text())))), 1)
        record = history.history(self.root, assets=True)[0]
        self.assertEqual((record['kind'], record['before']), ('removal', self.before))
        self.assertEqual(layout.check_layout(self.root)['recorded_changes'], 1)

    def test_second_removal_extends_the_chain_and_the_last_input_stays(self):
        self.remove()
        self.remove(1)
        self.assertEqual([r['receipt']['image']['file'] for r in history.history(self.root, assets=True)], ['images/0.png', 'images/1.png'])
        with self.assertRaisesRegex(ValueError, 'last input'):
            self.remove(2)

    def test_changed_snapshot_and_unrecorded_catalog_edits_fail(self):
        self.remove()
        snapshot = self.root / 'provenance/removals/0001/before/manifest.json'
        original = snapshot.read_bytes()
        snapshot.write_bytes(original + b' ')
        with self.assertRaisesRegex(ValueError, 'Changed snapshot'):
            history.history(self.root)
        snapshot.write_bytes(original)
        (self.root / 'batches/medium.txt').write_text('images/1.png\n')
        with self.assertRaisesRegex(ValueError, 'Active catalogs differ'):
            history.history(self.root)

    def test_missing_preserved_media_is_reported_and_never_recreated(self):
        self.remove()
        archive = self.root / history.history(self.root)[0]['receipt']['preserved_image']
        archive.unlink()
        with self.assertRaisesRegex(FileNotFoundError, archive.name):
            layout.check_layout(self.root)
        self.assertEqual(layout.check_layout(self.root, assets=False)['images'], 2)
        self.assertFalse(archive.exists())

    def test_unrecorded_restoration_fails(self):
        self.remove()
        (self.root / 'images/0.png').write_bytes((self.root / 'sources/0.png').read_bytes())
        with self.assertRaisesRegex(ValueError, 'Removed input was restored'):
            history.history(self.root, assets=True)

    def test_dry_run_changes_no_catalogs_or_media(self):
        self.assertEqual(self.remove(dry_run=True)['status'], 'planned')
        self.assertEqual(self.repin(dry_run=True)['status'], 'planned')
        self.assertEqual(history.catalogs(self.root), self.before)
        self.assertEqual(history.sha(self.root / 'images/0.png'), self.source_hash)
        self.assertFalse((self.root / 'provenance/removals').exists())
        self.assertFalse((self.root / 'provenance/repins').exists())

    def test_write_failure_rolls_back_catalogs_and_media(self):
        original = history.atomic_write
        for operation in (self.remove, self.repin):
            calls = 0
            def fail_once(path, raw):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError('injected write failure')
                original(path, raw)
            with patch.object(history, 'atomic_write', side_effect=fail_once), self.assertRaisesRegex(OSError, 'injected'):
                operation()
            self.assertEqual(history.catalogs(self.root), self.before)
            self.assertEqual(history.sha(self.root / 'images/0.png'), self.source_hash)
            self.assertEqual(history.sha(self.root / 'sources/0.png'), self.source_hash)
            self.assertFalse((self.root / 'provenance/removals').exists())
            self.assertFalse((self.root / 'provenance/repins').exists())

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
        (other / 'manifest.json').write_bytes(history.encode(m))
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
        self.assertEqual(history.catalogs(self.root), self.before)

    def test_layout_check_ties_checksums_batches_and_source_catalog_together(self):
        (self.root / 'batches/smoke.txt').write_text('images/9.png\n')
        with self.assertRaisesRegex(ValueError, 'Batch names an input outside'):
            layout.check_layout(self.root, assets=False)
        (self.root / 'batches/smoke.txt').write_text('images/0.png\n')
        sums = (self.root / 'SHA256SUMS.txt').read_text()
        (self.root / 'SHA256SUMS.txt').write_text(sums.replace(self.rows[2]['byte_sha256'] + '  sources/2.png', '0' * 64 + '  sources/2.png'))
        with self.assertRaisesRegex(ValueError, 'Source checksum differs from catalog'):
            layout.check_layout(self.root, assets=False)
        (self.root / 'SHA256SUMS.txt').write_text(sums)
        (self.root / 'sources/2.png').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'Source hash differs'):
            layout.check_layout(self.root)
        self.assertEqual(layout.check_layout(self.root, assets=False)['layout'], 'passed')

    def test_repin_replaces_input_and_source_bytes_with_a_verifiable_receipt(self):
        result = self.repin()
        self.assertEqual((result['status'], result['source_replaced'], result['previous_bytes']), ('repinned', True, 'preserved'))
        self.assertEqual(history.sha(self.root / 'images/0.png'), self.replacement_hash)
        self.assertEqual(history.sha(self.root / 'sources/0.png'), self.replacement_hash)
        manifest = json.loads((self.root / 'manifest.json').read_text())['images']
        self.assertEqual((manifest[0]['byte_sha256'], manifest[0]['pixels_rgb_sha256'], manifest[0]['width']), (self.replacement_hash, '', 1))
        self.assertEqual(manifest[1:], self.rows[1:])
        self.assertEqual(list(csv.DictReader(io.StringIO((self.root / 'manifest.csv').read_text())))[0]['byte_sha256'], self.replacement_hash)
        sums = self.sums()
        self.assertEqual((sums['images/0.png'], sums['sources/0.png'], sums['images/1.png']), (self.replacement_hash, self.replacement_hash, self.rows[1]['byte_sha256']))
        sources = list(csv.DictReader(io.StringIO((self.root / 'sources.csv').read_text())))
        self.assertEqual([s['source_sha256'] for s in sources], [self.replacement_hash, self.rows[1]['byte_sha256'], self.rows[2]['byte_sha256']])
        self.assertEqual((self.root / 'batches/batch-1.txt').read_text(), self.before['batches/batch-1.txt'].decode())
        record = history.history(self.root, assets=True)[0]
        receipt = record['receipt']
        self.assertEqual((record['kind'], receipt['image'], receipt['replacement']['byte_sha256']), ('repin', self.rows[0], self.replacement_hash))
        self.assertEqual(receipt['previous'], dict(observed_sha256=self.source_hash, matched_record=True, preserved=f'previews/repinned/{self.source_hash}.png'))
        self.assertEqual(history.sha(self.root / receipt['previous']['preserved']), self.source_hash)
        self.assertEqual(self.evidence.read_bytes(), b'{ "original": true }\n')
        self.assertEqual(layout.check_layout(self.root)['recorded_changes'], 1)
        with self.assertRaisesRegex(ValueError, 'Rebuilding a publication after recorded changes'):
            history.require_unchanged(self.root)
        collection_totals.update(self.fixtures)
        self.assertIn(self.replacement_hash, (self.fixtures / 'INDEX.csv').read_text())

    def test_repin_recovers_a_missing_input_and_records_that_nothing_was_there(self):
        (self.root / 'images/0.png').unlink()
        (self.root / 'sources/0.png').unlink()
        with self.assertRaisesRegex(ValueError, 'coverage differs'):
            layout.check_layout(self.root)
        result = self.repin()
        self.assertEqual(result['previous_bytes'], 'missing')
        receipt = history.history(self.root, assets=True)[0]['receipt']
        self.assertEqual(receipt['previous'], dict(observed_sha256=None, matched_record=False, preserved=None))
        self.assertFalse((self.root / 'previews/repinned').exists())
        self.assertEqual(layout.check_layout(self.root)['layout'], 'passed')

    def test_repin_refuses_non_equivalent_or_identical_replacements_and_removed_inputs(self):
        wide = Path(self.temp.name) / 'wide.png'
        wide.write_bytes(png(5, width=2))
        with self.assertRaisesRegex(ValueError, 'not equivalent'):
            self.repin(replacement=wide)
        same = Path(self.temp.name) / 'same.png'
        same.write_bytes(png(1))
        self.assertEqual(self.repin(replacement=same)['status'], 'identical')
        self.assertEqual(history.catalogs(self.root), self.before)
        self.assertFalse((self.root / 'provenance/repins').exists())
        inside = self.root / 'previews/candidate.png'
        inside.parent.mkdir(exist_ok=True); inside.write_bytes(png(7))
        with self.assertRaisesRegex(ValueError, 'outside the leaf'):
            self.repin(replacement=inside)
        self.remove()
        with self.assertRaisesRegex(ValueError, 'Active row differs'):
            self.repin()

    def test_removal_then_repin_form_one_chain_in_order(self):
        self.remove()
        self.repin(1)
        records = history.history(self.root, assets=True)
        self.assertEqual([r['kind'] for r in records], ['removal', 'repin'])
        self.assertEqual(records[1]['before']['manifest.json'], records[0]['after']['manifest.json'])
        self.assertEqual(layout.check_layout(self.root)['recorded_changes'], 2)
        second = history.history(self.root)[1]['entry'] / 'before/manifest.json'
        second.write_bytes(second.read_bytes() + b' ')
        with self.assertRaisesRegex(ValueError, 'Changed snapshot'):
            history.history(self.root)

    def test_changed_preserved_repin_bytes_fail_asset_checks(self):
        self.repin()
        preserved = self.root / history.history(self.root)[0]['receipt']['previous']['preserved']
        preserved.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError, 'Changed preserved bytes'):
            history.history(self.root, assets=True)

    def test_leaf_entry_point_runs_publication_checks_only_while_unchanged(self):
        script = self.root / 'tools/check.py'
        def run():
            out = io.StringIO()
            with patch('sys.argv', ['check.py']), redirect_stdout(out):
                layout.check_leaf(script, checks=[['Fixtures/tools/collection.py', '--help']])
            return json.loads(out.getvalue())
        with patch.object(layout, 'REPO', layout.REPO):
            before = run()
        self.assertEqual((before['specialized_scope'], len(before['specialized_checks'])), ('current_publication', 1))
        self.remove()
        after = run()
        self.assertTrue(after['specialized_scope'].startswith('historical: 1 recorded change'))
        self.assertEqual((after['specialized_checks'], after['recorded_changes']), ([], 1))

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
        (other / 'manifest.json').write_bytes(history.encode(m))
        (other / 'manifest.csv').write_bytes(history.csv_bytes((other / 'manifest.csv').read_bytes(), m['images']))
        (other / 'SHA256SUMS.txt').write_text(f'{self.rows[0]["byte_sha256"]}  images/0.png\n')
        text = collection_totals.render(self.fixtures)
        self.assertIn('4 active inputs · 2 collections · 3 distinct byte hashes', text)

    def test_index_lists_every_input_with_recovery_and_cross_leaf_sharing(self):
        other = self.fixtures / 'Heaps/Other'
        create(other, 'other-v1', 'prompt_heap', self.fixtures)
        (other / 'provenance/intake').mkdir()
        for name in ('prompt.json', 'candidates.jsonl', 'candidates.csv'):
            (other / 'provenance/intake' / name).write_text('{}' if name.endswith('.json') else '')
        m = json.loads((other / 'manifest.json').read_text()); m['images'] = [self.rows[1]]
        (other / 'manifest.json').write_bytes(history.encode(m))
        (other / 'manifest.csv').write_bytes(history.csv_bytes((other / 'manifest.csv').read_bytes(), m['images']))
        (other / 'SHA256SUMS.txt').write_text(f'{self.rows[1]["byte_sha256"]}  images/1.png\n{self.rows[1]["byte_sha256"]}  sources/1.png\n')
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

    def test_cli_removes_repins_regenerates_totals_and_repeats_without_another_record(self):
        arguments = ['collection', 'remove', self.rows[0]['byte_sha256'], '--reason', 'CLI regression']
        for expected in ('removed', 'already_removed'):
            output = io.StringIO()
            with patch('sys.argv', arguments), redirect_stdout(output):
                collection.main(self.fixtures)
            self.assertEqual(json.loads(output.getvalue())['status'], expected)
            collection_totals.update(self.fixtures, check=True)
            self.assertEqual(len(history.history(self.root)), 1)
        output = io.StringIO()
        with patch('sys.argv', ['collection', 'repin', 'images/1.png', '--leaf', str(self.root), '--from', str(self.replacement), '--reason', 'CLI re-pin']), redirect_stdout(output):
            collection.main(self.fixtures)
        self.assertEqual(json.loads(output.getvalue())['status'], 'repinned')
        collection_totals.update(self.fixtures, check=True)
        self.assertEqual([r['kind'] for r in history.history(self.root)], ['removal', 'repin'])
        with patch('sys.argv', ['collection', 'repin', self.rows[0]['byte_sha256'], '--from', str(self.replacement), '--reason', 'x']), self.assertRaises(SystemExit):
            collection.main(self.fixtures)


if __name__ == '__main__':
    unittest.main()
