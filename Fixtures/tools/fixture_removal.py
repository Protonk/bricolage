"""Remove active inputs while retaining verifiable publication history."""
from contextlib import contextmanager
from functools import wraps
import csv
import fcntl
import hashlib
import io
import inspect
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone

from fixture_layout import FIXTURES, require, sha

CATALOGS = ('manifest.json', 'manifest.csv', 'SHA256SUMS.txt', 'probes.csv', 'selections.json')


def safe(root, name):
    path = root / name
    require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and path.resolve().is_relative_to(root.resolve()), f'Unsafe removal path: {name}')
    require(not any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)),
            f'Symlink in removal path: {name}')
    return path


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def catalogs(root):
    names = [*CATALOGS, *(p.relative_to(root).as_posix() for p in sorted((root / 'batches').glob('*.txt'))) ]
    return {name: safe(root, name).read_bytes() for name in names}


def csv_bytes(raw, rows):
    fields = next(csv.reader(io.StringIO(raw.decode())))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\r\n' if b'\r\n' in raw else '\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def project(before, row):
    """Derive all live catalogs by removing exactly one recorded input."""
    name = row['file']
    manifest = json.loads(before['manifest.json'])
    require([r for r in manifest['images'] if r['file'] == name] == [row], f'Removal row differs: {name}')
    require(len(manifest['images']) > 1, 'Removing the last input is unsupported; retire the collection explicitly')
    after = dict(before)
    manifest['images'] = [r for r in manifest['images'] if r['file'] != name]
    after['manifest.json'] = encode(manifest)
    after['manifest.csv'] = csv_bytes(before['manifest.csv'], manifest['images'])
    lines = before['SHA256SUMS.txt'].decode().splitlines(keepends=True)
    require(sum(line.rstrip().split('  ', 1) == [row['byte_sha256'], name] for line in lines) == 1,
            f'Missing or changed input checksum: {name}')
    after['SHA256SUMS.txt'] = ''.join(line for line in lines if line.rstrip().split('  ', 1)[-1] != name).encode()
    for key, raw in before.items():
        if key.startswith('batches/'):
            after[key] = b''.join(line for line in raw.splitlines(keepends=True) if line.strip().decode() != name)
    probes = list(csv.DictReader(io.StringIO(before['probes.csv'].decode())))
    remaining = [p for p in probes if name not in (p['file_a'], p['file_b'])]
    if remaining != probes:
        after['probes.csv'] = csv_bytes(before['probes.csv'], remaining)
    selections = json.loads(before['selections.json'])
    selections['pairs'] = [p for p in selections['pairs'] if name not in (p['file_a'], p['file_b'])]
    # Controlled-shift families need their original source input.
    if row['transformation'] == 'source':
        selections['known_shift_families'] = [f for f in selections['known_shift_families'] if f != row['family_id']]
    if selections != json.loads(before['selections.json']):
        after['selections.json'] = encode(selections)
    return after


def history(root, *, assets=False):
    directory = root / 'provenance/removals'
    if not directory.exists():
        return []
    require(not directory.is_symlink(), f'Symlinked removal history: {directory}')
    entries = sorted(directory.iterdir())
    result, previous = [], None
    for number, entry in enumerate(entries, 1):
        require(entry.name == f'{number:04d}' and entry.is_dir(), f'Incomplete or unexpected removal record: {entry}')
        receipt = json.loads(safe(root, str(entry.relative_to(root) / 'receipt.json')).read_text())
        require(receipt['schema_version'] == 1 and receipt['reason'].strip(), f'Invalid removal receipt: {entry}')
        before = {name: safe(root, str(entry.relative_to(root) / 'before' / name)).read_bytes()
                  for name in receipt['before_sha256']}
        require(set(before) == set(CATALOGS) | {n for n in before if n.startswith('batches/') and len(Path(n).parts) == 2},
                f'Invalid removal catalog list: {entry}')
        require({name: digest(raw) for name, raw in before.items()} == receipt['before_sha256'], f'Changed removal snapshot: {entry}')
        require(previous is None or before == previous, f'Broken removal sequence: {entry}')
        row = receipt['image']
        require(Path(row['file']).parts[0] == 'images' and len(Path(row['file']).parts) == 2, 'Invalid removed input path')
        after = project(before, row)
        require({name: digest(raw) for name, raw in after.items()} == receipt['after_sha256'], f'Changed removal projection: {entry}')
        archive = safe(root, receipt['preserved_image'])
        require(Path(receipt['preserved_image']).parts[:2] == ('previews', 'removed'), 'Invalid preserved-image path')
        if assets:
            require(not safe(root, row['file']).exists(), f'Removed input was restored: {row["file"]}')
            require(sha(archive) == row['byte_sha256'], f'Changed preserved image: {archive}')
        result.append((entry, receipt, before))
        previous = after
    require(previous is None or catalogs(root) == previous, f'Active catalogs differ from recorded removals: {root}')
    return result


