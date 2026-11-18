#!/usr/bin/env python3
"""Sampling engine: draw N equal tickets and retain separate annotations.

Python 3.14 standard library only. No network, image processing or fixture mutations.
The JSON format and byte-exact sampling procedure are documented in README.md.
"""
import argparse
import csv
from contextlib import contextmanager
from dataclasses import dataclass, replace
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
import uuid


REPO = Path(__file__).resolve().parents[2]
UNIFORM_PROCEDURE = 'sha256-counter-rejection-partial-fisher-yates-v1'
POLICY = 'active-manifest-inputs; exact-byte-sha256-aliases; one-ticket-per-hash-v1'
POPULATION_SCHEMAS = (1, 2)  # 1 embedded metadata rows; 2 pins metadata files by hash only.
FIXTURE_AREAS = ('Heaps', 'Relationships')
SKIP_DIRS = {'images', 'sources', 'previews', 'provenance', '__pycache__'}
WORLD_MANIFEST = 'world.json'  # Beside the copies in a world directory: identities only.
RECEIPT_AUTHOR = 'Fixtures/sample'  # Author of the one annotation event each publication appends.
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


def read_json(path, what, code='record-invalid', missing='record-missing'):
    try:
        with path.open(encoding='utf-8') as stream:
            return json.load(stream)
    except FileNotFoundError:
        raise SamplerError(missing, f'{what} is missing: {path}', path=str(path)) from None
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
    require(p.parts and not p.is_absolute() and '..' not in p.parts and '\\' not in value and '\0' not in value,
            'fixture', f'{what} is an unsafe fixture path: {value}')
    return p


def fixture_path(repo, value):
    p = relative_path(value, 'Recorded location')
    require(p.parts[0] == 'Fixtures', 'fixture', 'Recorded location is outside Fixtures: ' + value)
    path = repo.joinpath(*p.parts)
    require(path.resolve().is_relative_to((repo / 'Fixtures').resolve()),
            'fixture', 'Recorded location resolves outside Fixtures: ' + value)
    return path


def leaf_relocations(repo):
    """Recorded leaf renames as former -> current repo-relative leaf paths.

    Read from every `Fixtures/provenance/*/relocations.json` move whose purpose is
    `leaf-rename`. An unreadable record is skipped here; the layout checks report it.
    """
    mapping = {}
    for record in sorted((Path(repo).resolve() / 'Fixtures/provenance').glob('*/relocations.json')):
        try:
            moves = json.loads(record.read_text(encoding='utf-8')).get('moves', [])
        except (OSError, ValueError):
            continue
        for move in moves:
            if (isinstance(move, dict) and move.get('purpose') == 'leaf-rename'
                    and isinstance(move.get('old'), str) and isinstance(move.get('new'), str)):
                mapping[move['old']] = move['new']
    return mapping


def relocated(repo, value):
    """The current repo-relative path for a recorded one inside a renamed leaf, or None."""
    mapping = leaf_relocations(repo)
    current, moved = value, False
    for _ in range(len(mapping) + 1):
        hit = next((old for old in mapping if current == old or current.startswith(old + '/')), None)
        if hit is None:
            break
        current, moved = mapping[hit] + current[len(hit):], True
    return current if moved and current != value else None


def location_status(repo, value, expected):
    """Do not turn changed bytes into a new identity or silently repair an alias.

    A location inside a recorded leaf rename is read at its current path, which is
    reported as `current_path`; the bytes must still match the recorded hash.
    """
    try:
        path = fixture_path(repo, value)
        current = None
        try:
            observed = file_hash(path)
        except FileNotFoundError:
            current = relocated(repo, value)
            if current is None:
                raise
            observed = file_hash(fixture_path(repo, current))
        result = dict(status='ok' if observed == expected else 'changed', observed_sha256=observed)
        if current is not None:
            result['current_path'] = current
        return result
    except FileNotFoundError:
        return dict(status='missing', observed_sha256=None)
    except (OSError, SamplerError) as error:
        return dict(status='inaccessible', observed_sha256=None,
                    error=f'{type(error).__name__}: {error}')


def active_leaves(fixtures):
    """Discover the same leaf directories for sampling, collection and validation."""
    found = []
    for area in FIXTURE_AREAS:
        for parent, dirs, files in os.walk(fixtures / area, followlinks=False):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            if 'manifest.json' in files:
                found.append(Path(parent))
    return sorted(found)


def manifests(repo):
    fixtures = Path(repo).resolve() / 'Fixtures'
    for area in FIXTURE_AREAS:
        root = fixtures / area
        require(root.is_dir(), 'fixture', f'Fixture area is missing: {root}', path=str(root))
    found = [leaf / 'manifest.json' for leaf in active_leaves(fixtures)]
    require(found, 'fixture', 'No active fixture manifests found under Fixtures/Heaps or Fixtures/Relationships')
    return found


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
            require(isinstance(row, dict), 'fixture', 'provenance/import-map.json contains a non-object row')
            key = row.get('final_file')
            if key:
                require(isinstance(key, str), 'fixture', 'provenance/import-map.json final_file must be text')
                require(key not in mapped, 'fixture', f'provenance/import-map.json lists {key} twice')
                mapped[key] = row
        # Pin the readable credit context too, so a changed SOURCES.md is reported.
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
            families = set(filter(None, field(row, 'parents', str, what, 'fixture').split('|')))
            family = field(row, 'family_id', str, what, 'fixture')
            if family:
                families.add(family)
            images.append(dict(name=name, expected=expected, record=row,
                               source_records=[s for s in sources if s.get('family_id') in families],
                               import_record=mapped.get(name)))
        unlisted = [p.relative_to(repo).as_posix() for p in sorted((leaf / 'images').rglob('*'))
                    if p.is_file() and p.relative_to(leaf).as_posix() not in seen]
    except SamplerError as error:
        raise SamplerError('fixture', f'Fixture leaf {rel}: {error}', leaf=rel, **error.details) from None
    except OSError as error:
        raise SamplerError('fixture', f'Fixture leaf {rel}: {error}', leaf=rel) from None
    return dict(leaf=leaf, fixture_path=rel, fixture_id=fixture_id, kind=kind, images=images,
                metadata_files=files, unlisted_inputs=unlisted)


