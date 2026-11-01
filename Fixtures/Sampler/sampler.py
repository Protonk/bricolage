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
DRAW_FIELDS = (('schema_version', int), ('sample_id', str), ('created_at', str),
               ('inventory_id', str), ('inventory_file', str), ('procedure', str),
               ('seed', str), ('requested_size', int), ('eligible_count', int),
               ('image_ids', list), ('draw_sha256', str))


class SamplerError(Exception):
    """A reported failure with a known cause. Nothing is repaired on the way out.

    Codes: usage (arguments or request), fixture (fixture metadata or layout),
    record-missing, record-invalid, record-damaged (a checksum differs), output
    (the disposable output directory) and io (the operating system refused).
    """
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code = code
        self.details = details

    def report(self):
        return dict(code=self.code, message=str(self), **self.details)


def require(condition, code, message, **details):
    if not condition:
        raise SamplerError(code, message, **details)


def field(record, key, kinds, what, code='record-invalid'):
    """Read one typed field, naming the record and field when it is absent or wrong."""
    require(isinstance(record, dict), code, f'{what} is not a JSON object')
    require(key in record, code, f'{what} lacks the field "{key}"')
    value = record[key]
    require(isinstance(value, kinds) and not (kinds is int and isinstance(value, bool)), code,
            f'{what} field "{key}" has the wrong type')
    return value


def utc():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                          separators=(',', ':')).encode('utf-8')
    except (ValueError, TypeError) as error:
        raise SamplerError('usage', f'Value is not exact JSON: {error}') from None


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read_json(path, what, code='record-invalid'):
    try:
        with path.open(encoding='utf-8') as stream:
            return json.load(stream)
    except FileNotFoundError:
        raise SamplerError('record-missing' if code == 'record-invalid' else code,
                           f'{what} is missing: {path}', path=str(path)) from None
    except UnicodeDecodeError:
        raise SamplerError(code, f'{what} is not UTF-8 text: {path}', path=str(path)) from None
    except json.JSONDecodeError as error:
        raise SamplerError(code, f'{what} is not valid JSON: {path} ({error})', path=str(path)) from None


def current_umask():
    value = os.umask(0)
    os.umask(value)
    return value


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
        os.chmod(name, 0o666 & ~current_umask())  # Records are ordinary files, not private ones.
        os.link(name, path)  # Exclusive publication, also safe against concurrent writers.
    finally:
        Path(name).unlink()


def relative_path(value, what):
    require(isinstance(value, str) and value, 'fixture', f'{what} is not a nonempty relative path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in value,
            'fixture', f'{what} is an unsafe fixture path: {value}')
    return p


def fixture_path(repo, value):
    p = relative_path(value, 'Recorded location')
    require(p.parts[0] == 'Fixtures', 'fixture', 'Recorded location is outside Fixtures: ' + value)
    path = repo.joinpath(*p.parts)
    require(path.resolve().is_relative_to((repo / 'Fixtures').resolve()),
            'fixture', 'Recorded location resolves outside Fixtures: ' + value)
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
    except (OSError, SamplerError) as error:
        return dict(status='inaccessible', observed_sha256=None,
                    error=f'{type(error).__name__}: {error}')


def manifests(repo):
    """Find active leaves at arbitrary depth, excluding archived/staged manifests."""
    repo = Path(repo).resolve()
    found = []
    for area in ('Heaps', 'Relationships'):
        root = repo / 'Fixtures' / area
        require(root.is_dir(), 'fixture', f'Fixture area is missing: {root}', path=str(root))
        for parent, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith('.'))
            if 'manifest.json' in files:
                found.append(Path(parent) / 'manifest.json')
    require(found, 'fixture', 'No active fixture manifests found under Fixtures/Heaps or Fixtures/Relationships')
    return sorted(found)


