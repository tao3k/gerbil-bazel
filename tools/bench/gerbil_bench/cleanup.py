import json
import re
import shutil
import time

from .storage import atomic_json, digest, fingerprint, lease, relative
from .protection import protected_paths


def plan(root, identifiers, *, keep_failed=False):
    """Only managed project copies are disposable; receipts, logs and inputs survive."""
    root = root.resolve()
    base = root / '.data/bench/runs'
    if base.resolve() != base:
        raise ValueError('managed root ancestors may not be symlinks')
    protected = list(protected_paths(root))
    deadline = time.monotonic() + 15
    targets = []
    for identifier in identifiers:
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', identifier):
            raise ValueError('safe direct run ID required')
        run = relative(root, '.data/bench/runs/' + identifier)
        if run.parent != base or run.is_symlink():
            raise ValueError('direct managed run required')
        receipt = run / 'receipt.json'
        record = json.loads(receipt.read_text())
        if record['state'] != 'terminal':
            raise ValueError('nonterminal run is protected')
        for project in sorted(run.glob('*/project')):
            if not project.parent.name.isdecimal():
                raise ValueError('only numbered managed round projects may be removed')
            if keep_failed and not any(row.get('index') == int(project.parent.name) and row.get('passed')
                                       for row in record.get('runs', [])):
                continue
            if project.is_symlink() or any(project == path or project.is_relative_to(path) or
                                          path.is_relative_to(project) for path in protected):
                raise ValueError('protected toolchain or symlink target')
            targets.append(dict(path=str(project.relative_to(root)), receiptSha256=digest(receipt),
                                **fingerprint(project, deadline=deadline)))
    return dict(schema=1, action='remove-managed-project-copies', targets=targets,
                keepFailed=keep_failed,
                reclaimableBytes=sum(target['bytes'] for target in targets))


def apply(root, plan_path, expected_sha):
    if digest(plan_path) != expected_sha:
        raise ValueError('plan approval digest mismatch')
    requested = json.loads(plan_path.read_text())
    identifiers = sorted({target['path'].split('/')[3] for target in requested['targets']})
    with lease(root, exclusive=True):
        current = plan(root, identifiers, keep_failed=requested.get('keepFailed', False))
        if current != requested:
            raise ValueError('cleanup plan changed; regenerate and review')
        receipt = dict(schema=1, planSha256=expected_sha, removed=[], state='running')
        result_path = plan_path.with_name(plan_path.stem + '-applied.json')
        if result_path.exists():
            raise ValueError('cleanup receipt already exists')
        atomic_json(result_path, receipt)
        try:
            for target in current['targets']:
                shutil.rmtree(relative(root, target['path']))
                receipt['removed'].append(target)
                atomic_json(result_path, receipt)
        finally:
            receipt['state'] = 'terminal'
            receipt['complete'] = len(receipt['removed']) == len(current['targets'])
            atomic_json(result_path, receipt)
    return receipt


def retain(root, identifier, policy):
    """Finalize terminal runs only; concurrent workloads defer cleanup, never get killed."""
    if policy not in ('receipts', 'failed', 'all'):
        raise ValueError('unknown retention policy')
    run = root / '.data/bench/runs' / identifier
    if policy == 'all':
        return dict(policy=policy, state='retained')
    plan_path = run / 'retention-plan.json'
    try:
        with lease(root, exclusive=True):
            value = plan(root, [identifier], keep_failed=policy == 'failed')
            atomic_json(plan_path, value)
        result = apply(root, plan_path, digest(plan_path))
        return dict(policy=policy, state='cleaned', removedProjects=len(result['removed']),
                    removedLogicalBytes=sum(row['bytes'] for row in result['removed']),
                    receipt=str(plan_path.with_name('retention-plan-applied.json').relative_to(root)))
    except (BlockingIOError, ValueError, OSError) as error:
        return dict(policy=policy, state='deferred', reason=type(error).__name__)