def compact_status(availability):
    """Keep only what an ok/missing/changed/inaccessible status needs to explain itself."""
    compact = dict(status=availability['status'])
    if availability['status'] == 'changed':
        compact['observed_sha256'] = availability['observed_sha256']
    if 'error' in availability:
        compact['error'] = availability['error']
    return compact


def checkout_hint(repo):
    """Where the snapshot was taken, as Git saw it. A hint only; the file pins are authoritative."""
    def git(*words):
        done = subprocess.run(['git', '-C', str(repo), *words], capture_output=True, text=True, timeout=60)
        return done.stdout if done.returncode == 0 else None
    try:
        commit = git('rev-parse', 'HEAD')
        if commit is None:
            return None
        status = git('status', '--porcelain')
        return dict(git_commit=commit.strip(), git_dirty=None if status is None else bool(status.strip()))
    except (OSError, subprocess.SubprocessError):
        return None


def build_inventory(repo):
    """Scan every active leaf. A leaf whose metadata fails is excluded and recorded, not fatal."""
    repo = Path(repo).resolve()
    tickets, metadata_files, unlisted, leaves = {}, [], [], []
    occurrences = 0
    for manifest_path in manifests(repo):
        rel = manifest_path.parent.relative_to(repo).as_posix()
        try:
            leaf = read_leaf(repo, manifest_path)
        except SamplerError as error:
            leaves.append(dict(fixture_path=rel, status='excluded', error=error.report()))
            continue
        leaves.append(dict(fixture_path=rel, fixture_id=leaf['fixture_id'], kind=leaf['kind'],
                           manifest_records=len(leaf['images']), status='ok'))
        metadata_files.extend(leaf['metadata_files'])
        unlisted.extend(leaf['unlisted_inputs'])
        for image in leaf['images']:
            image_id = 'sha256:' + image['expected']
            path = (leaf['leaf'] / image['name']).relative_to(repo).as_posix()
            alias = dict(path=path, fixture_path=leaf['fixture_path'],
                         fixture_id=leaf['fixture_id'], kind=leaf['kind'],
                         availability=compact_status(location_status(repo, path, image['expected'])))
            tickets.setdefault(image_id, dict(image_id=image_id, byte_sha256=image['expected'],
                                              aliases=[]))['aliases'].append(alias)
            occurrences += 1
    images = []
    for image_id in sorted(tickets):
        item = tickets[image_id]
        item['aliases'].sort(key=lambda a: a['path'])
        item['eligible'] = any(a['availability']['status'] == 'ok' for a in item['aliases'])
        images.append(item)
    leaves.sort(key=lambda leaf: leaf['fixture_path'])
    excluded = sum(leaf['status'] == 'excluded' for leaf in leaves)
    population = dict(schema_version=2, policy=POLICY, leaves=leaves, images=images,
                      metadata_files=sorted(metadata_files, key=lambda r: r['path']),
                      unlisted_inputs=sorted(unlisted),
                      counts=dict(leaves=len(leaves), excluded_leaves=excluded,
                                  manifest_records=occurrences, distinct_images=len(images),
                                  eligible=sum(i['eligible'] for i in images),
                                  alias_records=occurrences-len(images)))
    return dict(inventory_id=digest(population), created_at=utc(), checkout=checkout_hint(repo),
                population=population)


def validate_inventory(inventory):
    what = 'Inventory record'
    pop = field(inventory, 'population', dict, what)
    inventory_id = field(inventory, 'inventory_id', str, what)
    require(inventory_id == digest(pop), 'record-damaged', f'{what} {inventory_id}: checksum differs from its contents')
    require(field(pop, 'schema_version', int, what) in POPULATION_SCHEMAS and pop.get('policy') == POLICY,
            'record-invalid', f'{what} {inventory_id}: unsupported population schema or policy')
    images = field(pop, 'images', list, what)
    ids = [field(i, 'image_id', str, what) for i in images]
    require(ids == sorted(set(ids)), 'record-invalid', f'{what} {inventory_id}: tickets must be unique and sorted')
    for item in images:
        sha = field(item, 'byte_sha256', str, what)
        require(HEX.fullmatch(sha) and item['image_id'] == 'sha256:' + sha,
                'record-invalid', f'{what} {inventory_id}: invalid image identity {item["image_id"]}')
        aliases = field(item, 'aliases', list, what)
        for alias in aliases:
            field(alias, 'path', str, what)
            field(alias, 'fixture_path', str, what)
            field(field(alias, 'availability', dict, what), 'status', str, what)
        require(aliases and field(item, 'eligible', bool, what) == any(
            a['availability']['status'] == 'ok' for a in aliases),
            'record-invalid', f'{what} {inventory_id}: invalid eligibility for {item["image_id"]}')
    for record in field(pop, 'metadata_files', list, what):
        field(record, 'path', str, what)
        field(record, 'sha256', str, what)
    for leaf in pop.get('leaves', []):
        field(leaf, 'fixture_path', str, what)
        require(field(leaf, 'status', str, what) in ('ok', 'excluded'), 'record-invalid',
                f'{what} {inventory_id}: unknown leaf status {leaf["status"]}')
    field(pop, 'counts', dict, what)
    return inventory


def excluded_leaves(inventory):
    return [leaf for leaf in inventory['population'].get('leaves', []) if leaf['status'] == 'excluded']


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


@dataclass(frozen=True)
class DrawRequest:
    """Selection inputs shared by both entry points and reconstructed for replay.

    Exclusion is the resolved record, including its source and unmatched IDs.
    Seed may be omitted for a new draw; creation resolves it before selection.
    """
    size: int
    seed: str | None = None
    exclusion: dict | None = None
    procedure: str = UNIFORM_PROCEDURE

    @classmethod
    def from_record(cls, draw):
        exclusion = field(draw, 'exclusion', dict, 'Draw record') if 'exclusion' in draw else None
        return cls(draw['requested_size'], draw['seed'], exclusion, draw['procedure'])

    def record_fields(self):
        fields = dict(procedure=self.procedure, seed=self.seed, requested_size=self.size)
        if self.exclusion is not None:
            fields['exclusion'] = self.exclusion
        return fields


