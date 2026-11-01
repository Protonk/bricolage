"""Shared leaf layout checks and explicit compatibility with the 2026-11 moves.

This module never downloads, builds, repairs or compares fixture images.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

FIXTURES = Path(__file__).resolve().parents[1]
REPO = FIXTURES.parent
MIGRATION = FIXTURES / 'provenance/layout-2026-11'
CORE_FILES = {'README.md', 'SOURCES.md', 'manifest.json', 'manifest.csv',
              'sources.csv', 'SHA256SUMS.txt', 'probes.csv', 'selections.json'}
CORE_DIRS = {'images', 'sources', 'previews', 'batches', 'provenance', 'tools'}
INTAKE = {'prompt.json', 'candidates.csv', 'candidates.jsonl', 'HEAP_INSTRUCTIONS.md',
          'inventory.json', 'ordering.json', 'selection.json', 'EXCLUSIONS.txt'}
CONSTRUCTION = {'source-manifest.json', 'SOURCE_SHA256SUMS.txt', 'V06_SHA256SUMS.txt', 'BUILD.md'}
IMAGE_FIELDS = 'file batch family_id scene_id parents transformation relation_kind origin_count width height exif_orientation format byte_sha256 pixels_rgb_sha256'.split()
SOURCE_FIELDS = 'family_id source_filename scene_id subject credit_status source_sha256 width height exif_orientation source_url preprocessing view exposure_id original_path'.split()


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def evidence_path(root, name):
    """Resolve a historical root evidence name without changing its recorded identity.

    During migration old leaves remain readable. Two live copies are an error.
    Current tools write canonical paths directly; this helper is for historical
    evidence and cross-fixture audits, not an alternative publication location.
    """
    require(name in INTAKE | CONSTRUCTION, 'Not a relocatable evidence name: ' + name)
    root = Path(root)
    old = root / name
    new = root / 'provenance' / ('intake' if name in INTAKE else 'construction') / name
    require(not (old.exists() and new.exists()), 'Ambiguous evidence copies: ' + str(root / name))
    return new if new.exists() or (root / 'provenance/layout.json').exists() else old


def matches_tool_revision(path, *, blob=None, sha256=None):
    """Recognize an explicitly recorded migration of a historically pinned tool."""
    require(blob is not None or sha256 is not None, 'A historical tool hash is required')
    path = Path(path).resolve()
    raw = path.read_bytes()
    current_sha = hashlib.sha256(raw).hexdigest()
    current_blob = hashlib.sha1(f'blob {len(raw)}\0'.encode() + raw).hexdigest()
    if (blob is None or blob == current_blob) and (sha256 is None or sha256 == current_sha):
        return True
    receipt = MIGRATION / 'tool-changes.json'
    if not receipt.exists() or not path.is_relative_to(REPO):
        return False
    row = json.loads(receipt.read_text())['files'].get(path.relative_to(REPO).as_posix())
    return bool(row and row['after_sha256'] == current_sha
                and (blob is None or row['before_git_blob_sha1'] == blob)
                and (sha256 is None or row['before_sha256'] == sha256))


def discover(fixtures=None):
    fixtures = FIXTURES if fixtures is None else Path(fixtures)
    return sorted(p.parent for area in ('Heaps', 'Relationships')
                  for p in (fixtures / area).rglob('manifest.json')
                  if not set(p.relative_to(fixtures).parts[:-1]) &
                  {'images', 'sources', 'previews', 'provenance', '__pycache__'})


def check_layout(root, *, assets=True):
    root = Path(root).resolve()
    entries = {p.name for p in root.iterdir()} - {'.DS_Store', '__pycache__'}
    require(not entries - CORE_FILES - CORE_DIRS - {'AGENTS.md'},
            'Unexpected leaf-root entries: ' + str(sorted(entries - CORE_FILES - CORE_DIRS - {'AGENTS.md'})))
    for name in CORE_FILES:
        require((root / name).is_file(), 'Missing core file: ' + name)
    for name in CORE_DIRS:
        # Git does not store empty media directories. Metadata-only checks allow that.
        if assets or name not in {'images', 'sources', 'previews'}:
            require((root / name).is_dir(), 'Missing core directory: ' + name)
        require(not (root / name).is_symlink(), 'Symlinked core directory: ' + name)
    for name in ('tools/check.py', 'tools/requirements.txt', 'provenance/README.md'):
        require((root / name).is_file(), 'Missing standard entry: ' + name)
    manifest = json.loads((root / 'manifest.json').read_text())
    require(manifest['schema_version'] == 1, 'Unsupported manifest schema')
    require(manifest['kind'] in {'prompt_heap', 'curatorial_heap', 'derivatives', 'multiview'}, 'Unknown fixture kind')
    require(bool(manifest['fixture_id']), 'Missing fixture identity')
    rows = manifest['images']
    with (root / 'manifest.csv').open(newline='') as stream:
        reader = csv.DictReader(stream)
        require(reader.fieldnames == IMAGE_FIELDS, 'Unexpected image columns')
        require(list(reader) == [{k: str(v) for k, v in r.items()} for r in rows], 'CSV/JSON image records differ')
    with (root / 'sources.csv').open(newline='') as stream:
        require(csv.DictReader(stream).fieldnames == SOURCE_FIELDS, 'Unexpected source columns')
    names = [r['file'] for r in rows]
    require(len(names) == len(set(names)), 'Duplicate manifest paths')
    for name in names:
        require(Path(name).parts[0] == 'images' and len(Path(name).parts) == 2
                and not Path(name).is_absolute(), 'Invalid input path: ' + name)
    required = {'prompt.json', 'candidates.jsonl', 'candidates.csv'} if manifest['kind'] == 'prompt_heap' else (
        {'inventory.json', 'ordering.json', 'selection.json'} if manifest['kind'] == 'curatorial_heap' else set())
    for name in required:
        require((root / 'provenance/intake' / name).is_file(), 'Missing intake record: ' + name)
    if manifest['kind'] != 'prompt_heap':
        require(not (root / 'provenance/intake/prompt.json').exists(), 'Unexpected visual selection prompt')
    if manifest['kind'].endswith('_heap'):
        selection = json.loads((root / 'selections.json').read_text())
        with (root / 'probes.csv').open(newline='') as stream:
            require(not list(csv.DictReader(stream)) and not selection['pairs']
                    and not selection['known_shift_families'], 'Heap asserts pair expectations')
    if assets:
        require(rows, 'Empty fixture has no acquired inputs')
        actual = {p.relative_to(root).as_posix() for p in (root / 'images').iterdir() if p.name != '.DS_Store'}
        require(set(names) == actual, 'Manifest/input file coverage differs')
        for row in rows:
            require(sha(root / row['file']) == row['byte_sha256'], 'Input hash differs: ' + row['file'])
    from fixture_removal import history
    removals = history(root, assets=assets)
    return dict(removed_inputs=len(removals), fixture_id=manifest['fixture_id'], kind=manifest['kind'], images=len(rows), layout='passed', assets_checked=assets)


def check_leaf(script, checks):
    """Common entry point; specialized checks remain explicit and read-only."""
    import argparse
    parser = argparse.ArgumentParser(description='Check this fixture offline; never builds or downloads.')
    parser.add_argument('--metadata-only', action='store_true', help='Layout/catalog checks without local media or specialized validation')
    args = parser.parse_args()
    try:
        require(sys.version_info[:2] == (3, 14), 'Use the Python 3.14.x Fixtures/.venv')
        root = Path(script).resolve().parents[1]
        result = check_layout(root, assets=not args.metadata_only)
        result['specialized_scope'] = 'original_publication' if result['removed_inputs'] else 'current_publication'
        result['specialized_checks'] = []
        if not args.metadata_only:
            for command in checks:
                run = subprocess.run([sys.executable, str(REPO / command[0]), *command[1:]],
                                     cwd=REPO, text=True, capture_output=True)
                result['specialized_checks'].append(dict(command=command, exit_code=run.returncode,
                                                        stdout=run.stdout, stderr=run.stderr))
                require(run.returncode == 0, 'Specialized check failed: ' + ' '.join(command) + '\n' + run.stderr)
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'fixture check: {error}\n')