def read_leaf(repo, manifest_path):
    """Read and validate one leaf's metadata. Raises SamplerError naming the leaf."""
    leaf = manifest_path.parent
    rel = leaf.relative_to(repo).as_posix()
    files = []

    def metadata_bytes(path, what, required=True):
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            if not required:
                return None
            raise SamplerError('fixture', f'{what} is missing', path=path.relative_to(repo).as_posix()) from None
        files.append(dict(path=path.relative_to(repo).as_posix(),
                          sha256=hashlib.sha256(data).hexdigest()))
        return data

    def parse_json(data, what):
        try:
            return json.loads(data.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise SamplerError('fixture', f'{what} is not valid UTF-8 JSON: {error}') from None

    try:
        manifest = parse_json(metadata_bytes(manifest_path, 'manifest.json'), 'manifest.json')
        what = 'manifest.json'
        require(field(manifest, 'schema_version', int, what, 'fixture') == 1, 'fixture',
                'manifest.json has an unsupported schema_version')
        fixture_id = field(manifest, 'fixture_id', str, what, 'fixture')
        kind = field(manifest, 'kind', str, what, 'fixture')
        rows = field(manifest, 'images', list, what, 'fixture')
        raw = metadata_bytes(leaf / 'sources.csv', 'sources.csv')
        try:
            sources = list(csv.DictReader(io.StringIO(raw.decode('utf-8'))))
        except (UnicodeDecodeError, csv.Error) as error:
            raise SamplerError('fixture', f'sources.csv is unreadable: {error}') from None
        require(sources and 'family_id' in sources[0], 'fixture',
                'sources.csv needs a header with a family_id column and at least one row')
        mapping_data = metadata_bytes(leaf / 'provenance/import-map.json', 'import-map.json', required=False)
        mappings = parse_json(mapping_data, 'provenance/import-map.json') if mapping_data else []
        require(isinstance(mappings, list), 'fixture', 'provenance/import-map.json is not a list')
        mapped = {}
        for row in mappings:
            key = row.get('final_file') if isinstance(row, dict) else None
            if key:
                require(key not in mapped, 'fixture', f'provenance/import-map.json lists {key} twice')
                mapped[key] = row
        # Exact rows are embedded below; also retain the readable credit context's hash.
        metadata_bytes(leaf / 'SOURCES.md', 'SOURCES.md', required=False)
        images, seen = [], set()
        for n, row in enumerate(rows):
            what = f'manifest.json images[{n}]'
            name = field(row, 'file', str, what, 'fixture')
            local = relative_path(name, what)
            require(local.parts[0] == 'images' and len(local.parts) > 1, 'fixture',
                    f'{what} must be inside images/: {name}')
            require(name not in seen, 'fixture', f'manifest.json lists {name} twice')
            seen.add(name)
            expected = field(row, 'byte_sha256', str, what, 'fixture')
            require(HEX.fullmatch(expected), 'fixture', f'{what} byte_sha256 is not 64 lowercase hex digits')
            families = set(filter(None, str(row.get('parents', '')).split('|')))
            if row.get('family_id'):
                families.add(row['family_id'])
            images.append(dict(name=name, expected=expected, record=row,
                               source_records=[s for s in sources if s.get('family_id') in families],
                               import_record=mapped.get(name)))
        unlisted = [p.relative_to(repo).as_posix() for p in sorted((leaf / 'images').rglob('*'))
                    if p.is_file() and p.relative_to(leaf).as_posix() not in seen]
    except SamplerError as error:
        raise SamplerError('fixture', f'Fixture leaf {rel}: {error}', leaf=rel, **error.details) from None
    return dict(leaf=leaf, fixture_path=rel, fixture_id=fixture_id, kind=kind, images=images,
                metadata_files=files, unlisted_inputs=unlisted)


def build_inventory(repo):
    repo = Path(repo).resolve()
    tickets, metadata_files, unlisted = {}, [], []
    leaves = [read_leaf(repo, manifest_path) for manifest_path in manifests(repo)]
    occurrences = 0
    for leaf in leaves:
        metadata_files.extend(leaf['metadata_files'])
        unlisted.extend(leaf['unlisted_inputs'])
        for image in leaf['images']:
            image_id = 'sha256:' + image['expected']
            path = (leaf['leaf'] / image['name']).relative_to(repo).as_posix()
            alias = dict(path=path, fixture_path=leaf['fixture_path'],
                         fixture_id=leaf['fixture_id'], kind=leaf['kind'],
                         manifest_record=image['record'],
                         source_records=image['source_records'],
                         import_record=image['import_record'],
                         availability=location_status(repo, path, image['expected']))
            tickets.setdefault(image_id, dict(image_id=image_id, byte_sha256=image['expected'],
                                              aliases=[]))['aliases'].append(alias)
            occurrences += 1
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
    what = 'Inventory record'
    pop = field(inventory, 'population', dict, what)
    inventory_id = field(inventory, 'inventory_id', str, what)
    require(inventory_id == digest(pop), 'record-damaged', f'{what} {inventory_id}: checksum differs from its contents')
    require(field(pop, 'schema_version', int, what) == 1 and pop.get('policy') == POLICY,
            'record-invalid', f'{what} {inventory_id}: unsupported population schema or policy')
    images = field(pop, 'images', list, what)
    ids = [field(i, 'image_id', str, what) for i in images]
    require(ids == sorted(set(ids)), 'record-invalid', f'{what} {inventory_id}: tickets must be unique and sorted')
    for item in images:
        sha = field(item, 'byte_sha256', str, what)
        require(HEX.fullmatch(sha) and item['image_id'] == 'sha256:' + sha,
                'record-invalid', f'{what} {inventory_id}: invalid image identity {item["image_id"]}')
        aliases = field(item, 'aliases', list, what)
        require(aliases and field(item, 'eligible', bool, what) == any(
            a['availability']['status'] == 'ok' for a in aliases),
            'record-invalid', f'{what} {inventory_id}: invalid eligibility for {item["image_id"]}')
    field(pop, 'counts', dict, what)
    return inventory


def inventory_file(store, inventory_id):
    require(isinstance(inventory_id, str) and HEX.fullmatch(inventory_id), 'usage',
            f'Expected a full 64-hex inventory ID, got {inventory_id!r}')
    return Path(store) / 'inventories' / (inventory_id + '.json')


def save_inventory(store, inventory):
    validate_inventory(inventory)
    path = inventory_file(store, inventory['inventory_id'])
    try:
        new_json(path, inventory)
    except FileExistsError:
        existing = validate_inventory(read_json(path, 'Inventory record'))
        require(existing['population'] == inventory['population'], 'record-damaged',
                f'Existing inventory {path} does not match the population it claims')
        return existing
    return inventory


def load_inventory(store, inventory_id):
    path = inventory_file(store, inventory_id)
    value = validate_inventory(read_json(path, 'Inventory record'))
    require(value['inventory_id'] == inventory_id, 'record-invalid',
            f'Inventory file {path} holds a different inventory ID')
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
        require(0 < bound <= 2**256, 'usage', 'Invalid random bound')
        limit = 2**256 - (2**256 % bound)
        while True:
            word = self.word()
            if word < limit:
                return word % bound


def sample_ids(inventory, size, seed):
    validate_inventory(inventory)
    require(type(size) is int and size >= 0, 'usage', 'Sample size must be a nonnegative integer')
    pool = [i['image_id'] for i in inventory['population']['images'] if i['eligible']]
    require(size <= len(pool), 'usage', f'Requested {size} images; eligible population is {len(pool)}')
    rng = RandomStream(seed)
    for i in range(size):
        j = i + rng.randbelow(len(pool) - i)
        pool[i], pool[j] = pool[j], pool[i]
    return pool[:size]


def sample_dir(store, sample_id):
    require(isinstance(sample_id, str) and re.fullmatch(r'draw-[0-9a-f]{32}', sample_id), 'usage',
            f'Expected a full sample ID like draw-<32 hex digits>, got {sample_id!r}')
    return Path(store) / 'draws' / sample_id


def create_draw(store, inventory, size, seed=None):
    seed = secrets.token_hex(32) if seed is None else seed
    require(isinstance(seed, str), 'usage', 'Seed must be a string')
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


def read_draw(store, sample_id):
    """Read a draw record and check it against itself. The inventory is not consulted."""
    path = sample_dir(store, sample_id) / 'draw.json'
    draw = read_json(path, 'Draw record')
    what = f'Draw record {sample_id}'
    for key, kinds in DRAW_FIELDS:
        field(draw, key, kinds, what)
    payload = {k: v for k, v in draw.items() if k != 'draw_sha256'}
    require(draw['draw_sha256'] == digest(payload), 'record-damaged',
            f'{what}: checksum differs from its contents', path=str(path))
    require(draw['schema_version'] == 1 and draw['sample_id'] == sample_id, 'record-invalid',
            f'{what}: schema or sample ID differs from its location')
    require(draw['procedure'] == PROCEDURE, 'record-invalid',
            f'{what}: unsupported sampling procedure {draw["procedure"]}')
    require(HEX.fullmatch(draw['inventory_id']) and
            draw['inventory_file'] == 'inventories/' + draw['inventory_id'] + '.json',
            'record-invalid', f'{what}: snapshot reference differs')
    return draw


def replay_draw(store, draw):
    """Load the draw's snapshot and reproduce the original selection from it."""
    inventory = load_inventory(store, draw['inventory_id'])
    what = f'Draw record {draw["sample_id"]}'
    require(draw['eligible_count'] == inventory['population']['counts']['eligible'],
            'record-damaged', f'{what}: eligible count differs from its snapshot')
    require(draw['image_ids'] == sample_ids(inventory, draw['requested_size'], draw['seed']),
            'record-damaged', f'{what}: original draw does not reproduce from its snapshot')
    return inventory


def load_draw(store, sample_id):
    draw = read_draw(store, sample_id)
    return draw, replay_draw(store, draw)


def resolve_inventory(store, draw):
    """Replay for inspection: a missing or damaged snapshot is a problem, not a stop."""
    try:
        return replay_draw(store, draw), []
    except SamplerError as error:
        return None, [dict(kind='snapshot-unavailable', **error.report())]


def parse_events(text, draw):
    what = f'Annotation log for {draw["sample_id"]}'
    require(not text or text.endswith('\n'), 'record-damaged',
            f'{what} ends mid-line; preserve it for repair')
    events = []
    for sequence, line in enumerate(text.splitlines(), 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as error:
            raise SamplerError('record-damaged', f'{what} line {sequence} is not JSON: {error}') from None
        where = f'{what} event {sequence}'
        require(field(event, 'schema_version', int, where) == 1 and
                field(event, 'sequence', int, where) == sequence,
                'record-damaged', f'{where}: schema or sequence differs')
        require(field(event, 'sample_id', str, where) == draw['sample_id'] and
                field(event, 'draw_sha256', str, where) == draw['draw_sha256'],
                'record-damaged', f'{where} belongs to another draw')
        require('image_id' in event and (event['image_id'] is None or event['image_id'] in draw['image_ids']),
                'record-damaged', f'{where} names an image outside the original draw')
        require(isinstance(event.get('key'), str) and event['key'], 'record-damaged', f'{where}: empty key')
        require(event.get('operation') in ('set', 'delete'), 'record-damaged', f'{where}: unsupported operation')
        require(('value' in event) == (event['operation'] == 'set'), 'record-damaged',
                f'{where}: value presence does not match its operation')
        canonical(event)  # Reject non-JSON values such as NaN, also on reload.
        events.append(event)
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
    require(isinstance(key, str) and key, 'usage', 'Annotation key must be a nonempty string')
    require(image_id is None or image_id in draw['image_ids'], 'usage',
            f'Image {image_id} is not in draw {sample_id}')
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


def current_images(repo, draw, inventory):
    """Draw-ordered current locations; without a snapshot only identities are known."""
    indexed = {r['image_id']: r for r in inventory['population']['images']} if inventory else {}
    rows = []
    for n, image_id in enumerate(draw['image_ids'], 1):
        if image_id in indexed:
            rows.append(dict(position=n, **current_locations(repo, indexed[image_id])))
        else:
            rows.append(dict(position=n, image_id=image_id, available_path=None, locations=[]))
    return rows


def inspect_draw(store, sample_id, repo, paths_only=False):
    draw = read_draw(store, sample_id)
    inventory, problems = resolve_inventory(store, draw)
    current = current_images(repo, draw, inventory)
    if paths_only:
        return dict(schema_version=1, sample_id=sample_id, images=current, problems=problems)
    try:
        events = read_events(store, draw)
    except SamplerError as error:
        events = []
        problems.append(dict(kind='annotations-unreadable', **error.report()))
    indexed = {r['image_id']: r for r in inventory['population']['images']} if inventory else {}
    return dict(schema_version=1, draw=draw,
                snapshot_available=inventory is not None,
                images=[indexed.get(i, dict(image_id=i)) for i in draw['image_ids']],
                current_locations=current, annotations=annotation_state(events),
                annotation_history=events, problems=problems)


def verify_draw(store, sample_id, repo):
    draw = read_draw(store, sample_id)
    inventory, problems = resolve_inventory(store, draw)
    try:
        read_events(store, draw)
    except SamplerError as error:
        problems.append(dict(kind='annotations-unreadable', **error.report()))
    current = current_images(repo, draw, inventory)
    for row in current:
        for location in row['locations']:
            if location['status'] != 'ok':
                problems.append(dict(kind='image-unavailable', image_id=row['image_id'],
                                     **{k: v for k, v in location.items() if k != 'absolute_path'}))
    if inventory:
        selected = [i for i in inventory['population']['images'] if i['image_id'] in set(draw['image_ids'])]
        leaf_paths = {a['fixture_path'] for item in selected for a in item['aliases']}
        for record in inventory['population']['metadata_files']:
            if any(record['path'].startswith(leaf + '/') for leaf in leaf_paths):
                status = location_status(repo, record['path'], record['sha256'])
                if status['status'] != 'ok':
                    problems.append(dict(kind='metadata-changed', path=record['path'], **status))
    return dict(schema_version=1, sample_id=sample_id, record_valid=True,
                original_draw_reproduced=inventory is not None,
                requested_size=draw['requested_size'],
                images_available=sum(r['available_path'] is not None for r in current),
                problems=problems, ok=not problems)


def list_draws(store):
    """Every draw directory is listed; a damaged record is reported, not skipped."""
    draws, problems = [], []
    for path in sorted((Path(store) / 'draws').glob('draw-*/draw.json')):
        sample_id = path.parent.name
        try:
            draw = read_draw(store, sample_id)
            entry = {k: draw[k] for k in ('sample_id', 'created_at', 'requested_size',
                                          'inventory_id', 'seed')}
            entry['snapshot_present'] = inventory_file(store, draw['inventory_id']).is_file()
            entry['status'] = 'ok' if entry['snapshot_present'] else 'snapshot-missing'
        except SamplerError as error:
            entry = dict(sample_id=sample_id, created_at=None, status='damaged', error=error.report())
        if entry['status'] != 'ok':
            problems.append(dict(kind='draw-' + entry['status'], sample_id=sample_id))
        draws.append(entry)
    draws.sort(key=lambda r: (r['created_at'] or '', r['sample_id']))
    return dict(schema_version=1, draws=draws, problems=problems)


def population_problems(inventory):
    pop = inventory['population']
    problems = [dict(kind='alias-unavailable', image_id=i['image_id'], path=a['path'], **a['availability'])
                for i in pop['images'] for a in i['aliases'] if a['availability']['status'] != 'ok']
    problems.extend(dict(kind='unlisted-input', path=p) for p in pop['unlisted_inputs'])
    return problems


def inventory_report(inventory, store):
    pop = inventory['population']
    return dict(schema_version=1, inventory_id=inventory['inventory_id'],
                file=str(inventory_file(store, inventory['inventory_id']).resolve()),
                counts=pop['counts'], unlisted_inputs=pop['unlisted_inputs'],
                problems=population_problems(inventory))


def sample_output(repo, store):
    """Only this fixed scratch directory may be replaced by a draw."""
    output = Path(repo).resolve() / 'output'
    target = output / 'sampled'
    require(not output.is_symlink() and not target.is_symlink(), 'output',
            f'{output} and {target} must not be symlinks')
    require(not Path(store).resolve().is_relative_to(target), 'output',
            f'Sample records must be stored outside {target}')
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
                require(image['available_path'] is not None, 'output',
                        f'Selected image {image["image_id"]} is unavailable; nothing was published')
                source = Path(image['available_path'])
                sha256 = image['image_id'].removeprefix('sha256:')
                name = f"{image['position']:04d}-{sha256}{source.suffix}"
                destination = staged / name
                shutil.copyfile(source, destination)
                require(file_hash(destination) == sha256, 'output',
                        f'Copied image checksum differs: {name}; nothing was published')
                copied.append(dict(image, sampled_path=str(target / name)))
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            staged.rename(target)
        return copied
    finally:
        os.close(lock)


def draw_command(args):
    target = sample_output(args.repo, args.store)
    inventory = (load_inventory(args.store, args.inventory) if args.inventory
                 else build_inventory(args.repo))
    drawn = create_draw(args.store, inventory, args.size, args.seed)
    check = verify_draw(args.store, drawn['sample_id'], args.repo)
    images = inspect_draw(args.store, drawn['sample_id'], args.repo, paths_only=True)['images']
    for image in images:
        image['sampled_path'] = None
    result = dict(schema_version=1, draw=drawn, population=inventory_report(inventory, args.store),
                  images=images, current_check=check,
                  output=dict(directory=str(target), published=False), problems=[])
    if check['ok']:
        try:
            result['images'] = publish_sample(args.repo, args.store, result['images'])
            result['output']['published'] = True
        except (OSError, SamplerError) as error:
            result['output']['error'] = f'{type(error).__name__}: {error}'
    if not result['output']['published']:
        result['problems'].append(dict(kind='not-published', error=result['output'].get(
            'error', 'selected images or metadata failed the current check')))
    result['problems'].extend(check['problems'])
    result['problems'].extend(result['population']['problems'])
    return result


def annotation_value(args):
    if args.delete:
        return None
    try:
        if args.json is not None:
            return json.loads(args.json)
        if args.value_file == '-':
            return json.load(sys.stdin)
        return read_json(Path(args.value_file), 'Annotation value file', code='usage')
    except json.JSONDecodeError as error:
        raise SamplerError('usage', f'Annotation value is not valid JSON: {error}') from None


def run(args):
    if args.command == 'inventory':
        return inventory_report(save_inventory(args.store, build_inventory(args.repo)), args.store)
    if args.command == 'draw':
        return draw_command(args)
    if args.command == 'list':
        return list_draws(args.store)
    if args.command == 'show':
        return inspect_draw(args.store, args.sample_id, args.repo, args.paths)
    if args.command == 'verify':
        return verify_draw(args.store, args.sample_id, args.repo)
    return annotate(args.store, args.sample_id, args.key, annotation_value(args), args.image,
                    args.delete, args.author)


class Parser(argparse.ArgumentParser):
    """Argument mistakes are reported like every other failure: JSON on stdout, exit 2."""
    def error(self, message):
        self.print_usage(sys.stderr)
        emit_error(SamplerError('usage', message))
        raise SystemExit(2)


def emit_error(error):
    print(json.dumps(dict(schema_version=1, error=error.report()), ensure_ascii=False, indent=2))
    print(f'sampler: {error}', file=sys.stderr)


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
    parser = Parser(
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
    commands.add_parser('list', help='List persistent draws, including damaged ones')
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
        result = run(args)
    except SamplerError as error:
        emit_error(error)
        return 2
    except OSError as error:
        emit_error(SamplerError('io', f'{type(error).__name__}: {error}'))
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
    return 1 if result.get('problems') else 0


if __name__ == '__main__':
    sys.exit(main())
