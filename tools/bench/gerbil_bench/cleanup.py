import json
import re
import shutil

from .storage import atomic_json, digest, fingerprint, lease, relative


def plan(root, identifiers):
    """Only managed project copies are disposable; receipts, logs and inputs survive."""
    root = root.resolve()
    base = root / '.data/bench/runs'
    if base.resolve() != base:
        raise ValueError('managed root ancestors may not be symlinks')
    receipts = list(base.glob('*/receipt.json'))
    protected = []
    for receipt in receipts:
        record = json.loads(receipt.read_text())
        protected.extend(relative(root, path) for path in record['protectedPaths'])
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
            if project.is_symlink() or any(project == path or project.is_relative_to(path) or
                                          path.is_relative_to(project) for path in protected):
                raise ValueError('protected toolchain or symlink target')
            targets.append(dict(path=str(project.relative_to(root)), receiptSha256=digest(receipt),
                                **fingerprint(project)))
    return dict(schema=1, action='remove-managed-project-copies', targets=targets,
                reclaimableBytes=sum(target['bytes'] for target in targets))


def apply(root, plan_path, expected_sha):
    if digest(plan_path) != expected_sha:
        raise ValueError('plan approval digest mismatch')
    requested = json.loads(plan_path.read_text())
    identifiers = sorted({target['path'].split('/')[3] for target in requested['targets']})
    with lease(root, exclusive=True):
        current = plan(root, identifiers)
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
