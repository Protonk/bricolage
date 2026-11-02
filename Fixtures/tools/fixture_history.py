"""Record changes to a published leaf, with receipts a reader can verify.

Two changes exist: removing an active input and re-pinning one to replacement
bytes. Each writes a numbered receipt with the catalogs as they were, the
exact row, the reason and before/after hashes, and preserves the bytes it
retires. The chain of receipts must end at the live catalogs. Nothing here
rebuilds an earlier publication; the specialized validators describe the
publication as it was, and the shared layout check describes the leaf as it is.
"""
import csv
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone

from fixture_layout import require, sha

CATALOGS = ('manifest.json', 'manifest.csv', 'sources.csv', 'SHA256SUMS.txt', 'probes.csv', 'selections.json')
COPIES = {'source', 'byte_copy', 'singleton'}
DIRECTORIES = {'removal': 'provenance/removals', 'repin': 'provenance/repins'}


def safe(root, name):
    path = root / name
    require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and path.resolve().is_relative_to(root.resolve()), f'Unsafe path: {name}')
    require(not any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)),
            f'Symlink in path: {name}')
    return path


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def catalogs(root):
    names = [*CATALOGS, *(p.relative_to(root).as_posix() for p in sorted((root / 'batches').glob('*.txt')))]
    return {name: safe(root, name).read_bytes() for name in names}


def csv_bytes(raw, rows):
    fields = next(csv.reader(io.StringIO(raw.decode())))
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\r\n' if b'\r\n' in raw else '\n')
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def checksum_lines(raw):
    return raw.decode().splitlines(keepends=True)


def project_removal(before, row):
    """Derive the catalogs after removing exactly one recorded input."""
    name = row['file']
    manifest = json.loads(before['manifest.json'])
    require([r for r in manifest['images'] if r['file'] == name] == [row], f'Removal row differs: {name}')
    require(len(manifest['images']) > 1, 'Removing the last input is unsupported; retire the collection explicitly')
    after = dict(before)
    manifest['images'] = [r for r in manifest['images'] if r['file'] != name]
    after['manifest.json'] = encode(manifest)
    after['manifest.csv'] = csv_bytes(before['manifest.csv'], manifest['images'])
    lines = checksum_lines(before['SHA256SUMS.txt'])
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


def project_repin(before, receipt):
    """Derive the catalogs after one input's bytes are replaced; paths and sizes stay."""
    row, new = receipt['image'], receipt['replacement']['byte_sha256']
    name = row['file']
    manifest = json.loads(before['manifest.json'])
    require([r for r in manifest['images'] if r['file'] == name] == [row], f'Re-pin row differs: {name}')
    after = dict(before)
    for record in manifest['images']:
        if record['file'] == name:
            record['byte_sha256'] = new
            record['pixels_rgb_sha256'] = ''
    after['manifest.json'] = encode(manifest)
    after['manifest.csv'] = csv_bytes(before['manifest.csv'], manifest['images'])
    replaced = {name: (row['byte_sha256'], new)}
    if receipt['source_replaced']:
        replaced['sources/' + receipt['source_filename']] = (receipt['source_sha256_before'], new)
    lines, seen = [], set()
    for line in checksum_lines(before['SHA256SUMS.txt']):
        old, path = line.rstrip('\r\n').split('  ', 1)
        if path in replaced:
            require(old == replaced[path][0], f'Changed checksum before re-pin: {path}')
            seen.add(path)
            line = line.replace(old, replaced[path][1], 1)
        lines.append(line)
    require(seen == set(replaced), 'Missing checksum line for re-pinned bytes')
    after['SHA256SUMS.txt'] = ''.join(lines).encode()
    if receipt['source_replaced'] and 'sources.csv' in before:
        sources = list(csv.DictReader(io.StringIO(before['sources.csv'].decode())))
        hits = [s for s in sources if s['source_filename'] == receipt['source_filename']]
        require(len(hits) == 1 and hits[0]['source_sha256'] == receipt['source_sha256_before'], 'Source catalog differs before re-pin')
        hits[0]['source_sha256'] = new
        after['sources.csv'] = csv_bytes(before['sources.csv'], sources)
    return after


def load_record(root, kind, entry):
    receipt = json.loads(safe(root, str(entry.relative_to(root) / 'receipt.json')).read_text())
    require(receipt['schema_version'] == 1 and receipt['reason'].strip(), f'Invalid receipt: {entry}')
    require(receipt.get('kind', 'removal') == kind, f'Receipt kind differs from its directory: {entry}')
    before = {name: safe(root, str(entry.relative_to(root) / 'before' / name)).read_bytes()
              for name in receipt['before_sha256']}
    require(set(before) <= set(CATALOGS) | {n for n in before if n.startswith('batches/') and len(Path(n).parts) == 2},
            f'Invalid catalog list: {entry}')
    require({name: digest(raw) for name, raw in before.items()} == receipt['before_sha256'], f'Changed snapshot: {entry}')
    row = receipt['image']
    require(Path(row['file']).parts[0] == 'images' and len(Path(row['file']).parts) == 2, 'Invalid input path in receipt')
    after = project_removal(before, row) if kind == 'removal' else project_repin(before, receipt)
    require({name: digest(raw) for name, raw in after.items()} == receipt['after_sha256'], f'Changed projection: {entry}')
    return dict(kind=kind, entry=entry, receipt=receipt, before=before, after=after,
                at=receipt.get('changed_at') or receipt.get('removed_at'))


