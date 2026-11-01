#!/usr/bin/env python3
"""Sampling engine: draw N equal tickets and retain separate annotations.

Python 3.14 standard library only. No network, image processing or fixture mutations.
The JSON format and byte-exact sampling procedure are documented in README.md.
"""
import argparse
import csv
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import sys
import tempfile
from datetime import datetime, timezone
import uuid


REPO = Path(__file__).resolve().parents[2]
DEFAULT_STORE = Path(__file__).resolve().parent / 'records'
PROCEDURE = 'sha256-counter-rejection-partial-fisher-yates-v1'
POLICY = 'active-manifest-inputs; exact-byte-sha256-aliases; one-ticket-per-hash-v1'
SKIP_DIRS = {'images', 'sources', 'previews', 'provenance', '__pycache__', '.git'}
HEX = re.compile(r'[0-9a-f]{64}\Z')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    with path.open(encoding='utf-8') as stream:
        return json.load(stream)


def new_json(path, value):
    """Publish a complete new record atomically; never replace an existing one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + '\n'
    fd, name = tempfile.mkstemp(prefix='.pending-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(name, path)  # Exclusive publication, also safe against concurrent writers.
    finally:
        Path(name).unlink()


def relative_path(value):
    require(isinstance(value, str) and value, 'Expected a nonempty relative path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in value,
            'Unsafe fixture path: ' + value)
    return p


def fixture_path(repo, value):
    p = relative_path(value)
    require(p.parts[0] == 'Fixtures', 'Path is outside Fixtures: ' + value)
    path = repo.joinpath(*p.parts)
    require(path.resolve().is_relative_to((repo / 'Fixtures').resolve()),
            'Resolved path is outside Fixtures: ' + value)
    return path


def location_status(repo, value, expected):
    """Do not turn changed bytes into a new identity or silently repair an alias."""
    try:
        path = fixture_path(repo, value)
        observed = file_hash(path)
        return dict(status='ok' if observed == expected else 'changed',
                    observed_sha256=observed)
    except FileNotFoundError:
        return dict(status='missing', observed_sha256=None)
    except (OSError, ValueError) as error:
        return dict(status='inaccessible', observed_sha256=None,
                    error=f'{type(error).__name__}: {error}')


def manifests(repo):
    """Find active leaves at arbitrary depth, excluding archived/staged manifests."""
    repo = Path(repo).resolve()
    found = []
    for area in ('Heaps', 'Relationships'):
        root = repo / 'Fixtures' / area
        require(root.is_dir(), 'Missing fixture area: ' + str(root))
        for parent, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
            if 'manifest.json' in files:
                found.append(Path(parent) / 'manifest.json')
    require(found, 'No active fixture manifests found')
    return sorted(found)


def build_inventory(repo):
    repo = Path(repo).resolve()
    tickets, metadata_files, unlisted = {}, [], []
    leaves = manifests(repo)
    occurrences = 0

    def metadata_bytes(path):
        data = path.read_bytes()
        metadata_files.append(dict(path=path.relative_to(repo).as_posix(),
                                   sha256=hashlib.sha256(data).hexdigest()))
        return data

    for manifest_path in leaves:
        leaf = manifest_path.parent
        manifest = json.loads(metadata_bytes(manifest_path))
        require(manifest.get('schema_version') == 1, 'Unsupported fixture manifest schema')
        require(isinstance(manifest.get('fixture_id'), str), 'Missing fixture ID')
        source_path = leaf / 'sources.csv'
        sources = list(csv.DictReader(io.StringIO(metadata_bytes(source_path).decode('utf-8'))))
        mapping_path = leaf / 'provenance/import-map.json'
        mappings = json.loads(metadata_bytes(mapping_path)) if mapping_path.exists() else []
        mapped = {}
        for row in mappings:
            key = row.get('final_file')
            if key:
                require(key not in mapped, 'Duplicate import-map input: ' + key)
                mapped[key] = row
        # Exact rows are embedded below; also retain the readable credit context's hash.
        if (leaf / 'SOURCES.md').is_file():
            metadata_bytes(leaf / 'SOURCES.md')
        seen = set()
        for row in manifest['images']:
            name = row['file']
            local = relative_path(name)
            require(local.parts[0] == 'images' and len(local.parts) > 1,
                    'Manifest input must be inside images/: ' + name)
            require(name not in seen, 'Duplicate path in manifest: ' + name)
            seen.add(name)
            expected = row['byte_sha256']
            require(isinstance(expected, str) and HEX.fullmatch(expected), 'Invalid input SHA-256')
            image_id = 'sha256:' + expected
            path = (leaf / local).relative_to(repo).as_posix()
            families = set(filter(None, row.get('parents', '').split('|')))
            if row.get('family_id'):
                families.add(row['family_id'])
            alias = dict(path=path, fixture_path=leaf.relative_to(repo).as_posix(),
                         fixture_id=manifest['fixture_id'], kind=manifest['kind'],
                         manifest_record=row,
                         source_records=[s for s in sources if s['family_id'] in families],
                         import_record=mapped.get(name),
                         availability=location_status(repo, path, expected))
            tickets.setdefault(image_id, dict(image_id=image_id, byte_sha256=expected,
                                              aliases=[]))['aliases'].append(alias)
            occurrences += 1
        for path in sorted((leaf / 'images').rglob('*')):
            if path.is_file() and path.relative_to(leaf).as_posix() not in seen:
                unlisted.append(path.relative_to(repo).as_posix())
    images = []
    for image_id in sorted(tickets):
        item = tickets[image_id]
        item['aliases'].sort(key=lambda a: a['path'])
        item['eligible'] = any(a['availability']['status'] == 'ok' for a in item['aliases'])
        images.append(item)
    population = dict(schema_version=1, policy=POLICY, images=images,
                      metadata_files=sorted(metadata_files, key=lambda r: r['path']),
                      unlisted_inputs=sorted(unlisted),
                      counts=dict(leaves=len(leaves), manifest_records=occurrences,
                                  distinct_images=len(images),
                                  eligible=sum(i['eligible'] for i in images),
                                  alias_records=occurrences-len(images)))
    return dict(inventory_id=digest(population), created_at=utc(), population=population)


def validate_inventory(inventory):
    pop = inventory['population']
    require(inventory['inventory_id'] == digest(pop), 'Inventory snapshot checksum differs')
    require(pop['schema_version'] == 1 and pop['policy'] == POLICY, 'Unsupported inventory policy')
    ids = [i['image_id'] for i in pop['images']]
    require(ids == sorted(set(ids)), 'Inventory tickets must be unique and sorted')
    for item in pop['images']:
        require(HEX.fullmatch(item['byte_sha256']) and item['image_id'] == 'sha256:' + item['byte_sha256'],
                'Invalid image identity')
        require(item['aliases'] and item['eligible'] == any(
            a['availability']['status'] == 'ok' for a in item['aliases']), 'Invalid eligibility')
    return inventory


def inventory_file(store, inventory_id):
    require(HEX.fullmatch(inventory_id), 'Expected a full inventory ID')
    return Path(store) / 'inventories' / (inventory_id + '.json')


def save_inventory(store, inventory):
    validate_inventory(inventory)
    path = inventory_file(store, inventory['inventory_id'])
    try:
        new_json(path, inventory)
    except FileExistsError:
        existing = validate_inventory(read_json(path))
        require(existing['population'] == inventory['population'], 'Existing snapshot differs')
        return existing
    return inventory


def load_inventory(store, inventory_id):
    value = validate_inventory(read_json(inventory_file(store, inventory_id)))
    require(value['inventory_id'] == inventory_id, 'Inventory filename/identity differs')
    return value


class RandomStream:
    """Specified SHA-256 counter stream, with unbiased bounded integer rejection."""
    def __init__(self, seed):
        value = seed.encode('utf-8')
        self.prefix = b'hazy-fixture-sampler-v1\0' + len(value).to_bytes(8, 'big') + value
        self.counter = 0

    def word(self):
        value = hashlib.sha256(self.prefix + self.counter.to_bytes(16, 'big')).digest()
        self.counter += 1
        return int.from_bytes(value, 'big')

    def randbelow(self, bound):
        require(0 < bound <= 2**256, 'Invalid random bound')
        limit = 2**256 - (2**256 % bound)
        while True:
            word = self.word()
            if word < limit:
                return word % bound


def sample_ids(inventory, size, seed):
    validate_inventory(inventory)
    require(type(size) is int and size >= 0, 'Sample size must be a nonnegative integer')
    pool = [i['image_id'] for i in inventory['population']['images'] if i['eligible']]
    require(size <= len(pool), f'Requested {size} images; eligible population is {len(pool)}')
    rng = RandomStream(seed)
    for i in range(size):
        j = i + rng.randbelow(len(pool) - i)
        pool[i], pool[j] = pool[j], pool[i]
    return pool[:size]


def sample_dir(store, sample_id):
    require(re.fullmatch(r'draw-[0-9a-f]{32}', sample_id), 'Expected a full sample ID')
    return Path(store) / 'draws' / sample_id


def create_draw(store, inventory, size, seed=None):
    seed = secrets.token_hex(32) if seed is None else seed
    require(isinstance(seed, str), 'Seed must be a string')
    ids = sample_ids(inventory, size, seed)
    inventory = save_inventory(store, inventory)
    draw = dict(schema_version=1, sample_id='draw-' + uuid.uuid4().hex, created_at=utc(),
                inventory_id=inventory['inventory_id'],
                inventory_file='inventories/' + inventory['inventory_id'] + '.json',
                procedure=PROCEDURE, seed=seed, requested_size=size,
                eligible_count=inventory['population']['counts']['eligible'], image_ids=ids)
    draw['draw_sha256'] = digest(draw)
    new_json(sample_dir(store, draw['sample_id']) / 'draw.json', draw)
    return draw


def load_draw(store, sample_id):
    draw = read_json(sample_dir(store, sample_id) / 'draw.json')
    payload = {k: v for k, v in draw.items() if k != 'draw_sha256'}
    require(draw['draw_sha256'] == digest(payload), 'Original draw checksum differs')
    require(draw['schema_version'] == 1 and draw['sample_id'] == sample_id,
            'Draw identity/schema differs')
    require(draw['procedure'] == PROCEDURE, 'Unsupported sampling procedure')
    inventory = load_inventory(store, draw['inventory_id'])
    require(draw['inventory_file'] == 'inventories/' + draw['inventory_id'] + '.json',
            'Snapshot reference differs')
    require(draw['eligible_count'] == inventory['population']['counts']['eligible'],
            'Eligible count differs')
    require(draw['image_ids'] == sample_ids(inventory, draw['requested_size'], draw['seed']),
            'Original draw does not reproduce')
    return draw, inventory


def parse_events(text, draw):
    require(not text or text.endswith('\n'), 'Incomplete annotation log; preserve it for repair')
    events = [json.loads(line) for line in text.splitlines()]
    for sequence, event in enumerate(events, 1):
        require(event['schema_version'] == 1 and event['sequence'] == sequence,
                'Annotation schema/sequence differs')
        require(event['sample_id'] == draw['sample_id'] and
                event['draw_sha256'] == draw['draw_sha256'], 'Annotation belongs to another draw')
        require(event['image_id'] is None or event['image_id'] in draw['image_ids'],
                'Annotation image is not in the original draw')
        require(isinstance(event['key'], str) and event['key'], 'Empty annotation key')
        require(event['operation'] in ('set', 'delete'), 'Unsupported annotation operation')
        require(('value' in event) == (event['operation'] == 'set'), 'Annotation value differs')
        canonical(event)  # Reject non-JSON values such as NaN, also on reload.
    return events


def read_events(store, draw):
    path = sample_dir(store, draw['sample_id']) / 'annotations.jsonl'
    try:
        with path.open(encoding='utf-8') as stream:
            fcntl.flock(stream, fcntl.LOCK_SH)
            return parse_events(stream.read(), draw)
    except FileNotFoundError:
        return []


def annotate(store, sample_id, key, value=None, image_id=None, delete=False, author=None):
    draw, _ = load_draw(store, sample_id)
    require(isinstance(key, str) and key, 'Annotation key must be a nonempty string')
    require(image_id is None or image_id in draw['image_ids'], 'Image is not in this draw')
    canonical(value)
    path = sample_dir(store, sample_id) / 'annotations.jsonl'
    with path.open('a+', encoding='utf-8') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        events = parse_events(stream.read(), draw)
        event = dict(schema_version=1, sequence=len(events)+1, event_id=uuid.uuid4().hex,
                     created_at=utc(), sample_id=sample_id, draw_sha256=draw['draw_sha256'],
                     image_id=image_id, author=author, key=key,
                     operation='delete' if delete else 'set')
        if not delete:
            event['value'] = value
        # A delete removes the current value; it never erases the earlier events.
        stream.write(canonical(event).decode('utf-8') + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    return event


def annotation_state(events):
    state = dict(sample={}, images={})
    for event in events:
        target = state['sample'] if event['image_id'] is None else state['images'].setdefault(
            event['image_id'], {})
        if event['operation'] == 'set':
            target[event['key']] = event['value']
        else:
            target.pop(event['key'], None)
    return state


def current_locations(repo, item):
    locations = []
    for alias in item['aliases']:
        path = alias['path']
        locations.append(dict(path=path, absolute_path=str(Path(repo).resolve() / path),
                              **location_status(repo, path, item['byte_sha256'])))
    available = next((r['absolute_path'] for r in locations if r['status'] == 'ok'), None)
    return dict(image_id=item['image_id'], available_path=available, locations=locations)


def inspect_draw(store, sample_id, repo, paths_only=False):
    draw, inventory = load_draw(store, sample_id)
    indexed = {r['image_id']: r for r in inventory['population']['images']}
    current = [dict(position=n, **current_locations(repo, indexed[image_id]))
               for n, image_id in enumerate(draw['image_ids'], 1)]
    if paths_only:
        return current
    events = read_events(store, draw)
    return dict(draw=draw, images=[indexed[i] for i in draw['image_ids']],
                current_locations=current, annotations=annotation_state(events),
                annotation_history=events)


def verify_draw(store, sample_id, repo):
    draw, inventory = load_draw(store, sample_id)
    read_events(store, draw)
    indexed = {r['image_id']: r for r in inventory['population']['images']}
    selected = [indexed[i] for i in draw['image_ids']]
    current = [current_locations(repo, item) for item in selected]
    issues = [dict(image_id=r['image_id'], **location) for r in current
              for location in r['locations'] if location['status'] != 'ok']
    leaf_paths = {a['fixture_path'] for item in selected for a in item['aliases']}
    metadata_issues = []
    for record in inventory['population']['metadata_files']:
        if any(record['path'].startswith(leaf + '/') for leaf in leaf_paths):
            status = location_status(repo, record['path'], record['sha256'])
            if status['status'] != 'ok':
                metadata_issues.append(dict(path=record['path'], **status))
    return dict(sample_id=sample_id, record_valid=True, original_draw_reproduced=True,
                requested_size=draw['requested_size'],
                images_available=sum(r['available_path'] is not None for r in current),
                alias_issues=issues, fixture_metadata_issues=metadata_issues,
                ok=not issues and not metadata_issues)


def list_draws(store):
    result = []
    for path in sorted((Path(store) / 'draws').glob('draw-*/draw.json')):
        draw, _ = load_draw(store, path.parent.name)
        result.append({k: draw[k] for k in ('sample_id', 'created_at', 'requested_size',
                                           'inventory_id', 'seed')})
    return sorted(result, key=lambda r: (r['created_at'], r['sample_id']))


def inventory_report(inventory, store):
    pop = inventory['population']
    return dict(inventory_id=inventory['inventory_id'],
                file=str(inventory_file(store, inventory['inventory_id']).resolve()),
                counts=pop['counts'], unlisted_inputs=pop['unlisted_inputs'],
                alias_issues=[dict(image_id=i['image_id'], path=a['path'], **a['availability'])
                              for i in pop['images'] for a in i['aliases']
                              if a['availability']['status'] != 'ok'])


def sample_output(repo, store):
    """Only this fixed scratch directory may be replaced by a draw."""
    output = Path(repo).resolve() / 'output'
    target = output / 'sampled'
    require(not output.is_symlink() and not target.is_symlink(),
            'output/ and output/sampled/ must not be symlinks')
    require(not Path(store).resolve().is_relative_to(target),
            'Sample records must be stored outside output/sampled/')
    return target


def publish_sample(repo, store, images):
    """Verify independent copies before replacing the previous disposable output."""
    target = sample_output(repo, store)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Lock the parent directory itself: no persistent lock file in output/.
    lock = os.open(target.parent, os.O_RDONLY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        sample_output(repo, store)
        with tempfile.TemporaryDirectory(prefix='.sampled-', dir=target.parent) as temporary:
            staged = Path(temporary)
            copied = []
            for image in images:
                require(image['available_path'] is not None, 'Selected image is unavailable')
                source = Path(image['available_path'])
                sha256 = image['image_id'].removeprefix('sha256:')
                name = f"{image['position']:04d}-{sha256}{source.suffix}"
                destination = staged / name
                shutil.copyfile(source, destination)
                require(file_hash(destination) == sha256, 'Copied image checksum differs: ' + name)
                copied.append(dict(image, sampled_path=str(target / name)))
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            staged.rename(target)
        return copied
    finally:
        os.close(lock)


def main(argv=None):
    if sys.version_info[:2] != (3, 14):
        print('sampler: Python 3.14.x is required; run make setup-python and use Fixtures/sample.',
              file=sys.stderr)
        return 2
    argv = list(sys.argv[1:] if argv is None else argv)
    # A leading N is shorthand for "draw N", after any global options.
    index = 0
    while index < len(argv):
        argument = argv[index]
        if argument in ('--repo', '--store'):
            index += 2
        elif argument.startswith(('--repo=', '--store=')):
            index += 1
        else:
            if re.fullmatch(r'[+-]?[0-9]+', argument):
                argv.insert(index, 'draw')
            break
    parser = argparse.ArgumentParser(
        prog='Fixtures/sample', description=__doc__, allow_abbrev=False,
        epilog='Quick draw: Fixtures/sample N [--seed TEXT]. Replaces output/sampled/ with image copies; JSON paths are in images[].sampled_path.')
    parser.add_argument('--repo', type=Path, default=REPO, help='Checkout containing Fixtures/')
    parser.add_argument('--store', type=Path, default=DEFAULT_STORE, help='JSON record directory')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('inventory', help='Refresh and save an immutable population snapshot')
    draw = commands.add_parser('draw', help='Draw N equal tickets; refresh inventory by default')
    draw.add_argument('size', type=int)
    draw.add_argument('--seed', help='Exact UTF-8 seed text; generated and recorded if omitted')
    draw.add_argument('--inventory', help='Use this saved snapshot instead of rescanning fixtures')
    commands.add_parser('list', help='List persistent draws')
    show = commands.add_parser('show', help='Original draw, frozen metadata, current locations and annotations')
    show.add_argument('sample_id')
    show.add_argument('--paths', action='store_true', help='Only current image locations/statuses as JSON')
    check = commands.add_parser('verify', help='Replay original selection and report current file problems')
    check.add_argument('sample_id')
    note = commands.add_parser('annotate', help='Append or revise an arbitrary JSON annotation')
    note.add_argument('sample_id')
    note.add_argument('--image', help='Drawn image ID; omit for a sample-level annotation')
    note.add_argument('--key', required=True)
    note.add_argument('--author')
    data = note.add_mutually_exclusive_group(required=True)
    data.add_argument('--json', help='A JSON value, including null, scalars, objects or arrays')
    data.add_argument('--value-file', help='Read JSON from this file, or - for stdin')
    data.add_argument('--delete', action='store_true', help='Remove current value while retaining history')
    args = parser.parse_args(argv)
    try:
        if args.command == 'inventory':
            result = inventory_report(save_inventory(args.store, build_inventory(args.repo)), args.store)
        elif args.command == 'draw':
            target = sample_output(args.repo, args.store)
            inventory = (load_inventory(args.store, args.inventory) if args.inventory
                         else build_inventory(args.repo))
            drawn = create_draw(args.store, inventory, args.size, args.seed)
            result = dict(schema_version=1, draw=drawn, population=inventory_report(inventory, args.store),
                          images=inspect_draw(args.store, drawn['sample_id'], args.repo, paths_only=True),
                          current_check=verify_draw(args.store, drawn['sample_id'], args.repo),
                          output=dict(directory=str(target), published=False))
            for image in result['images']:
                image['sampled_path'] = None
            if result['current_check']['ok']:
                try:
                    result['images'] = publish_sample(args.repo, args.store, result['images'])
                    result['output']['published'] = True
                except (OSError, ValueError) as error:
                    result['output']['error'] = f'{type(error).__name__}: {error}'
        elif args.command == 'list':
            result = list_draws(args.store)
        elif args.command == 'show':
            result = inspect_draw(args.store, args.sample_id, args.repo, args.paths)
        elif args.command == 'verify':
            result = verify_draw(args.store, args.sample_id, args.repo)
        else:
            value = None
            if args.json is not None:
                value = json.loads(args.json)
            elif args.value_file:
                value = json.load(sys.stdin) if args.value_file == '-' else read_json(Path(args.value_file))
            result = annotate(args.store, args.sample_id, args.key, value, args.image,
                              args.delete, args.author)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
        if ((args.command == 'verify' and not result['ok']) or
                (args.command == 'draw' and not result['output']['published'])):
            return 1
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f'sampler: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
