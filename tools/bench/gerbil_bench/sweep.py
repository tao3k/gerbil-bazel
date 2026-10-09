"""Bounded repeated retirement using the same reviewed tree plan/apply contracts."""
from pathlib import Path
import json

from . import trees
from .storage import atomic_json, digest, lease, relative


def sweep(root, identifier, *, days=7, batches=1, batch=20, apply=False, exclude=()):
    root = root.resolve()
    if not identifier or Path(identifier).name != identifier or identifier in ('.', '..'):
        raise ValueError('one cleanup identifier required')
    if not 1 <= batches <= 100:
        raise ValueError('bounded cleanup batch count required')
    directory = relative(root, '.data/bench/cleanup/' + identifier)
    directory.mkdir(parents=True, exist_ok=False)
    receipt = dict(schema=1, state='running', complete=False, applied=apply, batches=[],
                   removedTargets=0, removedLogicalBytes=0)
    path = directory / 'receipt.json'
    atomic_json(path, receipt)
    preview_exclusions = list(exclude)
    try:
        for index in range(batches):
            plan_path = directory / ('plan-%03d.json' % index)
            with lease(root, exclusive=True):
                value = trees.plan(root, days=days, batch=batch, exclude=preview_exclusions)
                atomic_json(plan_path, value)
            row = dict(plan=str(plan_path.relative_to(root)), sha256=digest(plan_path),
                       targets=len(value['targets']))
            receipt['batches'].append(row)
            atomic_json(path, receipt)
            if not value['targets']:
                break
            if not apply:
                preview_exclusions.extend(target['path'] for target in value['targets'])
                continue
            try:
                result = trees.apply(root, plan_path, row['sha256'])
            finally:
                applied = plan_path.with_name(plan_path.stem + '-applied.json')
                if applied.is_file():
                    result = json.loads(applied.read_text())
                    row['complete'] = result['complete']
                    row['removedTargets'] = len(result['removed'])
                    row['removedLogicalBytes'] = result['removedLogicalBytes']
                    row['observedAvailableDeltaBytes'] = result['observedAvailableDeltaBytes']
                    receipt['removedTargets'] += row['removedTargets']
                    receipt['removedLogicalBytes'] += row['removedLogicalBytes']
                    atomic_json(path, receipt)
            if not result['complete']:
                raise ValueError('incomplete cleanup batch; stop sweep')
        receipt['complete'] = True
    except BaseException as error:
        receipt['error'] = type(error).__name__ + ': ' + str(error)
        raise
    finally:
        receipt['state'] = 'terminal'
        atomic_json(path, receipt)
    return receipt