def prepare_candidates(inventory, exclusion=None):
    """Resolve the snapshot to sorted byte identities, with one candidate per hash.

    No randomness or file access: saved exclusions are checked against this
    snapshot, and aliases stay in the inventory rather than becoming tickets.
    """
    validate_inventory(inventory)
    excluded = set(validate_exclusion(exclusion, inventory)) if exclusion is not None else set()
    return tuple(i['image_id'] for i in inventory['population']['images']
                 if i['eligible'] and i['image_id'] not in excluded)


def uniform_sample_ids(candidates, size, seed):
    """The original partial Fisher-Yates procedure; candidates are already prepared."""
    pool = list(candidates)
    rng = RandomStream(seed)
    for i in range(size):
        j = i + rng.randbelow(len(pool) - i)
        pool[i], pool[j] = pool[j], pool[i]
    return pool[:size]


SAMPLING_PROCEDURES = {UNIFORM_PROCEDURE: uniform_sample_ids}


def sampling_procedure(name, what='Draw request'):
    """Resolve the recorded algorithm identity for new draws and old-record replay."""
    require(isinstance(name, str) and name in SAMPLING_PROCEDURES, 'record-invalid',
            f'{what}: unsupported sampling procedure {name}')
    return SAMPLING_PROCEDURES[name]


def select_ids(candidates, size, seed, *, procedure=UNIFORM_PROCEDURE):
    """Select from prepared candidates without consulting inventory, paths or records."""
    algorithm = sampling_procedure(procedure)
    require(type(size) is int and size >= 0, 'usage', 'Sample size must be a nonnegative integer')
    require(isinstance(seed, str), 'usage', 'Seed must be a string')
    require(size <= len(candidates), 'usage', f'Requested {size} images; eligible population is {len(candidates)}')
    return algorithm(candidates, size, seed)


def sample_dir(store, sample_id):
    require(isinstance(sample_id, str) and re.fullmatch(r'draw-[0-9a-f]{32}', sample_id), 'usage',
            f'Expected a full sample ID like draw-<32 hex digits>, got {sample_id!r}')
    return Path(store) / 'draws' / sample_id


