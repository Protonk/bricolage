"""Finish a recorded removal, including validation and a commit of only its files.

An immutable operation record pins the scope and pre-change files. It lets a
retry distinguish our unfinished edits from somebody else's work. Per-leaf
receipts remain the authority for membership and preserved image bytes.
"""
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

import collection_totals
import fixture_history as history
from fixture_layout import check_layout, discover, require

OPERATIONS = 'provenance/removal-operations'


class Git:
    def __init__(self, repo):
        self.repo = Path(repo).resolve()
        require(Path(self.run('rev-parse', '--show-toplevel').strip()).resolve() == self.repo,
                f'Fixtures must belong to its own Git checkout: {self.repo}')
        self.run('rev-parse', '--verify', 'HEAD')

    def run(self, *args, binary=False, input=None, check=True):
        result = subprocess.run(['git', '-C', str(self.repo), '--literal-pathspecs', *args],
                                input=input, capture_output=True, text=not binary)
        if check and result.returncode:
            error = result.stderr.decode() if binary else result.stderr
            raise ValueError(f'git {args[0]} failed: {error.strip()}')
        return result.stdout if check else result

    def prepare(self):
        require(not self.run('ls-files', '--unmerged'), 'Resolve the Git index conflicts before removing an image')
        for name in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
            path = Path(self.run('rev-parse', '--path-format=absolute', '--git-path', name).strip())
            require(not path.exists(), f'Finish the current Git operation first: {path}')
        self.run('var', 'GIT_AUTHOR_IDENT')
        self.run('var', 'GIT_COMMITTER_IDENT')

    def blob_hash(self, revision, path):
        result = self.run('show', f'{revision}:{path}', binary=True, check=False)
        return history.digest(result.stdout) if result.returncode == 0 else None

    def clean(self, paths):
        for path in paths:
            status = self.run('status', '--porcelain=v1', '--untracked-files=all', '--', path)
            require(not status, f'Existing edits in removal target: {path}')
            require(self.blob_hash('HEAD', path) == file_hash(self.repo / path),
                    f'Removal target is not committed: {path}')

    def containing_commit(self, path):
        if self.blob_hash('HEAD', path) is None:
            return None
        return self.run('log', '-1', '--format=%H', '--', path).strip()

    def commit(self, paths, message):
        # --only keeps unrelated staged entries out of the commit and in the index.
        self.run('add', '--', *paths)
        self.run('commit', '--only', '--file=-', '--', *paths, input=message + '\n')
        return self.run('rev-parse', 'HEAD').strip()


def file_hash(path):
    require(not path.is_symlink(), f'Symlink in removal target: {path}')
    return history.sha(path) if path.exists() else None


def find_inputs(fixtures, selector, leaf=None):
    leaves = discover(fixtures)
    if leaf is not None:
        leaf = Path(leaf).resolve()
        require(leaf in leaves, f'Not an active collection: {leaf}')
        leaves = [leaf]
    digest = selector.removeprefix('sha256:')
    is_hash = re.fullmatch('[0-9a-f]{64}', digest) is not None
    active, removed = [], []
    for root in leaves:
        def matches(row):
            return (row['byte_sha256'] == digest if is_hash else
                    selector == row['file'] or Path(selector).resolve() == root / row['file'])
        manifest = json.loads((root / 'manifest.json').read_text())
        active.extend((root, row) for row in manifest['images'] if matches(row))
        removed.extend((root, entry) for entry in history.history(root)
                       if entry['kind'] == 'removal' and matches(entry['receipt']['image']))
    require(active or removed, f'No input matches: {selector}')
    if not is_hash:
        candidates = active or [(root, entry['receipt']['image']) for root, entry in removed]
        require(len(candidates) == 1, 'Ambiguous input; use a hash or --leaf and an images/ path: ' +
                ', '.join(str(root / row['file']) for root, row in candidates))
        root, row = candidates[0]
        scope = dict(image_id='sha256:' + row['byte_sha256'], leaf=str(root.relative_to(fixtures.parent)), file=row['file'])
    else:
        scope = dict(image_id='sha256:' + digest,
                     leaf=str(leaf.relative_to(fixtures.parent)) if leaf is not None else None, file=None)
    return scope, active, removed


def load_plan(path):
    try:
        require(not path.is_symlink(), f'Symlinked removal operation: {path}')
        plan = json.loads(path.read_text())
        require(plan['schema_version'] == 1 and plan['checksum'] == history.digest(history.encode(
            {key: value for key, value in plan.items() if key != 'checksum'})), 'Checksum or schema differs')
        return plan
    except (ValueError, KeyError, TypeError) as error:
        raise ValueError(f'Damaged removal operation {path}: {error}') from error