def history(root, *, assets=False):
    """Every recorded change in order, verified as a chain that ends at the live catalogs."""
    root = Path(root)
    records = []
    for kind, relative in DIRECTORIES.items():
        directory = root / relative
        if not directory.exists():
            continue
        require(not directory.is_symlink(), f'Symlinked history: {directory}')
        entries = sorted(directory.iterdir())
        for number, entry in enumerate(entries, 1):
            require(entry.name == f'{number:04d}' and entry.is_dir(), f'Incomplete or unexpected record: {entry}')
            records.append(load_record(root, kind, entry))
    records.sort(key=lambda r: (r['at'], r['kind'], r['entry'].name))
    previous = None
    for record in records:
        if previous is not None:
            shared = set(record['before']) & set(previous)
            require(all(record['before'][n] == previous[n] for n in shared), f'Broken change sequence: {record["entry"]}')
        if assets:
            verify_assets(root, record)
        previous = dict(previous or {}, **record['after'])
    if previous is not None:
        live = catalogs(root)
        require(all(live[n] == previous[n] for n in previous), f'Active catalogs differ from recorded changes: {root}')
    return records


def verify_assets(root, record):
    receipt, row = record['receipt'], record['receipt']['image']
    if record['kind'] == 'removal':
        archive = safe(root, receipt['preserved_image'])
        require(Path(receipt['preserved_image']).parts[:2] == ('previews', 'removed'), 'Invalid preserved-image path')
        require(not safe(root, row['file']).exists(), f'Removed input was restored: {row["file"]}')
        require(sha(archive) == row['byte_sha256'], f'Changed preserved image: {archive}')
    else:
        previous = receipt['previous']
        if previous['preserved']:
            require(Path(previous['preserved']).parts[:2] == ('previews', 'repinned'), 'Invalid preserved-bytes path')
            require(sha(safe(root, previous['preserved'])) == previous['observed_sha256'], f'Changed preserved bytes: {previous["preserved"]}')


def require_unchanged(root):
    require(not history(root), f'Rebuilding a publication after recorded changes is unsupported: {root}; the receipts are the record')


def atomic_write(path, raw):
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def next_entry(root, kind):
    directory = root / DIRECTORIES[kind]
    directory.mkdir(exist_ok=True)
    return directory, directory / f'{len([p for p in directory.iterdir() if not p.name.startswith(".")]) + 1:04d}'


def write_receipt(directory, entry, before, receipt):
    pending = Path(tempfile.mkdtemp(prefix='.pending-', dir=directory))
    for name, raw in before.items():
        path = pending / 'before' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    (pending / 'receipt.json').write_bytes(encode(receipt))
    return pending


def discard(directory, pending):
    shutil.rmtree(pending, ignore_errors=True)
    if directory.exists() and not any(directory.iterdir()):
        directory.rmdir()


