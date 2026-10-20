"""Unified CLI for the migrated isolated experiment workflows."""
import argparse
import importlib
import sys


COMMANDS = {
    'tool-entry': 'experiment_framework.tool_entry',
    'stdlib': 'run_stdlib_rebuild',
    'artifacts': 'verify_stdlib_rebuild_artifacts',
    'counters': 'run_stdlib_counter_profile',
    'counter-summary': 'summarize_stdlib_counter_profile',
    'counter-stacks': 'correlate_stdlib_counter_stacks',
    'compiler-frame': 'experiment_framework.compiler',
    'register-branch': 'audit_gvm_register_layout',
    'native-layout': 'audit_embedded_host_distance',
    'runtime-io': 'experiment_framework.runtime_io',
    'spawn-semantics': 'experiment_framework.spawn',
    'relink': 'experiment_framework.link',
    'retained': 'run_d1510_progressive',
    'three-lines': 'summarize_three_time_gates',
    'atomic': 'run_mcp_atomic_case',
    'compiler-metadata': 'experiment_framework.metadata',
    'resources': 'experiment_framework.resources',
    'hash-layout': 'experiment_framework.hash_layout',
    'native-lines': 'aggregate_native_cpu_lines',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=COMMANDS)
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    original = sys.argv
    try:
        sys.argv = [original[0] + ' ' + args.command, *args.arguments]
        return importlib.import_module(COMMANDS[args.command]).main()
    finally:
        sys.argv = original


if __name__ == '__main__':
    raise SystemExit(main())