def plan_removal(fixtures, scope, active, reason, message):
    repo = fixtures.parent
    operation = 'remove-' + uuid.uuid4().hex
    path = fixtures / OPERATIONS / (operation + '.json')
    before, states, targets, manifests = {}, {}, [], {}
    generated = [fixtures / 'COLLECTIONS.md', fixtures / 'INDEX.csv']
    for root in sorted({root for root, _ in active}):
        check_layout(root)
        catalogs = history.catalogs(root)
        generated.append(root / 'README.md')
        initial = dict(catalogs)
        number = sum(entry['kind'] == 'removal' for entry in history.history(root))
        for _, row in (item for item in active if item[0] == root):
            # Validate bytes and archive destination for every alias before changing any.
            history.remove(root, row, reason, dry_run=True)
            number += 1
            receipt = root / 'provenance/removals' / f'{number:04d}'
            targets.append(dict(leaf=root.relative_to(repo).as_posix(), image=row,
                                receipt=(receipt / 'receipt.json').relative_to(repo).as_posix()))
            for name in catalogs:
                before[(receipt / 'before' / name).relative_to(repo).as_posix()] = None
            before[(receipt / 'receipt.json').relative_to(repo).as_posix()] = None
            catalogs = history.project_removal(catalogs, row)
            for name, raw in catalogs.items():
                rel = (root / name).relative_to(repo).as_posix()
                states.setdefault(rel, set()).update((history.digest(initial[name]), history.digest(raw)))
        for name, raw in initial.items():
            # Receipts pin unchanged catalogs too: do not freeze somebody else's
            # uncommitted source/catalog edits into a removal history.
            before[(root / name).relative_to(repo).as_posix()] = history.digest(raw)
        manifests[root] = json.loads(catalogs['manifest.json'])
    for target in generated:
        before[target.relative_to(repo).as_posix()] = file_hash(target)
    before[path.relative_to(repo).as_posix()] = None
    for name in before:
        history.safe(repo, name)
    projected = collection_totals.generated_files(fixtures, manifests=manifests)
    plan = dict(schema_version=1, operation=operation, scope=scope, reason=reason,
                commit_message=message, targets=targets, before_sha256=before,
                catalog_states={p: sorted(values) for p, values in states.items() if p in before},
                generated_after_sha256={p.relative_to(repo).as_posix(): history.digest(projected[p].encode())
                                        for p in generated})
    plan['checksum'] = history.digest(history.encode(plan))
    return path, plan


def check_pending(git, path, plan, fixtures):
    """Accept only the pinned baseline or this operation's documented progress."""
    repo = git.repo
    allowed = {name: {sha} for name, sha in plan['before_sha256'].items()}
    for name, hashes in plan['catalog_states'].items():
        allowed[name].update(hashes)
    for name, expected in plan['generated_after_sha256'].items():
        allowed[name].add(expected)
    allowed[path.relative_to(repo).as_posix()] = {history.digest(history.encode(plan))}
    for target in plan['targets']:
        receipt = repo / target['receipt']
        if receipt.exists():
            root = repo / target['leaf']
            record = history.load_record(root, 'removal', receipt.parent)
            require(record['receipt'].get('operation') == plan['operation'] and
                    record['receipt']['image'] == target['image'] and record['receipt']['reason'] == plan['reason'],
                    f'Removal receipt does not belong to this operation: {receipt}')
            allowed[target['receipt']] = {file_hash(receipt)}
            for name, raw in record['before'].items():
                allowed[(receipt.parent / 'before' / name).relative_to(repo).as_posix()] = {history.digest(raw)}
    for name, original in plan['before_sha256'].items():
        history.safe(repo, name)
        current = file_hash(repo / name)
        require(current in allowed[name], f'Unexpected edits in pending removal: {name}')
        require(git.blob_hash('HEAD', name) == original, f'Committed removal target changed during recovery: {name}')
        require(git.blob_hash('', name) in {original, current}, f'Unexpected staged edits in pending removal: {name}')


def validate_removal(fixtures, scope, leaves):
    for leaf in leaves:
        check_layout(fixtures.parent / leaf)
    collection_totals.update(fixtures, check=True)
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'Sampler'))
    import sampler
    inventory = sampler.build_inventory(fixtures.parent)
    remaining = [alias for image in inventory['population']['images'] if image['image_id'] == scope['image_id']
                 for alias in image['aliases']]
    scoped = [alias for alias in remaining if (scope['leaf'] is None or alias['fixture_path'] == scope['leaf'])
              and (scope['file'] is None or alias['path'] == scope['leaf'] + '/' + scope['file'])]
    require(not scoped, f'Removed image is still in the active sampler inventory: {scope["image_id"]}')
    require(not any(leaf['status'] == 'excluded' and leaf['fixture_path'] in leaves
                    for leaf in inventory['population']['leaves']), 'An affected collection was excluded from the sampler')
    return dict(collections='passed', generated_files='current', sampler='passed',
                remaining_aliases=len(remaining), excluded_from_sampling=not remaining)