def historical_manifest(root, expected_sha):
    """Resolve a pinned audit to exact bytes, only through a validated removal chain."""
    current = root / 'manifest.json'
    records = history(root)
    if sha(current) == expected_sha:
        return current
    for entry, receipt, _ in records:
        if receipt['before_sha256']['manifest.json'] == expected_sha:
            return entry / 'before/manifest.json'
    raise ValueError(f'No preserved manifest matching {expected_sha}: {current}')


def require_unremoved(root):
    require(not history(root), f'Rebuilding a publication after removals is unsupported: {root}; reconcile its removal history explicitly')


def atomic_write(path, raw):
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def remove(root, row, reason, *, dry_run=False):
    root = Path(root).resolve()
    require(reason.strip(), 'A removal reason is required')
    from fixture_layout import check_layout
    with (root / 'previews/removal.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_layout(root)
        existing = history(root, assets=True)
        before = catalogs(root)
        after = project(before, row)
        image = safe(root, row['file'])
        require(sha(image) == row['byte_sha256'], f'Changed input: {image}')
        archive_name = f'previews/removed/{row["byte_sha256"]}{image.suffix}'
        archive = safe(root, archive_name)
        require(not archive.exists() or sha(archive) == row['byte_sha256'], f'Changed preserved image: {archive}')
        result = dict(status='planned' if dry_run else 'removed', file=row['file'], byte_sha256=row['byte_sha256'],
                      fixture=str(root), remaining_inputs=len(json.loads(after['manifest.json'])['images']))
        if dry_run:
            return result
        directory = root / 'provenance/removals'
        directory.mkdir(exist_ok=True)
        entry = directory / f'{len(existing)+1:04d}'
        pending = Path(tempfile.mkdtemp(prefix='.pending-', dir=directory))
        receipt = dict(schema_version=1, removed_at=datetime.now(timezone.utc).isoformat(), reason=reason,
                       image=row, preserved_image=archive_name,
                       before_sha256={n: digest(b) for n, b in before.items()},
                       after_sha256={n: digest(b) for n, b in after.items()})
        archived = archive.exists()
        try:
            for name, raw in before.items():
                path = pending / 'before' / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            (pending / 'receipt.json').write_bytes(encode(receipt))
            archive.parent.mkdir(parents=True, exist_ok=True)
            if not archived:
                shutil.copyfile(image, archive)
            for name, raw in after.items():
                if raw != before[name]:
                    atomic_write(root / name, raw)
            image.unlink()
            pending.rename(entry)
        except BaseException:
            for name, raw in before.items():
                atomic_write(root / name, raw)
            if not image.exists() and archive.exists():
                shutil.copyfile(archive, image)
            if not archived and archive.exists():
                archive.unlink()
            shutil.rmtree(pending, ignore_errors=True)
            if not any(directory.iterdir()):
                directory.rmdir()
            raise
        history(root, assets=True)
        return result


@contextmanager
def publication_view(root):
    """Give existing validators the original publication, without changing live inputs.

    Catalog projections and retained media are checked first. Only the affected
    leaf is mirrored; media is hard-linked, metadata copied, and scratch is removed.
    """
    root = Path(root).resolve()
    records = history(root, assets=True)
    if not records:
        yield root
        return
    from fixture_layout import check_layout
    check_layout(root)
    scratch = FIXTURES / 'output'
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='removal-check-', dir=scratch) as temp:
        view = Path(temp) / root.name
        def copy(source, destination):
            relative = Path(source).relative_to(root)
            if relative.parts[0] in {'images', 'sources', 'previews'}:
                os.link(source, destination)
            else:
                shutil.copyfile(source, destination)
        def ignore(directory, names):
            omitted = {'__pycache__', '.DS_Store', 'removal.lock'}
            if Path(directory) == root / 'provenance':
                omitted.add('removals')
            return omitted & set(names)
        shutil.copytree(root, view, copy_function=copy, ignore=ignore)
        for name, raw in records[0][2].items():
            (view / name).write_bytes(raw)
        for _, receipt, _ in records:
            os.link(root / receipt['preserved_image'], view / receipt['image']['file'])
        yield view


def publication_check(function):
    """Adapter for a validator whose first argument is the leaf path."""
    @wraps(function)
    def wrapped(root, *args, **kwargs):
        with publication_view(root) as view:
            return function(view, *args, **kwargs)
    return wrapped


def publication_artifacts(root):
    """Adapter for validators with a separate acquisition root and artifact path."""
    def decorate(function):
        signature = inspect.signature(function)
        @wraps(function)
        def wrapped(*args, **kwargs):
            bound = signature.bind(*args, **kwargs)
            bound.apply_defaults()
            artifacts = next(iter(bound.arguments.values()))
            if artifacts is not None:
                return function(*args, **kwargs)
            with publication_view(root()) as view:
                return function(view)
        return wrapped
    return decorate
