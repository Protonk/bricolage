"""SSI-specific publication rules, independent of local acquired assets."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import integrate
import ssi
from transport import dump, sha


class IntegrationTests(unittest.TestCase):
    def test_single_item_has_no_thirty_image_floor_or_pair_relationship(self):
        item = dict(final_file='images/opaque.png', source_path='sources/opaque.png',
                    family_id='ssi-opaque', width=12, height=20, exif_orientation=1,
                    format='PNG', sha256='digest', canonical_title='File:Example.svg',
                    frozen_title='File:Example.svg', reported_artist=None, license='Public domain',
                    source_url='https://commons.wikimedia.org/wiki/File:Example.svg',
                    requested_edge=1600, rendition='api_returned_rendition')
        rows, sources = integrate.records([item])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['relation_kind'], 'curatorial_selected')
        self.assertEqual(rows[0]['parents'], rows[0]['family_id'])
        self.assertEqual(rows[0]['scene_id'], '')
        self.assertEqual(sources[0]['scene_id'], '')
        self.assertNotIn('design_key', rows[0])
        self.assertEqual(integrate.records([]), ([], []))

    def test_build_refuses_existing_publication_before_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'Curatorial/US-Army-SSI'
            root.mkdir(parents=True)
            (root / 'manifest.json').write_text('preserved existing publication')
            with patch.object(ssi, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Published set already exists'):
                integrate.build()
            self.assertEqual((root / 'manifest.json').read_text(), 'preserved existing publication')
            self.assertEqual(list(root.iterdir()), [root / 'manifest.json'])

    def test_layout_rejects_child_fixture_before_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / 'Curatorial/US-Army-SSI'
            (root / 'Divisions').mkdir(parents=True)
            (root / 'Divisions/manifest.json').write_text('{}')
            with patch.object(ssi, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Unexpected child fixture'):
                integrate.check()

    def test_replacement_requires_preserved_snapshot_and_unchanged_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve() / 'Curatorial/US-Army-SSI'
            backup = root / 'provenance/publications/old'
            backup.mkdir(parents=True)
            (root / 'images').mkdir()
            image = root / 'images/a.png'
            image.write_bytes(b'unchanged source copy')
            manifest = dict(images=[dict(file='images/a.png', byte_sha256=sha(image))])
            dump(root / 'manifest.json', manifest)
            dump(backup / 'manifest.json', manifest)
            digest = sha(root / 'manifest.json')
            dump(backup / 'snapshot.json', dict(files={'manifest.json': digest}, contact_sheets=[]))
            with patch.object(ssi, 'ROOT', root):
                expected = integrate.replacement_snapshot(digest, 'provenance/publications/old')
                self.assertEqual(expected['images/a.png'], sha(image))
                image.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'Existing input changed'):
                    integrate.replacement_snapshot(digest, 'provenance/publications/old')


if __name__ == '__main__':
    unittest.main()