def remove_and_commit(fixtures, selector, reason, *, leaf=None, commit_message=None, dry_run=False):
    """Return a JSON-ready completion or incomplete-operation report; never hide partial removal."""
    fixtures = Path(fixtures).resolve()
    git = Git(fixtures.parent)
    git.prepare()
    require(reason.strip(), 'A removal reason is required')
    require(commit_message is None or commit_message.strip(), 'A commit message must not be empty')
    scope, active, removed = find_inputs(fixtures, selector, leaf)
    plans = [(path, load_plan(path)) for path in sorted((fixtures / OPERATIONS).glob('*.json'))]
    pending = [(path, plan) for path, plan in plans if git.containing_commit(path.relative_to(git.repo).as_posix()) is None]
    require(len(pending) <= 1, 'Multiple unfinished removal operations; inspect ' + str(fixtures / OPERATIONS))
    if pending:
        path, plan = pending[0]
        require(plan['scope'] == scope, f'Finish the pending removal first: {path} ({plan["scope"]["image_id"]})')
        require(plan['reason'] == reason and (commit_message is None or plan['commit_message'] == commit_message),
                f'Retry with the original reason and commit message recorded in {path}')
        check_pending(git, path, plan, fixtures)
    elif not active:
        leaves = {root.relative_to(git.repo).as_posix() for root, _ in removed}
        checks = validate_removal(fixtures, scope, leaves)
        receipts = [(entry['entry'] / 'receipt.json').relative_to(git.repo).as_posix() for _, entry in removed]
        git.clean(receipts)
        previous = [(path, plan) for path, plan in plans if plan['scope'] == scope]
        for _, plan in previous:
            git.clean(plan['before_sha256'])
        commit = (git.run('log', '-1', '--format=%H', '--',
                         *(path.relative_to(git.repo).as_posix() for path, _ in previous)).strip()
                  if previous else git.run('rev-parse', 'HEAD').strip())
        return dict(schema_version=1, status='already_removed', complete=True, image_id=scope['image_id'],
                    checks=checks, receipts=receipts, changed_files=[], commit=commit)
    else:
        collection_totals.update(fixtures, check=True)
        path, plan = plan_removal(fixtures, scope, active, reason, commit_message or reason)
        git.clean(plan['before_sha256'])
    result = dict(schema_version=1, status='planned' if dry_run else 'incomplete', complete=False,
                  image_id=scope['image_id'], scope=scope, operation=str(path),
                  receipts=[target['receipt'] for target in plan['targets']],
                  changed_files=[], checks=None, commit=None)
    if dry_run:
        result['changed_files'] = sorted(plan['before_sha256'])
        return result
    try:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            history.atomic_write(path, history.encode(plan))
        for target in plan['targets']:
            if not (git.repo / target['receipt']).exists():
                history.remove(git.repo / target['leaf'], target['image'], plan['reason'], operation=plan['operation'])
        # A failed generation may have replaced just some outputs. The immutable plan
        # lets the next invocation recognize those exact bytes and finish the rest.
        for target, content in collection_totals.generated_files(fixtures).items():
            name = target.relative_to(git.repo).as_posix()
            expected = plan['generated_after_sha256'].get(name)
            require(history.digest(content.encode()) == expected if expected is not None else
                    content == target.read_text(), f'Generated output changed outside the removal plan: {name}')
        collection_totals.update(fixtures)
        result['checks'] = validate_removal(fixtures, scope, {target['leaf'] for target in plan['targets']})
        check_pending(git, path, plan, fixtures)
        paths = sorted(name for name, old in plan['before_sha256'].items() if file_hash(git.repo / name) != old)
        result['changed_files'] = paths
        result['commit'] = git.commit(paths, plan['commit_message'])
        for name in paths:
            require(git.blob_hash('HEAD', name) == file_hash(git.repo / name), f'Commit differs from checked file: {name}')
        result.update(status='removed' if active else 'already_removed', complete=True)
    except (ValueError, OSError, KeyError) as error:
        result['error'] = str(error)
        result['changed_files'] = []
        for name, old in plan['before_sha256'].items():
            try:
                if file_hash(git.repo / name) != old:
                    result['changed_files'].append(name)
            except (ValueError, OSError) as inspection_error:
                result.setdefault('inspection_errors', []).append(f'{name}: {inspection_error}')
        result['next_step'] = f'Preserve this report and retry the same removal command to finish {path}.'
    return result
