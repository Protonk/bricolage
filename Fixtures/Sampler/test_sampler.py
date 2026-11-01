"""Offline mechanics tests; synthetic byte fixtures make no image-quality claims."""
import concurrent.futures
import contextlib
import hashlib
import io
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import sampler as s


if sys.version_info[:2] != (3, 14):
    raise RuntimeError('Sampler tests target Python 3.14.x only; run make test-sampler')


class SamplerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'checkout'
        self.store = self.repo / 'Fixtures/Sampler/records'
        for area in ('Heaps', 'Relationships'):
            (self.repo / 'Fixtures' / area).mkdir(parents=True)
        self.heap = self.make_leaf('Heaps/Curatorial/Nested/Leaf', [b'one', b'two'])
        self.related = self.make_leaf('Relationships/Variants', [b'three', b'four'])

    def make_leaf(self, name, blobs):
        leaf = self.repo / 'Fixtures' / name
        (leaf / 'images').mkdir(parents=True)
        rows = []
        for n, blob in enumerate(blobs):
            (leaf / f'images/{n}.png').write_bytes(blob)
            rows.append(dict(file=f'images/{n}.png', family_id='source-a', parents='source-a',
                             transformation='source' if n == 0 else 'variant',
                             byte_sha256=hashlib.sha256(blob).hexdigest()))
        (leaf / 'manifest.json').write_text(json.dumps(dict(schema_version=1, fixture_id=name,
                                                           kind='test', images=rows)))
        (leaf / 'sources.csv').write_text('family_id,source_filename,source_url,credit_status\n'
                                          'source-a,original.png,https://example.test/source,Example credit\n')
        return leaf

    def inventory(self):
        return s.build_inventory(self.repo)

    def draw(self, n=3, seed='test'):
        return s.create_draw(self.store, self.inventory(), n, seed)

    def cli(self, *args, input=None):
        return subprocess.run([sys.executable, str(Path(s.__file__)), '--repo', str(self.repo),
                               '--store', str(self.store), *args], input=input,
                              text=True, capture_output=True)

    def test_population_includes_nested_heaps_and_all_relationship_variants(self):
        inv = self.inventory()
        self.assertEqual(inv['population']['counts']['eligible'], 4)
        aliases = [a for i in inv['population']['images'] for a in i['aliases']]
        self.assertEqual({a['fixture_id'] for a in aliases},
                         {'Heaps/Curatorial/Nested/Leaf', 'Relationships/Variants'})
        self.assertEqual({a['manifest_record']['transformation'] for a in aliases}, {'source', 'variant'})
        self.assertTrue(all(a['source_records'][0]['credit_status'] == 'Example credit' for a in aliases))

    def test_archives_source_copies_and_previews_are_not_extra_tickets(self):
        before = self.inventory()['population']
        for folder in ('sources', 'previews', 'provenance/archive'):
            p = self.heap / folder
            p.mkdir(parents=True)
            (p / 'extra.png').write_bytes(b'not a fixture input')
            (p / 'manifest.json').write_text('{}')
        self.assertEqual(self.inventory()['population'], before)

    def test_byte_identical_copies_and_symlinks_share_one_ticket_with_all_aliases(self):
        extra = self.make_leaf('Heaps/Other', [b'one', b'one'])
        (extra / 'images/1.png').unlink()
        (extra / 'images/1.png').symlink_to(self.heap / 'images/0.png')
        inv = self.inventory()
        self.assertEqual(inv['population']['counts']['manifest_records'], 6)
        self.assertEqual(inv['population']['counts']['eligible'], 4)
        original = next(i for i in inv['population']['images'] if i['byte_sha256'] == hashlib.sha256(b'one').hexdigest())
        self.assertEqual(len(original['aliases']), 3)
        self.assertEqual(len(s.sample_ids(inv, 4, 'all')), 4)

    def test_population_and_draw_ignore_traversal_order(self):
        first = self.inventory()
        with patch.object(s, 'manifests', return_value=list(reversed(s.manifests(self.repo)))):
            second = self.inventory()
        self.assertEqual(first['inventory_id'], second['inventory_id'])
        self.assertEqual(first['population'], second['population'])
        self.assertEqual(s.sample_ids(first, 3, 'seed'), s.sample_ids(second, 3, 'seed'))

    def test_missing_changed_and_unlisted_files_are_visible(self):
        (self.heap / 'images/0.png').unlink()
        (self.heap / 'images/1.png').write_bytes(b'changed')
        (self.heap / 'images/unlisted.png').write_bytes(b'unlisted')
        inv = self.inventory()
        self.assertEqual(inv['population']['counts']['distinct_images'], 4)
        self.assertEqual(inv['population']['counts']['eligible'], 2)
        self.assertEqual(len(inv['population']['unlisted_inputs']), 1)
        states = [a['availability']['status'] for i in inv['population']['images'] for a in i['aliases']]
        self.assertCountEqual(states, ['missing', 'changed', 'ok', 'ok'])

    def test_inaccessible_alias_does_not_remove_its_usable_peer(self):
        extra = self.make_leaf('Heaps/Other', [b'one'])
        (extra / 'images/0.png').unlink()
        inv = self.inventory()
        self.assertEqual(inv['population']['counts']['eligible'], 4)
        with patch.object(s, 'file_hash', side_effect=PermissionError('denied')):
            result = s.location_status(self.repo, 'Fixtures/Heaps/x.png', '0'*64)
        self.assertEqual(result['status'], 'inaccessible')

    def test_path_escape_and_external_symlink_are_not_read(self):
        p = self.heap / 'images/0.png'
        p.unlink()
        p.symlink_to(Path(self.temp.name) / 'outside.png')
        inv = self.inventory()
        self.assertEqual(inv['population']['counts']['eligible'], 3)
        with self.assertRaisesRegex(ValueError, 'Unsafe fixture path'):
            s.fixture_path(self.repo, 'Fixtures/../secret')

    def test_requested_size_bounds_no_replacement_and_zero_draw(self):
        inv = self.inventory()
        self.assertEqual(s.sample_ids(inv, 0, 's'), [])
        self.assertEqual(set(s.sample_ids(inv, 4, 's')), {i['image_id'] for i in inv['population']['images']})
        for n in (-1, 5, True):
            with self.assertRaises(ValueError):
                s.sample_ids(inv, n, 's')
        r = self.cli('draw', '5')
        self.assertEqual(r.returncode, 2)
        self.assertIn('eligible population is 4', r.stderr)
        self.assertEqual(s.list_draws(self.store), [])

    def test_uniform_sampling_all_equiprobable_small_draw_paths(self):
        # 4 * 3 equally likely index paths: every ordered pair occurs exactly once.
        inv = self.inventory()
        results = []
        for first, second in itertools.product(range(4), range(3)):
            with patch.object(s.RandomStream, 'randbelow', side_effect=[first, second]):
                results.append(tuple(s.sample_ids(inv, 2, 'unused')))
        ids = [i['image_id'] for i in inv['population']['images']]
        self.assertCountEqual(results, list(itertools.permutations(ids, 2)))
        self.assertTrue(all(sum(i in pair for pair in results) == 6 for i in ids))

    def test_rejection_removes_modulo_bias(self):
        rng = s.RandomStream('test')
        with patch.object(rng, 'word', side_effect=[2**256 - 1, 5]) as word:
            self.assertEqual(rng.randbelow(3), 2)
            self.assertEqual(word.call_count, 2)

    def test_versioned_random_stream_golden_vector(self):
        rng = s.RandomStream('fixture-sampler-test-vector')
        self.assertEqual([hex(rng.word()) for _ in range(3)], [
            '0xb65854aac0329e56cdec17fe94660ef84568e9dd1b69a9f698669c1540ca9df',
            '0x9171d2d91cd57d4b593ecdd8450991ec236e25e26a3905c33a3c300beaf2904b',
            '0xb5ed3fe925f88139ebe40e91bc5891c979b3d6c5e709a1b6bd2edb18e058c7a',
        ])

    def test_persistence_generated_seed_and_inventory_reuse(self):
        inv = self.inventory()
        draw = s.create_draw(self.store, inv, 3)
        loaded, snapshot = s.load_draw(self.store, draw['sample_id'])
        self.assertEqual(loaded, draw)
        self.assertEqual(draw['image_ids'], s.sample_ids(snapshot, 3, draw['seed']))
        again = s.create_draw(self.store, self.inventory(), 3, draw['seed'])
        self.assertEqual(again['image_ids'], draw['image_ids'])
        self.assertNotEqual(again['sample_id'], draw['sample_id'])
        self.assertEqual(len(list((self.store / 'inventories').glob('*.json'))), 1)
        self.assertEqual(len(s.list_draws(self.store)), 2)

    def test_changes_do_not_rewrite_old_draw_or_replace_missing_images(self):
        draw = self.draw(4)
        self.make_leaf('Heaps/New', [b'new'])
        (self.heap / 'images/0.png').unlink()
        self.assertEqual(s.load_draw(self.store, draw['sample_id'])[0], draw)
        report = s.verify_draw(self.store, draw['sample_id'], self.repo)
        self.assertTrue(report['original_draw_reproduced'])
        self.assertEqual(report['images_available'], 3)
        self.assertFalse(report['ok'])
        self.assertEqual(self.cli('verify', draw['sample_id']).returncode, 1)
        self.assertEqual(self.cli('show', draw['sample_id']).returncode, 0)
        self.assertNotEqual(self.inventory()['inventory_id'], draw['inventory_id'])

    def test_changed_provenance_is_reported_while_frozen_metadata_survives(self):
        draw = self.draw(4)
        before = s.inspect_draw(self.store, draw['sample_id'], self.repo)['images']
        path = self.heap / 'sources.csv'
        path.write_text(path.read_text().replace('Example credit', 'Changed credit'))
        after = s.inspect_draw(self.store, draw['sample_id'], self.repo)['images']
        self.assertEqual(before, after)
        result = s.verify_draw(self.store, draw['sample_id'], self.repo)
        self.assertEqual(result['images_available'], 4)
        self.assertEqual(len(result['fixture_metadata_issues']), 1)
        self.assertEqual(result['fixture_metadata_issues'][0]['status'], 'changed')

    def test_records_and_fixture_paths_survive_checkout_relocation(self):
        draw = self.draw()
        relocated = (Path(self.temp.name) / 'moved-checkout').resolve()
        shutil.copytree(self.repo, relocated)
        store = relocated / 'Fixtures/Sampler/records'
        result = s.verify_draw(store, draw['sample_id'], relocated)
        self.assertTrue(result['ok'])
        shown = s.inspect_draw(store, draw['sample_id'], relocated, True)
        self.assertTrue(all(Path(r['available_path']).is_relative_to(relocated) for r in shown))

    def test_annotations_round_trip_revisions_deletions_and_metadata_separation(self):
        draw = self.draw()
        sid, image = draw['sample_id'], draw['image_ids'][0]
        original = (s.sample_dir(self.store, sid) / 'draw.json').read_bytes()
        before = self.inventory()['population']
        value = {'decision': 'accepted', 'tags': ['☃', 'a\nb'], 'nested': [None, True, 2.5]}
        s.annotate(self.store, sid, 'purpose', 'Example')
        s.annotate(self.store, sid, 'review', value, image_id=image, author='tester')
        s.annotate(self.store, sid, 'review', ['revised'], image_id=image)
        s.annotate(self.store, sid, 'purpose', delete=True)
        got = s.inspect_draw(self.store, sid, self.repo)
        self.assertEqual(got['annotations'], {'sample': {}, 'images': {image: {'review': ['revised']}}})
        self.assertEqual(got['annotation_history'][1]['value'], value)
        self.assertEqual((s.sample_dir(self.store, sid) / 'draw.json').read_bytes(), original)
        self.assertEqual(self.inventory()['population'], before)
        self.assertEqual(s.sample_ids(self.inventory(), 3, draw['seed']), draw['image_ids'])
        with self.assertRaises(ValueError):
            s.annotate(self.store, sid, 'review', 'bad', image_id='not-in-draw')

    def test_cli_stdin_json_null_and_reload(self):
        draw = self.draw()
        result = self.cli('annotate', draw['sample_id'], '--key', 'whatever', '--value-file', '-', input='null')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.cli('show', draw['sample_id'])
        self.assertIsNone(json.loads(result.stdout)['annotations']['sample']['whatever'])
        self.assertEqual(len(json.loads(self.cli('show', draw['sample_id'], '--paths').stdout)), 3)

    def test_public_engine_returns_persistent_draw_and_paths_from_another_cwd(self):
        store = self.repo / 'records with spaces'
        engine = Path(s.__file__).resolve().parent.parent / 'sample'
        command = [str(engine), '--repo', str(self.repo), '--store', str(store)]
        result = subprocess.run([*command, '3', '--seed', 'public engine'],
                                cwd=self.temp.name, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response['schema_version'], 1)
        draw = response['draw']
        self.assertEqual(draw['image_ids'], s.sample_ids(self.inventory(), 3, 'public engine'))
        self.assertEqual(response['population']['counts']['eligible'], 4)
        self.assertEqual([i['image_id'] for i in response['images']], draw['image_ids'])
        self.assertEqual([i['position'] for i in response['images']], [1, 2, 3])
        for image in response['images']:
            self.assertEqual('sha256:' + s.file_hash(Path(image['available_path'])), image['image_id'])
        self.assertEqual(s.load_draw(store, draw['sample_id'])[0], draw)
        old_syntax = subprocess.run([*command, 'draw', '3', '--seed', 'public engine'],
                                    cwd=self.temp.name, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(old_syntax.stdout)['draw']['image_ids'], draw['image_ids'])

    def test_shorthand_bounds_and_global_options(self):
        for size in ('-1', '5'):
            result = self.cli(size)
            self.assertEqual(result.returncode, 2)
            self.assertIn('sampler:', result.stderr)
        self.assertEqual(s.list_draws(self.store), [])
        result = self.cli('--repo=' + str(self.repo), '--store=' + str(self.store),
                          '2', '--seed', 'same')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['draw']['requested_size'], 2)

    def test_draw_reports_unavailable_saved_snapshot_with_nonzero_exit_and_keeps_record(self):
        inventory = s.save_inventory(self.store, self.inventory())
        (self.heap / 'images/0.png').unlink()
        result = self.cli('4', '--inventory', inventory['inventory_id'])
        self.assertEqual(result.returncode, 1, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(len(response['draw']['image_ids']), 4)
        self.assertEqual(sum(i['available_path'] is None for i in response['images']), 1)
        self.assertFalse(response['current_check']['ok'])
        self.assertEqual(s.load_draw(self.store, response['draw']['sample_id'])[0], response['draw'])

    def test_launcher_reports_missing_environment_and_runtime_rejects_other_minor_versions(self):
        engine = self.repo / 'Fixtures/sample'
        shutil.copy2(Path(s.__file__).resolve().parent.parent / 'sample', engine)
        result = subprocess.run([str(engine), '1'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('make setup-python', result.stderr)
        stderr = io.StringIO()
        with patch.object(s.sys, 'version_info', (3, 13)), contextlib.redirect_stderr(stderr):
            self.assertEqual(s.main(['1']), 2)
        self.assertIn('Python 3.14.x', stderr.getvalue())

    def test_concurrent_annotation_appends_preserve_every_event(self):
        draw = self.draw()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda n: s.annotate(self.store, draw['sample_id'], str(n), n), range(12)))
        events = s.read_events(self.store, draw)
        self.assertEqual([e['sequence'] for e in events], list(range(1, 13)))
        self.assertEqual(s.annotation_state(events)['sample'], {str(n): n for n in range(12)})

    def test_corrupt_history_and_records_fail_without_repairing_them(self):
        draw = self.draw()
        path = s.sample_dir(self.store, draw['sample_id']) / 'annotations.jsonl'
        path.write_text('{"partial":')
        with self.assertRaisesRegex(ValueError, 'Incomplete annotation'):
            s.annotate(self.store, draw['sample_id'], 'note', 'new')
        self.assertEqual(path.read_text(), '{"partial":')
        invpath = s.inventory_file(self.store, draw['inventory_id'])
        inventory = s.read_json(invpath)
        inventory['population']['images'].pop()
        invpath.write_text(json.dumps(inventory))
        with self.assertRaisesRegex(ValueError, 'checksum'):
            s.load_draw(self.store, draw['sample_id'])


if __name__ == '__main__':
    unittest.main()