def create_draw(store, inventory, request, *, sample_id=None):
    if request.seed is None:
        request = replace(request, seed=secrets.token_hex(32))
    sample_id = sample_id if sample_id is not None else 'draw-' + uuid.uuid4().hex
    directory = sample_dir(store, sample_id)
    candidates = prepare_candidates(inventory, request.exclusion)
    ids = select_ids(candidates, request.size, request.seed, procedure=request.procedure)
    inventory = save_inventory(store, inventory)
    draw = dict(schema_version=1, sample_id=sample_id, created_at=utc(),
                inventory_id=inventory['inventory_id'],
                inventory_file='inventories/' + inventory['inventory_id'] + '.json',
                **request.record_fields(),
                eligible_count=inventory['population']['counts']['eligible'], image_ids=ids)
    draw['draw_sha256'] = digest(draw)
    new_json(directory / 'draw.json', draw)
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
    sampling_procedure(draw['procedure'], what)
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
    request = DrawRequest.from_record(draw)
    candidates = prepare_candidates(inventory, request.exclusion)
    require(draw['image_ids'] == select_ids(candidates, request.size, request.seed, procedure=request.procedure),
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
    # Split on LF only: str.splitlines also breaks on U+2028/U+2029/U+0085, which a JSON string may contain.
    for sequence, line in enumerate(text.split('\n')[:-1], 1):
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


def events_from_stream(stream, draw):
    try:
        return parse_events(stream.read(), draw)
    except UnicodeDecodeError:
        raise SamplerError('record-damaged', f'Annotation log for {draw["sample_id"]} is not UTF-8 text',
                           path=str(stream.name)) from None


def read_events(store, draw):
    path = sample_dir(store, draw['sample_id']) / 'annotations.jsonl'
    try:
        with path.open(encoding='utf-8') as stream:
            fcntl.flock(stream, fcntl.LOCK_SH)
            return events_from_stream(stream, draw)
    except FileNotFoundError:
        return []
    except OSError as error:
        raise SamplerError('io', f'Cannot read annotation log for {draw["sample_id"]}: {error}',
                           path=str(path)) from None


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
        events = events_from_stream(stream, draw)
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
        status = location_status(repo, path, item['byte_sha256'])
        locations.append(dict(path=path, absolute_path=str(Path(repo).resolve() / status.get('current_path', path)),
                              **status))
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


def selected_items(draw, inventory):
    indexed = {r['image_id']: r for r in inventory['population']['images']}
    return [indexed[i] for i in draw['image_ids'] if i in indexed]


def pinned_metadata(repo, inventory, leaf_paths):
    """Compare each pinned metadata file of these leaves with the checkout now."""
    rows = []
    for record in inventory['population']['metadata_files']:
        if any(record['path'].startswith(leaf + '/') for leaf in leaf_paths):
            status = location_status(repo, record['path'], record['sha256'])
            status['status'] = {'ok': 'frozen'}.get(status['status'], status['status'])
            rows.append(dict(path=record['path'], pinned_sha256=record['sha256'], **status))
    return rows


def draw_summary(draw, inventory):
    """Membership of distinct selectable and selected byte IDs in the recorded tree."""
    population = inventory['population']
    candidates = set(prepare_candidates(inventory, draw.get('exclusion')))
    selected = set(draw['image_ids'])
    fixture_ids = {leaf['fixture_path']: leaf['fixture_id'] for leaf in population.get('leaves', [])
                   if leaf['status'] == 'ok'}
    members = {path: set() for path in fixture_ids}
    for image in population['images']:
        for alias in image['aliases']:
            path = alias['fixture_path']
            # Schema 1 recorded the leaf only on its aliases.
            fixture_ids.setdefault(path, alias.get('fixture_id'))
            ids = members.setdefault(path, set())
            if image['image_id'] in candidates:
                ids.add(image['image_id'])

    def counts(ids):
        return dict(eligible=len(ids), selected=len(selected.intersection(ids)))

    leaves, by_leaf = [], {}
    branch_members = {'Fixtures': set()}
    for path, ids in sorted(members.items()):
        row = dict(fixture_id=fixture_ids[path], fixture_path=path, **counts(ids))
        leaves.append(row)
        if row['selected']:
            by_leaf[path] = row['selected']
        for parent in PurePosixPath(path).parents:
            if parent.parts:
                branch_members.setdefault(str(parent), set()).update(ids)
    branches = {path: counts(ids) for path, ids in sorted(branch_members.items())}
    return dict(by_leaf=by_leaf, leaves=leaves, branches=branches)


class Provenance:
    """Resolve the live manifest and catalog rows behind a snapshot alias.

    Rows are read from the checkout, never stored in the snapshot. Each leaf's pinned
    metadata files are compared with the checkout; `frozen` means every pinned file of
    the leaf still has its recorded bytes, so the rows shown are exactly the frozen ones.
    """
    def __init__(self, repo, inventory):
        self.repo = Path(repo).resolve()
        self.inventory = inventory
        self.leaves = {}

    def leaf(self, leaf_path):
        if leaf_path not in self.leaves:
            pins = pinned_metadata(self.repo, self.inventory, [leaf_path])
            try:
                leaf_dir = fixture_path(self.repo, leaf_path)
                if not leaf_dir.is_dir() and relocated(self.repo, leaf_path):
                    leaf_dir = fixture_path(self.repo, relocated(self.repo, leaf_path))
                data = read_leaf(self.repo, leaf_dir / 'manifest.json')
                error = None
            except SamplerError as failure:
                data, error = None, failure.report()
            if data is not None:
                pinned = {relocated(self.repo, r['path']) or r['path'] for r in pins}
                pins.extend(dict(path=r['path'], pinned_sha256=None, status='unpinned', observed_sha256=r['sha256'])
                            for r in data['metadata_files'] if r['path'] not in pinned)
            frozen = error is None and all(r['status'] == 'frozen' for r in pins)
            self.leaves[leaf_path] = dict(data=data, error=error, metadata=pins,
                                          status='frozen' if frozen else 'unreadable' if error else 'changed')
        return self.leaves[leaf_path]

    def alias(self, alias):
        leaf = self.leaf(alias['fixture_path'])
        result = dict(path=alias['path'], fixture_path=alias['fixture_path'],
                      fixture_id=alias.get('fixture_id'), kind=alias.get('kind'),
                      status=leaf['status'], metadata=leaf['metadata'],
                      manifest_record=None, source_records=[], import_record=None)
        if leaf['error']:
            result['error'] = leaf['error']
            return result
        name = alias['path'].removeprefix(alias['fixture_path'] + '/')
        image = next((i for i in leaf['data']['images'] if i['name'] == name), None)
        if image is None:
            result['status'] = 'unlisted-now'
            return result
        result.update(manifest_record=image['record'], source_records=image['source_records'],
                      import_record=image['import_record'])
        return result


def metadata_problems(provenance_rows):
    """One problem per pinned file that no longer has its recorded bytes, deduplicated."""
    seen, problems = set(), []
    for row in provenance_rows:
        if 'error' in row and row['status'] == 'unreadable':
            key = ('leaf', row['fixture_path'])
            if key not in seen:
                seen.add(key)
                problems.append(dict(kind='leaf-unreadable', fixture_path=row['fixture_path'], **row['error']))
        for record in row['metadata']:
            if record['status'] != 'frozen' and ('file', record['path']) not in seen:
                seen.add(('file', record['path']))
                problems.append(dict(kind='metadata-changed', **record))
    return problems


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
    images, summary, checkout = [], dict(by_leaf={}), None
    if inventory:
        provenance = Provenance(repo, inventory)
        indexed = {r['image_id']: r for r in inventory['population']['images']}
        for n, image_id in enumerate(draw['image_ids'], 1):
            item = indexed.get(image_id, dict(image_id=image_id, aliases=[]))
            images.append(dict(position=n, **item,
                               provenance=[provenance.alias(a) for a in item['aliases']]))
        problems.extend(metadata_problems(row for image in images for row in image['provenance']))
        summary = draw_summary(draw, inventory)
        checkout = inventory.get('checkout')
    else:
        images = [dict(position=n, image_id=i) for n, i in enumerate(draw['image_ids'], 1)]
    return dict(schema_version=1, draw=draw, snapshot_available=inventory is not None,
                snapshot_checkout=checkout, summary=summary, images=images,
                current_locations=current, annotations=annotation_state(events),
                annotation_history=events, problems=problems)


def unlisted_images(repo, inventory, items, changed):
    """Selected images that no leaf lists any longer, one problem each.

    A leaf whose manifest still has its pinned bytes lists what it listed at the draw,
    so only leaves with a changed manifest are read again. A removal elsewhere in a
    leaf leaves the draw's own images listed. A removed or re-pinned image is named
    here whether or not a copy of its bytes remains, as one does in a checkout that
    has not run `collection reconcile`.
    """
    stale = {record['path'] for record in changed}
    provenance = Provenance(repo, inventory)

    def listed(item, alias):
        if alias['fixture_path'] + '/manifest.json' not in stale:
            return True
        record = provenance.alias(alias)['manifest_record']
        return record is not None and record.get('byte_sha256') == item['byte_sha256']

    return [dict(kind='image-unlisted', image_id=item['image_id'], paths=[alias['path'] for alias in item['aliases']],
                 message='No active manifest lists this image now; it was removed or replaced after the draw')
            for item in items if not any(listed(item, alias) for alias in item['aliases'])]


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
        items = selected_items(draw, inventory)
        leaf_paths = {a['fixture_path'] for item in items for a in item['aliases']}
        changed = [record for record in pinned_metadata(repo, inventory, leaf_paths)
                   if record['status'] != 'frozen']
        problems.extend(dict(kind='metadata-changed', **record) for record in changed)
        problems.extend(unlisted_images(repo, inventory, items, changed))
    # Missing redundant aliases and changed catalogs remain problems, but one verified
    # copy is sufficient to publish an identity that some leaf still lists. Record and
    # annotation failures, and an image no leaf lists any longer, still block.
    publication_ready = (inventory is not None and all(r['available_path'] is not None for r in current)
                         and all(p['kind'] in ('image-unavailable', 'metadata-changed') for p in problems))
    return dict(schema_version=1, sample_id=sample_id, record_valid=True,
                original_draw_reproduced=inventory is not None,
                requested_size=draw['requested_size'],
                images_available=sum(r['available_path'] is not None for r in current),
                problems=problems, ok=not problems, publication_ready=publication_ready)


def list_draws(store):
    """Every draw directory is listed; a damaged record is reported, not skipped."""
    draws, problems = [], []
    for path in sorted((Path(store) / 'draws').glob('draw-*')):
        if not path.is_dir():
            continue
        sample_id = path.name
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


def list_default_draws(repo):
    stores = (scratch_store(repo), durable_store(repo))
    rows, problems = {}, []
    for store in stores:
        report = list_draws(store)
        problems.extend(report['problems'])
        for row in report['draws']:
            sid = row['sample_id']
            if sid in rows:
                try:
                    if resolve_store(repo, sample_id=sid) != store:
                        continue
                except SamplerError as error:
                    row = dict(row, status='conflict')
                    problems.append(dict(kind='draw-conflict', sample_id=sid, error=error.report()))
            rows[sid] = dict(row, store=str(store.resolve()))
    return dict(schema_version=1, stores=[str(p.resolve()) for p in stores],
                draws=sorted(rows.values(), key=lambda r: (r['created_at'] or '', r['sample_id'])), problems=problems)


def population_problems(inventory):
    pop = inventory['population']
    problems = [dict(kind='leaf-excluded', fixture_path=leaf['fixture_path'], **leaf['error'])
                for leaf in excluded_leaves(inventory)]
    problems.extend(dict(kind='alias-unavailable', image_id=i['image_id'], path=a['path'], **a['availability'])
                    for i in pop['images'] for a in i['aliases'] if a['availability']['status'] != 'ok')
    problems.extend(dict(kind='unlisted-input', path=p) for p in pop['unlisted_inputs'])
    return problems


def inventory_report(inventory, store):
    pop = inventory['population']
    return dict(schema_version=1, inventory_id=inventory['inventory_id'],
                file=str(inventory_file(store, inventory['inventory_id']).resolve()),
                checkout=inventory.get('checkout'), counts=pop['counts'],
                leaves=pop.get('leaves', []), unlisted_inputs=pop['unlisted_inputs'],
                problems=population_problems(inventory))


def within(path, root):
    """Whether path is root or inside it, judged by the identity of its nearest existing ancestor.

    Comparing resolved paths alone misses case-insensitive filesystems and firmlinks,
    where two spellings name one directory.
    """
    path, root = Path(path), Path(root)
    try:
        anchor = os.stat(root)
    except OSError:
        return path.resolve().is_relative_to(root.resolve())
    for candidate in (path, *path.parents):
        try:
            if os.path.samestat(os.stat(candidate), anchor):
                return True
        except OSError:
            continue
    return False


def durable_store(repo):
    """The versioned store for retained draws."""
    return Path(repo) / 'Fixtures/Sampler/records'


def scratch_store(repo):
    """The default record store: disposable, under output/, so ordinary draws leave no diff."""
    return Path(repo) / 'Fixtures/output/records'


def resolve_store(repo, store=None, keep=False, sample_id=None):
    """Explicit stores take precedence. Otherwise find a world by its recorded ID."""
    require(store is None or not keep, 'usage', '--store and --keep name different stores; give one')
    if store is not None:
        return Path(store)
    durable = durable_store(repo)
    scratch = scratch_store(repo)
    if keep:
        return durable
    if sample_id is None or not sample_dir(durable, sample_id).exists():
        return scratch
    if sample_dir(scratch, sample_id).exists():
        # Older checkouts can have annotated copies seeded into scratch.
        if history_difference(scratch, durable, sample_id) > 0:
            return scratch
    return durable


def history_difference(source, destination, sample_id):
    """Signed event-count difference for compatible copies of a saved draw."""
    original = read_draw(source, sample_id)
    other = read_draw(destination, sample_id)
    left, right = read_events(source, original), read_events(destination, other)
    common = min(len(left), len(right))
    require(original == other and left[:common] == right[:common], 'record-conflict',
            f'Conflicting records for {sample_id} in {source} and {destination}; inspect each with --store')
    return len(left) - len(right)


def keep_draw(repo, source, sample_id):
    """Publish a validated draw and its complete annotation history in the kept store."""
    durable = durable_store(repo)
    draw, inventory = load_draw(source, sample_id)
    events = read_events(source, draw)
    origin = sample_dir(source, sample_id)
    target = sample_dir(durable, sample_id)
    if not target.exists():
        save_inventory(durable, inventory)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=target.parent, prefix='.keep-') as temp:
            staged = Path(temp) / sample_id
            staged.mkdir()
            shutil.copy2(origin / 'draw.json', staged / 'draw.json')
            if (origin / 'annotations.jsonl').exists():
                shutil.copy2(origin / 'annotations.jsonl', staged / 'annotations.jsonl')
            staged.rename(target)
    elif origin.resolve() != target.resolve():
        load_draw(durable, sample_id)
        if history_difference(source, durable, sample_id) > 0:
            # Older scratch copies may extend the kept history. Install the full log atomically.
            with tempfile.TemporaryDirectory(dir=target, prefix='.keep-') as temp:
                log = Path(temp) / 'annotations.jsonl'
                shutil.copy2(origin / log.name, log)
                log.replace(target / log.name)
        events = read_events(durable, draw)
    return dict(schema_version=1, world_id=sample_id, kept=True, directory=str(target.resolve()),
                inventory_id=draw['inventory_id'], annotation_count=len(events))


