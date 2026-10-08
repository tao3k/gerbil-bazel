#!/usr/bin/env python3
"""Package-neutral cold build/test qualification and reviewed artifact cleanup."""
import argparse
import json
from pathlib import Path

from gerbil_bench import cleanup, inventory, runner
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
    plan = commands.add_parser('cleanup-plan')
    plan.add_argument('--run', action='append', required=True)
    plan.add_argument('--output', required=True)
    apply = commands.add_parser('cleanup-apply')
    apply.add_argument('--plan', required=True)
    apply.add_argument('--sha256', required=True)
    scan = commands.add_parser('inventory')
    scan.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'run':
        receipt = runner.run(root, relative(root, args.profile), relative(root, args.toolchain), args.id, args.rounds)
        print(json.dumps({key: receipt[key] for key in ('package', 'decision', 'workers', 'runs')}))
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
        print(json.dumps(cleanup.apply(root, path, args.sha256)))
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
