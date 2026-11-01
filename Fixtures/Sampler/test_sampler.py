"""Offline mechanics tests; synthetic byte fixtures make no image-quality claims."""
import concurrent.futures
import contextlib
import hashlib
import io
import itertools
import json
import stat
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import sampler as s


if sys.version_info[:2] != (3, 14):
    raise RuntimeError('Sampler tests target Python 3.14.x only; run make -C Fixtures test-sampler')


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
        self.assertNotIn('manifest_record', aliases[0])  # Rows are pinned by hash, not stored.
        self.assertEqual([l['status'] for l in inv['population']['leaves']], ['ok', 'ok'])
        self.assertIn('checkout', inv)
        draw = s.create_draw(self.store, inv, 4, 'all')
        shown = s.inspect_draw(self.store, draw['sample_id'], self.repo)
        rows = [p for image in shown['images'] for p in image['provenance']]
        self.assertEqual({p['status'] for p in rows}, {'frozen'})
        self.assertEqual({p['manifest_record']['transformation'] for p in rows}, {'source', 'variant'})
        self.assertTrue(all(p['source_records'][0]['credit_status'] == 'Example credit' for p in rows))
        self.assertEqual(shown['summary']['by_leaf'],
                         {'Fixtures/Heaps/Curatorial/Nested/Leaf': 2, 'Fixtures/Relationships/Variants': 2})
        self.assertEqual(shown['problems'], [])

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
        with self.assertRaisesRegex(s.SamplerError, 'unsafe fixture path'):
            s.fixture_path(self.repo, 'Fixtures/../secret')

    def test_requested_size_bounds_no_replacement_and_zero_draw(self):
        inv = self.inventory()
        self.assertEqual(s.sample_ids(inv, 0, 's'), [])
        self.assertEqual(set(s.sample_ids(inv, 4, 's')), {i['image_id'] for i in inv['population']['images']})
        for n in (-1, 5, True):
            with self.assertRaises(s.SamplerError):
                s.sample_ids(inv, n, 's')
        r = self.cli('draw', '5')
        self.assertEqual(r.returncode, 2)
        self.assertIn('eligible population is 4', r.stderr)
        error = json.loads(r.stdout)['error']
        self.assertEqual(error['code'], 'usage')
        self.assertIn('eligible population is 4', error['message'])
        self.assertEqual(s.list_draws(self.store)['draws'], [])

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
        listed = s.list_draws(self.store)
        self.assertEqual(len(listed['draws']), 2)
        self.assertEqual({d['status'] for d in listed['draws']}, {'ok'})
        self.assertEqual(listed['problems'], [])

    def test_changes_do_not_rewrite_old_draw_or_replace_missing_images(self):
        draw = self.draw(4)
        self.make_leaf('Heaps/New', [b'new'])
        (self.heap / 'images/0.png').unlink()
        self.assertEqual(s.load_draw(self.store, draw['sample_id'])[0], draw)
        report = s.verify_draw(self.store, draw['sample_id'], self.repo)
        self.assertTrue(report['original_draw_reproduced'])
        self.assertEqual(report['images_available'], 3)
        self.assertFalse(report['ok'])
        self.assertEqual([p['kind'] for p in report['problems']], ['image-unavailable'])
        self.assertEqual(self.cli('verify', draw['sample_id']).returncode, 1)
        self.assertEqual(self.cli('show', draw['sample_id']).returncode, 0)
        self.assertNotEqual(self.inventory()['inventory_id'], draw['inventory_id'])

    def test_changed_provenance_is_reported_against_its_pin_and_shown_as_current(self):
        draw = self.draw(4)
        heap_rows = lambda shown: [p for image in shown['images'] for p in image['provenance']
                                   if p['fixture_path'] == 'Fixtures/Heaps/Curatorial/Nested/Leaf']
        before = heap_rows(s.inspect_draw(self.store, draw['sample_id'], self.repo))
        self.assertEqual({p['status'] for p in before}, {'frozen'})
        path = self.heap / 'sources.csv'
        path.write_text(path.read_text().replace('Example credit', 'Changed credit'))
        shown = s.inspect_draw(self.store, draw['sample_id'], self.repo)
        after = heap_rows(shown)
        self.assertEqual({p['status'] for p in after}, {'changed'})
        self.assertEqual(after[0]['source_records'][0]['credit_status'], 'Changed credit')
        changed = [m for m in after[0]['metadata'] if m['status'] != 'frozen']
        self.assertEqual([(m['path'], m['status']) for m in changed],
                         [('Fixtures/Heaps/Curatorial/Nested/Leaf/sources.csv', 'changed')])
        self.assertTrue(changed[0]['pinned_sha256'] != changed[0]['observed_sha256'])
        self.assertEqual([p['kind'] for p in shown['problems']], ['metadata-changed'])
        self.assertEqual(self.cli('show', draw['sample_id']).returncode, 1)
        result = s.verify_draw(self.store, draw['sample_id'], self.repo)
        self.assertEqual(result['images_available'], 4)
        self.assertEqual(len(result['problems']), 1)
        self.assertEqual(result['problems'][0]['kind'], 'metadata-changed')
        self.assertEqual(result['problems'][0]['status'], 'changed')
        # A leaf that can no longer be read is reported once, and the other leaf still resolves.
        (self.heap / 'manifest.json').write_text('{not json')
        shown = s.inspect_draw(self.store, draw['sample_id'], self.repo)
        self.assertEqual({p['status'] for p in heap_rows(shown)}, {'unreadable'})
        self.assertEqual(sorted(p['kind'] for p in shown['problems']),
                         ['leaf-unreadable', 'metadata-changed', 'metadata-changed'])
        self.assertTrue(all(p['status'] == 'frozen' for image in shown['images'] for p in image['provenance']
                            if p['fixture_path'] == 'Fixtures/Relationships/Variants'))

    def test_records_and_fixture_paths_survive_checkout_relocation(self):
        draw = self.draw()
        relocated = (Path(self.temp.name) / 'moved-checkout').resolve()
        shutil.copytree(self.repo, relocated)
        store = relocated / 'Fixtures/Sampler/records'
        result = s.verify_draw(store, draw['sample_id'], relocated)
        self.assertTrue(result['ok'])
        shown = s.inspect_draw(store, draw['sample_id'], relocated, True)['images']
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
        with self.assertRaises(s.SamplerError):
            s.annotate(self.store, sid, 'review', 'bad', image_id='not-in-draw')

    def test_cli_stdin_json_null_and_reload(self):
        draw = self.draw()
        result = self.cli('annotate', draw['sample_id'], '--key', 'whatever', '--value-file', '-', input='null')
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.cli('show', draw['sample_id'])
        self.assertIsNone(json.loads(result.stdout)['annotations']['sample']['whatever'])
        self.assertEqual(len(json.loads(self.cli('show', draw['sample_id'], '--paths').stdout)['images']), 3)

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
            copied = Path(image['sampled_path'])
            self.assertEqual(copied.parent, (self.repo / 'Fixtures/output/sampled').resolve())
            self.assertEqual('sha256:' + s.file_hash(copied), image['image_id'])
            self.assertEqual(copied.stem, image['image_id'].removeprefix('sha256:'))  # No position prefix.
        self.assertTrue(response['output']['published'])
        self.assertEqual(response['output']['directory'], str(copied.parent))
        self.assertEqual(s.load_draw(store, draw['sample_id'])[0], draw)
        old_syntax = subprocess.run([*command, 'draw', '3', '--seed', 'public engine'],
                                    cwd=self.temp.name, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(old_syntax.stdout)['draw']['image_ids'], draw['image_ids'])

    def test_world_is_relocatable_opaque_and_receipted(self):
        world = (Path(self.temp.name) / 'elsewhere' / 'world one').resolve()
        result = self.cli('3', '--seed', 'opaque', '--world', str(world))
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        manifest_path = Path(response['output']['manifest'])
        self.assertEqual(manifest_path, world / 'world.json')
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(sorted(manifest), ['images', 'schema_version', 'world_id'])
        self.assertEqual(manifest['world_id'], response['draw']['sample_id'])
        self.assertEqual([e['file'] for e in manifest['images']], sorted(e['file'] for e in manifest['images']))
        self.assertEqual({e['id'] for e in manifest['images']}, set(response['draw']['image_ids']))
        self.assertEqual(sorted(p.name for p in world.iterdir()), sorted([e['file'] for e in manifest['images']] + ['world.json']))
        for entry in manifest['images']:
            self.assertEqual(sorted(entry), ['file', 'id'])
            self.assertEqual('sha256:' + s.file_hash(world / entry['file']), entry['id'])
            self.assertEqual(Path(entry['file']).stem, entry['id'].removeprefix('sha256:'))
        text = manifest_path.read_text()
        for leak in ('Fixtures', 'Heaps', 'Relationships', 'position', 'seed', str(self.repo)):
            self.assertNotIn(leak, text)
        shown = s.inspect_draw(self.store, response['draw']['sample_id'], self.repo)
        receipt = shown['annotations']['sample']['publication']
        self.assertEqual((receipt['directory'], receipt['manifest'], receipt['image_count']),
                         (str(world), str(world / 'world.json'), 3))
        self.assertEqual([e['author'] for e in shown['annotation_history']], ['Fixtures/sample'])
        self.assertEqual(shown['problems'], [])

    def test_publish_rematerializes_a_draw_under_the_same_world_id(self):
        first = json.loads(self.cli('2', '--seed', 'again').stdout)
        sample_id = first['draw']['sample_id']
        other = (Path(self.temp.name) / 'other-world').resolve()
        result = self.cli('publish', sample_id, '--world', str(other))
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response['sample_id'], sample_id)
        self.assertTrue(response['output']['published'])
        manifests = [json.loads((Path(d) / 'world.json').read_text())
                     for d in (first['output']['directory'], other)]
        self.assertEqual(manifests[0], manifests[1])
        self.assertEqual(manifests[0]['world_id'], sample_id)
        shown = s.inspect_draw(self.store, sample_id, self.repo)
        self.assertEqual([e['key'] for e in shown['annotation_history']], ['publication', 'publication'])
        self.assertEqual(shown['annotations']['sample']['publication']['directory'], str(other))
        (self.heap / 'images/0.png').unlink()
        (self.related / 'images/0.png').unlink()
        result = self.cli('publish', sample_id, '--world', str(other))
        self.assertEqual(result.returncode, 1, result.stderr)
        response = json.loads(result.stdout)
        self.assertFalse(response['output']['published'])
        self.assertIn('not-published', [p['kind'] for p in response['problems']])
        self.assertEqual(json.loads((other / 'world.json').read_text()), manifests[1])  # Previous world intact.
        self.assertEqual(len(s.inspect_draw(self.store, sample_id, self.repo)['annotation_history']), 2)

    def test_next_draw_replaces_only_a_previous_world_and_copies_are_independent(self):
        output = self.repo / 'Fixtures/output'
        sampled = output / 'sampled'
        sampled.mkdir(parents=True)
        (sampled / 'world.json').write_text('{"schema_version": 1, "world_id": "draw-old", "images": []}')
        (sampled / 'old/subdir').mkdir(parents=True)
        (sampled / 'old/subdir/stale').write_bytes(b'stale')
        (sampled / 'external-link').symlink_to(self.heap, target_is_directory=True)
        (sampled / '.DS_Store').write_bytes(b'finder')
        (output / 'AGENTS.md').write_text('Keep this')
        (output / 'other-output').write_bytes(b'Keep this too')
        # A manifest alone does not make a directory a world: unlisted entries are refused by name, not deleted.
        refused = self.cli('3', '--seed', 'first')
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertIn('does not list: external-link, old', json.loads(refused.stdout)['error']['message'])
        self.assertEqual((sampled / 'old/subdir/stale').read_bytes(), b'stale')
        self.assertTrue((sampled / 'external-link').is_symlink())
        (sampled / 'external-link').unlink()
        shutil.rmtree(sampled / 'old')
        first = json.loads(self.cli('3', '--seed', 'first').stdout)  # Only .DS_Store is tolerated and removed.
        self.assertFalse((sampled / '.DS_Store').exists())
        self.assertEqual(stat.S_IMODE(sampled.stat().st_mode), 0o777 & ~s.current_umask())
        self.assertEqual(len(list(sampled.iterdir())), 4)  # Three copies and world.json.
        image = first['images'][0]
        Path(image['sampled_path']).write_bytes(b'edited copy')
        self.assertEqual('sha256:' + s.file_hash(Path(image['available_path'])), image['image_id'])
        second = self.cli('1', '--seed', 'second')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(len(list(sampled.iterdir())), 2)
        self.assertEqual(json.loads((sampled / 'world.json').read_text())['world_id'],
                         json.loads(second.stdout)['draw']['sample_id'])
        self.assertEqual((output / 'AGENTS.md').read_text(), 'Keep this')
        self.assertEqual((output / 'other-output').read_bytes(), b'Keep this too')
        self.assertTrue(self.heap.is_dir())
        self.assertEqual(s.load_draw(self.store, first['draw']['sample_id'])[0], first['draw'])
        self.assertEqual(self.cli('0').returncode, 0)
        self.assertEqual([p.name for p in sampled.iterdir()], ['world.json'])
        self.assertEqual(json.loads((sampled / 'world.json').read_text())['images'], [])

    def test_invalid_draw_and_failed_copy_preserve_previous_world(self):
        sampled = self.repo / 'Fixtures/output/sampled'
        sampled.mkdir(parents=True)
        stem = '0' * 64  # A listed file name is enough to count as a previous world; bytes are not rehashed.
        (sampled / 'world.json').write_text(json.dumps(dict(
            schema_version=1, world_id='draw-old', images=[dict(id='sha256:' + stem, file=stem + '.bin')])))
        sentinel = sampled / (stem + '.bin')
        sentinel.write_bytes(b'previous')
        self.assertEqual(self.cli('5').returncode, 2)
        draw = self.draw()
        images = s.inspect_draw(self.store, draw['sample_id'], self.repo, paths_only=True)['images']
        def corrupt_copy(source, destination):
            destination.write_bytes(b'incomplete copy')
        with patch.object(s.shutil, 'copyfile', side_effect=corrupt_copy):
            with self.assertRaisesRegex(s.SamplerError, 'checksum differs'):
                s.publish_world(self.repo, self.store, draw, images)
        self.assertEqual(sentinel.read_bytes(), b'previous')
        self.assertEqual(list(sampled.parent.iterdir()), [sampled])
        stdout = io.StringIO()
        with patch.object(s.shutil, 'copyfile', side_effect=OSError('disk full')), contextlib.redirect_stdout(stdout):
            status = s.main(['--repo', str(self.repo), '--store', str(self.store), '2'])
        self.assertEqual(status, 1)
        result = json.loads(stdout.getvalue())
        self.assertIn('disk full', result['output']['error'])
        self.assertFalse(result['output']['published'])
        self.assertTrue(all(i['sampled_path'] is None for i in result['images']))
        self.assertEqual(s.load_draw(self.store, result['draw']['sample_id'])[0], result['draw'])
        self.assertEqual(sentinel.read_bytes(), b'previous')
        self.assertEqual(s.read_events(self.store, result['draw']), [])  # No receipt without a publication.

    def test_failed_directory_exchange_preserves_the_previous_world(self):
        first = json.loads(self.cli('2').stdout)
        target = Path(first['output']['directory'])
        before = {p.name: p.read_bytes() for p in target.iterdir()}
        stdout = io.StringIO()
        with patch.object(s, 'exchange_directories', side_effect=OSError('exchange unavailable')), \
                contextlib.redirect_stdout(stdout):
            code = s.main(['--repo', str(self.repo), '--store', str(self.store), '3'])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertFalse(report['output']['published'])
        self.assertFalse(report['output']['receipt_recorded'])
        self.assertIn('exchange unavailable', report['output']['error'])
        self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
        self.assertEqual(list(target.parent.iterdir()), [target])
        self.assertEqual(s.read_events(self.store, report['draw']), [])

    def test_first_install_failure_leaves_no_visible_or_partial_world(self):
        stdout = io.StringIO()
        with patch.object(Path, 'rename', side_effect=OSError('rename failed')), contextlib.redirect_stdout(stdout):
            code = s.main(['--repo', str(self.repo), '--store', str(self.store), '3'])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertFalse(report['output']['published'])
        self.assertEqual(list((self.repo / 'Fixtures/output').iterdir()), [])

    def test_exchange_installs_complete_world_before_cleaning_old_directory(self):
        first = json.loads(self.cli('2').stdout)
        target = Path(first['output']['directory'])
        old_manifest = (target / 'world.json').read_bytes()
        draw = self.draw(3)
        images = s.inspect_draw(self.store, draw['sample_id'], self.repo, True)['images']
        original_cleanup = s.cleanup_world_stage

        def inspect_cleanup(staged):
            self.assertNotEqual(staged, target)
            self.assertEqual((staged / 'world.json').read_bytes(), old_manifest)
            new = json.loads((target / 'world.json').read_text())
            self.assertEqual(new['world_id'], draw['sample_id'])
            for row in new['images']:
                self.assertEqual('sha256:' + s.file_hash(target / row['file']), row['id'])
            return original_cleanup(staged)

        with patch.object(s, 'cleanup_world_stage', side_effect=inspect_cleanup) as cleanup:
            _, _, problems = s.publish_world(self.repo, self.store, draw, images)
        self.assertEqual(cleanup.call_count, 1)
        self.assertEqual(problems, [])

    def test_cleanup_failure_reports_installed_world_and_still_records_receipt(self):
        self.assertEqual(self.cli('2').returncode, 0)
        stdout = io.StringIO()
        with patch.object(s.shutil, 'rmtree', side_effect=OSError('cleanup denied')), contextlib.redirect_stdout(stdout):
            code = s.main(['--repo', str(self.repo), '--store', str(self.store), '3'])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertTrue(report['output']['published'])
        self.assertTrue(report['output']['receipt_recorded'])
        self.assertEqual([p['kind'] for p in report['problems']], ['world-cleanup-failed'])
        self.assertTrue(Path(report['problems'][0]['path']).is_dir())
        self.assertEqual(json.loads(Path(report['output']['manifest']).read_text())['world_id'],
                         report['draw']['sample_id'])
        self.assertEqual(len(s.read_events(self.store, report['draw'])), 1)

    def test_receipt_failure_is_nonzero_and_republication_can_record_a_new_receipt(self):
        stdout = io.StringIO()
        with patch.object(s, 'publish_receipt', side_effect=OSError('receipt denied')), contextlib.redirect_stdout(stdout):
            code = s.main(['--repo', str(self.repo), '--store', str(self.store), '2'])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 1)
        self.assertTrue(report['output']['published'])
        self.assertFalse(report['output']['receipt_recorded'])
        self.assertEqual([p['kind'] for p in report['problems']], ['publication-receipt-failed'])
        manifest = Path(report['output']['manifest']).read_bytes()
        self.assertEqual(s.read_events(self.store, report['draw']), [])
        again = self.cli('publish', report['draw']['sample_id'])
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertTrue(json.loads(again.stdout)['output']['receipt_recorded'])
        self.assertEqual(Path(report['output']['manifest']).read_bytes(), manifest)
        self.assertEqual(len(s.read_events(self.store, report['draw'])), 1)

    def test_missing_redundant_alias_is_reported_but_does_not_block_publication(self):
        extra = self.make_leaf('Heaps/Alias', [b'one'])
        (extra / 'images/0.png').unlink()
        run = self.cli('4')
        report = json.loads(run.stdout)
        self.assertEqual(run.returncode, 1)
        self.assertEqual(report['population']['counts']['eligible'], 4)
        self.assertEqual(report['current_check']['images_available'], 4)
        self.assertFalse(report['current_check']['ok'])
        self.assertTrue(report['current_check']['publication_ready'])
        self.assertTrue(report['output']['published'])
        self.assertTrue(report['output']['receipt_recorded'])
        self.assertEqual({p['kind'] for p in report['problems']}, {'image-unavailable', 'alias-unavailable'})
        self.assertEqual(self.cli('publish', report['draw']['sample_id']).returncode, 1)

    def test_unsafe_world_destinations_are_refused_before_drawing(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        (outside / 'keep').write_bytes(b'keep')
        link = self.repo / 'Fixtures/output/sampled'
        link.parent.mkdir(parents=True)
        link.symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.cli('1').returncode, 2)
        link.unlink()
        cases = {
            'non-world directory': ['--world', str(outside)],
            'inside the fixtures': ['--world', str(self.repo / 'Fixtures/Heaps/world')],
            'store inside the world': ['--store', str(outside / 'records'), '--world', str(outside)],
            'world containing the store': ['--world', str(self.repo / 'Fixtures/Sampler')],
            'a file': ['--world', str(outside / 'keep')],
            'a manifest-shaped file among other data': ['--world', str(outside)],
        }
        (outside / 'world.json').write_text('{"name": "not a world"}')
        if (self.repo / 'FIXTURES').exists():  # Case-insensitive filesystem: another spelling of the same directory.
            cases['inside the fixtures, spelled differently'] = ['--world', str(self.repo / 'FIXTURES/Heaps/world')]
            cases['store spelled differently'] = ['--world', str(self.repo / 'fixtures/Sampler/records/world')]
        for name, extra in cases.items():
            globals_, rest = (extra[:2], extra[2:]) if extra[0] == '--store' else ([], extra)
            result = self.cli(*globals_, '1', *rest)
            self.assertEqual(result.returncode, 2, name)
            self.assertEqual(json.loads(result.stdout)['error']['code'], 'output', name)
        self.assertEqual((outside / 'keep').read_bytes(), b'keep')
        self.assertEqual(sorted(p.name for p in outside.iterdir()), ['keep', 'world.json'])
        self.assertEqual(s.list_draws(self.store)['draws'], [])  # Refused before any record was created.

    def test_concurrent_publications_leave_one_complete_world(self):
        draws = [self.draw(2, 'first'), self.draw(3, 'second')]
        images = [s.inspect_draw(self.store, d['sample_id'], self.repo, True)['images'] for d in draws]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            published = list(pool.map(lambda pair: s.publish_world(self.repo, self.store, *pair)[0],
                                      zip(draws, images)))
        actual = {p.name for p in (self.repo / 'Fixtures/output/sampled').iterdir()}
        self.assertIn(actual, [{Path(row['sampled_path']).name for row in rows} | {'world.json'} for rows in published])

    def test_shorthand_bounds_and_global_options(self):
        for size in ('-1', '5'):
            result = self.cli(size)
            self.assertEqual(result.returncode, 2)
            self.assertIn('sampler:', result.stderr)
        self.assertEqual(s.list_draws(self.store)['draws'], [])
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
        self.assertFalse(response['output']['published'])
        self.assertFalse((self.repo / 'Fixtures/output/sampled').exists())
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

    def test_annotation_values_with_unicode_line_separators_stay_readable(self):
        draw = self.draw(1, 'separators')
        value = dict(note='line\u2028separator\u2029and\u0085next', directory='/tmp/w\u2028sep')
        s.annotate(self.store, draw['sample_id'], 'purpose', value)
        shown = s.inspect_draw(self.store, draw['sample_id'], self.repo)
        self.assertEqual(shown['annotations']['sample']['purpose'], value)
        self.assertEqual(s.verify_draw(self.store, draw['sample_id'], self.repo)['problems'], [])

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
        with self.assertRaisesRegex(s.SamplerError, 'ends mid-line'):
            s.annotate(self.store, draw['sample_id'], 'note', 'new')
        self.assertEqual(path.read_text(), '{"partial":')
        shown = s.inspect_draw(self.store, draw['sample_id'], self.repo)
        self.assertEqual([p['kind'] for p in shown['problems']], ['annotations-unreadable'])
        self.assertEqual(shown['draw'], draw)
        invpath = s.inventory_file(self.store, draw['inventory_id'])
        inventory = s.read_json(invpath, 'test')
        inventory['population']['images'].pop()
        invpath.write_text(json.dumps(inventory))
        with self.assertRaisesRegex(s.SamplerError, 'checksum') as caught:
            s.load_draw(self.store, draw['sample_id'])
        self.assertEqual(caught.exception.code, 'record-damaged')

    def test_malformed_leaves_are_named_with_their_field(self):
        manifest = self.heap / 'manifest.json'
        cases = [
            (lambda m: m.pop('kind'), 'lacks the field "kind"'),
            (lambda m: m['images'][0].pop('byte_sha256'), 'images\\[0\\] lacks the field "byte_sha256"'),
            (lambda m: m['images'][0].__setitem__('file', 'sources/0.png'), 'must be inside images/'),
            (lambda m: m.__setitem__('schema_version', 2), 'unsupported schema_version'),
        ]
        original = manifest.read_text()
        leaf_path = 'Fixtures/Heaps/Curatorial/Nested/Leaf'
        for mutate, expected in cases:
            value = json.loads(original)
            mutate(value)
            manifest.write_text(json.dumps(value))
            with self.assertRaisesRegex(s.SamplerError, 'Fixture leaf ' + leaf_path + ': .*' + expected) as caught:
                s.read_leaf(self.repo, manifest)
            self.assertEqual(caught.exception.code, 'fixture')
            self.assertEqual(caught.exception.details['leaf'], leaf_path)
        manifest.write_text(original)
        sources = self.heap / 'sources.csv'
        sources.unlink()
        with self.assertRaisesRegex(s.SamplerError, 'sources.csv is missing'):
            s.read_leaf(self.repo, manifest)
        sources.write_text('source_filename,credit\nx,y\n')
        with self.assertRaisesRegex(s.SamplerError, 'family_id column'):
            s.read_leaf(self.repo, manifest)

    def test_excluded_leaf_is_recorded_and_the_draw_proceeds_with_a_nonzero_exit(self):
        (self.heap / 'sources.csv').unlink()
        inv = self.inventory()
        self.assertEqual(inv['population']['counts'], dict(leaves=2, excluded_leaves=1, manifest_records=2,
                                                           distinct_images=2, eligible=2, alias_records=0))
        excluded = [l for l in inv['population']['leaves'] if l['status'] == 'excluded']
        self.assertEqual(excluded[0]['fixture_path'], 'Fixtures/Heaps/Curatorial/Nested/Leaf')
        self.assertIn('sources.csv is missing', excluded[0]['error']['message'])
        result = self.cli('2', '--seed', 'partial')
        self.assertEqual(result.returncode, 1, result.stderr)
        response = json.loads(result.stdout)
        self.assertTrue(response['output']['published'])
        self.assertEqual([p['kind'] for p in response['problems']], ['leaf-excluded'])
        self.assertEqual(response['problems'][0]['fixture_path'], 'Fixtures/Heaps/Curatorial/Nested/Leaf')
        self.assertEqual(response['summary']['by_leaf'], {'Fixtures/Relationships/Variants': 2})
        self.assertEqual(self.cli('inventory').returncode, 1)
        # Restoring the leaf changes the population and therefore the snapshot identity.
        (self.heap / 'sources.csv').write_text('family_id,credit_status\nsource-a,Example credit\n')
        self.assertNotEqual(self.inventory()['inventory_id'], inv['inventory_id'])
        self.assertEqual(self.inventory()['population']['counts']['eligible'], 4)

    def test_bad_leaf_field_types_and_paths_are_named_json_problems(self):
        path = self.heap / 'manifest.json'
        original = path.read_text()
        for key, value in [('family_id', ['wrong']), ('parents', {}), ('file', '.'), ('file', 'images/\0bad')]:
            with self.subTest(key=key, value=value):
                data = json.loads(original)
                data['images'][0][key] = value
                path.write_text(json.dumps(data))
                run = self.cli('inventory')
                self.assertEqual(run.returncode, 1, run.stderr)
                report = json.loads(run.stdout)
                self.assertEqual(report['counts']['eligible'], 2)
                self.assertEqual([p['kind'] for p in report['problems']], ['leaf-excluded'])
                self.assertIn('Fixtures/Heaps/Curatorial/Nested/Leaf', report['problems'][0]['message'])
                self.assertNotIn('Traceback', run.stderr)

    def test_unreadable_leaf_is_excluded_without_hiding_the_remaining_population(self):
        original_read = Path.read_bytes

        def read(path):
            if path == (self.heap / 'sources.csv').resolve():
                raise PermissionError('catalog denied')
            return original_read(path)

        with patch.object(Path, 'read_bytes', read):
            inventory = self.inventory()
        self.assertEqual(inventory['population']['counts']['eligible'], 2)
        self.assertIn('catalog denied', s.excluded_leaves(inventory)[0]['error']['message'])

    def test_non_utf8_annotations_are_reported_without_modifying_the_log(self):
        draw = self.draw()
        path = s.sample_dir(self.store, draw['sample_id']) / 'annotations.jsonl'
        damaged = b'\xff\n'
        path.write_bytes(damaged)
        for command in ('show', 'verify'):
            run = self.cli(command, draw['sample_id'])
            self.assertEqual(run.returncode, 1, run.stderr)
            report = json.loads(run.stdout)
            self.assertEqual([p['kind'] for p in report['problems']], ['annotations-unreadable'])
            self.assertEqual(report['problems'][0]['code'], 'record-damaged')
        run = self.cli('annotate', draw['sample_id'], '--key', 'note', '--json', 'null')
        self.assertEqual(run.returncode, 2, run.stderr)
        self.assertEqual(json.loads(run.stdout)['error']['code'], 'record-damaged')
        self.assertEqual(path.read_bytes(), damaged)

    def legacy_inventory(self):
        """A schema 1 snapshot as the first sampler release wrote it: rows embedded per alias."""
        current = self.inventory()
        pop = json.loads(json.dumps(current['population']))
        repo = self.repo.resolve()
        leaves = {m.parent.relative_to(repo).as_posix(): s.read_leaf(repo, m) for m in s.manifests(repo)}
        for item in pop['images']:
            for alias in item['aliases']:
                leaf = leaves[alias['fixture_path']]
                image = next(i for i in leaf['images'] if alias['path'].endswith('/' + i['name']))
                alias.update(manifest_record=image['record'], source_records=image['source_records'],
                             import_record=image['import_record'])
                alias['availability'] = dict(status=alias['availability']['status'],
                                             observed_sha256=item['byte_sha256'])
        pop['schema_version'] = 1
        del pop['leaves']
        del pop['counts']['excluded_leaves']
        return dict(inventory_id=s.digest(pop), created_at=s.utc(), population=pop)

    def test_schema_1_snapshots_still_load_replay_and_show(self):
        legacy = s.save_inventory(self.store, self.legacy_inventory())
        draw = s.create_draw(self.store, legacy, 3, 'legacy')
        loaded, snapshot = s.load_draw(self.store, draw['sample_id'])
        self.assertEqual(snapshot['population']['schema_version'], 1)
        self.assertEqual(loaded['image_ids'], s.sample_ids(self.inventory(), 3, 'legacy'))
        shown = s.inspect_draw(self.store, draw['sample_id'], self.repo)
        self.assertEqual({p['status'] for image in shown['images'] for p in image['provenance']}, {'frozen'})
        self.assertEqual(shown['problems'], [])
        self.assertTrue(s.verify_draw(self.store, draw['sample_id'], self.repo)['ok'])
        self.assertEqual(json.loads(self.cli('inventory').stdout)['counts']['excluded_leaves'], 0)
        self.assertEqual(self.cli('show', draw['sample_id'], '--paths').returncode, 0)

    def test_argument_mistakes_are_json_errors_too(self):
        result = self.cli('nonsense')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['error']['code'], 'usage')
        result = self.cli('show', 'draw-short')
        self.assertEqual(result.returncode, 2)
        self.assertIn('full sample ID', json.loads(result.stdout)['error']['message'])
        draw = self.draw()
        result = self.cli('annotate', draw['sample_id'], '--key', 'k', '--json', '{not json')
        self.assertEqual(result.returncode, 2)
        self.assertIn('not valid JSON', json.loads(result.stdout)['error']['message'])

    def test_list_reports_damaged_and_snapshotless_draws_without_hiding_the_rest(self):
        good, damaged, orphan = self.draw(1, 'good'), self.draw(1, 'damaged'), self.draw(1, 'orphan')
        (s.sample_dir(self.store, damaged['sample_id']) / 'draw.json').write_text('{"broken": true}')
        s.inventory_file(self.store, orphan['inventory_id']).unlink()
        result = self.cli('list')
        self.assertEqual(result.returncode, 1, result.stderr)
        listed = json.loads(result.stdout)
        status = {d['sample_id']: d['status'] for d in listed['draws']}
        self.assertEqual(status, {good['sample_id']: 'snapshot-missing', damaged['sample_id']: 'damaged',
                                  orphan['sample_id']: 'snapshot-missing'})
        broken = next(d for d in listed['draws'] if d['status'] == 'damaged')
        self.assertEqual(broken['error']['code'], 'record-invalid')
        self.assertIn('lacks the field', broken['error']['message'])
        self.assertEqual(len(listed['problems']), 3)

    def test_show_and_verify_degrade_when_the_snapshot_is_missing(self):
        draw = self.draw(2)
        s.inventory_file(self.store, draw['inventory_id']).unlink()
        result = self.cli('show', draw['sample_id'])
        self.assertEqual(result.returncode, 1, result.stderr)
        shown = json.loads(result.stdout)
        self.assertEqual(shown['draw'], draw)
        self.assertFalse(shown['snapshot_available'])
        self.assertEqual([p['kind'] for p in shown['problems']], ['snapshot-unavailable'])
        self.assertEqual(shown['problems'][0]['code'], 'record-missing')
        self.assertEqual([i['image_id'] for i in shown['current_locations']], draw['image_ids'])
        self.assertTrue(all(i['available_path'] is None for i in shown['current_locations']))
        verified = s.verify_draw(self.store, draw['sample_id'], self.repo)
        self.assertFalse(verified['original_draw_reproduced'])
        self.assertFalse(verified['ok'])
        with self.assertRaises(s.SamplerError):
            s.annotate(self.store, draw['sample_id'], 'k', 'v')

    def test_list_reports_draw_directories_whose_draw_json_is_missing(self):
        good, damaged = self.draw(1), self.draw(2)
        (s.sample_dir(self.store, damaged['sample_id']) / 'draw.json').unlink()
        run = self.cli('list')
        self.assertEqual(run.returncode, 1, run.stderr)
        report = json.loads(run.stdout)
        entries = {entry['sample_id']: entry for entry in report['draws']}
        self.assertEqual(entries[good['sample_id']]['status'], 'ok')
        self.assertEqual(entries[damaged['sample_id']]['status'], 'damaged')
        self.assertEqual(entries[damaged['sample_id']]['error']['code'], 'record-missing')
        self.assertEqual([p['kind'] for p in report['problems']], ['draw-damaged'])

    def test_inventory_exit_code_reports_fixture_problems(self):
        self.assertEqual(self.cli('inventory').returncode, 0)
        (self.heap / 'images/0.png').unlink()
        (self.heap / 'images/extra.png').write_bytes(b'extra')
        result = self.cli('inventory')
        self.assertEqual(result.returncode, 1)
        kinds = sorted(p['kind'] for p in json.loads(result.stdout)['problems'])
        self.assertEqual(kinds, ['alias-unavailable', 'unlisted-input'])

    def test_records_follow_the_umask(self):
        previous = os.umask(0o022)
        self.addCleanup(os.umask, previous)
        draw = self.draw()
        mode = (s.sample_dir(self.store, draw['sample_id']) / 'draw.json').stat().st_mode & 0o777
        self.assertEqual(mode, 0o644)
        self.assertEqual(s.inventory_file(self.store, draw['inventory_id']).stat().st_mode & 0o777, 0o644)


if __name__ == '__main__':
    unittest.main()