@contextmanager
def record_operation(repo, keeping):
    # Promotion changes the store that owns subsequent writes. Other CLI operations
    # share the lock and can run concurrently; keep gets a consistent handoff.
    fd = os.open(Path(repo) / 'Fixtures', os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX if keeping else fcntl.LOCK_SH)
        yield
    finally:
        os.close(fd)


def world_target(repo, store, world=None, *, sample_id=None):
    """Resolve a new publication path without modifying the filesystem."""
    repo = Path(repo).resolve()
    if world is None:
        sample_dir(store, sample_id)  # Validate the ID before using it as a directory name.
        world = repo / 'Fixtures/output/worlds' / sample_id
    target = Path(world)
    target = target.parent.resolve() / target.name
    require(not target.is_symlink(), 'output', f'World directory must not be a symlink: {target}')
    require(not within(target, repo / 'Fixtures') or within(target, repo / 'Fixtures/output'),
            'output', f'A world may not be written among the fixtures: {target}')
    require(all(not within(records, target) and not within(target, records)
                for records in {Path(store), scratch_store(repo), durable_store(repo)}),
            'output', f'Sample records and the world directory must not contain each other: {target}')
    require(not target.exists(), 'output', f'World destination already exists: {target}')
    require(not any((parent / WORLD_MANIFEST).is_file() for parent in target.parents),
            'output', f'World destination is inside an existing world: {target}')
    return target


