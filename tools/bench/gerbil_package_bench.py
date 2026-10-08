#!/usr/bin/env python3
"""Package-neutral cold build/test qualification and reviewed artifact cleanup."""
import argparse
import json
from pathlib import Path

from gerbil_bench import cleanup, dumps, inventory, retired, runner, trees
from gerbil_bench.storage import atomic_json, digest, lease, relative


def main():
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run')
    run.add_argument('--profile', required=True)
    run.add_argument('--toolchain', required=True)
    run.add_argument('--id', required=True)
    run.add_argument('--rounds', type=int, default=3)
    run.add_argument('--retention', choices=('receipts', 'failed', 'all'), default='receipts')
    plan = commands.add_parser('cleanup-plan')
    plan.add_argument('--run', action='append', required=True)
    plan.add_argument('--output', required=True)
    apply = commands.add_parser('cleanup-apply')
    apply.add_argument('--plan', required=True)
    apply.add_argument('--sha256', required=True)
    scan = commands.add_parser('inventory')
    scan.add_argument('--output', required=True)
    legacy = commands.add_parser('dump-plan')
    legacy.add_argument('--directory', action='append', required=True)
    legacy.add_argument('--output', required=True)
    cache = commands.add_parser('cache-plan')
    cache.add_argument('--directory', action='append', required=True)
    cache.add_argument('--output', required=True)
    old = commands.add_parser('retired-plan')
    old.add_argument('--older-days', type=int, default=7)
    old.add_argument('--scan-seconds', type=float, default=30)
    old.add_argument('--output', required=True)
    tree = commands.add_parser('tree-plan')
    tree.add_argument('--older-days', type=int, default=7)
    tree.add_argument('--batch', type=int, default=20)
    tree.add_argument('--completed', action='store_true')
    tree.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'run':
        receipt = runner.run(root, relative(root, args.profile), relative(root, args.toolchain),
                             args.id, args.rounds, args.retention)
        print(json.dumps({key: receipt[key] for key in ('package', 'decision', 'workers', 'runs', 'retention')}))
        return 0 if receipt['decision'] == 'ALLOW' else 1
    if args.command == 'cleanup-plan':
        output = relative(root, args.output)
        if not output.is_relative_to(root / '.data') or output.exists():
            parser.error('fresh .data plan output required')
        with lease(root, exclusive=True):
            value = cleanup.plan(root, args.run)
            atomic_json(output, value)
        print(json.dumps(dict(**value, planSha256=digest(output))))
    elif args.command == 'cleanup-apply':
        path = relative(root, args.plan)
        if not path.is_relative_to(root / '.data'):
            parser.error('plan must be in .data')
        action = json.loads(path.read_text())['action']
        operation = (trees.apply if action == 'retire-numbered-experiment-trees' else
                     retired.apply if action == 'remove-retired-generated-artifacts' else
                     dumps.apply if action in ('remove-legacy-gnu-compiler-dumps',
                                               'remove-legacy-package-build-caches') else cleanup.apply)
        value = operation(root, path, args.sha256)
        print(json.dumps(dict(state=value['state'], complete=value['complete'],
                              removedTargets=len(value['removed']),
                              removedLogicalBytes=(sum(row['bytes'] for row in value['removed'])
                                                   if all('bytes' in row for row in value['removed']) else None),
                              observedAvailableDeltaBytes=value.get('observedAvailableDeltaBytes'))))
    elif args.command == 'tree-plan':
        output = relative(root, args.output)
        if not output.is_relative_to(root / '.data') or output.exists():
            parser.error('fresh .data plan output required')
        with lease(root, exclusive=True):
            value = trees.plan(root, days=args.older_days, batch=args.batch, completed=args.completed)
            atomic_json(output, value)
        print(json.dumps(dict(targets=len(value['targets']), planSha256=digest(output))))
    elif args.command == 'retired-plan':
        output = relative(root, args.output)
        if not output.is_relative_to(root / '.data') or output.exists():
            parser.error('fresh .data plan output required')
        with lease(root, exclusive=True):
            value = retired.plan(root, days=args.older_days, seconds=args.scan_seconds)
            atomic_json(output, value)
        print(json.dumps(dict(complete=value['complete'], targets=len(value['targets']),
                              reclaimableBytes=value['reclaimableBytes'], planSha256=digest(output))))
    elif args.command in ('dump-plan', 'cache-plan'):
        output = relative(root, args.output)
        if not output.is_relative_to(root / '.data') or output.exists():
            parser.error('fresh .data plan output required')
        with lease(root, exclusive=True):
            value = dumps.plan(root, args.directory, kind='dumps' if args.command == 'dump-plan' else 'package-caches')
            atomic_json(output, value)
        print(json.dumps(dict(complete=value['complete'], files=len(value['targets']),
                              reclaimableBytes=value['reclaimableBytes'], planSha256=digest(output))))
    else:
        output = relative(root, args.output)
        if not output.is_relative_to(root / '.data') or output.exists():
            parser.error('fresh .data inventory output required')
        value = inventory.inventory(root)
        atomic_json(output, value)
        print(json.dumps({key: value[key] for key in ('complete', 'observedBytes', 'unvisitedEntries', 'wallSeconds')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
