"""Exclusion worlds use published IDs; the returned world and saved draw stay ordinary."""
import copy
import hashlib
import itertools
import json
from pathlib import Path
import shutil
import subprocess
import unittest
from unittest.mock import patch

import sampler as s
import test_sampler as mechanics


class SampleWithoutTests(unittest.TestCase):
    make_leaf = mechanics.SamplerTests.make_leaf
    inventory = mechanics.SamplerTests.inventory
    cli = mechanics.SamplerTests.cli

    def setUp(self):
        mechanics.SamplerTests.setUp(self)
        self.engine = s.REPO / 'Fixtures/sampleWithout'

    def world(self, size=2):
        result = self.cli(str(size), '--seed', 'exclusion source')
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def without(self, source, size, *options):
        return subprocess.run([str(self.engine), '--repo', str(self.repo), '--store', str(self.store),
                               str(source), str(size), *options], cwd=self.temp.name,
                              capture_output=True, text=True)

    def assert_rejected_without_drawing(self, source, size, *options):
        before = s.list_draws(self.store)
        inventories = sorted((self.store / 'inventories').glob('*.json'))
        result = self.without(source, size, *options)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('error', json.loads(result.stdout))
        self.assertEqual(s.list_draws(self.store), before)
        self.assertEqual(sorted((self.store / 'inventories').glob('*.json')), inventories)
        return json.loads(result.stdout)['error']

    def test_exact_aliases_are_excluded_and_world_copies_are_not_needed(self):
        source = self.world(1)
        source_dir = Path(source['output']['directory'])
        image = source['images'][0]
        self.make_leaf('Heaps/Alias', [Path(image['available_path']).read_bytes()])
        Path(image['sampled_path']).unlink()
        original_manifest = (source_dir / 'world.json').read_bytes()
        result = self.without(source_dir, 3, '--seed', 'remaining')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['output']['published'])
        self.assertEqual(report['output']['image_count'], 3)
        self.assertEqual(report['warnings'], [])
        self.assertEqual(report['problems'], [])
        self.assertEqual(report['population']['counts']['eligible'], 4)
        self.assertEqual(report['exclusion']['requested_count'], 1)
        self.assertEqual(report['exclusion']['matched_count'], 1)
        self.assertEqual(report['exclusion']['remaining_eligible'], 3)
        self.assertEqual(report['exclusion']['manifest_sha256'], hashlib.sha256(original_manifest).hexdigest())
        self.assertEqual(report['exclusion']['world_id'], source['output']['world_id'])
        expected = {i['image_id'] for i in self.inventory()['population']['images']} - {image['image_id']}
        self.assertEqual(set(report['draw']['image_ids']), expected)
        self.assertEqual(report['draw']['exclusion'], report['exclusion'])
        self.assertEqual((source_dir / 'world.json').read_bytes(), original_manifest)
        world = json.loads(Path(report['output']['manifest']).read_text())
        self.assertEqual(set(world), {'schema_version', 'world_id', 'images'})
        self.assertEqual({entry['id'] for entry in world['images']}, expected)

    def test_absent_ids_warn_and_unknown_additive_fields_are_ignored(self):
        source = self.world(1)
        directory = Path(source['output']['directory'])
        path = directory / 'world.json'
        manifest = json.loads(path.read_text())
        absent = 'sha256:' + '0' * 64
        manifest['images'].append(dict(id=absent, file='0' * 64 + '.png', optional='future'))
        manifest['images'].sort(key=lambda entry: entry['file'])
        manifest['optional'] = {'note': 'An additive field'}
        path.write_text(json.dumps(manifest))
        result = self.without(directory, 3)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['exclusion']['unmatched_image_ids'], [absent])
        self.assertEqual(report['exclusion']['requested_count'], 2)
        self.assertEqual(report['exclusion']['matched_count'], 1)
        self.assertEqual([warning['image_id'] for warning in report['warnings']], [absent])
        self.assertEqual(report['problems'], [])
        self.assertTrue(report['output']['receipt_recorded'])

    def test_unavailable_exclusion_warns_but_other_missing_fixtures_remain_problems(self):
        source = self.world(2)
        directory = source['output']['directory']
        missing = source['images'][0]
        Path(missing['available_path']).unlink()
        result = self.without(directory, 2)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['exclusion']['unmatched_image_ids'], [missing['image_id']])
        self.assertEqual(report['exclusion']['remaining_eligible'], 2)
        self.assertEqual({warning['kind'] for warning in report['warnings']}, {'exclusion-unmatched', 'alias-unavailable'})
        self.assertTrue(any('path' in warning for warning in report['warnings']))
        self.assertEqual(report['population']['problems'], [])
        self.assertEqual(report['problems'], [])
        Path(report['images'][0]['available_path']).unlink()  # Outside the supplied world's IDs.
        result = self.without(directory, 1)
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['output']['published'])
        self.assertEqual({problem['kind'] for problem in report['problems']}, {'alias-unavailable'})

    def test_filtered_draw_replays_and_republishes_without_the_input_world_or_original_draw(self):
        source = self.world(2)
        directory = Path(source['output']['directory'])
        result = self.without(directory, 2, '--seed', 'stable')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        again = self.without(directory, 2, '--seed', 'stable')
        self.assertEqual(json.loads(again.stdout)['draw']['image_ids'], report['draw']['image_ids'])
        self.assertNotEqual(json.loads(again.stdout)['draw']['sample_id'], report['draw']['sample_id'])
        shutil.rmtree(directory)
        shutil.rmtree(s.sample_dir(self.store, source['draw']['sample_id']))
        sample_id = report['draw']['sample_id']
        self.assertEqual(self.cli('verify', sample_id).returncode, 0)
        self.assertEqual(json.loads(self.cli('show', sample_id).stdout)['draw'], report['draw'])
        published = self.cli('publish', sample_id)
        self.assertEqual(published.returncode, 0, published.stderr)
        self.assertEqual(json.loads(published.stdout)['output']['world_id'], sample_id)
        self.assertEqual([image['image_id'] for image in json.loads(published.stdout)['images']], report['draw']['image_ids'])

    def test_zero_size_bounds_and_no_overlap_preserve_previous_world_and_records(self):
        source = self.world(3)
        directory = Path(source['output']['directory'])
        destination = Path(self.world(1)['output']['directory'])
        before = {p.name: p.read_bytes() for p in destination.iterdir()}
        error = self.assert_rejected_without_drawing(directory, 2, '--world', str(destination))
        self.assertIn('1 eligible images remain', error['message'])
        self.assertEqual({p.name: p.read_bytes() for p in destination.iterdir()}, before)
        self.assert_rejected_without_drawing(directory, -1)
        zero = self.without(directory, 0)
        self.assertEqual(zero.returncode, 0, zero.stderr)
        self.assertTrue(json.loads(zero.stdout)['output']['published'])
        self.assertEqual(json.loads(zero.stdout)['output']['image_count'], 0)
        empty_world = json.loads(zero.stdout)['output']['directory']
        self.assertIn('No image IDs', self.assert_rejected_without_drawing(empty_world, 0)['message'])
        manifest = dict(schema_version=1, world_id='a former world', images=[dict(id='sha256:' + '0' * 64, file='0' * 64 + '.png')])
        (directory / 'world.json').write_text(json.dumps(manifest))
        self.assertIn('No image IDs', self.assert_rejected_without_drawing(directory, 1)['message'])

    def test_malformed_manifests_name_world_json_and_leave_no_draw(self):
        source = self.world(2)
        directory = Path(source['output']['directory'])
        path = directory / 'world.json'
        good = json.loads(path.read_text())
        invalid = [None, [], {}, dict(good, schema_version=True), dict(good, schema_version=2),
                   dict(good, world_id=''), dict(good, images={}), dict(good, images=[None]),
                   dict(good, images=list(reversed(good['images']))), dict(good, images=[good['images'][0]] * 2)]
        for changes in ({'id': 'broken'}, {'file': '../' + good['images'][0]['file']},
                        {'file': '/tmp/' + good['images'][0]['file']}, {'file': good['images'][1]['file']},
                        {'file': 'name.png'}, {'id': True}):
            broken = copy.deepcopy(good)
            broken['images'][0].update(changes)
            invalid.append(broken)
        # One identity under two filenames passes the filename checks; the ID check must catch it.
        stem = good['images'][0]['file'].rsplit('.', 1)[0]
        invalid.append(dict(good, images=[dict(good['images'][0], file=stem + extension) for extension in ('.jpg', '.png')]))
        for manifest in invalid:
            with self.subTest(manifest=manifest):
                path.write_text(json.dumps(manifest))
                error = self.assert_rejected_without_drawing(directory, 1)
                self.assertIn('world.json', error['message'])
        for raw in (b'not json', b'\xff', b'[' * 2000 + b']' * 2000,
                    b'{"schema_version":1,"schema_version":1}', b'{"world_id":"\\ud800"}',
                    json.dumps(dict(good, invalid=float('nan'))).encode()):
            with self.subTest(raw=raw):
                path.write_bytes(raw)
                self.assertIn('world.json', self.assert_rejected_without_drawing(directory, 1)['message'])
        path.unlink()
        self.assertIn('world.json', self.assert_rejected_without_drawing(directory, 1)['message'])

    def test_input_world_cannot_be_used_as_output_or_record_store(self):
        source = self.world(1)
        directory = Path(source['output']['directory'])
        before = {p.name: p.read_bytes() for p in directory.iterdir()}
        for target in (directory, directory / 'nested', directory.parent):
            with self.subTest(target=target):
                self.assert_rejected_without_drawing(directory, 1, '--world', str(target))
        for store in (directory, directory / 'records'):
            result = self.without(directory, 1, '--store', str(store))
            self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual({p.name: p.read_bytes() for p in directory.iterdir()}, before)

    def test_exclusion_integrity_is_checked_against_the_saved_snapshot(self):
        source = self.world(1)
        report = json.loads(self.without(source['output']['directory'], 1).stdout)
        path = s.sample_dir(self.store, report['draw']['sample_id']) / 'draw.json'
        draw = json.loads(path.read_text())
        invalid = ((dict(draw['exclusion'], matched_count=0), 'exclusions or counts differ'),
                   (None, 'wrong type'))
        for exclusion, message in invalid:
            with self.subTest(exclusion=exclusion):
                draw['exclusion'] = exclusion
                draw['draw_sha256'] = s.digest({key: value for key, value in draw.items() if key != 'draw_sha256'})
                path.write_text(json.dumps(draw))
                verified = self.cli('verify', draw['sample_id'])
                self.assertEqual(verified.returncode, 1)
                self.assertFalse(json.loads(verified.stdout)['original_draw_reproduced'])
                self.assertIn(message, json.loads(verified.stdout)['problems'][0]['message'])
                self.assertEqual(self.cli('publish', draw['sample_id']).returncode, 2)

    def test_uniform_selection_from_the_remaining_pool(self):
        inventory = self.inventory()
        excluded = inventory['population']['images'][0]['image_id']
        remaining = [image['image_id'] for image in inventory['population']['images'] if image['image_id'] != excluded]
        exclusion = s.match_exclusion(dict(world_id='uniform-test', manifest_sha256='0' * 64,
                                          requested_image_ids=[excluded]), inventory)
        candidates = s.prepare_candidates(inventory, exclusion)
        outcomes = []
        for first, second in itertools.product(range(3), range(2)):
            with patch.object(s.RandomStream, 'randbelow', side_effect=[first, second]):
                outcomes.append(tuple(s.select_ids(candidates, 2, 'unused')))
        self.assertCountEqual(outcomes, list(itertools.permutations(remaining, 2)))

    def test_keep_and_help_use_the_public_entry_point(self):
        source = self.world(1)
        result = subprocess.run([str(self.engine), '--repo', str(self.repo), '--keep', source['output']['directory'], '1'],
                                cwd=self.temp.name, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['store'], str(self.store))
        help_result = subprocess.run([str(self.engine), '--help'], capture_output=True, text=True)
        help_text = ' '.join(help_result.stdout.split())
        self.assertIn('Fixtures/sampleWithout', help_text)
        self.assertIn('WORLD_DIRECTORY N', help_text)
        self.assertNotIn('--inventory', help_text)
        missing = self.repo / 'Fixtures/sampleWithout'
        shutil.copy2(self.engine, missing)
        result = subprocess.run([str(missing), source['output']['directory'], '1'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Python environment missing', result.stderr)
        self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