def copy_name(image):
    """The file name is the identity: the byte hash plus the original extension."""
    return image['image_id'].removeprefix('sha256:') + Path(image['available_path']).suffix


def world_manifest(draw, images):
    """What hazy receives beside the files: identities only, sorted by name, no order or origin."""
    entries = sorted((dict(id=i['image_id'], file=copy_name(i)) for i in images), key=lambda e: e['file'])
    return dict(schema_version=1, world_id=draw['sample_id'], images=entries)


def publish_world(repo, store, draw, images, world=None):
    """Build a complete world, then install it into a directory reserved by this caller."""
    target = world_target(repo, store, world, sample_id=draw['sample_id'])
    target.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix='.world-', dir=target.parent))
    copied = []
    try:
        world_target(repo, store, target)
        os.chmod(staged, 0o777 & ~current_umask())
        for image in images:
            require(image['available_path'] is not None, 'output',
                    f'Selected image {image["image_id"]} is unavailable')
            name = copy_name(image)
            shutil.copyfile(image['available_path'], staged / name)
            require('sha256:' + file_hash(staged / name) == image['image_id'], 'output',
                    f'Copied image checksum differs: {name}')
            copied.append(dict(image, sampled_path=str(target / name)))
        (staged / WORLD_MANIFEST).write_text(json.dumps(world_manifest(draw, images),
                                              ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        # mkdir fails even for an existing empty directory. rename consumes only
        # our own empty reservation; concurrent publishers cannot replace a world.
        target.mkdir()
        try:
            staged.rename(target)
        except BaseException:
            target.rmdir()
            raise
    except BaseException as error:
        try:
            shutil.rmtree(staged)
        except OSError as cleanup:
            raise SamplerError('output', f'{error}; staged files remain at {staged}: {cleanup}') from error
        raise
    return copied, target


def publish_receipt(store, draw, target, count):
    """One sampler-authored annotation event per publication; the clerk decides what else to keep."""
    value = dict(directory=str(target), manifest=str(target / WORLD_MANIFEST),
                 published_at=utc(), image_count=count)
    return annotate(store, draw['sample_id'], 'publication', value, author=RECEIPT_AUTHOR)


def publish_command(store, repo, draw, images, check, world):
    """Shared by draw and publish: copies, manifest, receipt, and a problems list."""
    result = dict(images=images, output=dict(world_id=draw['sample_id'], image_count=0,
                                           directory=None, manifest=None, published=False,
                                           receipt_recorded=False, next_steps=[]), problems=[])
    for image in images:
        image['sampled_path'] = None
    if check['publication_ready']:
        try:
            result['images'], target = publish_world(repo, store, draw, images, world)
            result['output'].update(directory=str(target), manifest=str(target / WORLD_MANIFEST),
                                    image_count=len(images), published=True)
        except (OSError, SamplerError) as error:
            result['output']['error'] = f'{type(error).__name__}: {error}'
        if result['output']['published']:
            try:
                publish_receipt(store, draw, target, len(images))
                result['output']['receipt_recorded'] = True
            except (OSError, SamplerError) as error:
                result['output']['error'] = f'{type(error).__name__}: {error}'
                result['problems'].append(dict(kind='publication-receipt-failed',
                                               error=result['output']['error']))
    if not result['output']['published']:
        result['problems'].append(dict(kind='not-published', error=result['output'].get(
            'error', 'selected images or records failed the current check')))
    result['problems'].extend(check['problems'])
    # Keep recovery next to the handoff. A receipt failure must never suggest a blind retry.
    record_options = (['--keep'] if Path(store).resolve() == durable_store(repo).resolve()
                      else ['--store', str(Path(store).resolve())])
    command = [str(REPO / 'Fixtures/sample'), '--repo', str(Path(repo).resolve()),
               *record_options, 'publish', draw['sample_id']]
    if world is not None and not os.path.lexists(world):
        command.extend(['--world', str(Path(world).absolute())])
    retry = shlex.join(command)
    steps = result['output']['next_steps']
    if not result['output']['published']:
        steps.append('No world was published for this draw. Resolve the named file, record, or output '
                     'problems, then republish the saved selection: ' + retry)
        if any(problem['kind'] == 'image-unlisted' for problem in result['problems']):
            # Nothing here can be resolved: the catalog change is the record. Do not suggest undoing it.
            steps.append('An image-unlisted problem names an image removed or replaced since this draw. '
                         'This selection cannot be republished from the current catalogs; draw again for a world without it.')
    elif not result['output']['receipt_recorded']:
        log = sample_dir(store, draw['sample_id']).resolve() / 'annotations.jsonl'
        steps.append(f'The world is usable. Preserve this response and inspect {log}; the receipt append '
                     'may be partial. Repair a damaged log explicitly before publishing a new receipt: ' + retry)
    return result


def read_exclusion_world(directory):
    """Read the published manifest only; the world's image copies are not required."""
    path = Path(directory) / WORLD_MANIFEST
    what = f'Exclusion world manifest {path}'

    def object_pairs(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'usage', f'{what}: duplicate JSON field {key!r}')
            value[key] = item
        return value

    try:
        raw = path.read_bytes()
        manifest = json.loads(raw.decode('utf-8'), object_pairs_hook=object_pairs)
        canonical(manifest)  # Reject non-JSON numbers and invalid Unicode even in extra fields.
    except (OSError, ValueError, RecursionError, SamplerError) as error:
        raise SamplerError('usage', f'Cannot read {what}: {error}', path=str(path)) from None
    require(field(manifest, 'schema_version', int, what, 'usage') == 1,
            'usage', f'{what}: expected the world.json format published by Fixtures/sample')
    world_id = field(manifest, 'world_id', str, what, 'usage')
    require(bool(world_id), 'usage', f'{what}: world_id must not be empty')
    rows = field(manifest, 'images', list, what, 'usage')
    ids, names = [], []
    for position, row in enumerate(rows):
        entry = f'{what} images[{position}]'
        image_id = field(row, 'id', str, entry, 'usage')
        require(re.fullmatch(r'sha256:[0-9a-f]{64}', image_id), 'usage', f'{entry}: invalid image ID {image_id!r}')
        name = field(row, 'file', str, entry, 'usage')
        require(name and PurePosixPath(name).name == name and '\\' not in name and '\0' not in name
                and Path(name).stem == image_id.removeprefix('sha256:'),
                'usage', f'{entry}: file must be the hash-named filename for its ID: {name!r}')
        ids.append(image_id)
        names.append(name)
    require(len(set(ids)) == len(ids), 'usage', f'{what}: duplicate image IDs')
    require(names == sorted(set(names)), 'usage', f'{what}: filenames must be unique and sorted')
    return dict(world_id=world_id, manifest_sha256=hashlib.sha256(raw).hexdigest(), requested_image_ids=sorted(ids))


def match_exclusion(source, inventory):
    eligible = {image['image_id'] for image in inventory['population']['images'] if image['eligible']}
    requested = set(source['requested_image_ids'])
    matched = sorted(requested & eligible)
    return dict(source, matched_image_ids=matched, unmatched_image_ids=sorted(requested - eligible),
                requested_count=len(requested), matched_count=len(matched), remaining_eligible=len(eligible) - len(matched))


def validate_exclusion(exclusion, inventory):
    """Reconstruct the exact pool from the saved snapshot without reopening the source world."""
    what = 'Draw exclusion'
    world_id = field(exclusion, 'world_id', str, what)
    sha = field(exclusion, 'manifest_sha256', str, what)
    require(world_id and HEX.fullmatch(sha), 'record-invalid', f'{what}: invalid source world identity')
    for key in ('requested_image_ids', 'matched_image_ids', 'unmatched_image_ids'):
        ids = field(exclusion, key, list, what)
        require(all(isinstance(i, str) and re.fullmatch(r'sha256:[0-9a-f]{64}', i) for i in ids),
                'record-invalid', f'{what}: invalid image ID in {key}')
        require(ids == sorted(set(ids)), 'record-invalid', f'{what}: {key} must be unique and sorted')
    for key in ('requested_count', 'matched_count', 'remaining_eligible'):
        field(exclusion, key, int, what)
    expected = match_exclusion(dict(world_id=world_id, manifest_sha256=sha,
                                    requested_image_ids=exclusion['requested_image_ids']), inventory)
    require(expected['matched_image_ids'] and all(exclusion[key] == value for key, value in expected.items()),
            'record-damaged', f'{what}: exclusions or counts differ from the saved population')
    return exclusion['matched_image_ids']


def protect_exclusion_world(source, destination):
    require(not within(destination, source) and not within(source, destination), 'output',
            f'Exclusion world and output/record destinations must not overlap: {source}, {destination}')


def request_from_args(args, inventory, source=None):
    """Translate either CLI's arguments and read world IDs into one draw request."""
    exclusion = match_exclusion(source, inventory) if source is not None else None
    if exclusion is not None:
        # No match can also mean the world's images sit in a leaf the inventory excluded
        # for unreadable metadata. This message does not say so; `Fixtures/sample inventory`
        # names excluded leaves. Other indirect causes are likewise left to that report.
        require(exclusion['matched_count'] > 0, 'usage',
                f'No image IDs in {Path(args.excluded_world) / WORLD_MANIFEST} match eligible fixtures', exclusion=exclusion)
        require(args.size <= exclusion['remaining_eligible'], 'usage',
                f'Requested {args.size} images; {exclusion["remaining_eligible"]} eligible images remain after exclusion',
                exclusion=exclusion)
    return DrawRequest(size=args.size, seed=args.seed, exclusion=exclusion)


def draw_command(args):
    sample_id = 'draw-' + uuid.uuid4().hex
    target = world_target(args.repo, args.store, args.world, sample_id=sample_id)  # Refuse before drawing.
    source = read_exclusion_world(args.excluded_world) if getattr(args, 'excluded_world', None) is not None else None
    if source is not None:
        protect_exclusion_world(args.excluded_world, target)
    if args.inventory:
        origin = args.store
        if args.default_store and not inventory_file(origin, args.inventory).exists():
            origin = durable_store(args.repo)
        inventory = load_inventory(origin, args.inventory)
    else:
        inventory = build_inventory(args.repo)
    request = request_from_args(args, inventory, source)
    drawn = create_draw(args.store, inventory, request, sample_id=sample_id)
    check = verify_draw(args.store, drawn['sample_id'], args.repo)
    images = inspect_draw(args.store, drawn['sample_id'], args.repo, paths_only=True)['images']
    published = publish_command(args.store, args.repo, drawn, images, check, args.world)
    population = inventory_report(inventory, args.store)
    warnings = []
    exclusion = request.exclusion
    if exclusion is not None:
        unmatched = set(exclusion['unmatched_image_ids'])
        warnings = [dict(kind='exclusion-unmatched', image_id=i,
                         message='Image ID is absent from the eligible fixture population; not excluded')
                    for i in exclusion['unmatched_image_ids']]
        # Unavailable exclusion identities reduce the exclusion list. Retain their
        # alias details as warnings; other population problems keep their usual status.
        population['warnings'] = [p for p in population['problems'] if p.get('image_id') in unmatched]
        population['problems'] = [p for p in population['problems'] if p.get('image_id') not in unmatched]
        warnings.extend(population['warnings'])
    result = dict(schema_version=1, output=published['output'], draw=drawn, population=population,
                  summary=draw_summary(drawn, inventory),
                  images=published['images'], current_check=check,
                  problems=published['problems'] + population['problems'])
    if exclusion is not None:
        result.update(exclusion=exclusion, warnings=warnings)
    return result


def republish_command(args):
    """Materialize an existing draw as a world again, under the same world ID."""
    draw, _ = load_draw(args.store, args.sample_id)
    if args.world is None:
        args.world = args.repo / 'Fixtures/output/worlds' / (args.sample_id + '-' + uuid.uuid4().hex)
    world_target(args.repo, args.store, args.world, sample_id=args.sample_id)
    check = verify_draw(args.store, args.sample_id, args.repo)
    images = inspect_draw(args.store, args.sample_id, args.repo, paths_only=True)['images']
    published = publish_command(args.store, args.repo, draw, images, check, args.world)
    return dict(schema_version=1, output=published['output'], sample_id=args.sample_id,
                images=published['images'], current_check=check, problems=published['problems'])


def annotation_value(args):
    if args.delete:
        return None
    try:
        if args.json is not None:
            return json.loads(args.json)
        if args.value_file == '-':
            return json.load(sys.stdin)
        return read_json(Path(args.value_file), 'Annotation value file', code='usage', missing='usage')
    except json.JSONDecodeError as error:
        raise SamplerError('usage', f'Annotation value is not valid JSON: {error}') from None


def run(args):
    if args.command == 'keep':
        return keep_draw(args.repo, args.store, args.sample_id)
    if args.command == 'inventory':
        return inventory_report(save_inventory(args.store, build_inventory(args.repo)), args.store)
    if args.command == 'draw':
        return draw_command(args)
    if args.command == 'publish':
        return republish_command(args)
    if args.command == 'list':
        return list_default_draws(args.repo) if args.default_store else list_draws(args.store)
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


def emit_error(error, repo=REPO):
    report = error.report()
    if error.code == 'output':
        directory = Path(repo).resolve() / 'Fixtures/output'
        report['next_step'] = (f'Use --world with a new directory under {directory}, or resolve '
                              'the named destination problem and retry the request.')
    print(json.dumps(dict(schema_version=1, error=report), ensure_ascii=False, indent=2))
    print(f'sampler: {error}', file=sys.stderr)


def argument_parser(without=False):
    parser = Parser(
        prog='Fixtures/sampleWithout' if without else 'Fixtures/sample',
        usage=None if without else 'Fixtures/sample N [--seed TEXT] [--world NEW_DIR]\n       Fixtures/sample [global options] COMMAND ...',
        description=('Draw N images from eligible fixtures minus the IDs in a published world.json. '
                     'Missing fixture IDs warn and reduce the exclusion list; source image copies are not read.'
                     if without else __doc__), allow_abbrev=False,
        epilog='From a neighboring repository: ../bricolage/Fixtures/sample 100. '
               'Uses its own Python environment; no directory change or imports needed. '
               'Read output first: published says whether the world is ready, directory names it, '
               'world_id identifies it, and image_count counts the published images. '
               'Each draw gets Fixtures/output/worlds/<sample_id>/. '
               'Use the returned directory, or choose a new path with --world DIR.')
    parser.add_argument('--repo', type=Path, default=REPO, help='Checkout containing Fixtures/')
    parser.add_argument('--store', type=Path, help='Explicit record directory. Ordinary draws use scratch and saved draws are found by ID.')
    parser.add_argument('--keep', action='store_true',
                        help='Use the versioned store Fixtures/Sampler/records: a draw meant to be committed')
    if without:
        parser.epilog = ('From a neighboring repository: ../bricolage/Fixtures/sampleWithout WORLD_DIRECTORY N. '
                         'Read output for the new world, exclusion for counts, and warnings for unmatched IDs. '
                         'No matches, invalid world.json, or too few remaining images is an error. '
                         'The input world stays untouched. Use Fixtures/sample to show, verify or publish the saved draw.')
        parser.add_argument('excluded_world', type=Path, metavar='WORLD_DIRECTORY', help='Directory containing published world.json')
        parser.add_argument('size', type=int, metavar='N')
        parser.add_argument('--seed', help='Exact UTF-8 seed text; generated and recorded if omitted')
        parser.add_argument('--world', type=Path, help='New directory to create; default Fixtures/output/worlds/<sample_id>')
        parser.set_defaults(command='draw', inventory=None)
        return parser
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('inventory', help='Refresh and save an immutable population snapshot')
    draw = commands.add_parser('draw', help='Draw N equal tickets and publish them as a world; refresh inventory by default')
    draw.add_argument('size', type=int)
    draw.add_argument('--seed', help='Exact UTF-8 seed text; generated and recorded if omitted')
    draw.add_argument('--inventory', help='Use this saved snapshot instead of rescanning fixtures')
    draw.add_argument('--world', type=Path, help='New directory to create; default Fixtures/output/worlds/<sample_id>')
    publish = commands.add_parser('publish', help='Materialize an existing draw as a world again')
    publish.add_argument('sample_id')
    publish.add_argument('--world', type=Path, help='New directory to create; default is a fresh path under Fixtures/output/worlds/')
    retain = commands.add_parser('keep', help='Save this draw, its inventory and annotation history for Git')
    retain.add_argument('sample_id', metavar='WORLD_ID')
    commands.add_parser('list', help='List scratch and kept draws, including damaged ones')
    show = commands.add_parser('show', help='Original draw, pinned provenance rows, current locations and annotations')
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
    return parser


def main(argv=None, *, without=False):
    if sys.version_info[:2] != (3, 14):
        setup = shlex.join(['make', '-C', str(REPO / 'Fixtures'), 'setup-python'])
        entry = REPO / 'Fixtures' / ('sampleWithout' if without else 'sample')
        print(f'sampler: Python 3.14.x is required. Run {setup}, then use {entry}.', file=sys.stderr)
        return 2
    argv = list(sys.argv[1:] if argv is None else argv)
    # A leading N is shorthand for "draw N", after any global options.
    index = 0
    while not without and index < len(argv):
        argument = argv[index]
        if argument in ('--repo', '--store'):
            index += 2
        elif argument.startswith(('--repo=', '--store=')) or argument == '--keep':
            index += 1
        else:
            if re.fullmatch(r'[+-]?[0-9]+', argument):
                argv.insert(index, 'draw')
            break
    args = argument_parser(without).parse_args(argv)
    try:
        if without:
            requested_store = args.store if args.store is not None else (durable_store(args.repo) if args.keep else scratch_store(args.repo))
            protect_exclusion_world(args.excluded_world, requested_store)
        args.default_store = args.store is None and not args.keep
        with record_operation(args.repo, args.command == 'keep'):
            args.store = resolve_store(args.repo, args.store, args.keep, getattr(args, 'sample_id', None))
            result = run(args)
            if args.command == 'keep':
                args.store = durable_store(args.repo)
        # Every response names the store it read or wrote, so a scratch draw cannot pass for a kept one.
        result = dict(schema_version=result.pop('schema_version'), store=str(args.store.resolve()), **result)
    except SamplerError as error:
        emit_error(error, args.repo)
        return 2
    except OSError as error:
        emit_error(SamplerError('io', f'{type(error).__name__}: {error}'))
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
    return 1 if result.get('problems') else 0


if __name__ == '__main__':
    sys.exit(main())