def remove(root, row, reason, *, dry_run=False):
    root = Path(root).resolve()
    require(reason.strip(), 'A removal reason is required')
    from fixture_layout import check_layout
    (root / 'previews').mkdir(exist_ok=True)
    with (root / 'previews/change.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_layout(root)
        history(root, assets=True)
        before = catalogs(root)
        after = project_removal(before, row)
        image = safe(root, row['file'])
        require(sha(image) == row['byte_sha256'], f'Changed input: {image}')
        archive_name = f'previews/removed/{row["byte_sha256"]}{image.suffix}'
        archive = safe(root, archive_name)
        require(not archive.exists() or sha(archive) == row['byte_sha256'], f'Changed preserved image: {archive}')
        result = dict(status='planned' if dry_run else 'removed', file=row['file'], byte_sha256=row['byte_sha256'],
                      fixture=str(root), remaining_inputs=len(json.loads(after['manifest.json'])['images']))
        if dry_run:
            return result
        directory, entry = next_entry(root, 'removal')
        receipt = dict(schema_version=1, kind='removal', changed_at=datetime.now(timezone.utc).isoformat(), reason=reason,
                       image=row, preserved_image=archive_name,
                       before_sha256={n: digest(b) for n, b in before.items()},
                       after_sha256={n: digest(b) for n, b in after.items()})
        receipt['removed_at'] = receipt['changed_at']
        archived = archive.exists()
        pending = None
        try:
            pending = write_receipt(directory, entry, before, receipt)
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
            if pending is not None:
                discard(directory, pending)
            raise
        history(root, assets=True)
        return result


def decoded(path):
    """Stored dimensions, orientation and format of an image file, via the pinned Pillow."""
    try:
        from PIL import Image
    except ImportError:
        raise ValueError('Re-pinning decodes the replacement; install Fixtures/tools/requirements.txt') from None
    with Image.open(path) as image:
        image.load()
        require(getattr(image, 'n_frames', 1) == 1, 'Replacement has more than one frame')
        return dict(width=image.width, height=image.height, exif_orientation=image.getexif().get(274, 1), format=image.format)


def repin(root, row, replacement, reason, *, dry_run=False):
    """Replace one active input's bytes with a decoded-equivalent file and record why.

    The replacement must decode to the recorded size, orientation and format.
    If the input is a byte copy of its source file, the source bytes change with
    it and the source catalog's hash follows. Whatever bytes were there are
    preserved under previews/repinned/; a missing input is simply recorded as
    missing. No network, no judgment about whether the replacement is right.
    """
    root = Path(root).resolve()
    replacement = Path(replacement).resolve()
    require(reason.strip(), 'A re-pin reason is required')
    require(replacement.is_file() and not replacement.is_symlink(), f'Replacement is not a regular file: {replacement}')
    require(not replacement.is_relative_to(root), 'Replacement must come from outside the leaf')
    from fixture_layout import check_layout
    (root / 'previews').mkdir(exist_ok=True)
    with (root / 'previews/change.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_layout(root, assets=False)
        history(root, assets=True)
        before = catalogs(root)
        manifest = json.loads(before['manifest.json'])
        require([r for r in manifest['images'] if r['file'] == row['file']] == [row], f'Active row differs: {row["file"]}')
        raw = replacement.read_bytes()
        new = digest(raw)
        measured = decoded(replacement)
        differences = {k: (row[k], v) for k, v in measured.items() if row[k] != v}
        require(not differences, 'Replacement is not equivalent to the recorded input: ' + json.dumps(differences))
        if new == row['byte_sha256']:
            return dict(status='identical', file=row['file'], byte_sha256=new, fixture=str(root))
        image = safe(root, row['file'])
        sources = list(csv.DictReader(io.StringIO(before['sources.csv'].decode())))
        source = next((s for s in sources if s['family_id'] == row['family_id']), None) if row['family_id'] else None
        source_replaced = bool(source and row['transformation'] in COPIES and source['source_sha256'] == row['byte_sha256'])
        observed = sha(image) if image.exists() else None
        preserved = f'previews/repinned/{observed}{image.suffix}' if observed else None
        receipt = dict(schema_version=1, kind='repin', changed_at=datetime.now(timezone.utc).isoformat(), reason=reason,
                       image=row, replacement=dict(byte_sha256=new, bytes=len(raw), **measured),
                       source_replaced=source_replaced, source_filename=source['source_filename'] if source_replaced else None,
                       source_sha256_before=source['source_sha256'] if source_replaced else None,
                       previous=dict(observed_sha256=observed, matched_record=observed == row['byte_sha256'], preserved=preserved),
                       before_sha256={n: digest(b) for n, b in before.items()})
        after = project_repin(before, receipt)
        receipt['after_sha256'] = {n: digest(b) for n, b in after.items()}
        result = dict(status='planned' if dry_run else 'repinned', file=row['file'], previous_sha256=row['byte_sha256'],
                      byte_sha256=new, source_replaced=source_replaced, previous_bytes='preserved' if observed else 'missing',
                      fixture=str(root))
        if dry_run:
            return result
        directory, entry = next_entry(root, 'repin')
        source_path = safe(root, 'sources/' + source['source_filename']) if source_replaced else None
        source_backup = source_path.read_bytes() if source_path and source_path.exists() else None
        keep = safe(root, preserved) if preserved else None
        pending = None
        try:
            pending = write_receipt(directory, entry, before, receipt)
            if keep is not None and not keep.exists():
                keep.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(image, keep)
            image.parent.mkdir(exist_ok=True)
            atomic_write(image, raw)
            if source_path is not None:
                source_path.parent.mkdir(exist_ok=True)
                atomic_write(source_path, raw)
            for name, value in after.items():
                if value != before[name]:
                    atomic_write(root / name, value)
            pending.rename(entry)
        except BaseException:
            for name, value in before.items():
                atomic_write(root / name, value)
            if keep is not None and keep.exists():
                shutil.copyfile(keep, image)
            elif observed is None and image.exists():
                image.unlink()
            if source_path is not None and source_backup is not None:
                atomic_write(source_path, source_backup)
            if pending is not None:
                discard(directory, pending)
            raise
        history(root, assets=True)
        check_layout(root)
        return result
